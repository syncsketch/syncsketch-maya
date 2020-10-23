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

import mayaCaptureWidget
import browser_widget



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


        #self.restore_ui_state()
        #Populate Treewidget with all items
        #self.asyncPopulateTree(withItems=True)
        self.restore_ui_state()



    def storeAccountData(self, s):
        logger.info(s)
        self.accountData = s



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

        value = database.read_cache('ps_open_afterUpload_checkBox')
        self.ui.ps_open_afterUpload_checkBox.setChecked(
            True if value == 'true' else False)

        reviewId = database.read_cache('target_review_id')
        if reviewId and self.current_user.is_logged_in() :
            logger.info("Restoring reviewId section for : {} ".format(reviewId))
            review = getReviewById(self.browser_widget.browser_treeWidget, reviewId=reviewId)
            logger.info("Restoring review section for : {} ".format(review))
            self.browser_widget.loadLeafs(review)


    def save_ui_state(self):
        ui_setting = {
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
        self.ui.ui_upload_pushButton.clicked.connect(self.upload)

        

        self.ui.video_thumb_pushButton.clicked.connect(self.update_clip_thumb)

        # Recorder
        self.ui.record_app.recorded.connect(self.update_record)
        self.ui.record_app.uploaded.connect(self.browser_widget.update_upload)

        # Browser
        self.browser_widget.target_changed.emit(self.target_changed)

    def decorate_ui(self):
        file_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        directory_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)


        self.ui.video_thumb_pushButton = QtWidgets.QPushButton()
        self.ui.video_thumb_pushButton.setContentsMargins(0, 0, 0, 0)
        
        # Used ?
        self.ui.ui_lastfile_layout = QtWidgets.QHBoxLayout()


        self.ui.cs_info_label = QtWidgets.QLabel()
        self.ui.cs_info_label.setStyleSheet("font: 9pt")

        self.ui.ps_lastfile_line_edit = RegularLineEdit(self)
        self.ui.ps_lastfile_line_edit.setReadOnly(1)
        
        self.ui.ps_filename_toolButton = RegularToolButton(self, icon=file_icon)
        self.ui.ps_filename_toolButton.clicked.connect(self.openFileNameDialog)

        self.ui.ui_lastfileSelection_layout = QtWidgets.QHBoxLayout()
        self.ui.ui_lastfileSelection_layout.addWidget(self.ui.ps_lastfile_line_edit)
        self.ui.ui_lastfileSelection_layout.addWidget(self.ui.ps_filename_toolButton)


        # To DO should be cleaner
        self.ui.video_thumbOverlay_pushButton = HoverButton(icon=play_icon)
        self.ui.video_thumbOverlay_pushButton.setIconSize(QtCore.QSize(320, 180))
        self.ui.video_thumbOverlay_pushButton.setToolTip('Play Clip')
        self.ui.video_thumbOverlay_pushButton.clicked.connect(self.play)


        # upload_layout - after upload
        
        self.ui.ps_open_afterUpload_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_open_afterUpload_checkBox.setChecked(True)
        self.ui.ps_open_afterUpload_checkBox.setText('Open SyncSketch')

        self.ui.ps_afterUpload_label = QtWidgets.QLabel("After Upload")

        self.ui.ps_record_after_layout = RegularGridLayout(self, label='After Upload')
        self.ui.ps_record_after_layout.addWidget(self.ui.ps_open_afterUpload_checkBox, 0, 1)
        
        self.ui.ui_upload_pushButton = RegularButton(self, icon = upload_icon, color=upload_color)
        self.ui.ui_upload_pushButton.setToolTip('Upload to SyncSketch Review Target')
        

        self.ui.ui_thumb_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_thumb_gridLayout.setSpacing(3)
        self.ui.ui_thumb_gridLayout.addLayout(self.ui.ui_lastfileSelection_layout, 0, 0)
        self.ui.ui_thumb_gridLayout.addLayout(self.ui.ui_lastfile_layout,  1, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.video_thumb_pushButton, 2, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.video_thumbOverlay_pushButton, 2, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.cs_info_label, 3, 0)

        # Adding ui_mainLeft_gridLayout
        self.ui.ui_clipSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_clipSelection_gridLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.ui_clipSelection_gridLayout.addLayout(self.ui.ui_thumb_gridLayout)
        self.ui.ui_clipSelection_gridLayout.addWidget(self.ui.ui_upload_pushButton)
        self.ui.ui_clipSelection_gridLayout.addLayout(self.ui.ps_record_after_layout, 10)

        self.ui.ui_upload_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_upload_groupbox.setTitle('FILE TO UPLOAD')
        self.ui.ui_upload_groupbox.setLayout(self.ui.ui_clipSelection_gridLayout)



        # LOGIN 
        indent = 9
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

        self.ui.ui_login_layout = QtWidgets.QHBoxLayout()
        self.ui.ui_login_layout.setSpacing(0)

        self.ui.ui_login_layout.addWidget(self.ui.syncsketchGUI_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.ui_login_label)
        self.ui.ui_login_layout.addWidget(self.ui.login_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.logout_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.signup_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.help_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.upgrade_pushButton)

        self.ui.ui_status_label = RegularStatusLabel()
        
        self.ui.ui_status_layout = QtWidgets.QHBoxLayout()
        self.ui.ui_status_layout.addWidget(self.ui.ui_status_label)
        self.ui.ui_status_layout.setContentsMargins(0, 0, 0, 10)


        # Capture Widget
        self.ui.record_app = mayaCaptureWidget.MayaCaptureWidget()

        # REVIEW TREE
        self.browser_widget = browser_widget.BrowserWidget()


        # Adding the two colums to main_layout
        self.ui.ui_mainLeft_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_mainLeft_gridLayout.setSpacing(1)

        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.record_app, 0, 0)
        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_upload_groupbox)
        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_upload_groupbox, 1, 0)

        self.ui.ui_mainRight_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_mainRight_gridLayout.setSpacing(2)
        self.ui.ui_mainRight_gridLayout.addWidget(self.browser_widget)
        
        self.ui.main_layout = QtWidgets.QGridLayout()
        self.ui.main_layout.setSpacing(6)
        self.ui.main_layout.setColumnMinimumWidth(0, 320)
        self.ui.main_layout.setColumnMinimumWidth(1, 320)
        self.ui.main_layout.setColumnStretch(0, 1)
        self.ui.main_layout.setColumnStretch(1, 0)

        self.ui.main_layout.addLayout(self.ui.ui_mainLeft_gridLayout, 0, 0)
        self.ui.main_layout.addLayout(self.ui.ui_mainRight_gridLayout, 0, 1)


        self.ui.master_layout.setSpacing(0)
        self.ui.master_layout.addLayout(self.ui.ui_login_layout)
        self.ui.master_layout.addLayout(self.ui.ui_status_layout)
        self.ui.master_layout.addLayout(self.ui.main_layout)

        


        # populate UI
        self.update_last_recorded()

    @QtCore.Slot(str)
    def update_record(self, file):
        logger.debug('Update Record Slot triggerd with File [{}]'.format(file))
        if file:
            playblast_filename = os.path.split(file)[-1]
            self.ui.ui_status_label.update('Playblast file [{}] is created.'.format(playblast_filename))
            self.update_last_recorded() 
        else:
            self.ui.ui_status_label.update('Playblast failed. %s'%message_is_not_connected , color=error_color)

    QtCore.Slot(str)
    def target_changed(self, targetdata):
        ui_to_toggle = [
            self.ui.ui_upload_pushButton,
            self.ui.ui_open_pushButton,
            self.ui.record_app.ps_upload_after_creation_checkBox,
        ]

        target = targetdata['target_url_type']

        if (target == "review") or (target == "media"):
            enable_interface(ui_to_toggle, True)
            self.ui.ui_status_label.update('Valid Review Selected.', color='LightGreen')
            self.ui.ui_upload_pushButton.setText("UPLOAD\n Clip to Review '%s'"%targetdata["name"])
            logger.info("Review or Media, enabling UI")
        else:
            enable_interface(ui_to_toggle, False)
            self.ui.ui_status_label.update('Please select a review to upload to, using the tree widget or by entering a SyncSketch link', color=warning_color)
            self.ui.ui_upload_pushButton.setText("CANNOT UPLOAD\nSelect a target to upload to(right panel)")
    
            


    def disconnect_account(self):
        self.current_user.logout()
        logout_view()
        self.isloggedIn(self)
        self.browser_widget.browser_treeWidget.clear()
        self.ui.ui_status_label.update('You have been successfully logged out', color=warning_color)
        self.restore_ui_state()
        #self.populate_review_panel(self,  force=True)





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

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_filters = "All Files(*);; "

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_filters, options=options)
        self.ui.ps_lastfile_line_edit.setText(fileName)
        database.dump_cache({"last_recorded_selection": fileName})


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



    # ==================================================================
    # Video Tab Functions


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

    ### Not used
    def update_current_clip(self):
        val = self.ui.ps_lastfile_line_edit.text()
        database.dump_cache({'selected_clip': val})

        info_string='Please select a format preset'
        info_string = self.ui.ui_formatPreset_comboBox.currentText()
        format_preset_file = path.get_config_yaml(PRESET_YAML)
        data = database._parse_yaml(yaml_file = format_preset_file)[val]
        self.ui.ps_preset_description.setText("%s | %s | %sx%s "%(data["encoding"],data["format"],data["width"],data["height"]))





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


    def upload(self):
        # savedata
        logger.info("Upload only function")
        self.save_ui_state()

        uploaded_item = syncsketchGUI.upload()

        if not uploaded_item:
            self.ui.ui_status_label.update('Upload Failed, please check log', color=error_color)
            return

        self.browser_widget.update_target_from_upload(uploaded_item['reviewURL'])

        #Upload done let's set url from that
        if database.read_cache("us_last_upload_url_pushButton"):
            logger.info("target_lineEdit.setText: {}".format(database.read_cache("us_last_upload_url_pushButton")))
            self.browser_widget.target_lineEdit.setText(database.read_cache("us_last_upload_url_pushButton"))
            self.browser_widget.select_item_from_target_input()
        else:
            logger.info("Nothing to set in the lineedit")


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
        self.browser_widget.browser_treeWidget.clear()

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
