import importlib
import logging

from .lib import database
from .lib import path
from .lib.gui import qt_utils
from .settings import CACHE_YAML, VIEWPORT_PRESET_YAML

logger = logging.getLogger("syncsketchGUI")


def record():
    from .devices import recoder

    return recoder.record()


def play():
    from .devices import player

    player.play()


def upload():
    from .devices import uploader

    return uploader.upload()


def install_shelf():
    _get_maya_shelf().install()


def uninstall_shelf():
    _get_maya_shelf().uninstall()


def add_timeline_context_menu():
    _get_maya_timeline().add_context_menu_item()


def remove_timeline_context_menu():
    _get_maya_timeline().remove_context_menu_item()


def build_menu():
    _get_maya_menu().build_menu()


def delete_menu():
    _get_maya_menu().delete_menu()


def refresh_menu_state():
    _get_maya_menu().refresh_menu_state()


def save_viewport_preset(preset_name):
    # TODO: move logic to a lower layer
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    _get_maya_scene().save_viewport_preset(cache, preset_name)


def new_viewport_preset(preset_name=None, source_preset=None):
    # TODO: move logic to a lower layer
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    _get_maya_scene().new_viewport_preset(cache, preset_name=None, source_preset="1", panel=None)


def apply_viewport_preset(preset_name):
    # TODO: move logic to a lower layer
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    _get_maya_scene().apply_viewport_preset(cache, preset_name)


def cycle_viewport_presets():
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    presets = list(database._parse_yaml(cache).keys())
    current_viewport_preset = database.read_cache('current_viewport_preset')

    try:
        next_preset_index = presets.index(current_viewport_preset) + 1
        next_preset = presets[next_preset_index]
    except ValueError:
        next_preset = presets[0]
    except IndexError:
        next_preset = presets[0]

    database.save_cache('current_viewport_preset', next_preset, yaml_file=CACHE_YAML)
    _get_maya_scene().apply_viewport_preset(cache, next_preset)


def show_login_window():
    from .lib.gui.web import LoginView

    _show_persistent_widget(LoginView)


def show_syncsketch_browser_window():
    from .lib.gui import qt_browser

    _show_persistent_widget(qt_browser.ReviewBrowserWidget)


def show_main_window():
    from .lib.gui import qt_main_window

    _show_persistent_widget(qt_main_window.MenuWindow)


def show_download_window():
    from .lib.gui import qt_download

    _show_persistent_widget(qt_download.DownloadWindow)


def show_viewport_preset_window():
    from .lib.gui import qt_viewport_preset

    _show_persistent_widget(qt_viewport_preset.ViewportPresetWindow)


def playblast():
    from .devices import recoder

    return recoder.record(upload_after_creation=False, play_after_creation=None, show_success_msg=True)


def playblast_with_options():
    import syncsketchGUI

    syncsketchGUI.show_main_window()


def playblast_and_upload():
    from .devices import recoder

    return recoder.record(upload_after_creation=True, play_after_creation=False, show_success_msg=True)


def playblast_and_upload_with_options():
    import syncsketchGUI

    syncsketchGUI.show_main_window()


def _show_persistent_widget(widget_cls):
    widget = qt_utils.get_persistent_widget(widget_cls)
    widget.show()


def _get_maya_scene():
    return importlib.import_module("syncsketchGUI.lib.maya.scene")


def _get_maya_shelf():
    return importlib.import_module("syncsketchGUI.lib.maya.shelf")


def _get_maya_timeline():
    return importlib.import_module("syncsketchGUI.lib.maya.timeline")


def _get_maya_menu():
    return importlib.import_module("syncsketchGUI.lib.maya.menu")
