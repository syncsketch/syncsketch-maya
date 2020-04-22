import logging
import syncsketchGUI
from syncsketchGUI.vendor.Qt import QtWidgets, QtCore
from syncsketchGUI.lib.gui.qt_widgets import SyncSketch_Window
from syncsketchGUI.lib import database, user
from syncsketchGUI.lib.gui.qt_widgets import RegularThumbnail, RegularComboBox, RegularStatusLabel, RegularLineEdit, RegularButton, RegularToolButton, RegularGridLayout, RegularQSpinBox
from syncsketchGUI.lib.maya import scene as maya_scene
import maya.cmds as cmds


logger = logging.getLogger("syncsketchGUI")
class DownloadWindow(SyncSketch_Window):
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
        from syncsketchGUI.gui import parse_url_data
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

        self.ui.main_layout.addLayout(self.ui.ui_downloadGeneral_layout)

        self.ui.thumbnail_pushButton = RegularThumbnail(width=480, height=270)
        self.ui.review_target_name = RegularLineEdit()
        self.ui.review_target_url = RegularLineEdit()
        self.ui.ui_status_label = RegularStatusLabel()
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.ui_status_label)
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.thumbnail_pushButton)
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.review_target_url)

        # GP Range Row
        self.ui.downloadGP_range_layout = RegularGridLayout(self, label = 'Frame Offset')
        self.ui.ui_downloadGP_rangeIn_textEdit   = RegularQSpinBox()
        self.ui.ui_downloadGP_rangeIn_textEdit.setValue(0)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMinimum(-100000)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMaximum(100000)
        self.ui.downloadGP_range_layout.addWidget(self.ui.ui_downloadGP_rangeIn_textEdit,  0, 1)
        self.ui.downloadGP_range_layout.setColumnStretch(2,0)

        # GP Application Row
        self.ui.downloadGP_application_layout = RegularGridLayout(self, label = 'After Download')
        self.ui.downloadGP_application_checkbox = QtWidgets.QCheckBox()
        self.ui.downloadGP_application_checkbox.setText("Apply")
        self.ui.downloadGP_application_checkbox.setChecked(1)
        self.ui.downloadGP_application_checkbox.setFixedWidth(60)
        self.ui.downloadGP_application_layout.setColumnStretch(1,0)
        self.ui.downloadGP_application_comboBox = RegularComboBox()
        self.ui.downloadGP_application_comboBox.addItems(maya_scene.get_available_cameras())
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_checkbox,  0, 1)
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_comboBox,  0, 2)
        self.ui.downloadGP_application_layout.setColumnStretch(2,1)

        self.ui.ui_downloadGP_pushButton = RegularButton()
        self.ui.ui_downloadGP_pushButton.clicked.connect(self.download_greasepencil)
        self.ui.ui_downloadGP_pushButton.setText("Download\nGrease Pencil")
        self.ui.ui_downloadVideoAnnotated_pushButton = RegularButton()
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

        self.ui.main_layout.addWidget(self.ui.ui_downloadGP_groupbox)


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
