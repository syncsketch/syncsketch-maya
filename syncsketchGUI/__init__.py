# -*- coding: UTF-8 -*-
# ======================================================================
# @Author   : SyncSketch LLC
# @Email    : dev@syncsketchGUI.com
# @Version  : 1.0.0
# ======================================================================
# Environment Detection

import os
import time
import webbrowser

try:
    from maya import cmds
    MAYA = True
except ImportError:
    MAYA = False

try:
    import nuke
    import nukescripts
    NUKE = True
except ImportError:
    NUKE = False

STANDALONE = False
if not MAYA and not NUKE:
    STANDALONE = True


# ======================================================================
# Global Variables
WAIT_TIME = 0.1 # seconds

# ======================================================================
# API Import

# ======================================================================
# Core Imports

from syncsketchGUI.lib import user, path
from syncsketchGUI.lib import video, database
from syncsketchGUI.lib.gui import icons, qt_utils, qt_widgets
import gui

# ======================================================================
# Maya Imports

if MAYA:
    from syncsketchGUI.lib.maya import shelf as maya_shelf, menu as maya_menu
    from syncsketchGUI.lib.maya import scene as maya_scene, timeline as maya_timeline

# ======================================================================
# Global Variables

PRESET_YAML = 'syncsketch_preset.yaml'
CACHE_YAML = 'syncsketch_cache.yaml'
VIEWPORT_PRESET_YAML = 'syncsketch_viewport.yaml'

# ======================================================================
# Module Functions

def show_login_dialog():
    gui.show_login_dialog()

def show_web_login_window():
    gui.show_web_login_window()

def reload_toolkit():
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
    
    if MAYA:
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
    gui.show_menu_window()

def show_download_window():
    gui.show_download_window()

def show_viewport_preset_window():
    gui.show_viewport_preset_window()

def get_current_file():
    # validate file name
    filename = database.read_cache('last_recorded_selection')

    if not filename:
        raise RuntimeError('There is no previously recorded video file.')

    filename = path.sanitize(filename)

    if not os.path.isfile(filename):
        raise RuntimeError('Please provide a valid file.')
        return
    else:
        return filename


def show_success_message(uploaded_item):

    title = 'Upload Successful'
    info_message = 'Your file has successfully been uploaded. Please follow this link:'

    UploadedMediaDialog = gui.InfoDialog(None,
                                          title,
                                          info_message,
                                          uploaded_item['reviewURL'])
    UploadedMediaDialog.exec_()


def play(filename = None):
    if not filename:
        filename = get_current_file()
    filename = path.make_safe(filename)
    video.play_in_default_player(filename)
    print 'Playing current video: {}'.format(filename.replace('"', ''))


def upload(open_after_upload = None, show_success_msg = False):
    uploaded_item = _upload()
    if not uploaded_item:
        return

    if open_after_upload is None:
        open_after_upload = True if database.read_cache('ps_open_afterUpload_checkBox') == 'true' else False

    if open_after_upload:
        webbrowser.open(uploaded_item['reviewURL'], new=2, autoraise=True)

    if not open_after_upload:
        show_success_message(uploaded_item)

    return uploaded_item


def download(current_user = None):
    if not current_user:
        current_user = user.SyncSketchUser()
    review_id = database.read_cache('target_review_id')
    media_id  = database.read_cache('target_media_id')
    print "current_user: %s"%current_user
    print "target_review_id: %s"%review_id
    print "target_media_id: %s"%media_id
    return current_user.download_greasepencil(review_id, media_id )


def record(upload_after_creation = None, play_after_creation = None,  show_success_msg = True):
    # This a wrapper function and if called individually should mirror all the same effect as hitting 'record' in the UI
    recordData = {}

    recordData["playblast_file"] = _record()

    # Post actions

    # To Do - post Recording script call
    # Upload to the selected review or playground if the box is checked
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
    if not MAYA:
        title = 'Maya Only Function'
        message = 'Recording is not yet functional outside of Maya.'
        WarningDialog(self.parent_ui, title, message)
        return

    # filename & path
    filepath = database.read_cache('ps_directory_lineEdit')
    filename = database.read_cache('us_filename_lineEdit')
    clipname = database.read_cache('ps_clipname_lineEdit')

    if not filepath or not filename:
        title = 'Playblast Location'
        message = 'Please specify playblast file name and location.'
        WarningDialog(self.parent_ui, title, message)
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
    print(preset)
    print("18888"*1000)

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

    # read from database Settings
    print(recArgs)
    playblast_file = maya_scene.playblast_with_settings(
        viewport_preset=database.read_cache('current_viewport_preset'),
        viewport_preset_yaml=VIEWPORT_PRESET_YAML,
        **recArgs
    )

    return playblast_file


def _upload(current_user = None, ):
    errorLog = None
    if not current_user:
        current_user = user.SyncSketchUser()
    username = current_user.get_name()
    upload_file = get_current_file()


    if not upload_file or not os.path.isfile(upload_file):
        self.update_tooltip('WebM file cannot be sourced. Uploading the original file.', color='LightYellow')

    # Try to upload to the last uploaded address first
    selected_item = database.read_cache('treewidget_selection')

    # if not selected_item:
    #     database.read_cache('target_review_id')

    # ToDo rename media_id to item_id
    item_type = database.read_cache('target_url_type')
    review_id = database.read_cache('target_review_id')
    item_id = database.read_cache('target_media_id')
    item_name = database.read_cache('target_url_item_name')

    # Upload To
    current_item = selected_item
    upload_to_value = str()

    if item_type == 'playground':
        upload_to_value = 'Playground(public)'
    else:
        upload_to_value = item_name
        print 'Selected Item: %s'%item_name

    time.sleep(WAIT_TIME)

    # Don't need to login if we're uploading to playground.
    # Treewidget item selection must be review type to upload.
    # If selection is other item type, warn the user.
    last_recorded_data = database.read_cache('last_recorded')

    postData = {
        "first_frame": last_recorded_data['start_frame'],
        "last_frame": last_recorded_data['end_frame'],
    }

    if item_type == 'playground':
        playground_email = database.get_playground_email()
        if not path.validate_email_address(playground_email):
            user_input = qt_widgets.InputDialog()
            if not user_input.response:
                return

            playground_email = user_input.response_text
            database.save_playground_email(playground_email)

        uploaded_item = user.upload_to_playground(upload_file, playground_email)

    elif item_type == 'review':
        print 'Uploading {} to {}'.format(upload_file, upload_to_value)
        uploaded_item = current_user.upload_media_to_review(review_id, upload_file, noConvertFlag = True, itemParentId = False, data = postData)
        import pprint
        pprint.pprint(uploaded_item)

    elif item_type == 'media':
        print 'Updating item {} with file {}'.format(upload_to_value, upload_file)
        print "item id %s"%item_id
        print "filepath %s"%upload_file
        print "Trying to upload %s to item_id %s, review %s"%(upload_file,item_id,review_id)
        uploaded_item = current_user.upload_media_to_review(review_id, upload_file, noConvertFlag = True, itemParentId = item_id, data = postData)
        import pprint
        pprint.pprint(uploaded_item)
    else:
        uploaded_item = None
        errorLog = 'You cannot upload to %s "%s" directly.\nPlease select a review in the tree widget to upload to!\n'%(item_type, item_name)

    if not uploaded_item:
        if not errorLog:
            errorLog = 'No Uploaded Item returned from Syncsketch'

        print 'ERROR: This Upload failed: %s'%(errorLog)
        return

    # try:
    review_data = current_user.get_review_data_from_id(review_id)
    review_url = review_data.get('reviewURL')
    uploaded_media_url = 'https://syncsketchGUI.com/sketch/{}#{}'.format(str(review_data.get('id')).rstrip('/'), uploaded_item['id'])
    print 'Upload successful. Uploaded item {} to {}'.format(upload_file, uploaded_media_url)
    # except:
    #     uploaded_media_url = uploaded_item.get('reviewURL')

    if 'none' in uploaded_media_url.lower():
        uploaded_media_url = str()

    if uploaded_media_url:
        uploaded_media_url.replace(path.playground_url, path.playground_display_url)
    uploaded_item['reviewURL'] = uploaded_media_url
    return uploaded_item



def playblast_and_upload():
    if not gui.confirm_upload_to_playground():
        return
    
    filepath = maya_scene.playblast()
    if not filepath:
        return
    
    webm_file = video.convert_to_webm(filepath)
    if not webm_file:
        return
    
    user_input = gui.InputDialog()
    if not user_input.response:
        return
    
    uploaded_media_url = user.upload_to_playground(webm_file, user_input.response_text)
    if not uploaded_media_url:
        return
    
    title = 'Upload Successful'
    info_message = 'Your file has successfully been uploaded. Please follow this link:'
    
    UploadedMediaDialog = gui.InfoDialog(title = title, info_text = info_message, media_url = uploaded_media_url.json()['reviewURL'])
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
    # print "current_viewport_preset %s"%current_viewport_preset
    print presets
    l = len(presets)
    # print current_viewport_preset

    i = 0
    if current_viewport_preset in presets:
        for k in range(l):
            i = k
            print "presets[%s] %s"%(i, presets[i])
            if current_viewport_preset == presets[i]:
                print "%s is a match"%i
                break
    else:
        i = 0

    i += 1
    if i >= l:
        i = 0

    database.save_cache('current_viewport_preset', presets[i], yaml_file = CACHE_YAML)
    maya_scene.apply_viewport_preset(cache, presets[i])

def createOrUpdatePlayblastCam():
    # apply_viewport_preset('')
    # apply_viewport_preset
    filePath = database.read_cache('last_recorded')
    maya_scene.createOrUpdatePlayblastCam(frameOffset=0, moviePath=filePath)
    # removePlayblastCam()
