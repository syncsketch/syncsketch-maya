from syncsketchGUI.installScripts import installGui
from syncsketchGUI.installScripts.maintenance import getVersionDifference
import os
import time
import webbrowser
import logging
from syncsketchGUI.lib.gui.syncsketchWidgets import infoDialog
import pprint
from pprint import pformat
from syncsketchGUI.lib import user as user

logger = logging.getLogger('syncsketchGUI')
print("logger: {}".format(logger))
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('[%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s]', "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)

logger.addHandler(ch)
# prevent logging from bubbling up to maya's logger
logger.propagate = 0


# ======================================================================
# Global Variables
WAIT_TIME = 0.1 # seconds
#global upgrade = 0


from syncsketchGUI.lib import user, path
from syncsketchGUI.lib import video, database
from syncsketchGUI.lib.gui import icons, qt_utils, qt_widgets
import gui

# ======================================================================
# Maya Imports
from syncsketchGUI.lib.maya import shelf as maya_shelf, menu as maya_menu
from syncsketchGUI.lib.maya import scene as maya_scene, timeline as maya_timeline

# ======================================================================
# Global Variables

PRESET_YAML = 'syncsketch_preset.yaml'
CACHE_YAML = 'syncsketch_cache.yaml'
VIEWPORT_PRESET_YAML = 'syncsketch_viewport.yaml'

# ======================================================================
# Module Functions


def show_web_login_window():
    gui.show_web_login_window()

def reload_toolkit():
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
    reload(icons)
    reload(user)
    reload(qt_widgets)
    reload(qt_utils)


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

def build_menu():
    maya_menu.build_menu()

def delete_menu():
    maya_menu.delete_menu()

def refresh_menu_state():
    maya_menu.refresh_menu_state()

def show_syncsketch_browser_window():
    gui.show_syncsketch_browser_window()

def show_menu_window():
    return gui.show_menu_window()

def show_download_window():
    gui.show_download_window()

def show_viewport_preset_window():
    gui.show_viewport_preset_window()


def get_current_file():
    # validate file name
    filename = database.read_cache('last_recorded_selection')

    if not filename:
        title = 'No File for Upload'
        message = 'There is no previously recorded video file, please record one first through The Widget'
        qt_widgets.WarningDialog(None, title, message)
        return


    filename = path.sanitize(filename)

    if not os.path.isfile(filename):
        title = 'Not a valid file'
        message = 'Please provide a valid file'
        logger.debug("{} is not a valid file".format(filename))
        qt_widgets.WarningDialog(None, title, message)
        return
    else:
        return filename


def show_success_message(uploaded_item):
    # todo: add offlineMode here as well
    title = 'Upload Successful'
    info_message = 'Your file has successfully been uploaded. Please follow this link:'

    UploadedMediaDialog = infoDialog.InfoDialog(None,
                                          title,
                                          info_message,
                                          uploaded_item)
    UploadedMediaDialog.exec_()


def play(filename = None):
    if not filename:
        filename = get_current_file()
    filename = path.make_safe(filename)
    video.play_in_default_player(filename)
    logger.info('Playing current video: {}'.format(filename.replace('"', '')))


def upload(open_after_upload = None, show_success_msg = False):

    logger.info("open_after_upload Url: {}".format(open_after_upload))
    uploaded_item = _upload()


    if not uploaded_item:
        return

    if open_after_upload is None:
        open_after_upload = True if database.read_cache('ps_open_afterUpload_checkBox') == 'true' else False

    if open_after_upload:
        url = path.make_url_offlineMode(uploaded_item['reviewURL'])
        logger.info("Url: {}".format(url))
        logger.info("Uploaded Item: {}".format(uploaded_item))
        logger.info("Opening Url: {}".format(uploaded_item['reviewURL']))
        webbrowser.open(url, new=2, autoraise=True)


    if not open_after_upload:
        logger.info("uploaded_item: {}".format(uploaded_item))
        show_success_message(path.make_url_offlineMode(uploaded_item['reviewURL']))

    return uploaded_item


def download(current_user = None):
    if not current_user:
        current_user = user.SyncSketchUser()
    review_id = database.read_cache('target_review_id')
    media_id  = database.read_cache('target_media_id')
    logger.info("current_user: %s"%current_user)
    logger.info("target_review_id: %s"%review_id)
    logger.info("target_media_id: %s"%media_id)
    return current_user.download_greasepencil(review_id, media_id )


def downloadVideo(current_user = None, media_id=None):
    if not current_user:
        current_user = user.SyncSketchUser()
    media_id  = media_id or database.read_cache('target_media_id')
    logger.info("current_user: %s"%current_user)
    logger.info("target_media_id: %s"%media_id)
    return current_user.download_converted_video(media_id)


def record(upload_after_creation = None, play_after_creation = None,  show_success_msg = True):
    # This a wrapper function and if called individually should mirror all the same effect as hitting 'record' in the UI
    recordData = {}
    capturedFile = _record()
    logger.info("capturedFile: {}".format(capturedFile))
    capturedFileNoExt, ext = os.path.splitext(capturedFile)
    if capturedFileNoExt[-5:] == '.####':
        #Reencode to quicktime
        recordData["playblast_file"] = video.encodeToH264Mov(
            capturedFile, output_file=capturedFileNoExt[:-5] + ".mov")
        logger.info("reencoded File: {}".format(recordData["playblast_file"]))
        database.dump_cache({"last_recorded_selection": recordData["playblast_file"]})
    
    else:
        recordData["playblast_file"] = capturedFile
    # Post actions

    # To Do - post Recording script call
    if upload_after_creation is None:
        upload_after_creation = True if database.read_cache('ps_upload_after_creation_checkBox') == 'true' else False

    if play_after_creation is None:
        play_after_creation = True if database.read_cache('ps_play_after_creation_checkBox') == 'true' else False

    open_after_creation = True if database.read_cache('ps_open_afterUpload_checkBox') == 'true' else False

    if upload_after_creation:
        uploaded_item = upload(open_after_upload = open_after_creation)
        recordData["uploaded_item"] = uploaded_item
    else:
        if play_after_creation:
            play(recordData["playblast_file"])

    return recordData


def _record():
    # filename & path
    filepath = database.read_cache('ps_directory_lineEdit')
    filename = database.read_cache('us_filename_lineEdit')
    clipname = database.read_cache('ps_clipname_lineEdit')

    if not filepath or not filename:
        title = 'Playblast Location'
        message = 'Please specify playblast file name and location.'
        return
        qt_widgets.WarningDialog(None, title, message)
        filepath = os.path.expanduser('~/Desktop/playblasts/')
        filename = 'playblast'
    if clipname:
        filename = filename + clipname
    filepath = path.sanitize(os.path.join(filepath, filename))

    # preset
    preset_file = path.get_config_yaml(PRESET_YAML)
    preset_data = database._parse_yaml(preset_file)
    preset_name = database.read_cache('current_preset')
    preset = preset_data.get(preset_name)

    start_frame, end_frame = maya_scene.get_InOutFrames(database.read_cache('current_range_type'))
    start_frame = database.read_cache('frame_start')
    end_frame = database.read_cache('frame_end')

    #setting up args for recording
    recArgs = {
            "show_ornaments":
                False,
            "start_frame":
                start_frame,
            "end_frame":
                end_frame,
            "camera":
                database.read_cache('selected_camera'),
            "format":
                preset.get('format'),
            "viewer":
                True if database.read_cache('ps_play_after_creation_checkBox') == 'true' else False,
            "filename":
                filepath,
            "width":
                preset.get('width'),
            "height":
                preset.get('height'),
            "overwrite":
                True if database.read_cache('ps_force_overwrite_checkBox') == 'true' else False,
            "compression":
                preset.get('encoding'),
            "off_screen":
                True
    }
    logger.info("recArgs: {}".format(recArgs))

    # read from database Settings
    playblast_file = maya_scene.playblast_with_settings(
        viewport_preset=database.read_cache('current_viewport_preset'),
        viewport_preset_yaml=VIEWPORT_PRESET_YAML,
        **recArgs
    )

    return playblast_file


def _upload(current_user=None, ):
    errorLog = None
    if not current_user:
        current_user = user.SyncSketchUser()
    username = current_user.get_name()
    upload_file = get_current_file()

    if not upload_file or not os.path.isfile(upload_file):
        return

    # Try to upload to the last uploaded address first
    selected_item = database.read_cache('treewidget_selection')
    logger.info("selected_item: {0}".format(selected_item))


    # ToDo rename media_id to item_id
    item_type = database.read_cache('target_url_type')
    review_id = database.read_cache('target_review_id')
    item_id = database.read_cache('target_media_id')
    item_name = database.read_cache('target_url_item_name')

    # Upload To
    current_item = selected_item
    upload_to_value = item_name
    logger.info('Selected Item: %s'%item_name)


    last_recorded_data = database.read_cache('last_recorded')

    postData = {
        "first_frame": last_recorded_data['start_frame'],
        "last_frame": last_recorded_data['end_frame'],
    }


    if item_type == 'review':
        logger.info('Uploading {} to {} with review_id {}'.format(upload_file, upload_to_value, review_id))
        uploaded_item = current_user.upload_media_to_review(review_id, upload_file, noConvertFlag = True, itemParentId = False, data = postData)
        #logger.info("uploaded_item: {0}".format(pformat(uploaded_item)))

    elif item_type == 'media':
        logger.info('Updating item {} with file {}'.format(upload_to_value, upload_file))
        logger.info("item id %s"%item_id)
        logger.info("filepath %s"%upload_file)
        logger.info("Trying to upload %s to item_id %s, review %s"%(upload_file,item_id,review_id))
        uploaded_item = current_user.upload_media_to_review(review_id, upload_file, noConvertFlag = True, itemParentId = item_id, data = postData)
        logger.info(pformat(uploaded_item))
    else:
        uploaded_item = None
        errorLog = 'You cannot upload to %s "%s" directly.\nPlease select a review in the tree widget to upload to!\n'%(item_type, item_name)

    if not uploaded_item:
        if not errorLog:
            errorLog = 'No Uploaded Item returned from Syncsketch'

        logger.info('ERROR: This Upload failed: %s'%(errorLog))
        return

    # * this is an old call, that we should replace with an async worker
    review_data = current_user.get_review_data_from_id(review_id)


    review_url = review_data.get('reviewURL')
    #uploaded_media_url = '{}'.format(review_url)
    uploaded_media_url = '{}#{}'.format(review_url, uploaded_item['id'])
    logger.info("review_data: {}".format(review_data))
    logger.info('Upload successful. Uploaded item {} to {}'.format(upload_file, uploaded_media_url))

    if 'none' in uploaded_media_url.lower():
        uploaded_media_url = ""

    uploaded_item['reviewURL'] = uploaded_media_url
    return uploaded_item



def playblast_and_upload():
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

    UploadedMediaDialog = infoDialog.InfoDialog(title = title, info_text = info_message, media_url = uploaded_media_url.json()['reviewURL'])
    UploadedMediaDialog.exec_()

def install_shelf():
    maya_shelf.install()

def uninstall_shelf():
    maya_shelf.uninstall()

def add_timeline_context_menu():
    maya_timeline.add_context_menu_item()

def remove_timeline_context_menu():
    maya_timeline.remove_context_menu_item()

def save_viewport_preset(preset_name):
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    maya_scene.save_viewport_preset(cache, preset_name)

def new_viewport_preset(preset_name=None, source_preset=None):
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    maya_scene.new_viewport_preset(cache, preset_name=None, source_preset="1", panel=None)

def apply_viewport_preset(preset_name):
    cache = path.get_config_yaml(VIEWPORT_PRESET_YAML)
    maya_scene.apply_viewport_preset(cache, preset_name)

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

