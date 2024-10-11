from aqt import mw
from aqt.utils import showInfo
from PyQt6.QtWidgets import QAction
from .gui import CustomInputDialog

def open_input_dialog():
    """Function to open the custom input dialog."""
    dialog = CustomInputDialog()
    dialog.exec_()

def setup_menu():
    """Add the custom flashcard generator to Anki's Tools menu."""
    action = QAction("Cards2Flash Generator", mw)
    action.triggered.connect(open_input_dialog)
    mw.form.menuTools.addAction(action)

# Setup the menu when the add-on is loaded
setup_menu()
