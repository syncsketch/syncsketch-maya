import webbrowser

from syncsketchGUI.vendor.Qt import QtCore, QtWidgets

from . import qt_presets

import logging

logger = logging.getLogger("syncsketchGUI")


class WarningDialog(QtWidgets.QMessageBox):
    """
    Customized modal dialog to be used for warnings.
    Dialog will be shown as soon as the class is called.
    """

    def __init__(self, parent, title, message):
        super(WarningDialog, self).__init__(parent)
        self.setIcon(QtWidgets.QMessageBox.Warning)
        self.setWindowIcon(qt_presets.logo_icon)
        self.setWindowTitle(title)
        self.setText(message)
        self.exec_()


class InputDialog(QtWidgets.QWidget):
    """
    Customized raw input dialog for getting user's email
    """

    def __init__(self,
                 parent=None,
                 title='Ready to upload your file!',
                 message='Once finished, we will email the review link to:'):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.response_text, self.response = \
            QtWidgets.QInputDialog.getText(self,
                                           title,
                                           message)


class StatusDialog(QtWidgets.QMessageBox):
    """
    Customized dialog to show the progress without the progress bar
    """

    def __init__(self, parent=None, title='', message=''):
        super(StatusDialog, self).__init__(parent)
        self.setIcon(QtWidgets.QMessageBox.Information)
        self.setWindowIcon(qt_presets.logo_icon)
        self.setWindowTitle(title)
        self.setText(message)
        self.exec_()


class InfoDialog(QtWidgets.QDialog):
    """
    Customized Popup Dialog
    """

    def __init__(self,
                 parent=None,
                 title='Upload Successful',
                 info_text='',
                 media_url=''):
        super(InfoDialog, self).__init__(parent)

        self.info_text = info_text
        self.media_url = media_url

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(title)
        self.resize(480, 50)

        self.setWindowIcon(qt_presets.logo_icon)

        self.create_layout()
        self.build_connections()

    def open_url(self):
        url = self.info_pushButton.text()
        webbrowser.open(url)

    def create_layout(self):
        self.info_title = QtWidgets.QLabel(self.info_text)
        self.info_pushButton = QtWidgets.QPushButton()
        self.info_pushButton.setText(self.media_url)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.info_title)
        main_layout.addWidget(self.info_pushButton)

        self.setLayout(main_layout)

    def build_connections(self):
        self.info_pushButton.clicked.connect(self.open_url)
