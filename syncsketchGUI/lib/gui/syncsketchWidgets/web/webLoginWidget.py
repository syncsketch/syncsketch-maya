import time
import json
import logging

from syncsketchGUI.vendor.Qt.QtWebKitWidgets import QWebView
import syncsketchGUI.lib.user as user
from syncsketchGUI.vendor.Qt import QtCore
from syncsketchGUI.lib.gui import qt_utils

logger = logging.getLogger("syncsketchGUI")

# empty methond to complie to web interface
def logout_view():
    pass

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
                    logger.info("tokenData: {0}".format(tokenData))
                    self.current_user.set_name(tokenData["email"])
                    self.current_user.set_token(tokenData["token"])
                    self.current_user.set_api_key(tokenData["token"])
                    self.current_user.auto_login()
                    break

                else:
                    logger.info("sleeping")
                    time.sleep(0.1)
            self.close()
            self.parent.update_login_ui()
            #todo: turn this into a signal
            #self.parent.asyncPopulateTree(withItems=False)
            self.parent.populateTree()
            #self.parent.asyncPopulateTree(withItems=True)
            self.parent.restore_ui_state()

    def _myBindingFunction(self):
        self.page().mainFrame().loadFinished.connect(self.changed)
        self.page().mainFrame().urlChanged.connect(self.changed)