import logging
import os 

from syncsketchGUI.settings import PRESET_YAML, VIEWPORT_PRESET_YAML

from ..lib import database, video, path

from ..lib.maya import scene as maya_scene
from ..lib.gui import qt_dialogs #TODO: Remove Qt dependency

from . import player
from . import uploader

logger = logging.getLogger("syncsketchGUI")

def record(upload_after_creation = None, play_after_creation = None,  show_success_msg = True):
    # This a wrapper function and if called individually should mirror all the same effect as hitting 'record' in the UI
    recordData = {}
    capturedFile = _record()
    if not capturedFile:
        return {"playblast_file": ""}
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
        uploaded_item = uploader.upload(open_after_upload = open_after_creation)
        recordData["uploaded_item"] = uploaded_item
    else:
        if play_after_creation:
            player.play(recordData["playblast_file"])

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
        qt_dialogs.WarningDialog(None, title, message)
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
                True,
            "sound":
                maya_scene.get_active_sound_node()

    }
    logger.info("recArgs: {}".format(recArgs))

    # read from database Settings
    playblast_file = maya_scene.playblast_with_settings(
        viewport_preset=database.read_cache('current_viewport_preset'),
        viewport_preset_yaml=VIEWPORT_PRESET_YAML,
        **recArgs
    )

    return playblast_file