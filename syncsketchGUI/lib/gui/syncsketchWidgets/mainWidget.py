import logging
import os
import time
import webbrowser
from syncsketchGUI.vendor.Qt import QtCore, QtGui, QtWidgets
logger = logging.getLogger("syncsketchGUI")



from syncsketchGUI.lib import video, user, database
from syncsketchGUI.lib.gui.qt_widgets import *
from syncsketchGUI.lib.gui.qt_utils import *
from syncsketchGUI.lib.maya import scene as maya_scene
from syncsketchGUI.lib.connection import is_connected, open_url
from syncsketchGUI.gui import  _maya_delete_ui, show_download_window
from syncsketchGUI.lib.gui.syncsketchWidgets.web import LoginView, OpenPlayerView, logout_view
import syncsketchGUI
from syncsketchGUI.gui import parse_url_data, get_current_item_from_ids, set_tree_selection, update_target_from_tree, getReviewById
from syncsketchGUI.lib.gui.icons import _get_qicon
from syncsketchGUI.lib.gui.literals import DEFAULT_VIEWPORT_PRESET, PRESET_YAML, VIEWPORT_YAML, DEFAULT_PRESET, uploadPlaceHolderStr, message_is_not_loggedin, message_is_not_connected
from syncsketchGUI.lib.async import Worker, WorkerSignals
from syncsketchGUI.installScripts.maintenance import getLatestSetupPyFileFromLocal, getVersionDifference
USER_ACCOUNT_DATA = None

class MenuWindow(SyncSketch_Window):
    """
    Main browser window of the syncsketchGUI services
    """
    window_name='syncsketchGUI_menu_window'
    window_label='SyncSketch'

    account_is_connected = False

    def __init__(self, parent):
        super(MenuWindow, self).__init__(parent=parent)
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        self.accountData = None
        self.reviewData = None
        self.mediaItemParent = None
        self.installer = None

        self.setMaximumSize(700, 650)
        self.decorate_ui()
        self.build_connections()
        self.accountData = self.retrievePanelData()


        # Load UI state
        self.update_login_ui()

        #Not logged in or outdated api, token
        self.setWindowTitle("Syncsketch - Version: {}".format(getLatestSetupPyFileFromLocal()))
        if not self.accountData:
            self.restore_ui_state()
            return

        #Populate Treewidget sparse
        #self.asyncProcessRunning = False
        self.populateTree()
        #self.restore_ui_state()
        #Populate Treewidget with all items
        #self.asyncPopulateTree(withItems=True)
        self.restore_ui_state()



    def storeReviewData(self, s):
        logger.info("storereviewData {}".format(s[0]))
        logger.info("storereviewData {}".format(s[1]))
        self.reviewData = s[0]

    def storeAccountData(self, s):
        logger.info(s)
        self.accountData = s

    def populateReviewPanel(self):
        self.ui.browser_treeWidget.clear()
        if self.accountData:
            self.populate_review_panel(self.accountData, force=True)
        else:
            logger.warning("No Accountdata found")

    def fetchData(self, user, logging=None, withItems=False):
        '''
        Meant to be called from a thread, access only local names
        '''
        try:
            account_data = user.get_account_data(withItems=withItems)
            if logging:
                pass
                #logging.warning('accountdata: '.format(account_data))
        except Exception as err:
            return None

        return account_data

    def load_leafs(self, user, reviewId=None):
        items = user.host_data.getMediaByReviewId(reviewId)['objects']
        return (items, reviewId)


    def populateReviewItems(self):
        items = self.reviewData
        if not self.mediaItemParent:
            logger.info("No Review Item parent, returning")
            return
        self.mediaItemParent.takeChildren()
        logger.info("takeChildren and populating reviewItems {} ".format(items))

        for media in items or []:
            #add UUID of the review container to the media, so we can use it in itemdata
            media['uuid'] = self.review['uuid']
            if not media.get('type'):
                specified_media_icon = media_unknown_icon
            elif 'video' in media.get('type').lower():
                specified_media_icon = media_video_icon
            elif 'image' in media.get('type').lower():
                specified_media_icon = media_image_icon
            elif 'sketchfab' in media.get('type').lower():
                specified_media_icon = media_sketchfab_icon
            else:
                specified_media_icon = media_unknown_icon

            media_treeWidgetItem = self._build_widget_item(parent = self.mediaItemParent,
                                                        item_name = media.get('name'),
                                                        item_type='media',
                                                        item_icon = specified_media_icon,
                                                        item_data = media)

            media_treeWidgetItem.sizeHint(80)
            # * this is an obsolute call
            #set_tree_selection(self.ui.browser_treeWidget, None)

            #Make sure we select the last uploaded item
        if database.read_cache("upload_to_value"):
            logger.info("true upload_to_value: {}".format(database.read_cache("upload_to_value")))
            #logger.info("upload_to_value is set, updating lineEdit")
            self.ui.target_lineEdit.setText(database.read_cache("upload_to_value"))
            self.select_item_from_target_input()
        else:
            logger.info("Nothing to set in the lineedit")
            logger.info('false upload_to_value')

    def currentItemChanged(self):
        pass

    # todo: remove last line call to remove sideffect
    def loadLeafs(self, target=None):
        '''
        '''
        if not target:
            logger.info("No Target")
            reviewId = database.read_cache('target_review_id')
            if reviewId:
                logger.info("Restoring reviewId section for : {} ".format(reviewId))
                target = getReviewById(self.ui.browser_treeWidget, reviewId=reviewId)
            else:
                return

        logger.info("target: {} target name: {}".format(type(target), target.text(0)))

        selected_item = target
        review = selected_item.data(1, QtCore.Qt.EditRole)
        item_type = selected_item.data(2, QtCore.Qt.EditRole)


        if item_type == "review":
            current_user = user.SyncSketchUser()
            current_user.auto_login()
            if not current_user.is_logged_in():
                return

            self.review = review
            self.reviewData = self.load_leafs(user=current_user, reviewId=review['id'])[0]
            logger.info("review['id']: {} reviewData: {}".format(review['id'], self.reviewData))
            self.mediaItemParent = target
            self.populateReviewItems()



    def populateTree(self):
        #Only called at the beginning of a sessions
        self.current_user = user.SyncSketchUser()
        if not self.current_user.is_logged_in():
            logger.info("User not logged in, returning")
            return

        logger.info("Trying to fetch data and co")
        #self.fetchData(user=self.current_user)
        self.accountData = self.current_user.get_account_data(withItems=False)

        self.populateReviewPanel()
        # * those two next commands might be switched
        self.loadLeafs()
        self.populateReviewItems()



    def closeEvent(self, event):
        logger.info("Closing Window")
        self.save_ui_state()
        event.accept()


    def restore_ui_state(self):
        logger.info("restoring ui state")
        self.ui.upgrade_pushButton.show() if getVersionDifference() else self.ui.upgrade_pushButton.hide()

        # self.ui.ui_record_pushButton.setEnabled(
        #     True if self.current_user.is_logged_in() else False)

        # self.ui.ps_upload_after_creation_checkBox.setEnabled(
        #     True if self.current_user.is_logged_in() else False)

        # self.ui.ui_upload_pushButton.setEnabled(
        #     True if self.current_user.is_logged_in() else False)

        # Playblast Settings
        value = self.sanitize(database.read_cache('ps_directory_lineEdit'))
        self.ui.ps_directory_lineEdit.setText(
            value if value else os.path.expanduser('~/Desktop/playblasts'))

        value = self.sanitize(database.read_cache('ps_clipname_lineEdit'))
        self.ui.ps_clipname_lineEdit.setText(value)

        value = database.read_cache('ps_play_after_creation_checkBox')
        self.ui.ps_play_after_creation_checkBox.setChecked(
            True if value == 'true' else False)

        value = database.read_cache('current_preset')
        self.ui.ui_formatPreset_comboBox.set_combobox_index(selection=value)

        self.populate_camera_comboBox()

        value = database.read_cache('current_range_type')
        self.ui.ui_range_comboBox.set_combobox_index(selection=value)

        # value = database.read_cache('ps_upload_after_creation_checkBox')
        # self.ui.ps_upload_after_creation_checkBox.setChecked(
        #     True if value == 'true' and self.current_user.is_logged_in() else False)

        value = database.read_cache('us_filename_lineEdit')
        self.ui.us_filename_lineEdit.setText(
            value if value else 'playblast')

        value = database.read_cache('ps_open_afterUpload_checkBox')
        self.ui.ps_open_afterUpload_checkBox.setChecked(
            True if value == 'true' else False)


        #Set FrameRange from the lider
        database.dump_cache({"frame_start":self.ui.ui_rangeIn_textEdit.text()})
        database.dump_cache({"frame_end":self.ui.ui_rangeOut_textEdit.text()})

        reviewId = database.read_cache('target_review_id')
        if reviewId and self.current_user.is_logged_in() :
            logger.info("Restoring reviewId section for : {} ".format(reviewId))
            review = getReviewById(self.ui.browser_treeWidget, reviewId=reviewId)
            logger.info("Restoring review section for : {} ".format(review))
            self.loadLeafs(review)


    def save_ui_state(self):
        ui_setting = {
            # Playblast Settings
            'ps_directory_lineEdit':
                self.sanitize(self.ui.ps_directory_lineEdit.text()),
            'ps_clipname_lineEdit':
                self.sanitize(self.ui.ps_clipname_lineEdit.text()),
            'current_range_type':
                self.ui.ui_range_comboBox.currentText(),
            'ps_play_after_creation_checkBox':
                self.bool_to_str(self.ui.ps_play_after_creation_checkBox.isChecked()),
            'ps_upload_after_creation_checkBox':
                self.bool_to_str(self.ui.ps_upload_after_creation_checkBox.isChecked()),
            'us_filename_lineEdit':
                self.ui.us_filename_lineEdit.text(),
            'ps_open_afterUpload_checkBox':
                self.bool_to_str(self.ui.ps_open_afterUpload_checkBox.isChecked())}
        database.dump_cache(ui_setting)


    def bool_to_str(self, val):
        strVal='true' if val else 'false'
        return strVal


    def sanitize(self, val):
        return val.rstrip().lstrip()


    def clear_ui_setting(self):
        database.dump_cache('clear')


    def build_connections(self):
        # Menu Bar
        self.ui.help_pushButton.clicked.connect(self.open_support)
        self.ui.login_pushButton.clicked.connect(self.connect_account)
        self.ui.upgrade_pushButton.clicked.connect(self.upgrade_plugin)
        self.ui.logout_pushButton.clicked.connect(self.disconnect_account)
        self.ui.syncsketchGUI_pushButton.clicked.connect(self.open_landing)
        self.ui.signup_pushButton.clicked.connect(self.open_signup)


        # Reviews
        self.ui.ui_record_pushButton.clicked.connect(self.playblast)
        self.ui.ui_upload_pushButton.clicked.connect(self.upload)

        self.ui.ui_download_pushButton.clicked.connect(self.download)

        self.ui.video_thumb_pushButton.clicked.connect(self.update_clip_thumb)

        #tree widget functions
        self.ui.browser_treeWidget.currentItemChanged.connect(self.validate_review_url)
        self.ui.browser_treeWidget.currentItemChanged.connect(self.currentItemChanged)
        self.ui.browser_treeWidget.doubleClicked.connect(self.open_upload_to_url)

        # Videos / Playblast Settings
        self.ui.ui_formatPreset_comboBox.currentIndexChanged.connect(self.update_current_preset)
        self.ui.ui_viewportpreset_comboBox.currentIndexChanged.connect(self.update_current_viewport_preset)
        self.ui.ui_cameraPreset_comboBox.currentIndexChanged.connect(self.update_current_camera)


        self.ui.ps_format_toolButton.clicked.connect(self.manage_preset)
        self.ui.ps_directory_toolButton.clicked.connect(self.get_directory_from_browser)

        self.ui.target_lineEdit.editingFinished.connect(self.select_item_from_target_input)

        # Videos / Playblast Settings
        self.ui.ui_viewport_toolButton.clicked.connect(self.manage_viewport_preset)

        self.ui.ui_range_toolButton.clicked.connect(self.set_in_out)
        self.ui.ui_camera_toolButton.clicked.connect(self.set_active_camera)

        self.ui.ui_range_comboBox.currentIndexChanged.connect(self.set_rangeFromComboBox)

        self.ui.ui_rangeIn_textEdit.textChanged.connect(self.store_frame)
        self.ui.ui_rangeOut_textEdit.textChanged.connect(self.store_frame)

        # Videos / Upload Settings
        self.ui.ui_open_pushButton.clicked.connect(self.open_upload_to_url)
        self.ui.ui_copyURL_pushButton.clicked.connect(self.copy_to_clipboard)


    def decorate_ui(self):
        file_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        directory_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        # Row 1
        # Setting up Main Layout
        indent = 9
        self.ui.master_layout.setSpacing(0)
        self.ui.ui_login_layout = QtWidgets.QHBoxLayout()
        self.ui.main_layout = QtWidgets.QGridLayout()
        self.ui.ui_status_layout = QtWidgets.QHBoxLayout()
        self.ui.ui_login_layout.setSpacing(0)
        self.ui.ui_status_layout.setContentsMargins(0, 0, 0, 10)
        self.ui.master_layout.addLayout(self.ui.ui_login_layout)
        self.ui.master_layout.addLayout(self.ui.ui_status_layout)
        self.ui.master_layout.addLayout(self.ui.main_layout)

        self.ui.main_layout.setSpacing(6)


        # Adding the two colums to main_layout
        self.ui.ui_mainLeft_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_mainRight_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_mainLeft_gridLayout.setSpacing(1)
        self.ui.ui_mainRight_gridLayout.setSpacing(2)
        self.ui.ui_reviewSelection_hBoxLayout = QtWidgets.QHBoxLayout()

        self.ui.main_layout.addLayout(self.ui.ui_mainLeft_gridLayout, 0, 0)
        self.ui.main_layout.addLayout(self.ui.ui_mainRight_gridLayout, 0, 1)

        self.ui.main_layout.setColumnMinimumWidth(0, 320)
        self.ui.main_layout.setColumnMinimumWidth(1, 320)
        self.ui.main_layout.setColumnStretch(0, 1)
        self.ui.main_layout.setColumnStretch(1, 0)

        # Adding ui_mainLeft_gridLayout
        self.ui.ui_record_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_clipSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_targetSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_targetSelection_gridLayout.setSpacing(3)

        self.ui.ui_record_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_record_groupbox)
        self.ui.ui_record_groupbox.setTitle('RECORD')
        self.ui.ui_record_groupbox.setLayout(self.ui.ui_record_gridLayout)

        self.ui.ui_upload_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_upload_groupbox)
        self.ui.ui_upload_groupbox.setTitle('FILE TO UPLOAD')
        self.ui.ui_upload_groupbox.setLayout(self.ui.ui_clipSelection_gridLayout)

        self.ui.ui_targetSelection_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_targetSelection_groupbox.setTitle('TARGET FOR UPLOAD')
        self.ui.ui_targetSelection_groupbox.setLayout(self.ui.ui_targetSelection_gridLayout)


        self.ui.ui_mainLeft_gridLayout.addLayout(self.ui.ui_record_gridLayout, 0, 0)
        self.ui.ui_mainLeft_gridLayout.addLayout(self.ui.ui_clipSelection_gridLayout, 1, 0)



        # Creating Review Selection Layout

        # - buttons for opening and copying to clipboard
        # - tree wdget
        self.ui.ui_treeWidget_layout = QtWidgets.QVBoxLayout()

        self.ui.browser_treeWidget = QtWidgets. QTreeWidget()


        self.ui.browser_treeWidget.header().setStyleSheet("color: %s"%success_color)

        highlight_palette = self.ui.browser_treeWidget.palette()
        highlight_palette.setColor(QtGui.QPalette.Highlight, highlight_color)
        self.ui.browser_treeWidget.setPalette(highlight_palette)
        self.ui.browser_treeWidget.setHeaderLabel('refresh')

        self.ui.browser_treeWidget.itemExpanded.connect(self.expandedTest)


        self.ui.browser_treeWidget.header().setSectionsClickable(True)
        self.ui.browser_treeWidget.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.ui.browser_treeWidget.header().sectionClicked.connect(self.refresh)
        self.ui.ui_treeWidget_layout.addWidget(self.ui.browser_treeWidget)


        self.ui.target_lineEdit = RegularLineEdit()
        self.ui.ui_open_pushButton = RegularToolButton(self, open_icon)
        self.ui.ui_copyURL_pushButton = RegularToolButton(self, copy_icon)
        self.ui.ui_reviewSelection_hBoxLayout.addWidget(self.ui.target_lineEdit)
        self.ui.ui_reviewSelection_hBoxLayout.addWidget(self.ui.ui_open_pushButton)
        self.ui.ui_reviewSelection_hBoxLayout.addWidget(self.ui.ui_copyURL_pushButton)


        self.ui.thumbnail_itemPreview = RegularThumbnail(width=320, height=180)
        self.ui.ui_mainRight_gridLayout.addWidget(self.ui.ui_targetSelection_groupbox)
        self.ui.ui_targetSelection_gridLayout.addLayout(self.ui.ui_treeWidget_layout)
        self.ui.ui_targetSelection_gridLayout.addLayout(self.ui.ui_reviewSelection_hBoxLayout)
        self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.thumbnail_itemPreview)
        self.ui.target_info_label = QtWidgets.QLabel()
        self.ui.target_info_label2 = QtWidgets.QLabel()

        # upload_layout -  format preset
        self.ui.upload_formatPreset_layout = RegularGridLayout(self, label='Format Preset')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_formatPreset_layout)
        self.ui.ui_formatPreset_comboBox = RegularComboBox(self)
        self.ui.ps_preset_description = QtWidgets.QLabel()
        self.ui.ps_preset_description.setStyleSheet("font: 9pt")
        self.ui.ps_preset_description.setIndent(5)
        self.ui.ps_format_toolButton = RegularToolButton(self, icon = file_icon)
        self.ui.upload_formatPreset_layout.addWidget(self.ui.ui_formatPreset_comboBox, 0, 1)
        self.ui.upload_formatPreset_layout.addWidget(self.ui.ps_format_toolButton, 0, 2)
        self.ui.upload_formatPreset_layout.addWidget(self.ui.ps_preset_description,  1, 1, 1, 2)

        # upload_layout - viewport preset
        self.ui.upload_viewportPreset_layout = RegularGridLayout(self, label='Viewport Preset')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_viewportPreset_layout)
        self.ui.ui_viewportpreset_comboBox = RegularComboBox(self)
        self.ui.ui_viewport_toolButton = RegularToolButton(self, icon = preset_icon)
        self.ui.upload_viewportPreset_layout.addWidget(self.ui.ui_viewportpreset_comboBox, 0, 1)
        self.ui.upload_viewportPreset_layout.addWidget(self.ui.ui_viewport_toolButton, 0, 2)

        # upload_layout - camera
        self.ui.upload_cameraPreset_layout = RegularGridLayout(self, label='Camera')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_cameraPreset_layout)
        self.ui.ui_cameraPreset_comboBox = RegularComboBox(self)
        self.ui.ui_camera_toolButton = RegularToolButton(self, icon = fill_icon)
        self.ui.upload_cameraPreset_layout.addWidget(self.ui.ui_cameraPreset_comboBox, 0, 1)
        self.ui.upload_cameraPreset_layout.addWidget(self.ui.ui_camera_toolButton, 0, 2)

        # upload_layout - range
        self.ui.upload_range_layout = RegularGridLayout(self, label='Frame Range')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_range_layout)
        self.ui.ui_range_comboBox = RegularComboBox(self)
        self.ui.ui_range_comboBox.addItems(["Start / End", "Time Slider","Highlighted","Current Frame"])
        self.ui.ui_range_toolButton = RegularToolButton(self, icon = fill_icon)
        self.ui.ui_rangeIn_textEdit  = RegularLineEdit()
        self.ui.ui_rangeOut_textEdit  = RegularLineEdit()
        self.ui.upload_range_layout.addWidget(self.ui.ui_range_comboBox, 0, 1)
        self.ui.upload_range_layout.addWidget(self.ui.ui_rangeIn_textEdit, 0, 2)
        self.ui.upload_range_layout.setColumnStretch(2,0)
        self.ui.upload_range_layout.addWidget(self.ui.ui_rangeOut_textEdit, 0, 3)
        self.ui.upload_range_layout.setColumnStretch(3,0)
        self.ui.ui_rangeIn_textEdit.setFixedWidth(40)
        self.ui.ui_rangeOut_textEdit.setFixedWidth(40)

        self.ui.ui_rangeIn_textEdit.setAlignment(QtCore.Qt.AlignRight)
        self.ui.ui_rangeOut_textEdit.setAlignment(QtCore.Qt.AlignRight)
        self.ui.upload_range_layout.addWidget(self.ui.ui_range_toolButton, 0, 4)

        self.onlyInt = QtGui.QIntValidator()
        self.ui.ui_rangeIn_textEdit.setValidator(self.onlyInt)
        self.ui.ui_rangeIn_textEdit.setPlaceholderText('Start')
        self.ui.ui_rangeOut_textEdit.setValidator(self.onlyInt)
        self.ui.ui_rangeOut_textEdit.setPlaceholderText('End')

        # upload_layout - Directory
        self.ui.upload_directory_layout = RegularGridLayout(self, label='Directory')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_directory_layout)
        self.ui.ps_directory_lineEdit = QtWidgets.QLineEdit()
        self.ui.ps_directory_lineEdit.setPlaceholderText('Output Directory')
        self.ui.ps_directory_toolButton = RegularToolButton(self, icon = directory_icon)
        self.ui.upload_directory_layout.addWidget(self.ui.ps_directory_lineEdit, 0, 1)
        self.ui.upload_directory_layout.addWidget(self.ui.ps_directory_toolButton, 0, 2)

        # record_layout - filename
        self.ui.upload_filename_layout = RegularGridLayout(self, label='Clip Name')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_filename_layout)
        self.ui.us_filename_lineEdit = QtWidgets.QLineEdit()
        self.ui.us_filename_lineEdit.setPlaceholderText('File Name or Prefix')
        self.ui.ps_filename_toolButton = RegularToolButton(self)

        self.ui.ps_filename_toolButton.setEnabled(0)
        self.ui.upload_filename_layout.addWidget(self.ui.us_filename_lineEdit, 0, 1)
        self.ui.upload_filename_layout.addWidget(self.ui.ps_filename_toolButton, 0, 2)

        # record_layout - clipname
        self.ui.upload_clipname_layout = RegularGridLayout(self, label='Clip Suffix ')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_clipname_layout)
        self.ui.ps_clipname_lineEdit = QtWidgets.QLineEdit()
        self.ui.ps_clipname_lineEdit.setPlaceholderText('Clip Suffix (optional)')
        self.ui.ps_clipname_toolButton = RegularToolButton(self)
        self.ui.ps_clipname_toolButton.setEnabled(0)
        self.ui.upload_clipname_layout.addWidget(self.ui.ps_clipname_lineEdit, 0, 1)
        self.ui.upload_clipname_layout.addWidget(self.ui.ps_clipname_toolButton, 0, 2)

        # record_layout - after record
        self.ui.upload_after_layout = RegularGridLayout(self, label='After Record')
        self.ui.ps_play_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_play_after_creation_checkBox.setChecked(True)
        self.ui.ps_play_after_creation_checkBox.setText('Play')
        self.ui.ps_upload_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_upload_after_creation_checkBox.setText('Upload')
        self.ui.upload_after_layout.addWidget(self.ui.ps_play_after_creation_checkBox, 0, 1)
        self.ui.upload_after_layout.addWidget(self.ui.ps_upload_after_creation_checkBox, 0, 2)
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_after_layout)
        # record_layout - record button
        self.ui.ui_record_pushButton = RegularButton(self, icon=record_icon, color=record_color)
        self.ui.ui_record_pushButton.setText("RECORD")
        self.ui.ui_record_gridLayout.addWidget(self.ui.ui_record_pushButton)

        # CLIP SELECTION
        # - - - - - - - - - -

        # - - -
        # record_layout - camera
        self.ui.ps_lastfile_line_edit = RegularLineEdit(self)

        self.ui.ps_lastfile_line_edit.setReadOnly(1)
        self.ui.video_thumb_pushButton = QtWidgets.QPushButton()
        self.ui.cs_info_label = QtWidgets.QLabel()
        self.ui.cs_info_label.setStyleSheet("font: 9pt")
        self.ui.video_thumb_pushButton.setContentsMargins(0, 0, 0, 0)

        self.ui.ui_thumb_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_thumb_gridLayout.setSpacing(3)
        self.ui.ui_clipSelection_gridLayout.addLayout(self.ui.ui_thumb_gridLayout)
        self.ui.video_thumbOverlay_pushButton = HoverButton(icon=play_icon)

        self.ui.ui_lastfile_layout = QtWidgets.QHBoxLayout()

        self.ui.ui_lastfileSelection_layout = QtWidgets.QHBoxLayout()
        self.ui.ps_filename_toolButton = RegularToolButton(self, icon=file_icon)
        self.ui.ps_filename_toolButton.clicked.connect(self.openFileNameDialog)
        self.ui.ui_lastfileSelection_layout.addWidget(self.ui.ps_lastfile_line_edit)
        self.ui.ui_lastfileSelection_layout.addWidget(self.ui.ps_filename_toolButton)


        self.ui.ui_thumb_gridLayout.addLayout(self.ui.ui_lastfileSelection_layout, 0, 0)
        self.ui.ui_thumb_gridLayout.addLayout(self.ui.ui_lastfile_layout,  1, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.video_thumb_pushButton, 2, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.video_thumbOverlay_pushButton, 2, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.cs_info_label, 3, 0)
        # To DO should be cleaner
        self.ui.video_thumbOverlay_pushButton.setIconSize(QtCore.QSize(320, 180))
        self.ui.video_thumbOverlay_pushButton.setToolTip('Play Clip')
        self.ui.video_thumbOverlay_pushButton.clicked.connect(self.play)


        self.ui.ui_clipSelection_gridLayout.setAlignment(QtCore.Qt.AlignCenter)
        # upload_layout - after upload
        self.ui.ps_record_after_layout = RegularGridLayout(self, label='After Upload')
        self.ui.ps_open_afterUpload_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_open_afterUpload_checkBox.setChecked(True)
        self.ui.ps_open_afterUpload_checkBox.setText('Open SyncSketch')
        self.ui.ps_afterUpload_label = QtWidgets.QLabel("After Upload")
        self.ui.ps_record_after_layout.addWidget(self.ui.ps_open_afterUpload_checkBox, 0, 1)
        self.ui.ui_clipSelection_gridLayout.addLayout(self.ui.ps_record_after_layout, 10)

        # ui_record_gridLayout
        self.ui.ui_upload_pushButton = RegularButton(self, icon = upload_icon, color=upload_color)
        self.ui.ui_upload_pushButton.setToolTip('Upload to SyncSketch Review Target')
        self.ui.ui_clipSelection_gridLayout.addWidget(self.ui.ui_upload_pushButton)


        # RIGHT PANEL
        # - - - - - - - - - -
        # download_layout
        self.ui.ui_download_pushButton = RegularButton(self, icon = download_icon, color=download_color)
        self.ui.ui_download_pushButton.setToolTip('Download from SyncSketch Review Target')
        self.ui.ui_download_pushButton.setText("DOWNLOAD")
        self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.ui_download_pushButton, 10)


        self.ui.ui_login_label = QtWidgets.QLabel()
        self.ui.ui_login_label.setText("You are not logged into SyncSketch")
        self.ui.ui_login_label.setMinimumHeight(header_size)
        self.ui.ui_login_label.setIndent(indent)
        self.ui.ui_login_label.setStyleSheet("background-color: rgba(255,255,255,.1);)")

        self.ui.syncsketchGUI_pushButton = RegularHeaderButton()
        self.ui.syncsketchGUI_pushButton.setIcon(logo_icon)
        self.ui.signup_pushButton = RegularHeaderButton()
        self.ui.signup_pushButton.setText("Sign Up")
        self.ui.logout_pushButton = RegularHeaderButton()
        self.ui.logout_pushButton.setText("Log Out")
        self.ui.login_pushButton = RegularHeaderButton()
        self.ui.login_pushButton.setText("Log In")
        self.ui.upgrade_pushButton = RegularHeaderButton()
        self.ui.upgrade_pushButton.hide()
        self.ui.upgrade_pushButton.setStyleSheet("color: %s"%success_color)

        self.ui.upgrade_pushButton.setText("Upgrade")
        self.ui.upgrade_pushButton.setToolTip("There is a new version")
        self.ui.help_pushButton = RegularHeaderButton()
        self.ui.help_pushButton.setIcon(help_icon)

        self.ui.ui_login_layout.addWidget(self.ui.syncsketchGUI_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.ui_login_label)

        self.ui.ui_login_layout.addWidget(self.ui.login_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.logout_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.signup_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.help_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.upgrade_pushButton)

        self.ui.ui_status_label = RegularStatusLabel()
        self.ui.ui_status_layout.addWidget(self.ui.ui_status_label)


        # populate UI
        filepath = os.path.expanduser('~/Desktop/playblasts')
        filepath = path.sanitize(filepath)
        self.ui.ps_directory_lineEdit.setText(filepath)

        self.ui.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, DEFAULT_PRESET)
        self.ui.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, DEFAULT_VIEWPORT_PRESET)
        self.update_last_recorded()

        self.ui.ui_range_comboBox.set_combobox_index(selection='Start / End')

        self.set_rangeFromComboBox()

    # * double check last item selected, looks like after this func, it stopped
    def expandedTest(self, target):

        """
        Select the item that is in the expanded hierarchy
        which triggers the load of items.
        """

        logger.info("Expanding treewidget: {}".format(target))
        selected_item = target
        #convert qmodelindex into a treewidget item
        item =  target #self.ui.browser_treeWidget.itemFromIndex(selected_item)
        try:
            logger.info("item.text {} selected_item {}".format(item.data(0, QtCore.Qt.EditRole), item.data(1, QtCore.Qt.EditRole)))
        except Exception as e:
            logger.info("Exception: ".format(e))
        item_type = item.data(2, QtCore.Qt.EditRole)
        if item_type == "review":
            logger.info("item_type is a review, expanding")
            if item.childCount() == 1 and not item.child(0).data(0, QtCore.Qt.EditRole):
                logger.info("Only single empty dummy item, delete and load childs")
                item.takeChildren()
                self.loadLeafs(item)
        else:
            logger.info("Not a review, nothing to expand")

            #User keeps pressing expand, so let's reload
            # * consolidate


            #item.setSelected(True)


    def disconnect_account(self):
        self.current_user.logout()
        logout_view()
        self.isloggedIn(self)
        self.ui.browser_treeWidget.clear()
        self.ui.ui_status_label.update('You have been successfully logged out', color=warning_color)
        self.restore_ui_state()
        #self.populate_review_panel(self,  force=True)

    def refresh(self):
        logger.info("Refresh Clicked, trying to refresh if logged in")
        #self.populate_review_panel(self, force=True)
        #self.asyncPopulateTree(withItems=False)
        self.populateTree()
        #self.repaint()

    def open_target_url(self):
        url = self.sanitize(self.ui.target_lineEdit.text())
        if url:
            webbrowser.open(path.make_url_offlineMode(url))


    def update_clip_thumb(self, imageWidget):
        last_recorded_file = database.read_cache('last_recorded')["filename"]
        imageWidget.setStyleSheet("background-color: rgba(0.2,0.2,0.2,1); border: none;")
        clippath = path.sanitize(last_recorded_file)
        fname = None
        try:
            fname = video.get_thumb(clippath)
        except:
            pass
        if not fname:
            imageWidget.setIcon(logo_icon)
        else:
            icon = _get_qicon(fname)
            imageWidget.setIcon(icon)
        imageWidget.setIconSize(QtCore.QSize(320, 180))
        self.setWindowIcon(logo_icon)


    def get_directory_from_browser(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.Directory
        options |= QtWidgets.QFileDialog.ShowDirsOnly
        options |= QtWidgets.QFileDialog.DontUseNativeDialog

        filePath = QtWidgets.QFileDialog.getExistingDirectory(self, options=options)

        if filePath:
            self.ui.ps_directory_lineEdit.setText(filePath)
            return filePath

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_filters = "All Files(*);; "

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_filters, options=options)
        self.ui.ps_lastfile_line_edit.setText(fileName)
        database.dump_cache({"last_recorded_selection": fileName})


    # todo refactor: this function does more than validation
    def validate_review_url(self, target = None):
        # self.populate_upload_settings()
        logger.info("Current Item changed")
        targetdata = update_target_from_tree(self, self.ui.browser_treeWidget)
        #todo: don't do that, that's very slow put this in the caching at the beginning
        #if target:
        #    logger.warning(self.current_user.get_review_data_from_id(targetdata['review_id']))
        #{'target_url_type': u'media', 'media_id': 692936, 'review_id': 300639, 'breadcrumb': '', 'target_url': 'https://syncsketch.com/sketch/300639#692936', 'upload_to_value': '', 'name': u'playblast'}
        self.ui.target_lineEdit.setText(database.read_cache('upload_to_value'))
        logger.info("target_lineEdit.setText validate_review_url: upload_to_value {}".format(database.read_cache('upload_to_value')))
        if target or targetdata:
            target = targetdata['target_url_type']

        ui_to_toggle = [
            self.ui.ui_download_pushButton,
            self.ui.ui_upload_pushButton,
            self.ui.ui_open_pushButton,
            self.ui.ps_upload_after_creation_checkBox,
            self.ui.ui_copyURL_pushButton,
            self.ui.ui_reviewSelection_hBoxLayout
        ]

        #todo remove sideffect
        if (target == "review") or (target == "media"):
            enable_interface(ui_to_toggle, True)
            self.ui.ui_status_label.update('Valid Review Selected.', color='LightGreen')
            logger.info("Review or Media, enabling UI")
        else:
            enable_interface(ui_to_toggle, False)
            self.ui.ui_status_label.update('Please select a review to upload to, using the tree widget or by entering a SyncSketch link', color=warning_color)
            self.ui.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)

        if target == "review":
            self.ui.ui_upload_pushButton.setText("UPLOAD\n Clip to Review '%s'"%targetdata["name"])
            # self.ui.us_ui_upload_pushButton.setStyleSheet(upload_color)

        elif target == "media":
            self.ui.ui_upload_pushButton.setText("UPLOAD\n Clip to Review '%s'"%targetdata["name"])
            # self.ui.us_ui_upload_pushButton.setStyleSheet(upload_color)x

            thumbURL = self.current_user.get_item_info(targetdata['media_id'])['objects'][0]['thumbnail_url']
            logger.info("thumbURL: {}".format(thumbURL))
            self.ui.thumbnail_itemPreview.set_icon_from_url(thumbURL)


        else:
            self.ui.ui_upload_pushButton.setText("CANNOT UPLOAD\nSelect a target to upload to(right panel)")



    # ==================================================================
    # Menu Item Functions

    def upgrade_plugin(self):
        from syncsketchGUI.installScripts.maintenance import handleUpgrade
        #attach the upgrader to the mainWindow so it doesn't go out of scope
        self.installer = handleUpgrade()

    def connect_account(self):

        if is_connected():
            _maya_delete_ui(LoginView.window_name)
            weblogin_window = LoginView(self)

        else:
            title='Not able to reach SyncSketch'
            message='Having trouble to connect to SyncSketch.\nMake sure you have an internet connection!'
            WarningDialog(self, title, message)

    def open_support(self):
        webbrowser.open(path.support_url)


    def open_contact(self):
        webbrowser.open(path.contact_url)

    def open_landing(self):
        webbrowser.open(path.home_url)

    def open_signup(self):
        webbrowser.open(path.signup_url)

    # ==================================================================
    # Reviews Tab Functions
    def open_player(self,url):
        PlayerView(self,url)

    def select_item_from_target_input(self, event=None):
        link = self.sanitize(self.ui.target_lineEdit.text())
        logger.info("Got Link from lineEdit: {}".format(link))

        if not link:
            link = database.read_cache('upload_to_value')
            logger.info("No link, reading from cache: {} ".format(link))
        #ids = get_ids_from_link(link)
        url_payload = parse_url_data(link)
        logger.info("url_payload: {} ".format(url_payload))


        currentItem = get_current_item_from_ids(self.ui.browser_treeWidget, url_payload, setCurrentItem=True)
        logger.info("current Item: {}".format(currentItem))

        if not currentItem:
            logger.info("Reviewitem does not exist, trying to load review and it's items{}".format(url_payload))

            iterator = QtWidgets.QTreeWidgetItemIterator(self.ui.browser_treeWidget, QtWidgets.QTreeWidgetItemIterator.All)

            while iterator.value():
                item = iterator.value()
                item_data = item.data(1, QtCore.Qt.EditRole)
                if item_data.get('uuid') == url_payload['uuid']:
                    logger.info("Found review with item_data: {} loading reviewItems ...".format(item_data))
                    #self.ui.browser_treeWidget.setCurrentItem(item, 1)
                    #self.ui.browser_treeWidget.scrollToItem(item)
                    self.loadLeafs(item)
                    break
                iterator +=1
            currentItem = get_current_item_from_ids(self.ui.browser_treeWidget, url_payload, setCurrentItem=True)



    # ==================================================================
    # Video Tab Functions

    def manage_preset(self):
        from syncsketchGUI.lib.gui.syncsketchWidgets.formatPresetWidget import FormatPresetWindow
        _maya_delete_ui(FormatPresetWindow.window_name)
        preset_window = FormatPresetWindow(self)
        preset_window.show()

    def manage_viewport_preset(self):
        from syncsketchGUI.lib.gui.syncsketchWidgets.viewportPresetWidget import ViewportPresetWindow
        _maya_delete_ui(ViewportPresetWindow.window_name)
        preset_viewport_window = ViewportPresetWindow(self)
        preset_viewport_window.show()

    # to do - should be able to wrap all of this in a single function
    # including synchronization

    def update_last_recorded(self, clips = None):
        try:
            clips = [clip["filename"] for clip in [database.read_cache('last_recorded')]]
        except:
            pass

        if clips:
            with suppressedUI(self.ui.ps_lastfile_line_edit):
                self.ui.ps_lastfile_line_edit.clear()
                self.ui.ps_lastfile_line_edit.setText(database.read_cache('last_recorded')['filename'])
            self.update_clip_info()


    def update_current_clip(self):
        val = self.ui.ps_lastfile_line_edit.text()
        database.dump_cache({'selected_clip': val})

        info_string='Please select a format preset'
        info_string = self.ui.ui_formatPreset_comboBox.currentText()
        format_preset_file = path.get_config_yaml(PRESET_YAML)
        data = database._parse_yaml(yaml_file = format_preset_file)[val]
        self.ui.ps_preset_description.setText("%s | %s | %sx%s "%(data["encoding"],data["format"],data["width"],data["height"]))


    def update_current_preset(self):
        val = self.ui.ui_formatPreset_comboBox.currentText()
        database.dump_cache({'current_preset': val})
        format_preset_file = path.get_config_yaml(PRESET_YAML)
        data = database._parse_yaml(yaml_file = format_preset_file)
        logger.info("data: {}".format(data))
        if data.has_key(val):
            data = data[val]
            #text = "%s | %s | %sx%s " %(data["encoding"], data["format"], data["width"], data["height"])
            text = "{} | {} | {}x{}".format(data["encoding"], data["format"], data["width"], data["height"])
        else:
            text = "no valid preset selected"
        self.ui.ps_preset_description.setText(text)


    def update_current_viewport_preset(self):
        val = self.ui.ui_viewportpreset_comboBox.currentText()
        database.dump_cache({'current_viewport_preset': val})


    def populate_camera_comboBox(self):
        value = database.read_cache('selected_camera')
        self.ui.ui_cameraPreset_comboBox.clear()
        active_cam = r"Active(%s)"%maya_scene.get_current_camera()
        self.cameras = [active_cam]
        self.cameras += maya_scene.get_available_cameras()
        self.ui.ui_cameraPreset_comboBox.addItems(self.cameras)
        logger.info("maya_scene.get_current_camera(): {}".format(maya_scene.get_current_camera()))
        self.ui.ui_cameraPreset_comboBox.set_combobox_index(selection=value, default=maya_scene.get_current_camera())


    def update_current_camera(self):
        logger.info("updating Camera")
        value = self.ui.ui_cameraPreset_comboBox.currentText()
        if not value or not len(value) or value == 'null':
            value = database.read_cache('selected_camera')
        if not value or value.startswith(r"Active"):
            camera = maya_scene.get_current_camera()
            database.dump_cache({'selected_camera': camera})
        else:
            database.dump_cache({'selected_camera': value})


    def store_frame(self):
        database.dump_cache({'frame_start': self.ui.ui_rangeIn_textEdit.text()})
        database.dump_cache({'frame_end': self.ui.ui_rangeOut_textEdit.text()})


    def open_upload_to_url(self):
        self.validate_review_url()
        url = path.make_url_offlineMode(database.read_cache('upload_to_value'))
        logger.info("Opening Url: {} ".format(url))
        if url:
            webbrowser.open(url)

    def playblast(self):
        # store current preset since subsequent calls will use that data exclusively
        # savedata
        self.save_ui_state()
        recordData = syncsketchGUI.record()
        playblast_file = recordData["playblast_file"]
        if not playblast_file:
            self.ui.ui_status_label.update('Playblast failed. %s'%message_is_not_connected , color=error_color)
            return

        playblast_filename = os.path.split(playblast_file)[-1]
        # self.ui.ps_clipname_lineEdit.setText(playblast_filename)
        self.ui.ui_status_label.update('Playblast file [{}] is created.'.format(playblast_filename))

        if self.ui.ps_upload_after_creation_checkBox.isChecked() and self.ui.ps_upload_after_creation_checkBox.isEnabled() :
            self.update_target_from_upload(recordData["uploaded_item"]['reviewURL'])
            logger.info("update_target_from_upload = {}".format(recordData["uploaded_item"]['reviewURL']))
        else:
            logger.info("Upload checkbox was not selected, returning here")
            return

        # Update the last recorded file and save the ui state
        # To do - need to update and selc the target url when item is updated
        if recordData.has_key('uploaded_item'):
            logger.info("uploaded_item %s"%recordData["uploaded_item"]["id"])

        #self.restore_ui_state()
        self.update_last_recorded()


    def set_active_camera(self):
        self.populate_camera_comboBox()
        self.ui.ui_cameraPreset_comboBox.set_combobox_index(selection=maya_scene.get_current_camera())

    def set_in_out(self, type="Time Slider"):
        range = maya_scene.get_InOutFrames(type)
        self.ui.ui_rangeIn_textEdit.setText(str(range[0]))
        self.ui.ui_rangeOut_textEdit.setText(str(range[1]))

    def manual_set_range(self, show=True):
        interface = [
            self.ui.ui_rangeIn_textEdit,
            self.ui.ui_rangeOut_textEdit,
            self.ui.ui_range_toolButton
        ]
        enable_interface(interface, show)

    def set_rangeFromComboBox(self):
        sel = self.ui.ui_range_comboBox.currentText()
        self.set_in_out(sel)
        if sel == r"Start / End":
            self.manual_set_range(True)
        else:
            self.manual_set_range(False)



    def update_clip_info(self):
        last_recorded_file = database.read_cache('last_recorded_selection')
        last_recorded_data = database.read_cache('last_recorded')
        # last_recorded_file = last_recorded_data["filename"]
        # last_recorded_file = path.sanitize(last_recorded_file)
        # Update Date / Time
        date_created = video.get_creation_date(last_recorded_file)
        if not date_created:
            date_created = str()

        # Update Info
        clip_info = video.probe(last_recorded_file)

        info_string = str()
        if not clip_info:
            error_message='N/A. Please check if the file exists.'
            self.ui.cs_info_label.setText(error_message)
            return

        if 'start_frame' in last_recorded_data.keys() and \
                        'end_frame' in last_recorded_data.keys():
            info_string += '[{} to {}]'.format(last_recorded_data['start_frame'],
                                             last_recorded_data['end_frame'])



        if 'avg_frame_rate' in clip_info['streams'][0].keys() and 'duration' in clip_info["format"].keys():
            base, diviser = clip_info["streams"][0]["avg_frame_rate"].split('/')
            duration = float(clip_info["format"]["duration"])
            fps =(float(base) / float(diviser))
            frames = int(duration * fps)
            info_string += ' {} Frames'.format(frames)

        if 'codec_name' in clip_info['streams'][0].keys():
            info_string += ' | {}'.format(clip_info['streams'][0]['codec_name'])

        if  'width' in clip_info['streams'][0].keys() and \
            'height' in clip_info['streams'][0].keys():
            info_string += ' | {}x{}'.format(clip_info['streams'][0]['width'],
                                                clip_info['streams'][0]['height'])

        self.ui.cs_info_label.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.ui.cs_info_label.setText(info_string + ' | ' +  date_created)

        self.ui.cs_info_label.setMinimumHeight(20)
        self.ui.setStyleSheet("QLabel {font-font-size : 10px; color: rgba(255,255,255,0.45)} ")
        self.update_clip_thumb(self.ui.video_thumb_pushButton)

    def play(self):
        syncsketchGUI.play()


    def update_target_from_upload(self, uploaded_media_url):
        logger.info("update_target_from_upload uploaded_media_url: {}".format(uploaded_media_url))
        if 'none' in uploaded_media_url.lower():
            uploaded_media_url = str()

        logger.info('Uploaded_media_url: %s'%uploaded_media_url)
        database.dump_cache({'us_last_upload_url_pushButton' : uploaded_media_url})
        self.ui.target_lineEdit.setText(uploaded_media_url)
        logger.info("target_lineEdit.setText {}".format(uploaded_media_url))

        self.select_item_from_target_input()
        #getReviewById(self.ui.browser_treeWidget, reviewId=reviewId)
        #self.ui.us_last_upload_url_pushButton.setText(uploaded_media_url)

        database.dump_cache({'upload_to_value' : uploaded_media_url})
        # todo this shouldn't be abstracted
        #self.refresh()



    def upload(self):
        # savedata
        logger.info("Upload only function")
        self.save_ui_state()

        uploaded_item = syncsketchGUI.upload()

        if not uploaded_item:
            self.ui.ui_status_label.update('Upload Failed, please check log', color=error_color)
            return

        self.update_target_from_upload(uploaded_item['reviewURL'])

        #Upload done let's set url from that
        if database.read_cache("us_last_upload_url_pushButton"):
            logger.info("target_lineEdit.setText: {}".format(database.read_cache("us_last_upload_url_pushButton")))
            self.ui.target_lineEdit.setText(database.read_cache("us_last_upload_url_pushButton"))
            self.select_item_from_target_input()
        else:
            logger.info("Nothing to set in the lineedit")

    # Upload Settings
    def download(self):
        logger.info("Download pressed")
        self.validate_review_url()
        show_download_window()
        return



    def copy_to_clipboard(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        link =  self.ui.target_lineEdit.text()
        # link = database.read_cache('us_last_upload_url_pushButton')
        cb.setText(link, mode=cb.Clipboard)


    def populate_upload_settings(self):
        if database.read_cache('target_url_type') not in ['account', 'project']:
            #todo yafes
            pass
            #self.ui.target_lineEdit.setText(database.read_cache('upload_to_value'))
            logger.info("database.read_cache('target_url_type') not in ['account', 'project']".format())
        else:
            self.ui.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)
            self.ui.target_lineEdit.setText(None)
            logger.info("target_lineEdit.setText: NONE".format())
        self.validate_review_url()
        # self.ui.us_name_lineEdit.setText(database.read_cache('target_url_type'))
        # self.ui.us_artist_lineEdit.setText(database.read_cache('target_url_username'))
        # self.ui.us_upload_to_pushButton.setText(database.read_cache('upload_to_value'))

    # ==================================================================
    # Tooltip Area Functions

    # loggedin window
    # todo: this is similar to is_logged_in, we might wan't to move it there
    def isloggedIn(self,loggedIn=False):
        if loggedIn:
            message =  "Successfully logged in as %s"%self.current_user.get_name()
            self.ui.ui_status_label.update(message, color = success_color)
        else:
            message = message_is_not_loggedin
            self.ui.ui_status_label.update(message, color=error_color)
        self.update_login_ui()


    # Tree Function
    def retrievePanelData(self):
        begin = time.time()
        if not is_connected():
            self.ui.ui_status_label.update(message_is_not_connected, color=error_color)
            self.isloggedIn(loggedIn=False)
            logger.info("\nNot connected to SyncSketch ...")
            return

        self.current_user = user.SyncSketchUser()
        logger.info("CurrentUser: {}".format(self.current_user))
        logger.info("isLoggedin: {}".format(self.current_user.is_logged_in()))
        # Always refresh Tree View
        self.ui.browser_treeWidget.clear()

        if self.current_user.is_logged_in():
            logger.info("User is logged in")

        else:
            logger.info("User is not logged in")
            return

        self.isloggedIn(self.current_user.is_logged_in())

        try:
            self.account_data = self.current_user.get_account_data()

        except Exception as err:
            self.account_data = None
            logger.info("err: {}".format(err))

        finally:
            if self.account_data:
                account_is_connected = True
                message='Connected and authorized with syncsketchGUI as "{}"'.format(self.current_user.get_name())
                color = success_color
            else:
                account_is_connected = False
                message='WARNING: Could not connect to SyncSketch. '
                message += message_is_not_connected
                color = error_color
            try:
                self.ui.ui_status_label.update(message, color)
            except:
                pass

        if not self.account_data or type(self.account_data) is dict:
            logger.info("Error: No SyncSketch account data found.")
            return

        logger.info("Account preperation took: {0}".format(time.time() - begin))
        return self.account_data

    def populate_review_panel(self, account_data=None, item_to_add = None, force = False):
        if not account_data:
            logger.info("No account_data found")
            return

        logger.info("account_data: {}".format(account_data))
        for account in account_data:
            account_treeWidgetItem = self._build_widget_item(parent = self.ui.browser_treeWidget,
                                                            item_name = account.get('name'),
                                                            item_type='account',
                                                            item_icon = account_icon,
                                                            item_data = account)
            # Add projects
            projects = account.get('projects')
            for project in projects:
                project_treeWidgetItem = self._build_widget_item(parent = account_treeWidgetItem,
                                                                item_name = project.get('name'),
                                                                item_type='project',
                                                                item_icon = project_icon,
                                                                item_data = project)
                # Add reviews
                reviews = project.get('reviews')

                for review in reviews:
                    review_treeWidgetItem = self._build_widget_item(parent = project_treeWidgetItem,
                                                                item_name = review.get('name'),
                                                                item_type='review',
                                                                item_icon = review_icon,
                                                                item_data = review)
                    # Add items
                    items = review.get('items')
                    # * If there are no reviews, create still a dumy element to get an arrow icon
                    # * to visualize that the item needs to be expanded
                    for media in items or [{'uuid':'', 'type':'video'}]:
                        #add UUID of the review container to the media, so we can use it in itemdata
                        media['uuid'] = review['uuid']
                        if not media.get('type'):
                            specified_media_icon = media_unknown_icon
                        elif 'video' in media.get('type').lower():
                            specified_media_icon = media_video_icon
                        elif 'image' in media.get('type').lower():
                            specified_media_icon = media_image_icon
                        elif 'sketchfab' in media.get('type').lower():
                            specified_media_icon = media_sketchfab_icon
                        else:
                            specified_media_icon = media_unknown_icon

                        media_treeWidgetItem = self._build_widget_item(parent = review_treeWidgetItem,
                                                                    item_name = media.get('name'),
                                                                    item_type='media',
                                                                    item_icon = specified_media_icon,
                                                                    item_data = media)

                        media_treeWidgetItem.sizeHint(80)

        logger.info("uploaded_to_value: {}".format(database.read_cache('upload_to_value')))
        url_payload = parse_url_data(database.read_cache('upload_to_value'))
        logger.info("url_payload: {}".format(url_payload))
        get_current_item_from_ids(self.ui.browser_treeWidget, url_payload, setCurrentItem=True)

        USER_ACCOUNT_DATA = account_data

        self.populate_upload_settings()
        return account_data

    def _build_widget_item(self, parent, item_name, item_type, item_icon, item_data):
        treewidget_item = QtWidgets.QTreeWidgetItem(parent, [item_name])
        treewidget_item.setData(1, QtCore.Qt.EditRole, item_data)
        treewidget_item.setData(2, QtCore.Qt.EditRole, item_type)
        treewidget_item.setIcon(0, item_icon)
        return treewidget_item