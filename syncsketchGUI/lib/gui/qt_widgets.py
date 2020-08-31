from syncsketchGUI.lib.gui import icons
from syncsketchGUI.lib.gui.icons import *
from syncsketchGUI.vendor.Qt import QtCore
from syncsketchGUI.vendor.Qt import QtGui
from syncsketchGUI.vendor.Qt import QtWidgets
from syncsketchGUI.lib.connection import is_connected
#from syncsketchGUI.vendor.Qt.QtWebKitWidgets import QWebView
from syncsketchGUI.lib import database
from syncsketchGUI.lib import user as user
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
        self.setWindowIcon(logo_icon)
        self.setWindowTitle(title)
        self.setText(message)
        self.exec_()


class InputDialog(QtWidgets.QWidget):
    """
    Customized raw input dialog for getting user's email
    """
    def __init__(  self,
                    parent = None,
                    title = 'Ready to upload your file!',
                    message='Once finished, we will email the review link to:'):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.response_text, self.response = \
            QtWidgets.QInputDialog.getText( self,
                                            title,
                                            message)


class StatusDialog(QtWidgets.QMessageBox):
    """
    Customized dialog to show the progress without the progress bar
    """
    def __init__(self, parent = None):
        super(StatusDialog, self).__init__(parent)

        self.setIcon(QtWidgets.QMessageBox.Warning)
        self.setWindowIcon(logo_icon)
        self.setWindowTitle('title')
        self.setText('message')
        self.exec_()


class RegularThumbnail(QtWidgets.QPushButton):

    def __init__(self, parent=None, width = 320, height =180):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: rgba(0,0,0,0.1); border: none; margin: 0;")
        self.setIcon(logo_icon)
        self.setIconSize(QtCore.QSize(width, height))
        self.setMinimumSize(width,height)
        self.setToolTip('Play Clip')

    def set_icon_from_image(self, imagefile='icon_manage_presets_100.png'):
        # print "exists: %s"%os.path.exists(imagefile)
        return
        newIcon = icons._get_qicon(icon_name=imagefile)

        self.setIcon(newIcon)

    def set_icon_from_url(self, url):
        newIcon = icons._get_qicon_from_url(url)
        self.setIcon(newIcon)
        return

    def clear(self):
        self.setIcon(QtGui.QIcon())

class HoverButton(QtWidgets.QPushButton):

    def __init__(self, parent=None, icon = None):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.setMouseTracking(True)

        if icon:
            self.icon = icon
        else:
            self.icon = logo_icon
        self.setIcon(self.icon)
        self.setStyleSheet("background-color: rgba(0,0,0,0.0); border: none; margin: 0;")

    def enterEvent(self,event):
        self.setStyleSheet("background-color: rgba(255,255,255,0.15); border: none; Text-align:bottom;")

    def leaveEvent(self,event):
        self.setStyleSheet("background-color: rgba(0,0,0,0); border: none; ; Text-align:bottom;")


class RegularHeaderButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, color ='white'):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.color = color;
        self.bgColor = button_color
        self.hoverColor = button_color_hover
        self.setMouseTracking(True)
        self.setMinimumSize(40,40)
        self.setIconSize(QtCore.QSize(32, 32))

        self.setMaximumWidth(header_size)
        self.setMaximumHeight(header_size)

        self.setStyleSheet("margin:1; background-color: rgba(255,255,255,0.1); border: none;")

    def enterEvent(self, event):
        self.setStyleSheet("margin:1; background-color: rgba(255,255,255,0.2); border: none;")
    def leaveEvent(self, event):
        self.setStyleSheet("margin:1; background-color: rgba(255,255,255,0.1); border: none;")


class RegularStatusLabel(QtWidgets.QLabel):
    def __init__(self, parent=None, color ='white', bgColor='rgba(0,0,0,0.3)'):
        QtWidgets.QLabel.__init__(self, parent=parent)
        indent = 9
        self.color = color
        self.bgColor = bgColor
        self.setColors(self.color, self.bgColor)
        self.setMargin(0)
        self.setMinimumHeight(header_size/2)
        self.setAlignment(QtCore.Qt.AlignCenter)

    def update(self, message, color=success_color):
        self.setColors(color)
        self.setText(message)
        self.repaint()
        QtWidgets.qApp.processEvents()

    def setColors(self, color ='white', bgColor='rgba(0,0,0,0.3)', borderColor='rgba(0,0,0,0.1)'):
        self.setStyleSheet("background-color: %s;  color: %s; border-bottom: 1px solid %s; border-top: 1px solid %s;"%(bgColor, color,borderColor , borderColor))



class RegularLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        QtWidgets.QLineEdit.__init__(self, parent=parent)
    def mousePressEvent(self, e):
        self.selectAll()


class RegularButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, icon = None, color ='white'):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.color = color
        self.bgColor = button_color
        self.hoverColor = button_color_hover
        if icon:
            self.setIcon(icon)
        self.setMouseTracking(True)
        self.setMinimumSize(40,40)
        self.setStyleSheet("color: %s"%color)

    def enterEvent(self, event):
        return
        self.setStyleSheet("margin: 0; background: %s; padding: 10px; border-radius: 4px; border: 0; color: %s;"%(self.hoverColor,self.color))

    def leaveEvent(self, event):
        return
        self.setStyleSheet("margin: 0; background: %s; padding: 10px; border-radius: 4px; border: 0; color: %s;"%(self.bgColor,self.color))

class RegularGridLayout(QtWidgets.QGridLayout):
    def __init__(self, parent=None, label = ''):
        QtWidgets.QGridLayout.__init__(self)
        self.label = QtWidgets.QLabel(label)
        self.addWidget(self.label,  0, 0)
        self.setColumnMinimumWidth(0,90)
        self.setColumnStretch(0,0)
        self.setColumnStretch(1,1)
        self.setSpacing(2)


class RegularQSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        QtWidgets.QSpinBox.__init__(self, parent=parent)
        self.setButtonSymbols(self.NoButtons)


class RegularComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None, color ='white'):
        QtWidgets.QComboBox.__init__(self, parent=parent)

        self.color = color;
        self.bgColor = button_color
        self.hoverColor = button_color_hover
        self.setMouseTracking(True)


    def set_combobox_index(self, selection=None, default=None):
        if selection:
            index = self.findText(selection)
            if index != -1:
                self.setCurrentIndex(index)
        elif default:
            self.set_combobox_index(selection=default)
        else:
            self.setCurrentIndex(0)


    def populate_combo_list(self, file, defaultValue=None, currentValue='current preset'):
        combo_file = path.get_config_yaml(file)
        combo_data = database._parse_yaml(combo_file)

        if not combo_data:
            return

        combo_items = combo_data.keys()
        if not combo_items:
            return

        self.clear()
        self.addItems(combo_items)
        current_preset = combo_data.get(currentValue)
        self.set_combobox_index(selection=current_preset, default=defaultValue)


    def enterEvent(self, event):
        return
        self.setStyleSheet("margin: 0; background: %s; padding: 5px; border-radius: 4px; border: 0; color: %s;"%(self.hoverColor,self.color))

    def leaveEvent(self, event):
        return
        self.setStyleSheet("margin: 0; background: %s; padding: 5px; border-radius: 4px; border: 0; color: %s;"%(self.bgColor,self.color))


class RegularToolButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, icon=None, color ='white'):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.color = color;
        self.bgColor = button_color
        self.hoverColor = button_color_hover
        self.setMouseTracking(True)
        self.setText('')
        if icon:
            self.setIcon(icon)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setMaximumSize(QtCore.QSize(19, 19))
        self.setStyleSheet("background: rgba(255,255,255,0.1);")

    def enterEvent(self, event):
        self.setStyleSheet("background: rgba(255,255,255,0.2);")
        return

    def leaveEvent(self, event):
        self.setStyleSheet("background: rgba(255,255,255,0.1);")
        return


class SyncSketch_Window(QtWidgets.QMainWindow):
    """
    SyncSketch Main Preset Window Class
    """
    window_name = 'syncsketch_window'
    window_label = 'SyncSketch'

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        MAYA = True
        self.setWindowFlags(QtCore.Qt.Window)
        self.ui = QtWidgets.QWidget()
        self.ui.master_layout = QtWidgets.QVBoxLayout()
#        self.ui.master_layout.setMargin(0)
        self.ui.setLayout(self.ui.master_layout)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.parent = parent

        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        self.setCentralWidget(self.ui)
        self.setWindowIcon(logo_icon)

        self.ui.main_layout = QtWidgets.QVBoxLayout()
        #self.ui.main_layout.setMargin(0)
        self.ui.main_layout.setSpacing(3)
        self.ui.master_layout.addLayout(self.ui.main_layout)

        if MAYA:
            self.setProperty('saveWindowPref', True)

        self.align_to_center(self.parent)



    def align_to_center(self, align_object):
        """
        If the UI has a parent, align to it.
        If not, align to the center of the desktop.
        """
        ui_size = self.geometry()

        if align_object:
            align_object_center = align_object.frameGeometry().center()
            x_coordinate = align_object_center.x() -(ui_size.width() / 2)
            y_coordinate = align_object_center.y() -(ui_size.height() / 2)

        else:
            desktop_screen = QtWidgets.QDesktopWidget().screenGeometry()
            x_coordinate =(desktop_screen.width() - ui_size.width()) / 2
            y_coordinate =(desktop_screen.height() - ui_size.height()) / 2

        self.move(x_coordinate, y_coordinate)
        return self.geometry()

    def cancel(self):
        logger.info("Closing Synsketch GUI Window")
        self.close()

    def update_login_ui(self):
        '''
        Updates the UI based on whether the user is logged in
        '''
        self.current_user = user.SyncSketchUser()
        if self.current_user.is_logged_in() and is_connected():
            logger.info("self.current_user.is_logged_in() {} is_connected() {} ".format(self.current_user.is_logged_in(),is_connected() ))
            username = self.current_user.get_name()
            self.ui.ui_login_label.setText("Logged into SyncSketch as \n%s" % username)
            self.ui.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
            self.ui.login_pushButton.hide()
            self.ui.signup_pushButton.hide()
            self.ui.logout_pushButton.show()
        else:
            self.ui.ui_login_label.setText("You are not logged into SyncSketch")
            self.ui.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
            self.ui.login_pushButton.show()
            self.ui.signup_pushButton.show()
            self.ui.logout_pushButton.hide()

