import os
import time

from syncsketchGUI.vendor.Qt import QtCore, QtGui, QtWidgets

from syncsketchGUI.lib import user
from syncsketchGUI.literals import message_is_not_connected

from syncsketchGUI.installScripts.maintenance import get_latest_setup_py_file_from_local

from . import qt_browser
from . import qt_menu
from . import qt_recorder
from . import qt_upload
from . import qt_presets
from . import qt_utils
from . import qt_windows

import logging

logger = logging.getLogger("syncsketchGUI")


class MenuWindow(qt_windows.SyncSketchWindow):
    """
    Main browser window of the syncsketchGUI services
    """
    window_name = 'syncsketchGUI_menu_window'
    window_label = 'SyncSketch'

    account_is_connected = False

    def __init__(self, parent=None):
        super(MenuWindow, self).__init__(parent=parent)

        self.installer = None

        self.setMaximumSize(700, 650)
        self.setWindowTitle("Syncsketch - Version: {}".format(get_latest_setup_py_file_from_local()))

        self._create_ui()
        self._layout_ui()
        self._connect_ui()
        self._restore_ui()

    def closeEvent(self, event):
        logger.info("Closing Window")
        event.accept()

    def _create_ui(self):

        self._ui_upload = qt_upload.UploadWidget()
        self._ui_menu = qt_menu.MenuWidget()
        self._ui_recorder = qt_recorder.MayaPlayblastRecorderWidget()
        self._ui_browser = qt_browser.ReviewBrowserWidget()

    def _connect_ui(self):

        # Menu
        self._ui_menu.logged_out.connect(self._ui_browser.refresh)
        self._ui_menu.logged_in.connect(self._ui_browser.refresh)

        # Upload
        self._ui_upload.uploaded.connect(self.item_uploaded)

        # Recorder
        self._ui_recorder.recorded.connect(self.update_record)
        self._ui_recorder.uploaded.connect(self._ui_browser.update_target_from_url)

        # Browser
        self._ui_browser.target_changed.connect(self.target_changed)

    def _layout_ui(self):

        # Adding the two colums to main_layout
        lay_grid_left = QtWidgets.QGridLayout()
        lay_grid_left.setSpacing(1)

        lay_grid_left.addWidget(self._ui_recorder, 0, 0)
        lay_grid_left.addWidget(self._ui_upload, 1, 0)

        lay_vbox_right = QtWidgets.QVBoxLayout()
        lay_vbox_right.setSpacing(2)
        lay_vbox_right.addWidget(self._ui_browser)

        lay_grid_main = QtWidgets.QGridLayout()
        lay_grid_main.setSpacing(6)
        lay_grid_main.setColumnMinimumWidth(0, 320)
        lay_grid_main.setColumnMinimumWidth(1, 320)
        lay_grid_main.setColumnStretch(0, 1)
        lay_grid_main.setColumnStretch(1, 0)

        lay_grid_main.addLayout(lay_grid_left, 0, 0)
        lay_grid_main.addLayout(lay_vbox_right, 0, 1)

        lay_vbox_master = QtWidgets.QVBoxLayout()
        lay_vbox_master.setSpacing(0)
        lay_vbox_master.addWidget(self._ui_menu)
        lay_vbox_master.addLayout(lay_grid_main)

        self.lay_main.addLayout(lay_vbox_master)

    @QtCore.Slot(str)
    def update_record(self, file):
        logger.debug('Update Record Slot triggerd with File [{}]'.format(file))
        if file:
            playblast_filename = os.path.split(file)[-1]
            self._ui_menu.set_status('Playblast file [{}] is created.'.format(playblast_filename))
            self._ui_upload.update_last_recorded()
        else:
            self._ui_menu.set_status('Playblast failed.', color=qt_presets.error_color)

    QtCore.Slot(str)
    def target_changed(self, targetdata):
        ui_to_toggle = [
            self._ui_upload.ui_upload_pushButton,
            self._ui_recorder.ps_upload_after_creation_checkBox,
        ]

        target = targetdata['target_url_type']

        if (target == "review") or (target == "media"):
            qt_utils.enable_interface(ui_to_toggle, True)
            self._ui_menu.set_status('Valid Review Selected.', color='LightGreen')
            self._ui_upload.ui_upload_pushButton.setText("UPLOAD\n Clip to Review '%s'" % targetdata["name"])
            logger.info("Review or Media, enabling UI")
        else:
            qt_utils.enable_interface(ui_to_toggle, False)
            self._ui_menu.set_status(
                'Please select a review to upload to, using the tree widget or by entering a SyncSketch link',
                color=qt_presets.warning_color)
            self._ui_upload.ui_upload_pushButton.setText("CANNOT UPLOAD\nSelect a target to upload to(right panel)")

    QtCore.Slot(dict)

    def item_uploaded(self, uploaded_item):

        if not uploaded_item:
            self._ui_menu.set_status('Upload Failed, please check log', color=qt_presets.error_color)
            return

        self._ui_browser.update_target_from_url(uploaded_item['reviewURL'])

    def _restore_ui(self):
        logger.info("restoring ui state")

    def retrieve_panel_data(self):
        begin = time.time()
        logger.warning("Use of deprecated function retrievePanelData")
        current_user = user.SyncSketchUser()

        try:
            self.account_data = current_user.get_account_data()
        except Exception as err:
            self.account_data = None
            logger.info("err: {}".format(err))

        finally:
            if self.account_data:
                message = 'Connected and authorized with syncsketchGUI as "{}"'.format(current_user.get_name())
                color = qt_presets.success_color
            else:
                message = 'WARNING: Could not connect to SyncSketch. '
                message += message_is_not_connected
                color = qt_presets.error_color

        if not self.account_data or type(self.account_data) is dict:
            logger.info("Error: No SyncSketch account data found.")
            return

        logger.info("Account preparation took: {0}".format(time.time() - begin))
        return self.account_data
