import logging

logger = logging.getLogger('syncsketchGUI')
print("logger: {}".format(logger))
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s]',
                              "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)

logger.addHandler(ch)
# prevent logging from bubbling up to maya's logger
logger.propagate = 0

from .settings import CACHE_YAML, VIEWPORT_YAML, PRESET_YAML

# ======================================================================
# Module Public Interface

from .actions import install_shelf

# These functions are used from within the Shelf Tools
from .actions import show_main_window as show_menu_window  # Supports older shelf installations
from .actions import show_main_window
from .actions import record
from .actions import play
from .actions import upload
from .actions import show_download_window
from .actions import cycle_viewport_presets
from .actions import show_viewport_preset_window


def reload_toolkit():
    """
    Exists to support older shelf installations. Might become deprecated.
    """
    pass


# ======================================================================
# Module Utilities

def _reload_toolkit():
    """
    Convenient Method to reload
    """
    from syncsketchGUI.lib import path
    from syncsketchGUI.lib import database
    from syncsketchGUI.lib import video
    from syncsketchGUI.lib import user
    import gui

    reload(database)
    reload(video)
    reload(gui)
    reload(path)
    reload(user)

    from syncsketchGUI.lib.maya import menu as maya_menu
    from syncsketchGUI.lib.maya import scene as maya_scene
    from syncsketchGUI.lib.maya import shelf as maya_shelf
    from syncsketchGUI.lib.maya import timeline as maya_timeline
    from syncsketchGUI.vendor import capture as maya_capture

    reload(maya_menu)
    reload(maya_scene)
    reload(maya_shelf)
    reload(maya_capture)
    reload(maya_timeline)
