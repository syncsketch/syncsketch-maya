from syncsketchGUI.vendor.Qt.QtWebKitWidgets import QWebView

from syncsketchGUI.lib import user as user
from syncsketchGUI.vendor.Qt import QtCore
from .. import qt_utils
from ...path import get_syncsketch_url


class OpenPlayer(QWebView):
    """
    Login Window Class
    """
    window_name = 'Login'
    window_label = 'Login to SyncSketch'

    def __init__(self, parent, url=None):
        super(OpenPlayer, self).__init__(parent)
        if not url:
            url = "{}/pro".format(get_syncsketch_url())

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
