from syncsketchGUI.lib import database

PRESET_YAML = 'syncsketch_preset.yaml'
VIEWPORT_YAML = 'syncsketch_viewport.yaml'
DEFAULT_PRESET = database.read_cache('current_preset')
uploadPlaceHolderStr = "Pick a review/item or paste a SyncSketch URL here"
message_is_not_loggedin = "Please sign into your account by clicking 'Log-In' or create a free Account by clicking 'Sign up'."
message_is_not_connected = "WARNING: Could not connect to SyncSketch. It looks like you may not have an internet connection?"
DEFAULT_VIEWPORT_PRESET = database.read_cache('current_viewport_preset')