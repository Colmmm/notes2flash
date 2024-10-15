from aqt.qt import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QApplication
from aqt import mw
from aqt.utils import showInfo
from .notes2flash import notes2flash
from aqt.deckbrowser import DeckBrowser

class CustomInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Flashcard Generator")
        
        # Get default values from config
        config = mw.addonManager.getConfig(__name__)
        default_google_doc_id = config.get('default_google_doc_id', '')
        default_anki_deck_name = config.get('default_anki_deck_name', '')
        
        # Create layout
        layout = QVBoxLayout()

        # Input for Google Doc ID
        self.google_doc_label = QLabel("Enter Google Doc ID:")
        layout.addWidget(self.google_doc_label)
        self.google_doc_input = QLineEdit(default_google_doc_id)
        layout.addWidget(self.google_doc_input)

        # Input for Anki Deck Name
        self.deck_name_label = QLabel("Enter Anki Deck Name:")
        layout.addWidget(self.deck_name_label)
        self.deck_name_input = QLineEdit(default_anki_deck_name)
        layout.addWidget(self.deck_name_input)

        # Progress label
        self.progress_label = QLabel("Status: Ready")
        layout.addWidget(self.progress_label)

        # Button to confirm
        self.submit_button = QPushButton("Submit")
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit_data)

        # Set layout to dialog
        self.setLayout(layout)

    def submit_data(self):
        google_doc_id = self.google_doc_input.text()
        deck_name = self.deck_name_input.text()

        # Validate inputs
        if not google_doc_id or not deck_name:
            showInfo("Both fields are required.")
            return

        # Disable submit button and change text
        self.submit_button.setEnabled(False)
        self.submit_button.setText("Processing...")

        try:
            # Call backend function to start notes2flash
            self.update_progress("Processing...")
            notes2flash(google_doc_id, deck_name, progress_callback=self.update_progress)
            self.update_progress("Complete")
            showInfo("Flashcards generated successfully!")
            self.refresh_anki_decks()
            self.accept()  # Close the dialog
        except Exception as e:
            showInfo(f"Error occurred: {e}")
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
