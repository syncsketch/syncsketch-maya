import logging
import webbrowser

from syncsketchGUI.installScripts.maintenance import get_version_difference
from syncsketchGUI.lib import path, user
from syncsketchGUI.lib.connection import is_connected
from syncsketchGUI.literals import (message_is_not_connected,
                                    message_is_not_loggedin)
from syncsketchGUI.vendor.Qt import QtCore, QtWidgets

from . import qt_dialogs, qt_presets, qt_regulars, qt_utils, web

logger = logging.getLogger("syncsketchGUI")


class MenuWidget(QtWidgets.QWidget):
    logged_out = QtCore.Signal()
    logged_in = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(MenuWidget, self).__init__(*args, **kwargs)

        self._create_ui()
        self._layout_ui()
        self._connect_ui()

        self.update_login_ui()

        self._restore_ui_state()

    def _create_ui(self):
        self._ui_label_login = self._create_label_login()
        self._ui_pb_syncsketch = self._create_pb_syncsketch()
        self._ui_pb_signup = self._create_pb_signup()
        self._ui_pb_logout = self._create_pb_logout()
        self._ui_pb_login = self._create_pb_login()
        self._ui_pb_help = self._create_pb_help()
        self._ui_pb_upgrade = self._create_pb_upgrade()
        self._ui_label_status = self._create_label_status()

    def _layout_ui(self):

        lay_login = QtWidgets.QHBoxLayout()
        lay_login.setSpacing(0)

        lay_login.addWidget(self._ui_pb_syncsketch)
        lay_login.addWidget(self._ui_label_login)
        lay_login.addWidget(self._ui_pb_login)
        lay_login.addWidget(self._ui_pb_logout)
        lay_login.addWidget(self._ui_pb_signup)
        lay_login.addWidget(self._ui_pb_help)
        lay_login.addWidget(self._ui_pb_upgrade)

        lay_status = QtWidgets.QHBoxLayout()
        lay_status.setContentsMargins(0, 0, 0, 10)
        lay_status.addWidget(self._ui_label_status)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(lay_login)
        main_layout.addLayout(lay_status)

        self.setLayout(main_layout)

    def _connect_ui(self):
        self._ui_pb_help.clicked.connect(self.open_support)
        self._ui_pb_login.clicked.connect(self.connect_account)
        self._ui_pb_upgrade.clicked.connect(self.upgrade_plugin)
        self._ui_pb_logout.clicked.connect(self.disconnect_account)
        self._ui_pb_syncsketch.clicked.connect(self.open_landing)
        self._ui_pb_signup.clicked.connect(self.open_signup)
        self.logged_in.connect(self.update_login_ui)

    def _restore_ui_state(self):
        self._ui_pb_upgrade.show() if get_version_difference() else self._ui_pb_upgrade.hide()

    def _create_label_login(self):
        label_login = QtWidgets.QLabel()
        label_login.setText("You are not logged into SyncSketch")
        label_login.setMinimumHeight(qt_presets.header_size)
        label_login.setIndent(9)
        label_login.setStyleSheet("background-color: rgba(255,255,255,.1);)")
        return label_login

    def _create_pb_syncsketch(self):
        pb_syncsketch = qt_regulars.HeaderButton()
        pb_syncsketch.setIcon(qt_presets.logo_icon)
        return pb_syncsketch

    def _create_pb_signup(self):
        pb_signup = qt_regulars.HeaderButton()
        pb_signup.setText("Sign Up")
        return pb_signup

    def _create_pb_logout(self):
        pb_logout = qt_regulars.HeaderButton()
        pb_logout.setText("Log Out")
        return pb_logout

    def _create_pb_login(self):
        pb_login = qt_regulars.HeaderButton()
        pb_login.setText("Log In")
        return pb_login

    def _create_pb_upgrade(self):
        pb_upgrade = qt_regulars.HeaderButton()
        pb_upgrade.hide()
        pb_upgrade.setStyleSheet("color: %s" % qt_presets.success_color)
        pb_upgrade.setText("Upgrade")
        pb_upgrade.setToolTip("There is a new version")
        return pb_upgrade

    def _create_pb_help(self):
        pb_help = qt_regulars.HeaderButton()
        pb_help.setIcon(qt_presets.help_icon)
        return pb_help

    def _create_label_status(self):
        return qt_regulars.StatusLabel()

    def open_support(self):
        webbrowser.open(path.support_url)

    def connect_account(self):

        if is_connected():
            login = qt_utils.get_persistent_widget(web.LoginView, self)
            login.show()

        else:
            title = 'Not able to reach SyncSketch'
            message = 'Having trouble to connect to SyncSketch.\nMake sure you have an internet connection!'
            qt_dialogs.WarningDialog(self, title, message)

    def set_status(self, message, **kwargs):
        self._ui_label_status.update(message, kwargs)

    def upgrade_plugin(self):
        from syncsketchGUI.installScripts.maintenance import handle_upgrade

        # attach the upgrader to the mainWindow so it doesn't go out of scope
        self.installer = handle_upgrade()

    def disconnect_account(self):
        current_user = user.SyncSketchUser()
        current_user.logout()
        web.logout_view()
        self.update_login_ui()
        self.logged_out.emit()
        self._ui_label_status.update('You have been successfully logged out', color=qt_presets.warning_color)
        self._restore_ui_state()

    def open_landing(self):
        webbrowser.open(path.home_url)

    def open_signup(self):
        webbrowser.open(path.signup_url)

    def update_login_ui(self):  # TODO: Evaluate if neccessary here and maybe remove
        """
        Updates the UI based on whether the user is logged in
        """
        current_user = user.SyncSketchUser()
        user_is_logged_in = current_user.is_logged_in()
        _is_connected = is_connected()
        logger.info("current_user: '{}', is_logged_in: '{}'".format(current_user.name, user_is_logged_in))

        if user_is_logged_in and _is_connected:
            username = current_user.get_name()
            self._ui_label_login.setText("Logged into SyncSketch as \n%s" % username)
            self._ui_label_login.setStyleSheet("color: white; font-size: 11px;")
            self._ui_pb_login.hide()
            self._ui_pb_signup.hide()
            self._ui_pb_logout.show()
            self.isloggedIn(loggedIn=True)
        elif not _is_connected:
            self._ui_label_status.update(message_is_not_connected, color=qt_presets.error_color)
            logger.info("\nNot connected to SyncSketch ...")

        else:
            self._ui_label_login.setText("You are not logged into SyncSketch")
            self._ui_label_login.setStyleSheet("color: white; font-size: 11px;")
            self._ui_pb_login.show()
            self._ui_pb_signup.show()
            self._ui_pb_logout.hide()
            self.isloggedIn(loggedIn=False)

    # loggedin window
    # todo: this is similar to is_logged_in, we might wan't to move it there
    def isloggedIn(self, loggedIn=False):
        current_user = user.SyncSketchUser()
        if loggedIn:
            message = "Successfully logged in as %s" % current_user.get_name()
            self._ui_label_status.update(message, color=qt_presets.success_color)
        else:
            message = message_is_not_loggedin
            self._ui_label_status.update(message, color=qt_presets.error_color)
