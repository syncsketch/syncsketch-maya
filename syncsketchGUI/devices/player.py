import logging
import os 

from ..lib import path
from ..lib import database
from ..lib import video

from ..lib.gui import qt_dialogs #Remove QT dependency

logger = logging.getLogger("syncsketchGUI")

def play(filename = None):
    if not filename:
        filename = _get_current_file()
    filename = path.make_safe(filename)
    video.play_in_default_player(filename)
    logger.info('Playing current video: {}'.format(filename.replace('"', '')))

def _get_current_file():
    # validate file name
    filename = database.read_cache('last_recorded_selection')

    if not filename:
        title = 'No File for Upload'
        message = 'There is no previously recorded video file, please record one first through The Widget'
        qt_dialogs.WarningDialog(None, title, message)
        return


    filename = path.sanitize(filename)

    if not os.path.isfile(filename):
        title = 'Not a valid file'
        message = 'Please provide a valid file'
        logger.debug("{} is not a valid file".format(filename))
        qt_dialogs.WarningDialog(None, title, message)
        return
    else:
        return filename