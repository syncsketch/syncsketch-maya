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
from syncsketchGUI.gui import parse_url_data, set_tree_selection, getReviewById
from syncsketchGUI.lib.gui.icons import _get_qicon
from syncsketchGUI.lib.gui.literals import DEFAULT_VIEWPORT_PRESET, PRESET_YAML, VIEWPORT_YAML, DEFAULT_PRESET, uploadPlaceHolderStr, message_is_not_loggedin, message_is_not_connected
from syncsketchGUI.lib.async import Worker, WorkerSignals
from syncsketchGUI.installScripts.maintenance import getLatestSetupPyFileFromLocal, getVersionDifference

import mayaCaptureWidget
import browser_widget
import menu_widget
import upload_widget

class MenuWindow(SyncSketch_Window):
    """
    Main browser window of the syncsketchGUI services
    """
    window_name='syncsketchGUI_menu_window'
    window_label='SyncSketch'

    account_is_connected = False

    def __init__(self, parent):
        super(MenuWindow, self).__init__(parent=parent)
        #self.threadpool = QtCore.QThreadPool()
        #self.threadpool.setMaxThreadCount(1)
        # self.accountData = None


        self.installer = None

        self.setMaximumSize(700, 650)
        self.decorate_ui()
        # populate UI

        self.build_connections()
        #self.accountData = self.retrievePanelData()


        # Load UI state
        #self.update_login_ui()

        #Not logged in or outdated api, token
        self.setWindowTitle("Syncsketch - Version: {}".format(getLatestSetupPyFileFromLocal()))
        # if not self.accountData:
        #     self.restore_ui_state()
        #     return


        #self.restore_ui_state()
        #Populate Treewidget with all items
        #self.asyncPopulateTree(withItems=True)
        self.restore_ui_state()


    # TODO: delete if not needed
    # def storeAccountData(self, s):
    #     logger.info(s)
    #     self.accountData = s



    # def fetchData(self, user, logging=None, withItems=False):
    #     '''
    #     Meant to be called from a thread, access only local names
    #     '''
    #     try:
    #         account_data = user.get_account_data(withItems=withItems)
    #         if logging:
    #             pass
    #             #logging.warning('accountdata: '.format(account_data))
    #     except Exception as err:
    #         return None

    #     return account_data

    def closeEvent(self, event):
        logger.info("Closing Window")
        event.accept()




    def build_connections(self):
        # Menu Bar

        self.menu_widget.logged_out.connect(self.browser_widget.clear)
        self.menu_widget.logged_in.connect(self.browser_widget.refresh)
        #self.menu_widget.logged_out.connect(self.restore_ui_state)

        # Reviews
        

        # Upload
        self.upload_widget.uploaded.connect(self.item_uploaded)

        # Recorder
        self.ui.record_app.recorded.connect(self.update_record)
        self.ui.record_app.uploaded.connect(self.browser_widget.update_target_from_url)

        # Browser
        self.browser_widget.target_changed.emit(self.target_changed)
        

    def decorate_ui(self):
        

        self.upload_widget = upload_widget.UploadWidget()
        self.menu_widget = menu_widget.MenuWidget()
        self.ui.record_app = mayaCaptureWidget.MayaCaptureWidget()
        self.browser_widget = browser_widget.BrowserWidget()


        # Adding the two colums to main_layout
        self.ui.ui_mainLeft_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_mainLeft_gridLayout.setSpacing(1)

        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.record_app, 0, 0)
        #self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_upload_groupbox)
        self.ui.ui_mainLeft_gridLayout.addWidget(self.upload_widget, 1, 0)

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
        self.ui.master_layout.addWidget(self.menu_widget)
        self.ui.master_layout.addLayout(self.ui.main_layout)

        
    @QtCore.Slot(str)
    def update_record(self, file):
        logger.debug('Update Record Slot triggerd with File [{}]'.format(file))
        if file:
            playblast_filename = os.path.split(file)[-1]
            self.menu_widget.set_status('Playblast file [{}] is created.'.format(playblast_filename))
            self.upload_widget.update_last_recorded() 
        else:
            self.menu_widget.set_status('Playblast failed. %s'%message_is_not_connected , color=error_color)

    QtCore.Slot(str)
    def target_changed(self, targetdata):
        ui_to_toggle = [
            self.upload_widget.ui_upload_pushButton,
            self.upload_widget.ui_open_pushButton,
            self.ui.record_app.ps_upload_after_creation_checkBox,
        ]

        target = targetdata['target_url_type']

        if (target == "review") or (target == "media"):
            enable_interface(ui_to_toggle, True)
            self.menu_widget.set_status('Valid Review Selected.', color='LightGreen')
            self.upload_widget.ui_upload_pushButton.setText("UPLOAD\n Clip to Review '%s'"%targetdata["name"])
            logger.info("Review or Media, enabling UI")
        else:
            enable_interface(ui_to_toggle, False)
            self.menu_widget.set_status('Please select a review to upload to, using the tree widget or by entering a SyncSketch link', color=warning_color)
            self.upload_widget.ui_upload_pushButton.setText("CANNOT UPLOAD\nSelect a target to upload to(right panel)")
    
            
    QtCore.Slot(dict)
    def item_uploaded(self, uploaded_item):
      
        if not uploaded_item:
            self.menu_widget.set_status('Upload Failed, please check log', color=error_color)
            return

        self.browser_widget.update_target_from_url(uploaded_item['reviewURL'])

        #Upload done let's set url from that
        # if database.read_cache("us_last_upload_url_pushButton"):
        #     logger.info("target_lineEdit.setText: {}".format(database.read_cache("us_last_upload_url_pushButton")))
        #     self.browser_widget.target_lineEdit.setText(database.read_cache("us_last_upload_url_pushButton"))
        #     self.browser_widget.select_item_from_target_input()
        # else:
        #     logger.info("Nothing to set in the lineedit")

        #self.populate_review_panel(self,  force=True)


    def restore_ui_state(self):
        logger.info("restoring ui state")
        
        #self.browser_widget.restore_ui_state()

        # self.ui.ui_record_pushButton.setEnabled(
        #     True if self.current_user.is_logged_in() else False)

        # self.ui.ps_upload_after_creation_checkBox.setEnabled(
        #     True if self.current_user.is_logged_in() else False)

        # self.ui.ui_upload_pushButton.setEnabled(
        #     True if self.current_user.is_logged_in() else False)

        

    # TODO: Delete if not needed
    # def update_current_clip(self):
    #     val = self.ui.ps_lastfile_line_edit.text()
    #     database.dump_cache({'selected_clip': val})

    #     info_string='Please select a format preset'
    #     info_string = self.ui.ui_formatPreset_comboBox.currentText()
    #     format_preset_file = path.get_config_yaml(PRESET_YAML)
    #     data = database._parse_yaml(yaml_file = format_preset_file)[val]
    #     self.ui.ps_preset_description.setText("%s | %s | %sx%s "%(data["encoding"],data["format"],data["width"],data["height"]))

    # TODO: Delete if not needed
    # def sanitize(self, val):
    #     return val.rstrip().lstrip()

    # TODO: Delete if not needed
    # def clear_ui_setting(self):
    #     database.dump_cache('clear')

    # FIXME: needed ?
    # def open_contact(self):
    #     webbrowser.open(path.contact_url)


    # Reviews Tab Functions
    # TODO: Delelte if not needed
    # def open_player(self,url):
    #     PlayerView(self,url)


    def retrievePanelData(self):
        begin = time.time()

        logger.warn("Use of deprecated function retrievePanelData")
        
        
        # Always refresh Tree View
        #self.browser_widget.browser_treeWidget.clear()


        current_user = user.SyncSketchUser()

        try:
            self.account_data = current_user.get_account_data()

        except Exception as err:
            self.account_data = None
            logger.info("err: {}".format(err))

        finally:
            if self.account_data:
                message='Connected and authorized with syncsketchGUI as "{}"'.format(current_user.get_name())
                color = success_color
            else:
                message='WARNING: Could not connect to SyncSketch. '
                message += message_is_not_connected
                color = error_color
            
        if not self.account_data or type(self.account_data) is dict:
            logger.info("Error: No SyncSketch account data found.")
            return

        logger.info("Account preperation took: {0}".format(time.time() - begin))
        return self.account_data
