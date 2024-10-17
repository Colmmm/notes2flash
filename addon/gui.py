from aqt.qt import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QApplication, QComboBox, QMessageBox
from aqt import mw
from aqt.utils import showInfo
from .notes2flash import notes2flash
from .workflow_engine import WorkflowEngine
from aqt.deckbrowser import DeckBrowser
import os
import yaml

class CustomInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Flashcard Generator")
        
        self.layout = QVBoxLayout()
        self.input_fields = {}

        # Dropdown for Workflow Configuration
        self.workflow_label = QLabel("Select Workflow Configuration:")
        self.layout.addWidget(self.workflow_label)
        self.workflow_dropdown = QComboBox()
        self.populate_workflow_dropdown()
        self.layout.addWidget(self.workflow_dropdown)
        self.workflow_dropdown.currentIndexChanged.connect(self.on_workflow_changed)

        # Progress label
        self.progress_label = QLabel("Status: Ready")
        self.layout.addWidget(self.progress_label)

        # Button to confirm
        self.submit_button = QPushButton("Submit")
        self.layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit_data)

        # Set layout to dialog
        self.setLayout(self.layout)

        # Initialize with the first workflow
        self.on_workflow_changed(0)

    def populate_workflow_dropdown(self):
        workflow_dir = os.path.join(os.path.dirname(__file__), "workflow_configs")
        workflow_files = [f for f in os.listdir(workflow_dir) if f.endswith('.yml')]
        self.workflow_dropdown.addItems(workflow_files)

    def on_workflow_changed(self, index):
        # Clear existing input fields
        for widget in self.input_fields.values():
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.input_fields.clear()

        # Load the selected workflow configuration
        workflow_file = self.workflow_dropdown.currentText()
        workflow_path = os.path.join(os.path.dirname(__file__), "workflow_configs", workflow_file)
        try:
            workflow_config = WorkflowEngine.load_workflow_config(workflow_path)
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Error in workflow configuration: {str(e)}")
            return

        # Create input fields based on user_inputs in the workflow config
        for input_name in workflow_config.get('user_inputs', []):
            label = QLabel(f"Enter {input_name}:")
            self.layout.insertWidget(self.layout.count() - 2, label)  # Insert before progress label
            input_field = QLineEdit()
            self.layout.insertWidget(self.layout.count() - 2, input_field)
            self.input_fields[input_name] = input_field

    def submit_data(self):
        workflow_config = self.workflow_dropdown.currentText()
        user_inputs = {name: field.text() for name, field in self.input_fields.items()}

        # Validate inputs
        if any(not value for value in user_inputs.values()):
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        # Disable submit button and change text
        self.submit_button.setEnabled(False)
        self.submit_button.setText("Processing...")

        try:
            # Get full path to workflow config
            workflow_config_path = os.path.join(os.path.dirname(__file__), "workflow_configs", workflow_config)

            # Call backend function to start notes2flash
            self.update_progress("Processing...")
            result = notes2flash(workflow_config_path, user_inputs, progress_callback=self.update_progress)
            self.update_progress("Complete")
            QMessageBox.information(self, "Success", f"Flashcards generated successfully! {result.get('cards_added', 0)} cards added.")
            self.refresh_anki_decks()
            self.accept()  # Close the dialog
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            # Re-enable submit button and restore text
            self.submit_button.setEnabled(True)
            self.submit_button.setText("Submit")

    def update_progress(self, status):
        self.progress_label.setText(f"Status: {status}")
        QApplication.processEvents()  # Force GUI update

    def refresh_anki_decks(self):
        mw.deckBrowser.refresh()
        mw.reset()

def show_dialog(parent=None):
    dialog = CustomInputDialog(parent)
    dialog.exec()
