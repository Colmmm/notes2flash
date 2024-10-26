from aqt.qt import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                         QApplication, QComboBox, QMessageBox, QCheckBox, 
                         QTextEdit, QWidget, QThread, pyqtSignal, QTimer)
from aqt import mw
from aqt.utils import showInfo
from .notes2flash import notes2flash
from .workflow_engine import WorkflowEngine
from aqt.deckbrowser import DeckBrowser
import os
import yaml
import json
import logging

class Notes2FlashWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, workflow_config_path, user_inputs, debug_mode):
        super().__init__()
        self.workflow_config_path = workflow_config_path
        self.user_inputs = user_inputs
        self.debug_mode = debug_mode

    def run(self):
        try:
            result = notes2flash(
                self.workflow_config_path, 
                self.user_inputs, 
                progress_callback=lambda msg: self.progress.emit(msg),
                debug=self.debug_mode
            )
            self.finished.emit(result)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            if self.debug_mode:
                try:
                    with open('notes2flash.log', 'r') as log_file:
                        error_message += "\n\nDebug information:\n" + log_file.read()
                except:
                    error_message += "\n\nCould not read debug log."
            self.error.emit(error_message)

class CustomInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notes2Flash")
        
        self.layout = QVBoxLayout()
        self.input_fields = {}
        self.input_labels = {}

        # Dropdown for Workflow Configuration
        self.workflow_label = QLabel("Select Workflow Configuration:")
        self.layout.addWidget(self.workflow_label)
        self.workflow_dropdown = QComboBox()
        self.populate_workflow_dropdown()
        self.layout.addWidget(self.workflow_dropdown)
        self.workflow_dropdown.currentIndexChanged.connect(self.on_workflow_changed)

        # Container for dynamic input fields
        self.input_container = QWidget()
        self.input_layout = QVBoxLayout(self.input_container)
        self.layout.addWidget(self.input_container)

        # Debug mode checkbox
        self.debug_checkbox = QCheckBox("Enable Debug Mode")
        self.layout.addWidget(self.debug_checkbox)

        # Progress label
        self.progress_label = QLabel("Status: Ready")
        self.layout.addWidget(self.progress_label)

        # Long process notice (hidden initially)
        self.long_process_label = QLabel("Large documents can take a while to process...")
        self.long_process_label.hide()
        self.layout.addWidget(self.long_process_label)

        # Button to confirm
        self.submit_button = QPushButton("Submit")
        self.layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit_data)

        # Set layout to dialog
        self.setLayout(self.layout)

        # Initialize worker to None
        self.worker = None

        # Setup timers
        self.dots_timer = QTimer()
        self.dots_timer.setInterval(500)  # Update every 500ms
        self.dots_timer.timeout.connect(self.update_dots)
        self.dots_count = 0

        self.long_process_timer = QTimer()
        self.long_process_timer.setSingleShot(True)
        self.long_process_timer.timeout.connect(lambda: self.long_process_label.show())

        # Load last used workflow and inputs
        self.load_last_workflow_and_inputs()

    def populate_workflow_dropdown(self):
        workflow_dir = os.path.join(os.path.dirname(__file__), "workflow_configs")
        workflow_files = [f for f in os.listdir(workflow_dir) if f.endswith('.yml')]
        self.workflow_dropdown.addItems(workflow_files)

    def load_last_workflow_and_inputs(self):
        user_inputs = self.load_user_inputs()
        last_workflow = user_inputs.get('last_workflow')
        if last_workflow:
            index = self.workflow_dropdown.findText(last_workflow)
            if index >= 0:
                self.workflow_dropdown.setCurrentIndex(index)
            else:
                self.workflow_dropdown.setCurrentIndex(0)
        else:
            self.workflow_dropdown.setCurrentIndex(0)
        
        # Explicitly call on_workflow_changed to ensure input fields are populated
        self.on_workflow_changed(self.workflow_dropdown.currentIndex())

    def update_dots(self):
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.submit_button.setText(f"Processing{dots}")

    def on_workflow_changed(self, index):
        # Clear existing input fields and labels
        for widget in self.input_fields.values():
            self.input_layout.removeWidget(widget)
            widget.deleteLater()
        for widget in self.input_labels.values():
            self.input_layout.removeWidget(widget)
            widget.deleteLater()
        self.input_fields.clear()
        self.input_labels.clear()

        # Load the selected workflow configuration
        workflow_file = self.workflow_dropdown.currentText()
        workflow_path = os.path.join(os.path.dirname(__file__), "workflow_configs", workflow_file)
        try:
            workflow_config = WorkflowEngine.load_workflow_config(workflow_path)
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Error in workflow configuration: {str(e)}")
            return

        # Load saved user inputs for this workflow
        user_inputs = self.load_user_inputs()
        saved_inputs = user_inputs.get(workflow_file, {})

        # Create input fields based on user_inputs in the workflow config
        for input_name in workflow_config.get('user_inputs', []):
            label = QLabel(f"Enter {input_name}:")
            self.input_layout.addWidget(label)
            input_field = QLineEdit()
            input_field.setText(saved_inputs.get(input_name, ""))
            self.input_layout.addWidget(input_field)
            self.input_fields[input_name] = input_field
            self.input_labels[input_name] = label

        # Update the layout to reflect the changes
        self.input_layout.update()

    def submit_data(self):
        workflow_config = self.workflow_dropdown.currentText()
        user_inputs = {name: field.text() for name, field in self.input_fields.items()}

        # Validate inputs
        if any(not value for value in user_inputs.values()):
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        # Save user inputs
        self.save_user_inputs(workflow_config, user_inputs)

        # Start processing animation
        self.submit_button.setEnabled(False)
        self.dots_timer.start()
        
        # Hide the long process label (in case it was shown from a previous run)
        self.long_process_label.hide()
        
        # Start the timer for showing the long process message
        self.long_process_timer.start(5000)  # Show message after 5 seconds

        workflow_config_path = os.path.join(os.path.dirname(__file__), "workflow_configs", workflow_config)
        
        # Create and setup worker thread
        self.worker = Notes2FlashWorker(
            workflow_config_path,
            user_inputs,
            self.debug_checkbox.isChecked()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.start()

    def on_processing_finished(self, result):
        # Stop timers
        self.dots_timer.stop()
        self.long_process_timer.stop()
        
        # Reset UI
        self.submit_button.setEnabled(True)
        self.submit_button.setText("Submit")
        self.long_process_label.hide()
        self.update_progress("Complete")
        
        QMessageBox.information(self, "Success", 
            f"Flashcards generated successfully! {result.get('cards_added', 0)} cards added.")
        self.refresh_anki_decks()
        self.accept()

    def on_processing_error(self, error_message):
        # Stop timers
        self.dots_timer.stop()
        self.long_process_timer.stop()
        
        # Reset UI
        self.submit_button.setEnabled(True)
        self.submit_button.setText("Submit")
        self.long_process_label.hide()
        
        self.show_error_dialog("Error", error_message)

    def update_progress(self, status):
        self.progress_label.setText(f"Status: {status}")

    def refresh_anki_decks(self):
        mw.deckBrowser.refresh()
        mw.reset()

    def show_error_dialog(self, title, message):
        error_dialog = QDialog(self)
        error_dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(message)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        close_button = QPushButton("Close")
        close_button.clicked.connect(error_dialog.accept)
        layout.addWidget(close_button)
        error_dialog.setLayout(layout)
        error_dialog.exec()

    def load_user_inputs(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'user_inputs.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_user_inputs(self, workflow, inputs):
        user_inputs = self.load_user_inputs()
        user_inputs[workflow] = inputs
        user_inputs['last_workflow'] = workflow
        with open(os.path.join(os.path.dirname(__file__), 'user_inputs.json'), 'w') as f:
            json.dump(user_inputs, f)

def show_dialog(parent=None):
    dialog = CustomInputDialog(parent)
    dialog.exec()
