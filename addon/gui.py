from aqt.qt import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from aqt.utils import showInfo
from .notes2flash import notes2flash
import subprocess

class CustomInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Flashcard Generator")
        
        # Create layout
        layout = QVBoxLayout()

        # Input for Google Doc ID
        self.google_doc_label = QLabel("Enter Google Doc ID:")
        layout.addWidget(self.google_doc_label)
        self.google_doc_input = QLineEdit()
        layout.addWidget(self.google_doc_input)

        # Input for Anki Deck Name
        self.deck_name_label = QLabel("Enter Anki Deck Name:")
        layout.addWidget(self.deck_name_label)
        self.deck_name_input = QLineEdit()
        layout.addWidget(self.deck_name_input)

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
        
        # Show info with the provided inputs
        showInfo(f"Google Doc ID: {google_doc_id}\nDeck Name: {deck_name}")
        
        # Call backend function to start notes2flash
        notes2flash(google_doc_id, deck_name)


