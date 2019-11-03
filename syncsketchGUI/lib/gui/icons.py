from syncsketchGUI.lib import path
from syncsketchGUI.vendor.Qt import QtGui
import urllib
import tempfile


def _get_qicon(icon_name='syncsketch_ui_100.png'):
    '''
    Get logo path and return a QtGui.QIcon object
    '''
    icon_fullname = path.get_icon(icon_name)
    if not icon_fullname:
        return QtGui.QIcon()

    qicon = QtGui.QIcon(icon_fullname)
    return qicon

def _get_qicon_from_url(url):
    '''
    Get logo path and return a QtGui.QIcon object
    '''

    testfile = urllib.URLopener()
    tmpname = tempfile.NamedTemporaryFile(delete=False)
    try:
        thumb = testfile.retrieve(url, tmpname.name)
    except:
        icon_fullname = path.get_icon('syncsketch_ui_100.png')
        pass
    qicon = _get_qicon(tmpname.name)
    # lets remove the temp image file after we have the qicon file in memory

    return qicon


# icons
logo_icon = _get_qicon('syncsketch_ui_100.png')
record_icon = _get_qicon('icon_record_100.png')
play_icon   = _get_qicon('icon_play_100.png')
upload_icon = _get_qicon('icon_upload_100.png')
preset_icon = _get_qicon('icon_manage_presets_100.png')
target_icon = _get_qicon('icon_target_100.png')
download_icon = _get_qicon('icon_download_100.png')
account_icon = _get_qicon('icon_account_small.png')
project_icon = _get_qicon('icon_project_small.png')
review_icon = _get_qicon('icon_review_small.png')
refresh_icon = _get_qicon('icon_refresh.png')
trash_icon = _get_qicon('icon_trash.png')
new_icon = _get_qicon('icon_new.png')
rename_icon = _get_qicon('icon_rename.png')
settings_icon = _get_qicon('icon_settings.png')
help_icon = _get_qicon('icon_help.png')
add_icon = _get_qicon('icon_add.png')
delete_icon = _get_qicon('icon_delete.png')
edit_icon = _get_qicon('icon_edit.png')

media_icon = _get_qicon('icon_misc_small.png')
media_unknown_icon = _get_qicon('icon_misc_small.png')
media_video_icon = _get_qicon('icon_video_small.png')
media_image_icon = _get_qicon('icon_image_small.png')
media_sketchfab_icon = _get_qicon('icon_3d_small.png')

fill_icon = _get_qicon('icon_fill.png')
copy_icon = _get_qicon('icon_copy.png')
open_icon = _get_qicon('icon_open.png')

# colors
record_color = 'rgb(239, 108, 103);'
play_color = 'rgb(86, 196, 156);'
upload_color = 'rgb(255, 198, 82)'
download_color = 'rgb(198, 198, 198);'


highlight_color = QtGui.QColor(255, 198, 82)
success_color = 'rgb(86, 196, 156);'
warning_color = 'rgb(200, 200, 150);'
error_color = 'rgb(230, 100, 100);'
disabled_color = 'rgb(150, 150, 150);'


button_color = 'rgba(43.0, 53.0   , 59.0  , 1.0);'
button_color_hover = 'rgba(47.0, 58.0   , 65.0  , 1.0);'

header_size = 50
