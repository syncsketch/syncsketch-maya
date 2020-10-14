import os
import sys
import logging 
import json
from syncsketchGUI.vendor.Qt import QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel
from syncsketchGUI.lib import user
from syncsketchGUI.lib.gui import qt_utils

logger = logging.getLogger("syncsketchGUI")

"""
Although not ideal, logoutview has to be a global variable in order to be persistent. 
Otherwise when declared in logout_view function, logoutview will run out of scope before url is fully loaded, since
load method runs asynchron. 
 """
logoutview = QtWebEngineWidgets.QWebEngineView()
logout_url = "https://syncsketch.com/app/logmeout/"

def logout_view():
    logger.debug("Logout View with: {}".format(logout_url))
    logoutview.load(QtCore.QUrl(logout_url))

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

    loggedIn = QtCore.Signal
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
        #self.loggedIn.connect(self.update_login) # refactor outside of class
        self.load(QtCore.QUrl("https://syncsketch.com/login/?next=/users/getToken/&simple=1"))

        self.show()
        self.activateWindow()

        #qt_utils.align_to_center(self, self.parent)

        self.setProperty('saveWindowPref', True)
    
    def update_login(self):
        self.close()
        self.parent.update_login_ui()
        #todo: turn this into a signal
        #self.parent.asyncPopulateTree(withItems=False)
        self.parent.populateTree()
        #self.parent.asyncPopulateTree(withItems=True)
        self.parent.restore_ui_state()

    @QtCore.Slot()
    def login(self):
        
        token_data = self.page().qt_object.token_data
        if token_data:
            token_dict = json.loads(token_data)
            current_user = user.SyncSketchUser()
            current_user.set_name(token_dict["email"])
            current_user.set_token(token_dict["token"])
            current_user.set_api_key(token_dict["token"])
            current_user.auto_login()
            #self.loggedIn.emit()
            logger.info("User: {} logged id".format(token_dict["email"]))

            self.update_login()




