from aqt import mw
from aqt.qt import *
from anki.hooks import addHook
from .gui import show_dialog

def on_notes2flash():
    show_dialog(mw)

action = QAction("Notes2Flash", mw)
action.triggered.connect(on_notes2flash)
mw.form.menuTools.addAction(action)

# Config handling
def update_config(new_config):
    mw.addonManager.writeConfig(__name__, new_config)

def init_config():
    config = mw.addonManager.getConfig(__name__)
    if config is None:
        config = {}
    if 'openrouter_api_key' not in config:
        config['openrouter_api_key'] = ""
        update_config(config)

init_config()
