from syncsketchGUI.vendor.Qt import QtWidgets, QtCore, QtGui

from syncsketchGUI.lib import connection
from syncsketchGUI.lib import user

import qt_presets

import logging
logger = logging.getLogger("syncsketchGUI")

class SyncSketchWindow(QtWidgets.QMainWindow):
    """
    SyncSketch Main Preset Window Class
    """
    window_name = 'syncsketch_window'
    window_label = 'SyncSketch'

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        MAYA = True
        self.setWindowFlags(QtCore.Qt.Window)

#        self.ui.master_layout.setMargin(0)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.parent = parent

        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        
        self.setWindowIcon(qt_presets.logo_icon)

        self.ui = QtWidgets.QWidget()
        self.lay_main = QtWidgets.QVBoxLayout()
        self.ui.setLayout(self.lay_main)
        self.setCentralWidget(self.ui)


        if MAYA:
            self.setProperty('saveWindowPref', True)

        self.align_to_center(self.parent)



    def align_to_center(self, align_object):
        """
        If the UI has a parent, align to it.
        If not, align to the center of the desktop.
        """
        ui_size = self.geometry()

        if align_object:
            align_object_center = align_object.frameGeometry().center()
            x_coordinate = align_object_center.x() -(ui_size.width() / 2)
            y_coordinate = align_object_center.y() -(ui_size.height() / 2)

        else:
            desktop_screen = QtWidgets.QDesktopWidget().screenGeometry()
            x_coordinate =(desktop_screen.width() - ui_size.width()) / 2
            y_coordinate =(desktop_screen.height() - ui_size.height()) / 2

        self.move(x_coordinate, y_coordinate)
        return self.geometry()

    def cancel(self):
        logger.info("Closing Synsketch GUI Window")
        self.close()

    def update_login_ui(self): # TODO: Evaluate if neccessary here and maybe removed
        '''
        Updates the UI based on whether the user is logged in
        '''
        logger.warning("This function might become depracted in near future")
        self.current_user = user.SyncSketchUser()
        if self.current_user.is_logged_in() and connection.is_connected():
            logger.info("self.current_user.is_logged_in() {} is_connected() {} ".format(self.current_user.is_logged_in(),is_connected() ))
            username = self.current_user.get_name()
            self.ui.ui_login_label.setText("Logged into SyncSketch as \n%s" % username)
            self.ui.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
            self.ui.login_pushButton.hide()
            self.ui.signup_pushButton.hide()
            self.ui.logout_pushButton.show()
        else:
            self.ui.ui_login_label.setText("You are not logged into SyncSketch")
            self.ui.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
            self.ui.login_pushButton.show()
            self.ui.signup_pushButton.show()
            self.ui.logout_pushButton.hide()

