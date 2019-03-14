# -*- coding: utf-8 -*-
# @Author: yafes
# @Date:   2019-03-12 11:07:16
# @Last Modified by:   yafes
# @Last Modified time: 2019-03-12 11:07:18
class InfoDialog(QtWidgets.QDialog):
    """
    Customized Popup Dialog
    """
    def __init__(  self,
                    parent = None,
                    title = 'Upload Successful',
                    info_text = '',
                    media_url = ''):

        super(InfoDialog, self).__init__(parent)

        self.info_text = info_text
        self.media_url = media_url

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(title)
        self.resize(480, 50)

        self.setWindowIcon(logo_icon)

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
