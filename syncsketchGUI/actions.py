import logging
import importlib

from .lib import path
from .lib import database
from .lib import user

from .lib.gui import qt_utils


VIEWPORT_PRESET_YAML = 'syncsketch_viewport.yaml' #TODO: Remove global state

logger = logging.getLogger("syncsketchGUI")

def record():
    from .devices import recoder
    recoder.record()

def play():
    from .devices import player
    player.play()

def upload():
    from .devices import uploader
    uploader.upload()

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
    #TODO: move logic to a lower layer
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    _get_maya_scene().save_viewport_preset(cache, preset_name)

def new_viewport_preset(preset_name=None, source_preset=None):
     #TODO: move logic to a lower layer
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    _get_maya_scene().new_viewport_preset(cache, preset_name=None, source_preset="1", panel=None)

def apply_viewport_preset(preset_name):
     #TODO: move logic to a lower layer
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    _get_maya_scene().apply_viewport_preset(cache, preset_name)

def cycle_viewport_presets():
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    presets = database._parse_yaml(cache).keys()
    current_viewport_preset = database.read_cache('current_viewport_preset')
    logger.info(presets)
    l = len(presets)


    i = 0
    if current_viewport_preset in presets:
        for k in range(l):
            i = k
            logger.info("presets[%s] %s"%(i, presets[i]))
            if current_viewport_preset == presets[i]:
                logger.info("%s is a match"%i)
                break
    else:
        i = 0

    i += 1
    if i >= l:
        i = 0

    database.save_cache('current_viewport_preset', presets[i], yaml_file = CACHE_YAML)
    maya_scene.apply_viewport_preset(cache, presets[i])

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

#FIXME
def playblast_and_upload():
    from .lib.gui import qt_dialogs
    from syncsketchGUI.lib.maya import scene as maya_scene
    filepath = maya_scene.playblast()
    if not filepath:
        return

    webm_file = video.convert_to_webm(filepath)
    if not webm_file:
        return

    user_input = gui.InputDialog()
    if not user_input.response:
        return

    if not uploaded_media_url:
        return

    title = 'Upload Successful'
    info_message = 'Your file has successfully been uploaded. Please follow this link:'

    UploadedMediaDialog = qt_dialogs.InfoDialog(title = title, info_text = info_message, media_url = uploaded_media_url.json()['reviewURL'])
    UploadedMediaDialog.exec_()


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