from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from aqt.utils import showInfo
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
        
        # Call backend function to start the Docker process
        self.start_docker_process(google_doc_id, deck_name)

    def start_docker_process(self, google_doc_id, deck_name):
        """
        Function to trigger the docker processes using the provided Google Doc ID and deck name.
        """
        try:
            # Create a custom env file with user inputs
            with open('user_inputs.env', 'w') as f:
                f.write(f'GOOGLE_DOC_ID={google_doc_id}\n')
                f.write(f'DECK_NAME={deck_name}\n')

            # Start the docker services
            subprocess.run(['docker-compose', 
                            '--env-file user_inputs.env',
                            'up', '-d', 'google-docs-scraper', 'process-notes', 'anki-connect'], check=True)

        except subprocess.CalledProcessError as e:
            showInfo(f"Error running Docker: {e}")

        except Exception as e:
            showInfo(f"An unexpected error occurred: {str(e)}")

