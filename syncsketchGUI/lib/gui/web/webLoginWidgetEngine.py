import json
import logging

from syncsketchGUI.lib import user
from syncsketchGUI.lib.maya.menu import refresh_menu_state
from syncsketchGUI.lib.path import get_syncsketch_url
from syncsketchGUI.vendor.Qt import QtCore, QtWebChannel, QtWebEngineWidgets

logger = logging.getLogger("syncsketchGUI")

"""
Although not ideal, logoutview has to be a global variable in order to be persistent. 
Otherwise when declared in logout_view function, logoutview will run out of scope before url is fully loaded, since
load method runs asynchron. 
 """
logoutview = QtWebEngineWidgets.QWebEngineView()
logout_url = "{}/app/logmeout/".format(get_syncsketch_url())


def logout_view():
    logger.debug("Logout View with: {}".format(logout_url))
    logoutview.load(QtCore.QUrl(logout_url))
    refresh_menu_state()


class Element(QtCore.QObject):
    loaded = QtCore.Signal()

    def __init__(self, parent=None):
        super(Element, self).__init__(parent)
        self._is_loaded = False
        self._token_data = None

    @property
    def token_data(self):
        return self._token_data

    @QtCore.Slot()
    def set_loaded(self):
        self._is_loaded = True
        self.loaded.emit()

    @QtCore.Slot(str)
    def set_token_data(self, value):
        self._token_data = value


class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.loadFinished.connect(self.onLoadFinished)
        self.qt_object = Element()

    @QtCore.Slot(bool)
    def onLoadFinished(self, ok):
        if ok:
            self.load_qwebchannel()
            self.load_objects()

    def load_qwebchannel(self):
        file = QtCore.QFile(":/qtwebchannel/qwebchannel.js")
        if file.open(QtCore.QIODevice.ReadOnly):
            content = file.readAll()
            file.close()
            self.runJavaScript(content.data().decode("utf8"))
        if self.webChannel() is None:
            channel = QtWebChannel.QWebChannel(self)
            self.setWebChannel(channel)

    def load_objects(self):
        if self.webChannel() is not None:
            self.webChannel().registerObject("qt_object", self.qt_object)
            _script = r"""
            new QWebChannel(qt.webChannelTransport, function (channel) {

                    qt_object = channel.objects.qt_object;
                    qt_object.set_token_data(window.getTokenData())
                    qt_object.set_loaded()
            }); 
            """

            self.runJavaScript(_script)


class LoginView(QtWebEngineWidgets.QWebEngineView):
    logged_in = QtCore.Signal
    window_name = 'syncsketchGUI_login_window'
    window_label = 'Login to SyncSketch'

    def __init__(self, parent=None):
        super(LoginView, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)

        self.setMaximumSize(650, 600)
        self.setMinimumSize(650, 600)

        page = WebEnginePage(self)
        self.setPage(page)

        page.qt_object.loaded.connect(self.login)
        self.load(QtCore.QUrl("{}/login/?next=/users/getToken/&simple=1".format(get_syncsketch_url())))

        self.show()
        self.activateWindow()

        self.setProperty('saveWindowPref', True)

    def update_login(self, email, token):

        current_user = user.SyncSketchUser()
        current_user.set_name(email)
        current_user.set_token(token)
        current_user.set_api_key(token)
        current_user.auto_login()

        logger.info("User: {} logged id".format(email))

        refresh_menu_state()

        self.close()

        if self.parent:
            self.parent.logged_in.emit()

    @QtCore.Slot()
    def login(self):
        token_data = self.page().qt_object.token_data
        if token_data:
            token_dict = json.loads(token_data)
            self.update_login(email=token_dict.get('email'), token=token_dict.get('token'))
