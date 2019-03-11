from syncsketchGUI.vendor.Qt.QtWebKit import *
from syncsketchGUI.vendor.Qt.QtWebKitWidgets import *
import syncsketchGUI.lib.user as user
from syncsketchGUI.vendor.Qt import QtCore
from lib.gui import qt_utils
import time
import json
import logging
logger = logging.getLogger(__name__)

class WebLoginWindow(QWebView):
    """
    Login Window Class
    """
    window_name = 'syncsketchGUI_login_window'
    window_label = 'Login to SyncSketch'

    def __init__(self, parent):
        super(WebLoginWindow, self).__init__(parent)

        self.parent = parent
        self.current_user = user.SyncSketchUser()

        self.setMaximumSize(650, 600)

        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)

        self.load(QtCore.QUrl("https://syncsketch.com/login/?next=/users/getToken/&simple=1"))

        self.show()
        self.activateWindow()
        self._myBindingFunction()

        qt_utils.align_to_center(self, self.parent)

        self.setProperty('saveWindowPref', True)



    def changed(self):
        '''Store user tokens'''
        thisUrl = self.url().toString()
        if thisUrl == "https://syncsketch.com/users/getToken/":
            command = """window.getTokenData()"""
            for _ in range(20):
                jsonData = self.page().mainFrame().evaluateJavaScript(command)
                if isinstance(jsonData, unicode):
                    tokenData = json.loads(jsonData)
                    self.current_user.set_name(tokenData["email"])
                    # todo we should remove api_key
                    self.current_user.set_token(tokenData["token"])
                    self.current_user.set_api_key(tokenData["token"])
                    self.current_user.auto_login()
                    break

                else:
                    logger.info("sleeping")
                    time.sleep(0.1)
            self.close()
            update_login_ui(self.parent)
            populate_review_panel(self.parent)



    def _myBindingFunction(self):
        self.page().mainFrame().loadFinished.connect(self.changed)
        self.page().mainFrame().urlChanged.connect(self.changed)


    def _plot(self):
        command =('return getTokenData()')
        me = self.page().mainFrame().evaluateJavaScript(command)
