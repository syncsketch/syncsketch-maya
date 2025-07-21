import logging

from syncsketchGUI.lib import database, path
from syncsketchGUI.vendor.Qt import QtCore, QtWidgets

from . import qt_presets

logger = logging.getLogger("syncsketchGUI")


class HoverButton(QtWidgets.QPushButton):

    def __init__(self, parent=None, icon=None):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.setMouseTracking(True)

        if icon:
            self.icon = icon
        else:
            self.icon = qt_presets.logo_icon
        self.setIcon(self.icon)
        self.setStyleSheet("background-color: rgba(0,0,0,0.0); border: none; margin: 0;")

    def enterEvent(self, event):
        self.setStyleSheet("background-color: rgba(255,255,255,0.15); border: none; Text-align:bottom;")

    def leaveEvent(self, event):
        self.setStyleSheet("background-color: rgba(0,0,0,0); border: none; ; Text-align:bottom;")


class HeaderButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, color='white'):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.color = color
        self.bgColor = qt_presets.button_color
        self.hoverColor = qt_presets.button_color_hover
        self.setMouseTracking(True)
        self.setMinimumSize(40, 40)
        self.setIconSize(QtCore.QSize(32, 32))

        self.setMaximumWidth(qt_presets.header_size)
        self.setMaximumHeight(qt_presets.header_size)

        self.setStyleSheet("margin:1; background-color: rgba(255,255,255,0.1); border: none;")

    def enterEvent(self, event):
        self.setStyleSheet("margin:1; background-color: rgba(255,255,255,0.2); border: none;")

    def leaveEvent(self, event):
        self.setStyleSheet("margin:1; background-color: rgba(255,255,255,0.1); border: none;")


class StatusLabel(QtWidgets.QLabel):
    def __init__(self, parent=None, color='white', bgColor='rgba(0,0,0,0.3)'):
        QtWidgets.QLabel.__init__(self, parent=parent)
        indent = 9
        self.color = color
        self.bgColor = bgColor
        self.setColors(self.color, self.bgColor)
        self.setMargin(0)
        self.setMinimumHeight(qt_presets.header_size / 2)
        self.setAlignment(QtCore.Qt.AlignCenter)

    def update(self, message, color=qt_presets.success_color):
        self.setColors(color)
        self.setText(message)
        self.repaint()
        # QtWidgets.qApp.processEvents()

    def setColors(self, color='white', bgColor='rgba(0,0,0,0.3)', borderColor='rgba(0,0,0,0.1)'):
        self.setStyleSheet(
            "background-color: %s;  color: %s; border-bottom: 1px solid %s; border-top: 1px solid %s;" % (
                bgColor, color, borderColor, borderColor))


class LineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        QtWidgets.QLineEdit.__init__(self, parent=parent)

    def mousePressEvent(self, e):
        self.selectAll()


class Button(QtWidgets.QPushButton):
    def __init__(self, parent=None, icon=None, color='white'):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.color = color
        self.bgColor = qt_presets.button_color
        self.hoverColor = qt_presets.button_color_hover
        if icon:
            self.setIcon(icon)
        self.setMouseTracking(True)
        self.setMinimumSize(40, 40)
        self.setStyleSheet("color: {}".format(color))

    def enterEvent(self, event):
        return
        self.setStyleSheet("margin: 0; background: {}; padding: 10px; border-radius: 4px; border: 0; color: {};".format(
            self.hoverColor, self.color))

    def leaveEvent(self, event):
        return
        self.setStyleSheet(
            "margin: 0; background: {}; padding: 10px; border-radius: 4px; border: 0; color: {};".format(self.bgColor,
                                                                                                         self.color))


class GridLayout(QtWidgets.QGridLayout):
    def __init__(self, parent=None, label=''):
        QtWidgets.QGridLayout.__init__(self)
        self.label = QtWidgets.QLabel(label)
        self.addWidget(self.label, 0, 0)
        self.setColumnMinimumWidth(0, 90)
        self.setColumnStretch(0, 0)
        self.setColumnStretch(1, 1)
        self.setSpacing(2)


class QSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        QtWidgets.QSpinBox.__init__(self, parent=parent)
        self.setButtonSymbols(self.NoButtons)


class ComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None, color='white'):
        QtWidgets.QComboBox.__init__(self, parent=parent)

        self.color = color
        self.bgColor = qt_presets.button_color
        self.hoverColor = qt_presets.button_color_hover
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
        self.setStyleSheet(
            "margin: 0; background: {}; padding: 5px; border-radius: 4px; border: 0; color: {};".format(self.hoverColor,
                                                                                                        self.color))

    def leaveEvent(self, event):
        return
        self.setStyleSheet(
            "margin: 0; background: {}; padding: 5px; border-radius: 4px; border: 0; color: {};".format(self.bgColor,
                                                                                                        self.color))


class ToolButton(QtWidgets.QPushButton):
    def __init__(self, parent=None, icon=None, color='white'):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.color = color
        self.bgColor = qt_presets.button_color
        self.hoverColor = qt_presets.button_color_hover
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


class Thumbnail(QtWidgets.QPushButton):

    def __init__(self, parent=None, width=320, height=180):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: rgba(0,0,0,0.1); border: none; margin: 0;")
        self.setIcon(qt_presets.logo_icon)
        self.setIconSize(QtCore.QSize(width, height))
        self.setMinimumSize(width, height)
        self.setToolTip('Play Clip')

    def set_icon_from_image(self, imagefile='icon_manage_presets_100.png'):
        # print "exists: %s"%os.path.exists(imagefile)
        return
        newIcon = qt_presets._get_qicon(icon_name=imagefile)

        self.setIcon(newIcon)

    def set_icon_from_url(self, url):
        newIcon = qt_presets._get_qicon_from_url(url)
        self.setIcon(newIcon)
        return

    def clear(self):
        self.setIcon(qt_presets.logo_icon)
