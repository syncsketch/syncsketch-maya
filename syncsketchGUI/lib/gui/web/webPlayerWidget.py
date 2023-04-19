from syncsketchGUI.lib import user as user
from syncsketchGUI.vendor.Qt import QtCore
from syncsketchGUI.vendor.Qt.QtWebKitWidgets import QWebView

from .. import qt_utils


class OpenPlayer(QWebView):
    """
    Login Window Class
    """
    window_name = 'Login'
    window_label = 'Login to SyncSketch'

    def __init__(self, parent, url='https://syncsketch.com/pro'):
        super(OpenPlayer, self).__init__(parent)

        self.parent = parent
        self.current_user = user.SyncSketchUser()

        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        self.setWindowFlags(QtCore.Qt.Window)

        self.load(QtCore.QUrl(url))

        self.show()
        self.activateWindow()
        self._myBindingFunction()
        qt_utils.align_to_center(self, self.parent)

        self.setProperty('saveWindowPref', True)
