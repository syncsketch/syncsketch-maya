import logging


from syncsketchGUI.vendor.Qt import QtWidgets, QtCore

from syncsketchGUI.lib import database, user
from syncsketchGUI.lib.maya import scene as maya_scene

import maya.cmds as cmds

from . import qt_windows
from . import qt_regulars

logger = logging.getLogger("syncsketchGUI")

class DownloadWindow(qt_windows.SyncSketchWindow):
    """
    UI Frame to handle Download Actions
    """
    window_name = 'syncsketchGUI_preset_window'
    window_label = 'Download And Application'

    def __init__(self, parent=None):
        super(DownloadWindow, self).__init__(parent=parent)
        self.decorate_ui()
        self.align_to_center(self.parent)

        current_user = user.SyncSketchUser()
        self.ui.review_target_url.editingFinished.connect(self.editingFinished)
        self.media_id = None

        if not current_user.is_logged_in():
            logger.info("Please Login to syncsketch to Download content")
            return


        try:
            target_media_id = int(database.read_cache('target_media_id'))
            logger.info("target_media_id: {}".format(target_media_id))
        except Exception as e:
            logger.info(e)
            cmds.warning("No target media selected, please select an item from the UI")
            return


        self.item_data = current_user.get_item_info(int(database.read_cache('target_media_id')))['objects'][0]

        review_id = database.read_cache('target_review_id')
        media_id  = database.read_cache('target_media_id')
        target_url  = database.read_cache('upload_to_value')
        thumb_url = current_user.get_item_info(media_id)['objects'][0]['thumbnail_url']


        self.ui.review_target_url.setText(target_url)
        self.ui.thumbnail_pushButton.set_icon_from_url(thumb_url)
        self.ui.review_target_name.setText(self.item_data['name'])

    def editingFinished(self):
        text = self.ui.review_target_url.text()
        current_user = user.SyncSketchUser()

        if not current_user.is_logged_in():
            logger.info("You are not logged in, please use the syncsketchGUI to log in first")
            return


        cleanUrl = parse_url_data(text)
        media_id = cleanUrl.get('id')
        if media_id:
            self.media_id = media_id
            item = current_user.get_item_info(media_id)
            #todo : try except this part if user is not logged in
            thumb_url = item['objects'][0]['thumbnail_url']
            self.ui.thumbnail_pushButton.set_icon_from_url(thumb_url)
        else:
            logger.info("The URL is not accessible {} with  id {} doesn't exist".format(text, media_id))


    def decorate_ui(self):
        self.ui.ui_greasepencilDownload_layout = QtWidgets.QVBoxLayout()
        self.ui.ui_downloadGeneral_layout = QtWidgets.QVBoxLayout()
        self.ui.ui_downloadGP_layout = QtWidgets.QVBoxLayout()

        self.lay_main.addLayout(self.ui.ui_downloadGeneral_layout)

        self.ui.thumbnail_pushButton = qt_regulars.Thumbnail(width=480, height=270)
        self.ui.review_target_name = qt_regulars.LineEdit()
        self.ui.review_target_url = qt_regulars.LineEdit()
        self.ui.ui_status_label = qt_regulars.StatusLabel()
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.ui_status_label)
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.thumbnail_pushButton)
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.review_target_url)

        # GP Range Row
        self.ui.downloadGP_range_layout = qt_regulars.GridLayout(self, label = 'Frame Offset')
        self.ui.ui_downloadGP_rangeIn_textEdit   = qt_regulars.QSpinBox()
        self.ui.ui_downloadGP_rangeIn_textEdit.setValue(0)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMinimum(-100000)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMaximum(100000)
        self.ui.downloadGP_range_layout.addWidget(self.ui.ui_downloadGP_rangeIn_textEdit,  0, 1)
        self.ui.downloadGP_range_layout.setColumnStretch(2,0)

        # GP Application Row
        self.ui.downloadGP_application_layout = qt_regulars.GridLayout(self, label = 'After Download')
        self.ui.downloadGP_application_checkbox = QtWidgets.QCheckBox()
        self.ui.downloadGP_application_checkbox.setText("Apply")
        self.ui.downloadGP_application_checkbox.setChecked(1)
        self.ui.downloadGP_application_checkbox.setFixedWidth(60)
        self.ui.downloadGP_application_layout.setColumnStretch(1,0)
        self.ui.downloadGP_application_comboBox = qt_regulars.ComboBox()
        self.ui.downloadGP_application_comboBox.addItems(maya_scene.get_available_cameras())
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_checkbox,  0, 1)
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_comboBox,  0, 2)
        self.ui.downloadGP_application_layout.setColumnStretch(2,1)

        self.ui.ui_downloadGP_pushButton = qt_regulars.Button()
        self.ui.ui_downloadGP_pushButton.clicked.connect(self.download_greasepencil)
        self.ui.ui_downloadGP_pushButton.setText("Download\nGrease Pencil")
        self.ui.ui_downloadVideoAnnotated_pushButton = qt_regulars.Button()
        self.ui.ui_downloadVideoAnnotated_pushButton.clicked.connect(self.download_video_annotated)
        self.ui.ui_downloadVideoAnnotated_pushButton.setText("Download\nAnnotated Video")

        self.ui.download_buttons_layout = QtWidgets.QHBoxLayout()
        self.ui.download_buttons_layout.addWidget(self.ui.ui_downloadGP_pushButton)
        self.ui.download_buttons_layout.addWidget(self.ui.ui_downloadVideoAnnotated_pushButton)
        #
        self.ui.ui_downloadGP_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_downloadGP_groupbox.setTitle('Grease Pencil')
        self.ui.ui_downloadGP_groupbox.setLayout(self.ui.ui_downloadGP_layout)
        self.ui.ui_downloadGP_layout.addLayout(self.ui.downloadGP_range_layout)
        self.ui.ui_downloadGP_layout.addLayout(self.ui.downloadGP_application_layout)
        self.ui.ui_downloadGP_layout.addLayout(self.ui.download_buttons_layout)

        self.lay_main.addWidget(self.ui.ui_downloadGP_groupbox)


    def download_greasepencil(self):
        """Downloads the greasepencil """
        downloaded_item = syncsketchGUI.download()
        offset = int(self.ui.ui_downloadGP_rangeIn_textEdit.value())
        if downloaded_item:
            if offset is not 0:
                logger.info("Offsetting by %s frames"%offset)
                downloaded_item = maya_scene.modifyGreasePencil(downloaded_item, offset)
            maya_scene.apply_greasepencil(downloaded_item, clear_existing_frames = True)
        else:
            logger.info("Error: Could not download grease pencil file...")

    def download_video_annotated(self):
        """Downloads the annoated video"""
        downloaded_item = syncsketchGUI.downloadVideo(media_id=self.media_id)
        if downloaded_item:
            logger.info(downloaded_item)
            camera = self.ui.downloadGP_application_comboBox.currentText()
            maya_scene.apply_imageplane(downloaded_item, camera)


def parse_url_data(link=database.read_cache('upload_to_value')):
    '''
    simple url parser that extract uuid, review_id and revision_id
    '''
    #url = 'https://www.syncsketch.com/sketch/bff609f9cbac/#711273/637821'
    #       https://syncsketch.com/sketch/bff609f9cbac#711680

    #Remove reduntant path and check if it's expected
    logger.info("link parser: {}".format(link))
    if not link:
        logger.info("Link isn't a link: {}".format(link))
        return

    baseUrl = 'https://syncsketch.com/sketch/'

    #Remove leading forward slash
    if link[-1] == "/":
        link = link[:-1]

    #Remove www
    link = link.replace("www.", "")

    data = {"uuid":0, "id":0, "revision_id":0}
    #Add a slash so we don't need to chase two different cases
    if not link.split("#")[0][-1] == "/":
        link = "/#".join(link.split("#"))
        logger.info("Modified link: {}".format(link))


    if not link[0:len(baseUrl)] == baseUrl:
        logger.info("URL need's to start with: {}".format(baseUrl))
        return data


    #Find UUID
    payload = link[len(baseUrl):].split("/")

    if len(link) > 0:
        uuidPart = (re.findall(r"([a-fA-F\d]{12})", payload[0]))
        if uuidPart:
            data['uuid'] = uuidPart[0]
        else:
            print("link need's to be of the form https://www.syncsketch.com/sketch/bff609f9cbac/ got {}".format(link))
    #Find ID
    if len(payload) > 1:
        if payload[1].startswith("#"):
            data['id'] = payload[1][1:]
        else:
            print("link need's to be of the form https://www.syncsketch.com/sketch/bff609f9cbac/#711273 got {}".format(link))

    if len(payload) > 3:
        pass
        #handle revision
    return data