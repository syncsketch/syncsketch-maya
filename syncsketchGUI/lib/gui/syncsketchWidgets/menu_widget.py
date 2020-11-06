import logging
import webbrowser

logger = logging.getLogger("syncsketchGUI")

from syncsketchGUI.vendor.Qt import QtCore, QtGui, QtWidgets
from syncsketchGUI.lib.gui.icons import success_color, logo_icon, header_size, help_icon, error_color, warning_color
from syncsketchGUI.lib.gui.qt_widgets import RegularHeaderButton, RegularStatusLabel, WarningDialog
from syncsketchGUI.lib import path, user
from syncsketchGUI.lib.connection import is_connected
from syncsketchGUI.lib.gui.syncsketchWidgets.web import LoginView, logout_view
from syncsketchGUI.gui import  _maya_delete_ui
from syncsketchGUI.lib.gui.literals import message_is_not_loggedin, message_is_not_connected
from syncsketchGUI.installScripts.maintenance import getVersionDifference

class MenuWidget(QtWidgets.QWidget):

    logged_out = QtCore.Signal()
    logged_in = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(MenuWidget, self).__init__(*args, **kwargs)

        self._decorate_ui()
        self._build_connections()

        self.update_login_ui()

        self._restore_ui_state()


    def _decorate_ui(self):
        indent = 9
        self.ui_login_label = QtWidgets.QLabel()
        self.ui_login_label.setText("You are not logged into SyncSketch")
        self.ui_login_label.setMinimumHeight(header_size)
        self.ui_login_label.setIndent(indent)
        self.ui_login_label.setStyleSheet("background-color: rgba(255,255,255,.1);)")

        self.syncsketchGUI_pushButton = RegularHeaderButton()
        self.syncsketchGUI_pushButton.setIcon(logo_icon)
        self.signup_pushButton = RegularHeaderButton()
        self.signup_pushButton.setText("Sign Up")
        self.logout_pushButton = RegularHeaderButton()
        self.logout_pushButton.setText("Log Out")
        self.login_pushButton = RegularHeaderButton()
        self.login_pushButton.setText("Log In")
        self.upgrade_pushButton = RegularHeaderButton()
        self.upgrade_pushButton.hide()
        self.upgrade_pushButton.setStyleSheet("color: %s"%success_color)

        self.upgrade_pushButton.setText("Upgrade")
        self.upgrade_pushButton.setToolTip("There is a new version")
        self.help_pushButton = RegularHeaderButton()
        self.help_pushButton.setIcon(help_icon)

        self.ui_login_layout = QtWidgets.QHBoxLayout()
        self.ui_login_layout.setSpacing(0)

        self.ui_login_layout.addWidget(self.syncsketchGUI_pushButton)
        self.ui_login_layout.addWidget(self.ui_login_label)
        self.ui_login_layout.addWidget(self.login_pushButton)
        self.ui_login_layout.addWidget(self.logout_pushButton)
        self.ui_login_layout.addWidget(self.signup_pushButton)
        self.ui_login_layout.addWidget(self.help_pushButton)
        self.ui_login_layout.addWidget(self.upgrade_pushButton)

        self.ui_status_label = RegularStatusLabel()
        
        self.ui_status_layout = QtWidgets.QHBoxLayout()
        self.ui_status_layout.addWidget(self.ui_status_label)
        self.ui_status_layout.setContentsMargins(0, 0, 0, 10)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(self.ui_login_layout)
        main_layout.addLayout(self.ui_status_layout)

        self.setLayout(main_layout)        


    def _build_connections(self):
        self.help_pushButton.clicked.connect(self.open_support)
        self.login_pushButton.clicked.connect(self.connect_account)
        self.upgrade_pushButton.clicked.connect(self.upgrade_plugin)
        self.logout_pushButton.clicked.connect(self.disconnect_account)
        self.syncsketchGUI_pushButton.clicked.connect(self.open_landing)
        self.signup_pushButton.clicked.connect(self.open_signup)
        self.logged_in.connect(self.update_login_ui)


    def _restore_ui_state(self):
        self.upgrade_pushButton.show() if getVersionDifference() else self.upgrade_pushButton.hide()

    def open_support(self):
        webbrowser.open(path.support_url)

    def connect_account(self):

        if is_connected():
            _maya_delete_ui(LoginView.window_name)
            weblogin_window = LoginView(self)

        else:
            title='Not able to reach SyncSketch'
            message='Having trouble to connect to SyncSketch.\nMake sure you have an internet connection!'
            WarningDialog(self, title, message)

    def set_status(self, message, **kwargs):
       self.ui_status_label.update(message, kwargs)
        

    def upgrade_plugin(self):
        from syncsketchGUI.installScripts.maintenance import handleUpgrade
        #attach the upgrader to the mainWindow so it doesn't go out of scope
        self.installer = handleUpgrade()

    def disconnect_account(self):
        current_user = user.SyncSketchUser()
        current_user.logout()
        logout_view()
        self.update_login_ui()
        self.logged_out.emit()
        self.ui_status_label.update('You have been successfully logged out', color=warning_color)
        self._restore_ui_state()

    def open_landing(self):
        webbrowser.open(path.home_url)

    def open_signup(self):
        webbrowser.open(path.signup_url)
    

    def update_login_ui(self): # TODO: Evaluate if neccessary here and maybe remove
        '''
        Updates the UI based on whether the user is logged in
        '''
        current_user = user.SyncSketchUser()
        logger.info("CurrentUser: {}".format(current_user))
        logger.info("isLoggedin: {}".format(current_user.is_logged_in()))

        
    
        if current_user.is_logged_in() and is_connected():
            logger.info("current_user.is_logged_in() {} is_connected() {} ".format(current_user.is_logged_in(),is_connected() ))
            username = current_user.get_name()
            self.ui_login_label.setText("Logged into SyncSketch as \n%s" % username)
            self.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
            self.login_pushButton.hide()
            self.signup_pushButton.hide()
            self.logout_pushButton.show()
            self.isloggedIn(loggedIn=True)

        elif not is_connected():
            self.ui_status_label.update(message_is_not_connected, color=error_color)    
            logger.info("\nNot connected to SyncSketch ...")
 
        else:
            self.ui_login_label.setText("You are not logged into SyncSketch")
            self.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
            self.login_pushButton.show()
            self.signup_pushButton.show()
            self.logout_pushButton.hide()
            self.isloggedIn(loggedIn=False)
    
    
    # loggedin window
    # todo: this is similar to is_logged_in, we might wan't to move it there
    def isloggedIn(self,loggedIn=False):
        current_user = user.SyncSketchUser()
        if loggedIn:
            message =  "Successfully logged in as %s"%current_user.get_name()
            self.ui_status_label.update(message, color = success_color)
        else:
            message = message_is_not_loggedin
            self.ui_status_label.update(message, color=error_color)
