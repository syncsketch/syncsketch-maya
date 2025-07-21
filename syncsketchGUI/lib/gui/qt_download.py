import logging

from syncsketchGUI import literals
from syncsketchGUI.devices import downloader
from syncsketchGUI.lib import database, user
from syncsketchGUI.lib.maya import scene as maya_scene
from syncsketchGUI.vendor.Qt import QtWidgets

from ..path import parse_url_data
from . import qt_dialogs, qt_presets, qt_regulars, qt_windows

logger = logging.getLogger("syncsketchGUI")


class DownloadWindow(qt_windows.SyncSketchWindow):
    """
    UI Frame to handle Download Actions
    """

    window_name = 'syncsketchGUI_preset_window'
    window_label = 'Download And Application'

    def __init__(self, parent=None):
        super(DownloadWindow, self).__init__(parent=parent)
        self.maya_version = maya_scene.get_current_maya_version()

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
            logger.debug("target_media_id: {}".format(target_media_id))
        except Exception as e:
            logger.info(e)
            return

        self.item_data = current_user.get_item_info(int(database.read_cache('target_media_id')))['objects'][0]

        review_id = database.read_cache('target_review_id')
        media_id = database.read_cache('target_media_id')
        target_url = database.read_cache('upload_to_value')
        thumb_url = current_user.get_item_info(media_id)['objects'][0]['thumbnail_url']

        self.ui.review_target_url.setText(target_url)
        self.ui.thumbnail_pushButton.set_icon_from_url(thumb_url)
        self.ui.review_target_name.setText(self.item_data['name'])

    def editingFinished(self):
        text = self.ui.review_target_url.text()
        current_user = user.SyncSketchUser()

        if not current_user.is_logged_in():
            logger.warning("You are not logged in, please use the syncsketchGUI to log in first")
            return

        cleanUrl = parse_url_data(text)
        media_id = cleanUrl.get('id')
        if media_id:
            self.media_id = media_id
            item = current_user.get_item_info(media_id)
            # todo : try except this part if user is not logged in
            thumb_url = item['objects'][0]['thumbnail_url']
            self.ui.thumbnail_pushButton.set_icon_from_url(thumb_url)
        else:
            logger.error("The URL is not accessible {} with  id {} doesn't exist".format(text, media_id))

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
        self.ui.downloadGP_range_layout = qt_regulars.GridLayout(self, label='Frame Offset')
        self.ui.ui_downloadGP_rangeIn_textEdit = qt_regulars.QSpinBox()
        self.ui.ui_downloadGP_rangeIn_textEdit.setValue(0)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMinimum(-100000)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMaximum(100000)
        self.ui.downloadGP_range_layout.addWidget(self.ui.ui_downloadGP_rangeIn_textEdit, 0, 1)
        self.ui.downloadGP_range_layout.setColumnStretch(2, 0)

        # GP Application Row
        self.ui.downloadGP_application_layout = qt_regulars.GridLayout(self, label='After Download')
        self.ui.downloadGP_application_checkbox = QtWidgets.QCheckBox()
        self.ui.downloadGP_application_checkbox.setText("Apply")
        self.ui.downloadGP_application_checkbox.setChecked(1)
        self.ui.downloadGP_application_checkbox.setFixedWidth(60)
        self.ui.downloadGP_application_layout.setColumnStretch(1, 0)
        self.ui.downloadGP_application_comboBox = qt_regulars.ComboBox()
        self.ui.downloadGP_application_comboBox.addItems(maya_scene.get_available_cameras())
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_checkbox, 0, 1)
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_comboBox, 0, 2)
        self.ui.downloadGP_application_layout.setColumnStretch(2, 1)

        self.ui.ui_downloadVideoAnnotated_pushButton = qt_regulars.Button()
        self.ui.ui_downloadVideoAnnotated_pushButton.clicked.connect(self.download_video_annotated)
        self.ui.ui_downloadVideoAnnotated_pushButton.setText("Download\nAnnotated Video")

        if self.maya_version >= 2023:
            self._blue_pencil_options_ui()
        else:
            self._grease_pencil_options_ui()

    def _grease_pencil_options_ui(self):
        self.ui.ui_downloadGP_pushButton = qt_regulars.Button()
        self.ui.ui_downloadGP_pushButton.setText("Download\nGrease Pencil")
        self.ui.ui_downloadGP_pushButton.clicked.connect(self.download_greasepencil)

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

    def _blue_pencil_options_ui(self):
        self.ui.download_tabs = QtWidgets.QTabWidget()
        # Blue Pencil Tab
        self.ui.download_sketches_tab = QtWidgets.QWidget()
        self.ui.download_tabs.addTab(self.ui.download_sketches_tab, "Blue Pencil")
        # Download Sketches button
        self.ui.ui_download_sketches_button = qt_regulars.Button()
        self.ui.ui_download_sketches_button.setText("Download Sketches")
        self.ui.ui_download_sketches_button.clicked.connect(self.download_sketches)
        # Path to downloaded sketches and copy buttoin
        self.ui.download_sketches_path = qt_regulars.LineEdit()
        self.ui.copy_sketches_path_button = qt_regulars.ToolButton(self, qt_presets.copy_icon)
        self.ui.copy_sketches_path_button.clicked.connect(self.copy_sketches_path)
        self.ui.sketches_path_layout = QtWidgets.QVBoxLayout()
        self.ui.sketches_path_label = QtWidgets.QLabel("Path to downloaded sketches:")
        self.ui.sketches_path_layout.addWidget(self.ui.sketches_path_label)
        self.ui.sketches_path_copy_layout = QtWidgets.QHBoxLayout()
        self.ui.sketches_path_copy_layout.addWidget(self.ui.download_sketches_path)
        self.ui.sketches_path_copy_layout.addWidget(self.ui.copy_sketches_path_button)
        self.ui.sketches_path_layout.addLayout(self.ui.sketches_path_copy_layout)
        # Import Blue Pencil button
        self.ui.import_blue_pencil = qt_regulars.Button()
        self.ui.import_blue_pencil.setText("Import as Blue Pencil Layer")
        self.ui.import_blue_pencil.clicked.connect(self.import_bluepencil)
        # Blue Pencil Tab Layout
        self.ui.sketches_groupbox_layout = QtWidgets.QVBoxLayout()
        self.ui.download_sketches_tab.setLayout(self.ui.sketches_groupbox_layout)
        self.ui.sketches_groupbox_layout.addWidget(self.ui.ui_download_sketches_button)
        self.ui.sketches_groupbox_layout.addLayout(self.ui.sketches_path_layout)
        self.ui.sketches_groupbox_layout.addWidget(self.ui.import_blue_pencil)
        # Video Tab
        self.ui.download_video_tab = QtWidgets.QWidget()
        self.ui.download_tabs.addTab(self.ui.download_video_tab, "Annotated Video")
        self.ui.video_groupbox_layout = QtWidgets.QVBoxLayout()
        self.ui.download_video_tab.setLayout(self.ui.video_groupbox_layout)
        self.ui.ui_downloadVideoAnnotated_pushButton.setText("Download Annotated Video")
        self.ui.video_groupbox_layout.addWidget(self.ui.ui_downloadVideoAnnotated_pushButton)
        self.lay_main.addWidget(self.ui.download_tabs)

    def download_greasepencil(self):
        """Downloads the greasepencil"""
        downloaded_greasepencile_path = downloader.download_greasepencil()
        offset = int(self.ui.ui_downloadGP_rangeIn_textEdit.value())
        if downloaded_greasepencile_path:
            if offset != 0:
                logger.info("Offsetting by {} frames".format(offset))
                downloaded_greasepencile_path = maya_scene.add_frame_offset_to_grease_pencil_zip(
                    downloaded_greasepencile_path, offset
                )
            maya_scene.apply_greasepencil(downloaded_greasepencile_path, clear_existing_frames=True)
        else:
            logger.error("Error: Could not download grease pencil file...")

    def download_sketches(self):
        downloaded_sketches_path = downloader.download_greasepencil()
        self.ui.download_sketches_path.setText(downloaded_sketches_path)

    def copy_sketches_path(self):
        # copy path to clipboard
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.ui.download_sketches_path.text())

    def import_bluepencil(self):
        # open file dialog to import blue pencil frames from zip
        maya_scene.import_bluepencil()

    def download_video_annotated(self):
        """
        Downloads the annotated video
        """

        if not self._quicktime_available():
            qt_dialogs.WarningDialog(None, literals.qtff_not_supported, literals.quicktime_install_instructions)
            return

        downloaded_item = downloader.download_video(media_id=self.media_id)
        if downloaded_item:
            logger.info(downloaded_item)
            camera = self.ui.downloadGP_application_comboBox.currentText()
            maya_scene.apply_imageplane(downloaded_item, camera)

    def _quicktime_available(self):
        if "qt" in maya_scene.get_available_formats():
            return True
        else:
            return False
