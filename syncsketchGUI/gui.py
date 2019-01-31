# -*- coding: UTF-8 -*-
# ======================================================================
# @Author   : SyncSketch LLC
# @Email    : dev@syncsketch.com
# @Version  : 1.0.0
# ======================================================================
import codecs
import json
import os
import platform
import socket
import sys
import time
import webbrowser
import tempfile
from functools import partial

from vendor.Qt.QtWebKit import *
from vendor.Qt.QtWebKitWidgets import *
from vendor.Qt.QtWidgets import QApplication

import syncsketchGUI
from lib import video, user, database
from syncsketchGUI.lib.gui.qt_widgets import *
from syncsketchGUI.lib.gui import qt_utils
from syncsketchGUI.lib.gui.qt_utils import *

from syncsketchGUI.lib.gui.icons import *
from syncsketchGUI.lib.gui.icons import _get_qicon
from syncsketchGUI.lib.connection import *
from vendor import mayapalette
from vendor import yaml
from vendor.Qt import QtCompat
from vendor.Qt import QtCore
from vendor.Qt import QtGui
from vendor.Qt import QtWidgets

# ======================================================================
# Environment Detection

PLATFORM = platform.system()
BINDING = QtCompat.__binding__

try:
    from maya import cmds
    import maya.mel as mel
    MAYA = True
except ImportError:
    MAYA = False

try:
    import nuke
    import nukescripts
    NUKE = True
except ImportError:
    NUKE = False

STANDALONE = False
if not MAYA and not NUKE:
    STANDALONE = True

if MAYA:
    from syncsketchGUI.lib.maya import scene as maya_scene

# ======================================================================
# Global Variables

PALETTE_YAML = 'syncsketch_palette.yaml'
PRESET_YAML = 'syncsketch_preset.yaml'
VIEWPORT_YAML = 'syncsketch_viewport.yaml'


DEFAULT_PRESET = 'Default(for speedy upload)'
DEFAULT_VIEWPORT_PRESET = database.read_cache('current_viewport_preset')

uploadPlaceHolderStr = "Pick a review/item or paste a SyncSketch URL here"
message_is_not_loggedin = "Please sign into your account by clicking 'Log-In' or create a free Account by clicking 'Sign up'."
message_is_not_connected = "WARNING: Could not connect to SyncSketch. It looks like you may not have an internet connection?"

WAIT_TIME = 0.00 # seconds

USER_ACCOUNT_DATA = None

# ======================================================================
# DCC application helper functions

def _maya_delete_ui(ui_name):
    """
    Delete existing UI in Maya
    """
    if cmds.control(ui_name, exists = True):
        cmds.deleteUI(ui_name)

def _maya_main_window():
    """
    Return Maya's main window
    """
    for obj in QtWidgets.qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')

def _maya_web_window():
    """
    Return Maya's main window
    """
    for obj in QtWidgets.qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')


# ======================================================================
# Misc Utilities

def bool_to_str(val):
    strVal = 'true' if val else 'false'
    return strVal

def str_to_bool(val):
    return True if val=='true' else False,

def sanitize(val):
    return val.rstrip().lstrip()
#


# ======================================================================
# Module Utilities

def _call_ui_for_standalone(ui_object):
    app = QtWidgets.QApplication(sys.argv)
    app_ui = ui_object(None)

    if not PLATFORM == 'Darwin' and BINDING == 'PySide' or BINDING == 'PyQt4':
        palette_file = path.get_config_yaml(PALETTE_YAML)
        style_data = database._parse_yaml(palette_file)
        mayapalette.set_palette_from_dict(style_data)
        mayapalette.set_style()
        mayapalette.set_maya_tweaks()

    app_ui.show()
    sys.exit(app.exec_())
    return app_ui

def _call_ui_for_maya(ui_object):
    app_ui = ui_object(parent = _maya_main_window())
    app_ui.show()
    return app_ui

def _call_web_ui_for_maya(ui_object):
    app_ui = ui_object(parent=_maya_web_window())
    app_ui.show()
    return app_ui

def _build_widget_item(parent, item_name, item_type, item_icon, item_data):
    treewidget_item = QtWidgets.QTreeWidgetItem(parent, [item_name])
    treewidget_item.setData(1, QtCore.Qt.EditRole, item_data)
    treewidget_item.setData(2, QtCore.Qt.EditRole, item_type)
    treewidget_item.setIcon(0, item_icon)
    return treewidget_item

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
# ======================================================================
# Module Classes

class OpenPlayer(QWebView):
    """
    Login Window Class
    """
    window_name = 'fdfd'
    window_label = 'Login fd SyncSketch'

    def __init__(self, parent, url='https://syncsketch.com/pro'):
        super(OpenPlayer, self).__init__(parent)

        self.parent = parent
        self.current_user = user.SyncSketchUser()

        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        self.setWindowFlags(QtCore.Qt.Window)

        self.load(QtCore.QUrl(url))
        # self.load(QtCore.QUrl("https://syncsketch.com/login/?next=/users/getToken/&simple=1"))
        # self.setWindowFlags(QtCore.Qt.SplashScreen)

        self.show()
        self.activateWindow()
        self._myBindingFunction()
        qt_utils.align_to_center(self, self.parent)

        if MAYA:
            self.setProperty('saveWindowPref', True)

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
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint )

        self.load(QtCore.QUrl("https://syncsketch.com/login/?next=/users/getToken/&simple=1"))

        self.show()
        self.activateWindow()
        self._myBindingFunction()

        qt_utils.align_to_center(self, self.parent)

        if MAYA:
            self.setProperty('saveWindowPref', True)



    def changed(self):
        thisUrl = self.url().toString()
        if thisUrl == "https://syncsketch.com/users/getToken/":
            command = """window.getTokenData()"""
            for i in range(20):
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
                    print "sleeping"
                    time.sleep(0.1)
            self.close()
            update_login_ui(self.parent)
            populate_review_panel(self.parent)



    def _myBindingFunction(self):
        # self.loadStarted.connect(self._plot)
        # self.page().mainFrame().loadStarted.connect(self.onStart)
        self.page().mainFrame().loadFinished.connect(self.changed)
        self.page().mainFrame().urlChanged.connect(self.changed)
        # self.loadingChanged.connect(self.changed)
        # self.page().mainFrame().loadFinished.connect(self._plot)

    def _plot(self):
        command =('return getTokenData()')
        me = self.page().mainFrame().evaluateJavaScript(command)



def update_login_ui(self):
    #user Login
    self.current_user = user.SyncSketchUser()
    if self.current_user.is_logged_in() and is_connected():
        username = self.current_user.get_name()
        self.ui.ui_login_label.setText("Logged into SyncSketch as \n%s" % username)
        self.ui.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
        self.ui.login_pushButton.hide()
        self.ui.signup_pushButton.hide()
        self.ui.logout_pushButton.show()
    else:
        # self.ui.ui_login_label.setText("You're not logged in")
        # self.ui.logged_in_groupBox.hide()
        self.ui.ui_login_label.setText("You are not logged into SyncSketch")
        self.ui.ui_login_label.setStyleSheet("color: white; font-size: 11px;")
        self.ui.login_pushButton.show()
        self.ui.signup_pushButton.show()
        self.ui.logout_pushButton.hide()

class DownloadWindow(SyncSketch_Window):
    """
    Video Preset Window Class
    """
    window_name = 'syncsketchGUI_preset_window'
    window_label = 'Download And Application'

    def __init__(self, parent=None):
        super(DownloadWindow, self).__init__(parent=parent)
        self.decorate_ui()
        self.align_to_center(self.parent)

        current_user = user.SyncSketchUser()
        self.item_data = current_user.get_item_info(int(database.read_cache('target_media_id')))['objects'][0]

        review_id = database.read_cache('target_review_id')
        media_id  = database.read_cache('target_media_id')
        target_url  = database.read_cache('upload_to_value')
        self.ui.review_target_url.setText(target_url)
        self.ui.thumbnail_pushButton.set_icon_from_url(current_user.get_item_info(media_id)['objects'][0]['thumb'])
        self.ui.review_target_name.setText(self.item_data['name'])


    def decorate_ui(self):
        self.ui.ui_greasepencilDownload_layout = QtWidgets.QVBoxLayout()
        self.ui.ui_downloadGeneral_layout = QtWidgets.QVBoxLayout()
        self.ui.ui_downloadGP_layout = QtWidgets.QVBoxLayout()

        self.ui.main_layout.addLayout(self.ui.ui_downloadGeneral_layout)

        self.ui.thumbnail_pushButton = RegularThumbnail(width=480, height=270)
        self.ui.review_target_name = RegularLineEdit()
        self.ui.review_target_url = RegularLineEdit()
        self.ui.ui_status_label = RegularStatusLabel()
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.ui_status_label)
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.thumbnail_pushButton)
        self.ui.ui_downloadGeneral_layout.addWidget(self.ui.review_target_url)

        # GP Range Row
        self.ui.downloadGP_range_layout = RegularGridLayout(self, label = 'Frame Offset')
        self.ui.ui_downloadGP_rangeIn_textEdit   = RegularQSpinBox()
        self.ui.ui_downloadGP_rangeIn_textEdit.setValue(0)
        self.ui.ui_downloadGP_rangeIn_textEdit.setMinimum(-10000)
        self.ui.downloadGP_range_layout.addWidget(self.ui.ui_downloadGP_rangeIn_textEdit,  0, 1)
        self.ui.downloadGP_range_layout.setColumnStretch(2,0)

        # GP Application Row
        self.ui.downloadGP_application_layout = RegularGridLayout(self, label = 'After Download')
        self.ui.downloadGP_application_checkbox = QtWidgets.QCheckBox()
        self.ui.downloadGP_application_checkbox.setText("Apply")
        self.ui.downloadGP_application_checkbox.setChecked(1)
        self.ui.downloadGP_application_checkbox.setFixedWidth(60)
        self.ui.downloadGP_application_layout.setColumnStretch(1,0)
        self.ui.downloadGP_application_comboBox = RegularComboBox()
        self.ui.downloadGP_application_comboBox.addItems(["... to active Viewport/Camera"])
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_checkbox,  0, 1)
        self.ui.downloadGP_application_layout.addWidget(self.ui.downloadGP_application_comboBox,  0, 2)
        self.ui.downloadGP_application_layout.setColumnStretch(2,1)

        self.ui.ui_downloadGP_pushButton = RegularButton()
        self.ui.ui_downloadGP_pushButton.clicked.connect(self.download_greasepencil)
        self.ui.ui_downloadGP_pushButton.setText("Download\nGrease Pencil")
        self.ui.ui_downloadVideoAnnotated_pushButton = RegularButton()
        self.ui.ui_downloadVideoAnnotated_pushButton.clicked.connect(self.download_video_annotated)
        self.ui.ui_downloadVideoAnnotated_pushButton.setText("Download\nAnnotated Video")

        self.ui.download_buttons_layout = QtWidgets.QHBoxLayout()
        self.ui.download_buttons_layout.addWidget(self.ui.ui_downloadGP_pushButton)
        self.ui.download_buttons_layout.addWidget(self.ui.ui_downloadVideoAnnotated_pushButton)
        #
        self.ui.ui_downloadGP_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_downloadGP_groupbox.setTitle('Grease Pencil')
        self.ui.ui_downloadGP_groupbox.setLayout(self.ui.ui_downloadGP_layout)
        self.ui.ui_downloadGP_layout.addLayout(self.ui.downloadGP_range_layout)
        self.ui.ui_downloadGP_layout.addLayout(self.ui.downloadGP_application_layout)
        self.ui.ui_downloadGP_layout.addLayout(self.ui.download_buttons_layout)

        self.ui.main_layout.addWidget(self.ui.ui_downloadGP_groupbox)


    def setAutoFrame(self):
        if not self.item_data:
            current_user = user.SyncSketchUser()
            self.item_data = current_user.get_item_info(int(database.read_cache('target_media_id')))['objects'][0]
        current_start_frame = cmds.playbackOptions(q=True, animationStartTime = True)
        print int(current_start_frame)
        print int(self.item_data['first_frame'])
        print ( int(current_start_frame) - int(self.item_data['first_frame']) - 1 )
        self.ui.ui_downloadGP_rangeIn_textEdit.setValue( int(current_start_frame) - int(self.item_data['first_frame']) - 1 )

    def download_greasepencil(self):
        downloaded_item = syncsketchGUI.download()
        offset = int(self.ui.ui_downloadGP_rangeIn_textEdit.value())
        if downloaded_item:
            if offset is not 0:
                print "Offsetting by %s frames"%offset
                downloaded_item = maya_scene.modifyGreasePencil(downloaded_item, offset)
            maya_scene.apply_greasepencil(downloaded_item, clear_existing_frames = True)
        else:
            print "Error: Could not download grease pencil file..."

    def download_video_annotated(self):
        print  "Not Implemented yet"

class FormatPresetWindow(SyncSketch_Window):
    """
    Video Preset Window Class
    """
    window_name = 'syncsketchGUI_preset_window'
    window_label = 'Recording Preset Manager'

    def __init__(self, parent=None, icon=None, color ='white'):
        super(FormatPresetWindow, self).__init__(parent=parent)

        self.decorate_ui()
        self.build_connections()
        self.populate_ui()

    def decorate_ui(self):
        self.ui.ui_formatpreset_layout = QtWidgets.QHBoxLayout()
        self.ui.ui_formatpreset_layout.setSpacing(1)
        self.ui.ui_formatPreset_comboBox = RegularComboBox()
        self.ui.ui_formatpreset_layout.addWidget(self.ui.ui_formatPreset_comboBox)


        self.ui.ps_new_preset_pushButton = RegularToolButton()
        self.ui.ps_new_preset_pushButton.setIcon(add_icon)

        self.ui.ps_rename_preset_pushButton = RegularToolButton()
        self.ui.ps_rename_preset_pushButton.setIcon(edit_icon)

        self.ui.ps_delete_preset_pushButton = RegularToolButton()
        self.ui.ps_delete_preset_pushButton.setIcon(delete_icon)

        self.ui.ui_formatpreset_layout.addWidget(self.ui.ps_rename_preset_pushButton)
        self.ui.ui_formatpreset_layout.addWidget(self.ui.ps_new_preset_pushButton)
        self.ui.ui_formatpreset_layout.addWidget(self.ui.ps_delete_preset_pushButton)


            # 720p HD

        self.ui.ui_format_layout = RegularGridLayout(self, label = 'Format' )
        self.ui.format_comboBox = RegularComboBox()
        self.ui.ui_format_layout.addWidget(self.ui.format_comboBox, 0, 1)
            # avi, qt

        self.ui.ui_encoding_layout = RegularGridLayout(self, label = 'Encoding' )
        self.ui.encoding_comboBox = RegularComboBox()
        self.ui.ui_encoding_layout.addWidget(self.ui.encoding_comboBox, 0, 1)
            # H.264

        # upload_layout - range
        self.ui.ui_resolution_layout = RegularGridLayout(self, label = 'Resolution')
        self.ui.ui_resolution_comboBox = RegularComboBox(self)
        self.ui.ui_resolution_comboBox.addItems(["Custom", "From Render Settings","From Viewport"])
        self.ui.width_spinBox  = RegularQSpinBox()
        self.ui.ui_resolutionX_label  = QtWidgets.QLabel()
        self.ui.ui_resolutionX_label.setText("x")
        self.ui.ui_resolutionX_label.setFixedWidth(8)
        self.ui.height_spinBox  = RegularQSpinBox()
        self.ui.ui_resolution_layout.addWidget(self.ui.ui_resolution_comboBox,  0, 1)
        self.ui.ui_resolution_layout.addWidget(self.ui.width_spinBox,  0, 2)
        self.ui.ui_resolution_layout.setColumnStretch(2,0)
        self.ui.ui_resolution_layout.addWidget(self.ui.ui_resolutionX_label,  0, 3)
        self.ui.ui_resolution_layout.addWidget(self.ui.height_spinBox,  0, 4)
        self.ui.ui_resolution_layout.setColumnStretch(3,0)
        self.ui.width_spinBox.setFixedWidth(45)
        self.ui.height_spinBox.setFixedWidth(45)
        self.ui.width_spinBox.setMinimum(4)
        self.ui.width_spinBox.setMaximum(32000)
        self.ui.height_spinBox.setMinimum(4)
        self.ui.height_spinBox.setMaximum(32000)

        self.ui.scaleButton_layout = QtWidgets.QHBoxLayout()
        for key,factor in {"¼":0.25, "½":0.5, "¾":0.75, "1":1.0, "2":2.0}.iteritems():
            print "key: %s\nfactor: %s"%(key, factor)
            btn = RegularToolButton()
            btn.setText(key)
            self.ui.scaleButton_layout.addWidget(btn)
            btn.setFixedWidth(20)
            btn.clicked.connect(partial(self.multiply_res, factor))


        self.ui.ui_resolution_layout.addLayout(self.ui.scaleButton_layout,  0, 5)

        self.ui.width_spinBox.setAlignment(QtCore.Qt.AlignRight)
        self.ui.height_spinBox.setAlignment(QtCore.Qt.AlignRight)


        self.ui.buttons_horizontalLayout = QtWidgets.QHBoxLayout()
        self.ui.cancel_pushButton = RegularButton()
        self.ui.cancel_pushButton.setText("Cancel")
        self.ui.save_pushButton = RegularButton()
        self.ui.save_pushButton.setText("Save")
        self.ui.buttons_horizontalLayout.setSpacing(1)
        self.ui.buttons_horizontalLayout.addWidget(self.ui.cancel_pushButton)
        self.ui.buttons_horizontalLayout.addWidget(self.ui.save_pushButton)

        self.ui.main_layout.addLayout(self.ui.ui_formatpreset_layout)
        self.ui.main_layout.addLayout(self.ui.ui_format_layout)
        self.ui.main_layout.addLayout(self.ui.ui_encoding_layout)
        self.ui.main_layout.addLayout(self.ui.ui_resolution_layout)
        self.ui.main_layout.addLayout(self.ui.buttons_horizontalLayout)
        self.ui.master_layout.addLayout(self.ui.main_layout)

    def multiply_res(self, factor):
        height = self.ui.height_spinBox.value()
        width = self.ui.width_spinBox.value()
        self.ui.height_spinBox.setValue(int(height*factor))
        self.ui.width_spinBox.setValue(int(width*factor))

    def build_connections(self):
        self.ui.save_pushButton.clicked.connect(self.save)
        self.ui.cancel_pushButton.clicked.connect(self.cancel)

        self.ui.ui_formatPreset_comboBox.currentIndexChanged.connect(self.load_preset_from_selection)
        self.ui.format_comboBox.currentIndexChanged.connect(self.update_encoding_list)

    def populate_ui(self):
        """
        Populate the UI based on the available values
        depending on what the user has installed and what the DCC tool has to offer
        """
        # Get the values from the host DCC
        if MAYA:

            formats = maya_scene.get_available_formats()
            encodings = maya_scene.get_available_compressions()
        else:
            formats = list()
            encodings = list()

        # Populate the preset names
        self.ui.ui_formatPreset_comboBox.clear()

        self.ui.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, defaultValue= DEFAULT_PRESET )

        # Populate the values to the fields based on the preset
        self.ui.format_comboBox.clear()
        self.ui.encoding_comboBox.clear()
        self.ui.width_spinBox.clear()
        self.ui.height_spinBox.clear()

        self.ui.ui_formatPreset_comboBox.addItems([DEFAULT_PRESET])
        # self.ui.viewport_name_comboBox.addItems(['Hussah!'])
        self.ui.format_comboBox.addItems(formats)
        self.ui.encoding_comboBox.addItems(encodings)
        self.ui.width_spinBox.setValue(1920)
        self.ui.height_spinBox.setValue(1080)

    def update_encoding_list(self):
        """
        Refresh the available compressions.
        """
        if MAYA:

            format = self.ui.format_comboBox.currentText()
            encodings = maya_scene.get_available_compressions(format)
            self.ui.encoding_comboBox.clear()
            self.ui.encoding_comboBox.addItems(encodings)

    def load_preset(self, preset_name=None):
        """
        Load the user's current preset from yaml
        """
        preset_file = path.get_config_yaml(PRESET_YAML)
        preset_data = database._parse_yaml(preset_file)
        if not preset_data:
            return

        if not preset_name:
            qt_utils.self.ui.ui_formatPreset_comboBox.set_combobox_index( selection=DEFAULT_PRESET)
            qt_utils.self.ui.format_comboBox.set_combobox_index( selection='avi')
            self.ui.encoding_comboBox.set_combobox_index( selection='none')
            self.ui.width_spinBox.setValue(1280)
            self.ui.height_spinBox.setValue(720)


        elif preset_name == DEFAULT_PRESET:
            self.ui.ui_formatPreset_comboBox.set_combobox_index( selection=DEFAULT_PRESET)

            if sys.platform == 'darwin':
                format = 'avfoundation'
                encoding = 'H.264'

            elif sys.platform == 'linux2':
                format = 'movie'
                encoding = 'H.264'

            elif sys.platform == 'win32':
                format = 'avi'
                encoding = 'none'

        else:
            preset = preset_data.get(preset_name)
            if not preset:
                return
            print preset
            format = preset.get('format')
            encoding = preset.get('encoding')
            width = preset.get('width')
            height = preset.get('height')

            self.ui.ui_formatPreset_comboBox.set_combobox_index( selection=preset_name)
            self.ui.format_comboBox.set_combobox_index( selection=format)
            self.ui.encoding_comboBox.set_combobox_index( selection=encoding)
            self.ui.width_spinBox.setValue(width)
            self.ui.height_spinBox.setValue(height)

    def load_preset_from_selection(self):
        """
        Load the currently selected preset from the combobox list
        """
        selected_preset = self.ui.ui_formatPreset_comboBox.currentText()
        self.load_preset(selected_preset)

    def save(self):
        preset_file = path.get_config_yaml(PRESET_YAML)
        preset_data = database._parse_yaml(preset_file)

        preset_name = self.ui.ui_formatPreset_comboBox.currentText()
        format = self.ui.format_comboBox.currentText()
        encoding = self.ui.encoding_comboBox.currentText()
        width = self.ui.width_spinBox.value()
        height = self.ui.height_spinBox.value()

        new_data = dict()
        if preset_name == DEFAULT_PRESET:
            new_data = {'current_preset': preset_name}

        else:
            new_data = {'current_preset': preset_name,
                        preset_name:
                            {'encoding': encoding,
                             'format': format,
                             'height': height,
                             'width': width}}
        if preset_data:
            preset_data.update(new_data)
        else:
            preset_data = new_data

        with codecs.open(preset_file, 'w', encoding='utf-8') as f_out:
            yaml.safe_dump(preset_data, f_out, default_flow_style=False)

        self.parent.ui.ui_formatPreset_comboBox.populate_combo_list( PRESET_YAML, preset_name)

        self.close()



class ViewportPresetWindow(SyncSketch_Window):
    """
    Video Preset Window Class
    """
    window_name = 'syncsketchGUI_viewport_preset_window'
    window_label = 'Viewport Preset Manager'

    def __init__(self, parent=None):
        super(ViewportPresetWindow, self).__init__(parent=parent)
        self.decorate_ui()
        self.build_connections()
        self.populate_ui()

        if MAYA:
            self.build_screenshot()


    def decorate_ui(self):
        self.ui.ps_thumb_horizontalLayout = QtWidgets.QGridLayout()
        self.ui.screenshot_pushButton = RegularThumbnail(width=480, height=270)
        self.ui.ui_thumbcamera_label = HoverButton(icon=refresh_icon)
        self.ui.ui_thumbcamera_label.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.ui.ui_thumbcamera_label.setMinimumSize(480, 270)
        self.ui.ps_thumb_horizontalLayout.addWidget(self.ui.screenshot_pushButton,0,0)
        self.ui.ps_thumb_horizontalLayout.addWidget(self.ui.ui_thumbcamera_label,0,0)


        # Viewport Preset Selection and Handling
        self.ui.ps_preset_horizontalLayout = QtWidgets.QHBoxLayout()
        self.ui.ui_viewportpreset_comboBox = RegularComboBox()


        self.ui.ps_new_preset_pushButton = RegularToolButton()
        self.ui.ps_new_preset_pushButton.setIcon(add_icon)

        self.ui.ps_rename_preset_pushButton = RegularToolButton()
        self.ui.ps_rename_preset_pushButton.setIcon(edit_icon)

        self.ui.ps_delete_preset_pushButton = RegularToolButton()
        self.ui.ps_delete_preset_pushButton.setIcon(delete_icon)

        self.ui.ps_refresh_pushButton = RegularToolButton()
        self.ui.ps_refresh_pushButton.setIcon(refresh_icon)

        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_refresh_pushButton)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ui_viewportpreset_comboBox)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_rename_preset_pushButton)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_new_preset_pushButton)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_delete_preset_pushButton)

        # Viewport Preset Application
        self.ui.buttons_horizontalLayout = QtWidgets.QHBoxLayout()

        self.ui.ps_apply_preset_pushButton = RegularButton()
        self.ui.ps_apply_preset_pushButton.setText("Apply \nto current view")
        self.ui.buttons_horizontalLayout.addWidget(self.ui.ps_apply_preset_pushButton)

        self.ui.ps_applyToAll_preset_pushButton = RegularButton()
        self.ui.ps_applyToAll_preset_pushButton.setText("Apply\nto all views")
        self.ui.buttons_horizontalLayout.addWidget(self.ui.ps_applyToAll_preset_pushButton)

        self.ui.ps_save_preset_pushButton = RegularButton()
        self.ui.ps_save_preset_pushButton.setText("Override preset\nfrom view")
        self.ui.buttons_horizontalLayout.addWidget(self.ui.ps_save_preset_pushButton)

        self.ui.ui_status_label = RegularStatusLabel()

        self.ui.ui_status_label.setFixedHeight(30)
        self.ui.master_layout.setSpacing(1)
        self.ui.master_layout.addWidget(self.ui.ui_status_label)
        self.ui.master_layout.addLayout(self.ui.ps_thumb_horizontalLayout)
        self.ui.master_layout.addLayout(self.ui.ps_preset_horizontalLayout)
        self.ui.master_layout.addLayout(self.ui.buttons_horizontalLayout)

    def build_connections(self):
        self.ui.ps_refresh_pushButton.clicked.connect(self.build_screenshot)
        self.ui.screenshot_pushButton.clicked.connect(self.build_screenshot)
        self.ui.ui_thumbcamera_label.clicked.connect(self.build_screenshot)
        self.ui.ps_new_preset_pushButton.clicked.connect(self.new_preset)
        self.ui.ps_rename_preset_pushButton.clicked.connect(self.rename_preset)
        self.ui.ps_delete_preset_pushButton.clicked.connect(self.delete_preset)
        self.ui.ps_apply_preset_pushButton.clicked.connect(self.apply_preset)
        self.ui.ps_applyToAll_preset_pushButton.clicked.connect(self.apply_preset_to_all)
        self.ui.ps_save_preset_pushButton.clicked.connect(self.override_preset)
        self.ui.ui_viewportpreset_comboBox.activated.connect(self.set_to_current_preset)


    def new_preset(self, new_preset_name = None):
        title = 'Creating Preset'
        message = 'Please choose a name for this preset.'
        user_input = InputDialog(self, title, message)
        if not user_input.response:
            return
        new_preset_name = user_input.response_text

        if not new_preset_name:
            return

        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        new_preset_name =  maya_scene.new_viewport_preset(preset_file, new_preset_name)
        database.save_cache("current_viewport_preset", new_preset_name)
        self.populate_ui()
        self.build_screenshot()
        event.accept()

    def delete_preset(self, preset_name = None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        maya_scene.delete_viewport_preset(preset_file, preset_name)
        self.populate_ui()
        self.ui.ui_viewportpreset_comboBox.set_combobox_index(0)
        self.build_screenshot()


    def rename_preset(self, preset_name=None, new_preset_name=None):
        title = 'Renaming Preset'
        message = 'Please choose a name for this preset.'
        # user_input = InputDialog(self, title, message)
        current_preset = self.ui.ui_viewportpreset_comboBox.currentText()
        new_preset_name, response =  QtWidgets.QInputDialog.getText(self, "Rename this preset",  "Please enter a new Name:", QtWidgets.QLineEdit.Normal, current_preset )
        print new_preset_name
        if not new_preset_name:
            return
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = current_preset
            new_preset_name = maya_scene.rename_viewport_preset(preset_file, preset_name, new_preset_name)
        if not new_preset_name:
            title = 'Error Renaming'
            message = 'It appears this name already exists.'
            WarningDialog(self, title, message)
            return
        database.save_cache("current_viewport_preset", new_preset_name)
        self.populate_ui()
        self.setParent_preset()

    def apply_preset_to_all(self, preset_name = None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        panels = maya_scene.get_all_mdoelPanels()
        maya_scene.apply_viewport_preset(preset_file, preset_name, panels)

    def apply_preset(self, preset_name = None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        maya_scene.apply_viewport_preset(preset_file, preset_name)



    def override_preset(self, preset_name = None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        maya_scene.save_viewport_preset(preset_file, preset_name)
        self.build_screenshot(preset_name)


    def build_screenshot(self, preset_name = None):
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()

        preset_file = path.get_config_yaml(VIEWPORT_YAML)

        current_camera = database.read_cache('selected_camera')
        fname = maya_scene.screenshot_current_editor( preset_file, preset_name, camera = current_camera)
        self.ui.ui_status_label.update(preset_name)
        if not fname:
            self.ui.screenshot_pushButton.setIcon(logo_icon)
        else:
            icon = _get_qicon(fname)
            self.ui.screenshot_pushButton.setIcon(icon)
            self.ui.ui_status_label.update("Previewing Preset '%s' - from camera '%s'"%(preset_name,current_camera))
        self.ui.screenshot_pushButton.setText('')
        self.ui.screenshot_pushButton.setIconSize(QtCore.QSize(480, 270))

        self.setWindowIcon(logo_icon)


    def populate_ui(self):
        """
        Populate the UI based on the available values
        depending on what the user has installed and what the DCC tool has to offer
        """
        # Get the values from the host DCC
        # Populate the viewport names
        self.ui.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, defaultValue= database.read_cache('current_viewport_preset'))


    def set_to_current_preset(self):
        """
        Load the currently selected preset from the combobox list
        """
        self.setParent_preset()
        self.build_screenshot()

    def setParent_preset(self):
        database.save_cache("current_viewport_preset", self.ui.ui_viewportpreset_comboBox.currentText())
        try:
            self.parent.ui.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, defaultValue= database.read_cache('current_viewport_preset'))
        except:
            pass

    def closeEvent(self, event):
        self.setParent_preset()
        event.accept()






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

# tree function
def get_current_item_from_ids(tree, ids=None):
    # tree.setCurrentItem(tree.topLevelItem(0), 0)
    if ids is None:
        ids = []
    if not ids:
        return

    if len(ids) > 1:
        id = int(ids[1])
    else:
        id = int(ids[0])
    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)
    # by default select first item(playground)
    # todo: make sure we're not parsing for the correct review id
    while iterator.value():
        item = iterator.value()
        item_data = item.data(1, QtCore.Qt.EditRole)
        if item_data.get('id') == id:
            tree.setCurrentItem(item, 1)
            tree.scrollToItem(item)
        iterator +=1
    return item_data

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def get_ids_from_link(link = database.read_cache('upload_to_value')):
    if not link:
        return
    return link.split('/')[-1].split('#')

# loggedin window
def isloggedIn(self,loggedIn=False):
    if loggedIn:
        message =  "Successfully logged in as %s"%self.current_user.get_name()
        self.ui.ui_status_label.update(message, color = success_color)
    else:
        message = message_is_not_loggedin
        self.ui.ui_status_label.update(message, color=error_color)
    update_login_ui(self)


# Tree Function
def populate_review_panel(self, playground_only = False, item_to_add = None, force = False):
    if not is_connected():
        self.ui.ui_status_label.update(message_is_not_connected, color=error_color)
        isloggedIn(self,loggedIn=False)
        print "\nNot connected to SyncSketch ..."
        return

    self.current_user = user.SyncSketchUser()

    # Always refresh Tree View
    self.ui.browser_treeWidget.clear()

    if not self.current_user.is_logged_in():
        return
    else:
        print "Updating Account Data ..."



    # Add playground
    playground_data = {u'reviewURL': path.playground_url, u'id' : u'playground'}
    playground_item = _build_widget_item(  parent = self.ui.browser_treeWidget,
                                            item_name = 'Playground',
                                            item_type = 'playground',
                                            item_icon = playground_icon,
                                            item_data = playground_data)
    if playground_only:
        return

    ### self.ui.ui_status_label.update('Getting data from SyncSketch...')

    isloggedIn(self, self.current_user.is_logged_in())

    global USER_ACCOUNT_DATA

    if USER_ACCOUNT_DATA and not force:
        account_data =  USER_ACCOUNT_DATA

    else:
        # todo: fix connection verification
        # if not connection.is_connected():
        #     message = 'WARNING: No Internet connection'
        #     message += 'Please check your internet connection and try refreshing again.'
        #     color = error_color
        #     self.ui.ui_status_label.update(message, color)
        #     return 'unconnected'
        #
        # else:
        try:
            account_data = self.current_user.get_account_data()

        except Exception, err:
            account_data = None
            print u'%s' %(err)

        finally:
            if account_data:
                account_is_connected = True
                message = 'Connected and authorized with syncsketchGUI as "{}"'.format(self.current_user.get_name())
                color = success_color
            else:
                account_is_connected = False
                message = 'WARNING: Could not connect to SyncSketch. '
                message += message_is_not_connected
                color = error_color
            try:
                self.ui.ui_status_label.update(message, color)
            except:
                pass

    if not account_data or type(account_data) is dict:
        print "Error: No SyncSketch account data found."
        return

    # Add account
    for account in account_data:
        account_treeWidgetItem = _build_widget_item(   parent = self.ui.browser_treeWidget,
                                                        item_name = account.get('name'),
                                                        item_type = 'account',
                                                        item_icon = account_icon,
                                                        item_data = account)
        # Add projects
        projects = account.get('projects')
        for project in projects:
            project_treeWidgetItem = _build_widget_item(   parent = account_treeWidgetItem,
                                                            item_name = project.get('name'),
                                                            item_type = 'project',
                                                            item_icon = project_icon,
                                                            item_data = project)
            # Add reviews
            reviews = project.get('reviews')
            for review in reviews:
                review_treeWidgetItem = _build_widget_item(parent = project_treeWidgetItem,
                                                            item_name = review.get('name'),
                                                            item_type = 'review',
                                                            item_icon = review_icon,
                                                            item_data = review)
                # Add items
                items = review.get('items')
                for media in items:


                    if not media.get('type'):
                        specified_media_icon = media_unknown_icon
                    elif 'video' in media.get('type').lower():
                        specified_media_icon = media_video_icon
                    elif 'image' in media.get('type').lower():
                        specified_media_icon = media_image_icon
                    elif 'sketchfab' in media.get('type').lower():
                        specified_media_icon = media_sketchfab_icon
                    else:
                        specified_media_icon = media_unknown_icon

                    # specified_media_icon = icons._get_qicon_from_url(media.get('thumbnail_url'))
                    media_treeWidgetItem = _build_widget_item( parent = review_treeWidgetItem,
                                                                item_name = media.get('name'),
                                                                item_type = 'media',
                                                                item_icon = specified_media_icon,
                                                                item_data = media)

                    media_treeWidgetItem.sizeHint(80)

    ids = get_ids_from_link(database.read_cache('upload_to_value'))
    get_current_item_from_ids(self.ui.browser_treeWidget, ids)
    USER_ACCOUNT_DATA = account_data

    self.populate_upload_settings()
    return account_data


class MenuWindow(SyncSketch_Window):
    """
    Main browser window of the syncsketchGUI services
    """
    window_name     = 'syncsketchGUI_menu_window'
    window_label    = 'SyncSketch'

    account_is_connected = False

    def __init__(self, parent):
        super(MenuWindow, self).__init__(parent=parent)
        self.setMaximumSize(700, 650)

        self.decorate_ui()
        self.build_connections()

        # Load UI state
        self.restore_ui_state()

        update_login_ui(self)


    def closeEvent(self, event):
        self.save_ui_state()
        event.accept()

    def restore_ui_state(self):

        # Playblast Settings
        value = sanitize(database.read_cache('ps_directory_lineEdit'))
        self.ui.ps_directory_lineEdit.setText(
            value if value else os.path.expanduser('~/Desktop/playblasts'))

        value = sanitize(database.read_cache('ps_clipname_lineEdit'))
        self.ui.ps_clipname_lineEdit.setText(value)

        value = database.read_cache('ps_play_after_creation_checkBox')
        self.ui.ps_play_after_creation_checkBox.setChecked(
            True if value == 'true' else False)

        # value = database.read_cache('ps_force_overwrite_checkBox')
        # self.ui.ps_force_overwrite_checkBox.setChecked(
        #     True if value == 'true' else False)

        value = database.read_cache('current_preset')
        self.ui.ui_formatPreset_comboBox.set_combobox_index( selection=value)

        self.populate_camera_comboBox()

        value = database.read_cache('current_range_type')
        self.ui.ui_range_comboBox.set_combobox_index(selection=value)

        value = database.read_cache('ps_upload_after_creation_checkBox')
        self.ui.ps_upload_after_creation_checkBox.setChecked(
            True if value == 'true' else False)

        value = database.read_cache('us_filename_lineEdit')
        self.ui.us_filename_lineEdit.setText(
            value if value else 'playblast')

        value = database.read_cache('ps_open_afterUpload_checkBox')
        self.ui.ps_open_afterUpload_checkBox.setChecked(
            True if value == 'true' else False)


    def save_ui_state(self):
        ui_setting = {
            # Playblast Settings
            'ps_directory_lineEdit':
                sanitize(self.ui.ps_directory_lineEdit.text()),

            'ps_clipname_lineEdit':
                sanitize(self.ui.ps_clipname_lineEdit.text()),

            'current_range_type':
                self.ui.ui_range_comboBox.currentText(),

            # 'ps_force_overwrite_checkBox':
            #     'true' if self.ui.ps_force_overwrite_checkBox.isChecked() else 'false',

            'ps_play_after_creation_checkBox':
                bool_to_str( self.ui.ps_play_after_creation_checkBox.isChecked() ),

            'ps_upload_after_creation_checkBox':
                bool_to_str( self.ui.ps_upload_after_creation_checkBox.isChecked() ),


            'us_filename_lineEdit':
                self.ui.us_filename_lineEdit.text(),


            'ps_open_afterUpload_checkBox':
                bool_to_str( self.ui.ps_open_afterUpload_checkBox.isChecked() )}


        database.dump_cache(ui_setting)


    def clear_ui_setting(self):
        database.dump_cache('clear')

    def build_connections(self):
        # Menu Bar
        # self.ui.menuLogin.triggered.connect(self.connect_account)
        self.ui.help_pushButton.clicked.connect(self.open_support)
        # self.ui.help_pushButton.clicked.connect(self.open_contact)
        # self.ui.help_pushButton.clicked.connect(self.open_terms_of_service)
        self.ui.login_pushButton.clicked.connect(self.connect_account)
        # self.ui.help_pushButton.clicked.connect(self.open_terms_of_service)
        self.ui.logout_pushButton.clicked.connect(self.disconnect_account)
        self.ui.syncsketchGUI_pushButton.clicked.connect(self.open_landing)
        self.ui.signup_pushButton.clicked.connect(self.open_signup)


        # Reviews
        self.ui.ui_record_pushButton.clicked.connect(self.playblast)
        self.ui.ui_upload_pushButton.clicked.connect(self.upload)

        self.ui.ui_download_pushButton.clicked.connect(self.download)

        self.ui.video_thumb_pushButton.clicked.connect(self.update_clip_thumb)

        #tree widget functions
        self.ui.browser_treeWidget.currentItemChanged.connect(self.validate_review_url)
        self.ui.browser_treeWidget.doubleClicked.connect(self.open_upload_to_url)

        # Videos / Playblast Settings
        self.ui.ui_formatPreset_comboBox.currentIndexChanged.connect(self.update_current_preset)
        self.ui.ui_viewportpreset_comboBox.currentIndexChanged.connect(self.update_current_viewport_preset)
        self.ui.ui_cameraPreset_comboBox.currentIndexChanged.connect(self.update_current_camera)

        self.ui.ps_lastfile_comboBox.currentIndexChanged.connect(self.update_last_recorded)

        self.ui.ps_format_toolButton.clicked.connect(self.manage_preset)
        self.ui.ps_directory_toolButton.clicked.connect(self.get_directory_from_browser)

        self.ui.target_lineEdit.editingFinished.connect(self.select_item_from_target_input)
        # Videos / Playblast Settings
        self.ui.ui_viewport_toolButton.clicked.connect(self.manage_viewport_preset)

        self.ui.ui_range_toolButton.clicked.connect(self.set_in_out)
        self.ui.ui_camera_toolButton.clicked.connect(self.set_active_camera)

        self.ui.ui_range_comboBox.currentIndexChanged.connect(self.set_rangeFromComboBox)

        self.ui.ui_rangeIn_textEdit.textChanged.connect(self.store_frame)
        self.ui.ui_rangeOut_textEdit.textChanged.connect(self.store_frame)

        # Videos / Upload Settings
        self.ui.ui_open_pushButton.clicked.connect(self.open_upload_to_url)
        self.ui.ui_copyURL_pushButton.clicked.connect(self.copy_to_clipboard)


    def decorate_ui(self):


        # Playblast Settings
        file_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)

        directory_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        # Row 1
        # Setting up Main Layout

        indent = 9
        self.ui.master_layout.setSpacing(0)
        self.ui.ui_login_layout = QtWidgets.QHBoxLayout()
        self.ui.main_layout = QtWidgets.QGridLayout()
        self.ui.ui_status_layout = QtWidgets.QHBoxLayout()
        self.ui.ui_login_layout.setSpacing(0)
        self.ui.ui_status_layout.setContentsMargins(0,0,0,10)
        self.ui.master_layout.addLayout(self.ui.ui_login_layout)
        self.ui.master_layout.addLayout(self.ui.ui_status_layout)
        self.ui.master_layout.addLayout(self.ui.main_layout)

        self.ui.main_layout.setSpacing(6)
#        self.ui.main_layout.setMargin(5)
        # self.ui.main_layout.setSpacing(3)

        # Adding the two colums to main_layout
        self.ui.ui_mainLeft_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_mainRight_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_mainLeft_gridLayout.setSpacing(1)
        self.ui.ui_mainRight_gridLayout.setSpacing(2)
        self.ui.ui_reviewSelection_hBoxLayout = QtWidgets.QHBoxLayout()

        # self.ui.ui_target_groupbox = QtWidgets.QGroupBox()
        # self.ui.main_layout.addWidget(self.ui.ui_mainRight_gridLayout, 0,1)
        # self.ui.ui_target_groupbox.setTitle('TARGET')
        # self.ui.ui_target_groupbox.setLayout(self.ui.ui_mainRight_gridLayout)

        self.ui.main_layout.addLayout(self.ui.ui_mainLeft_gridLayout, 0,0)
        self.ui.main_layout.addLayout(self.ui.ui_mainRight_gridLayout, 0,1)

        self.ui.main_layout.setColumnMinimumWidth(0,320)
        self.ui.main_layout.setColumnMinimumWidth(1,320)
        self.ui.main_layout.setColumnStretch(0,1)
        self.ui.main_layout.setColumnStretch(1,0)

        # Adding ui_mainLeft_gridLayout
        self.ui.ui_record_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_clipSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_targetSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui.ui_targetSelection_gridLayout.setSpacing(3)

        self.ui.ui_record_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_record_groupbox)
        self.ui.ui_record_groupbox.setTitle('RECORD')
        self.ui.ui_record_groupbox.setLayout(self.ui.ui_record_gridLayout)

        self.ui.ui_upload_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_mainLeft_gridLayout.addWidget(self.ui.ui_upload_groupbox)
        self.ui.ui_upload_groupbox.setTitle('FILE TO UPLOAD')
        self.ui.ui_upload_groupbox.setLayout(self.ui.ui_clipSelection_gridLayout)

        self.ui.ui_targetSelection_groupbox = QtWidgets.QGroupBox()
        self.ui.ui_targetSelection_groupbox.setTitle('TARGET FOR UPLOAD')
        self.ui.ui_targetSelection_groupbox.setLayout(self.ui.ui_targetSelection_gridLayout)


        self.ui.ui_mainLeft_gridLayout.addLayout(self.ui.ui_record_gridLayout,0,0)
        self.ui.ui_mainLeft_gridLayout.addLayout(self.ui.ui_clipSelection_gridLayout,1,0)



        # self.ui.ui_record_layout.setObjectName("record_layout")

        # Creating Review Selection Layout

        # - buttons for opening and copying to clipboard
        # - tree wdget

        self.ui.ui_treeWidget_layout = QtWidgets.QVBoxLayout()

        self.ui.browser_treeWidget = QtWidgets. QTreeWidget()
        self.ui.browser_treeWidget.header().setStyleSheet("color: %s"%success_color)

        highlight_palette = self.ui.browser_treeWidget.palette()
        highlight_palette.setColor(QtGui.QPalette.Highlight, highlight_color)
        self.ui.browser_treeWidget.setPalette(highlight_palette)
        self.ui.browser_treeWidget.setHeaderLabel('refresh')
        #self.ui.browser_treeWidget.header().setSectionsClickable(True)
        self.ui.browser_treeWidget.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.ui.browser_treeWidget.header().sectionClicked.connect(self.refresh)
        self.ui.ui_treeWidget_layout.addWidget(self.ui.browser_treeWidget)


        self.ui.target_lineEdit = RegularLineEdit()
        self.ui.ui_open_pushButton = RegularToolButton(self, open_icon)
        self.ui.ui_copyURL_pushButton = RegularToolButton(self, copy_icon)
        self.ui.ui_reviewSelection_hBoxLayout.addWidget(self.ui.target_lineEdit)
        self.ui.ui_reviewSelection_hBoxLayout.addWidget(self.ui.ui_open_pushButton)
        self.ui.ui_reviewSelection_hBoxLayout.addWidget(self.ui.ui_copyURL_pushButton)

        # creating HBox Layout with all
        # self.ui.target_select_label = QtWidgets.QLabel()
        # self.ui.target_select_label.setText('Paste a link or select a review/media file above')
        # self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.target_select_label)

        self.ui.thumbnail_itemPreview = RegularThumbnail(width=320, height=180)
        self.ui.ui_mainRight_gridLayout.addWidget(self.ui.ui_targetSelection_groupbox)
        self.ui.ui_targetSelection_gridLayout.addLayout(self.ui.ui_treeWidget_layout)
        self.ui.ui_targetSelection_gridLayout.addLayout(self.ui.ui_reviewSelection_hBoxLayout)
        self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.thumbnail_itemPreview)
        self.ui.target_info_label = QtWidgets.QLabel()
        # self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.target_info_label)
        self.ui.target_info_label2 = QtWidgets.QLabel()
        # self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.target_info_label2)

        # self.ui.target_info_label.setText('Hey there')
        # self.ui.target_info_label2.setText('Hey there')

        # upload_layout -  format preset
        self.ui.upload_formatPreset_layout = RegularGridLayout(self, label = 'Format Preset' )
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_formatPreset_layout)
        self.ui.ui_formatPreset_comboBox = RegularComboBox(self)
        self.ui.ps_preset_description = QtWidgets.QLabel()
        self.ui.ps_preset_description.setStyleSheet("font: 9pt")
        self.ui.ps_preset_description.setIndent(5)
        self.ui.ps_format_toolButton = RegularToolButton(self, icon = file_icon)
        self.ui.upload_formatPreset_layout.addWidget(self.ui.ui_formatPreset_comboBox,  0, 1)
        self.ui.upload_formatPreset_layout.addWidget(self.ui.ps_format_toolButton,  0, 2)
        self.ui.upload_formatPreset_layout.addWidget(self.ui.ps_preset_description,  1, 1,1,2)

        # upload_layout - viewport preset
        self.ui.upload_viewportPreset_layout = RegularGridLayout(self, label = 'Viewport Preset')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_viewportPreset_layout)
        self.ui.ui_viewportpreset_comboBox = RegularComboBox(self)
        self.ui.ui_viewport_toolButton = RegularToolButton(self, icon = preset_icon)
        self.ui.upload_viewportPreset_layout.addWidget(self.ui.ui_viewportpreset_comboBox,  0, 1)
        self.ui.upload_viewportPreset_layout.addWidget(self.ui.ui_viewport_toolButton,  0, 2)

        # upload_layout - camera
        self.ui.upload_cameraPreset_layout = RegularGridLayout(self, label = 'Camera')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_cameraPreset_layout)
        self.ui.ui_cameraPreset_comboBox = RegularComboBox(self)
        self.ui.ui_camera_toolButton = RegularToolButton(self, icon = fill_icon)
        self.ui.upload_cameraPreset_layout.addWidget(self.ui.ui_cameraPreset_comboBox,  0, 1)
        self.ui.upload_cameraPreset_layout.addWidget(self.ui.ui_camera_toolButton,  0, 2)

        # upload_layout - range
        self.ui.upload_range_layout = RegularGridLayout(self, label = 'Frame Range')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_range_layout)
        self.ui.ui_range_comboBox = RegularComboBox(self)
        self.ui.ui_range_comboBox.addItems(["Start / End", "Time Slider","Highlighted","Current Frame"])
        self.ui.ui_range_toolButton = RegularToolButton(self, icon = fill_icon)
        self.ui.ui_rangeIn_textEdit  = RegularLineEdit()
        self.ui.ui_rangeOut_textEdit  = RegularLineEdit()
        self.ui.upload_range_layout.addWidget(self.ui.ui_range_comboBox,  0, 1)
        self.ui.upload_range_layout.addWidget(self.ui.ui_rangeIn_textEdit,  0, 2)
        self.ui.upload_range_layout.setColumnStretch(2,0)
        self.ui.upload_range_layout.addWidget(self.ui.ui_rangeOut_textEdit,  0, 3)
        self.ui.upload_range_layout.setColumnStretch(3,0)
        self.ui.ui_rangeIn_textEdit.setFixedWidth(40)
        self.ui.ui_rangeOut_textEdit.setFixedWidth(40)

        self.ui.ui_rangeIn_textEdit.setAlignment(QtCore.Qt.AlignRight)
        self.ui.ui_rangeOut_textEdit.setAlignment(QtCore.Qt.AlignRight)
        self.ui.upload_range_layout.addWidget(self.ui.ui_range_toolButton,  0, 4)

        self.onlyInt = QtGui.QIntValidator()
        self.ui.ui_rangeIn_textEdit.setValidator(self.onlyInt)
        self.ui.ui_rangeIn_textEdit.setPlaceholderText('Start')
        self.ui.ui_rangeOut_textEdit.setValidator(self.onlyInt)
        self.ui.ui_rangeOut_textEdit.setPlaceholderText('End')

        # upload_layout - Directory
        self.ui.upload_directory_layout = RegularGridLayout(self, label = 'Directory')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_directory_layout)
        self.ui.ps_directory_lineEdit = QtWidgets.QLineEdit()
        self.ui.ps_directory_lineEdit.setPlaceholderText('Output Directory')
        self.ui.ps_directory_toolButton = RegularToolButton(self, icon = directory_icon)
        self.ui.upload_directory_layout.addWidget(self.ui.ps_directory_lineEdit,  0, 1)
        self.ui.upload_directory_layout.addWidget(self.ui.ps_directory_toolButton,  0, 2)

        # record_layout - filename
        self.ui.upload_filename_layout = RegularGridLayout(self, label = 'Clip Name')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_filename_layout)
        self.ui.us_filename_lineEdit = QtWidgets.QLineEdit()
        self.ui.us_filename_lineEdit.setPlaceholderText('File Name or Prefix')
        self.ui.ps_filename_toolButton = RegularToolButton(self)

        self.ui.ps_filename_toolButton.setEnabled(0)
        self.ui.upload_filename_layout.addWidget(self.ui.us_filename_lineEdit,  0, 1)
        self.ui.upload_filename_layout.addWidget(self.ui.ps_filename_toolButton,  0, 2)

        # record_layout - clipname
        self.ui.upload_clipname_layout = RegularGridLayout(self, label = 'Clip Suffix ')
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_clipname_layout)
        self.ui.ps_clipname_lineEdit = QtWidgets.QLineEdit()
        self.ui.ps_clipname_lineEdit.setPlaceholderText('Clip Suffix (optional)')
        self.ui.ps_clipname_toolButton = RegularToolButton(self)
        self.ui.ps_clipname_toolButton.setEnabled(0)
        self.ui.upload_clipname_layout.addWidget(self.ui.ps_clipname_lineEdit,  0, 1)
        self.ui.upload_clipname_layout.addWidget(self.ui.ps_clipname_toolButton,  0, 2)

        # record_layout - after record
        self.ui.upload_after_layout = RegularGridLayout(self, label = 'After Record')
        self.ui.ps_play_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_play_after_creation_checkBox.setChecked(True)
        self.ui.ps_play_after_creation_checkBox.setText('Play')
        self.ui.ps_upload_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_upload_after_creation_checkBox.setText('Upload')
        self.ui.upload_after_layout.addWidget(self.ui.ps_play_after_creation_checkBox,  0, 1)
        self.ui.upload_after_layout.addWidget(self.ui.ps_upload_after_creation_checkBox,  0, 2)
        self.ui.ui_record_gridLayout.addLayout(self.ui.upload_after_layout)
        # record_layout - record button
        self.ui.ui_record_pushButton = RegularButton(self, icon = record_icon, color=record_color)
        self.ui.ui_record_pushButton.setText("RECORD")
        self.ui.ui_record_gridLayout.addWidget(self.ui.ui_record_pushButton)

        # CLIP SELECTION
        # - - - - - - - - - -

        # - - -
        # record_layout - camera
        self.ui.ps_lastfile_comboBox = RegularComboBox(self)

        self.ui.ps_lastfile_comboBox.setEditable(1)
        self.ui.video_thumb_pushButton = QtWidgets.QPushButton()
        self.ui.cs_info_label = QtWidgets.QLabel()
        self.ui.cs_info_label.setStyleSheet("font: 9pt")
        self.ui.video_thumb_pushButton.setContentsMargins(0, 0, 0, 0)

        self.ui.ui_thumb_gridLayout = QtWidgets.QGridLayout()
        self.ui.ui_thumb_gridLayout.setSpacing(3)
        self.ui.ui_clipSelection_gridLayout.addLayout(self.ui.ui_thumb_gridLayout)
        self.ui.video_thumbOverlay_pushButton = HoverButton(icon = play_icon)

        self.ui.ui_lastfile_layout = QtWidgets.QHBoxLayout()

        self.ui.ui_lastfileSelection_layout = QtWidgets.QHBoxLayout()
        self.ui.ps_filename_toolButton = RegularToolButton(self, icon = file_icon)
        self.ui.ps_filename_toolButton.clicked.connect(self.openFileNameDialog)
        self.ui.ui_lastfileSelection_layout.addWidget(self.ui.ps_lastfile_comboBox)
        self.ui.ui_lastfileSelection_layout.addWidget(self.ui.ps_filename_toolButton)


        self.ui.ui_thumb_gridLayout.addLayout(self.ui.ui_lastfileSelection_layout,  0, 0)
        self.ui.ui_thumb_gridLayout.addLayout(self.ui.ui_lastfile_layout,  1, 0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.video_thumb_pushButton,2,0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.video_thumbOverlay_pushButton,2,0)
        self.ui.ui_thumb_gridLayout.addWidget(self.ui.cs_info_label,3,0)
        # To DO should be cleaner
        self.ui.video_thumbOverlay_pushButton.setIconSize(QtCore.QSize(320, 180))
        self.ui.video_thumbOverlay_pushButton.setToolTip('Play Clip')
        self.ui.video_thumbOverlay_pushButton.clicked.connect(self.play)


        self.ui.ui_clipSelection_gridLayout.setAlignment(QtCore.Qt.AlignCenter)
        # upload_layout - after upload
        self.ui.ps_record_after_layout = RegularGridLayout(self, label = 'After Upload')
        self.ui.ps_open_afterUpload_checkBox = QtWidgets.QCheckBox()
        self.ui.ps_open_afterUpload_checkBox.setChecked(True)
        self.ui.ps_open_afterUpload_checkBox.setText('Open SyncSketch')
        self.ui.ps_afterUpload_label = QtWidgets.QLabel("After Upload")
        self.ui.ps_record_after_layout.addWidget(self.ui.ps_open_afterUpload_checkBox,  0, 1)
        self.ui.ui_clipSelection_gridLayout.addLayout(self.ui.ps_record_after_layout,  10)

        # ui_record_gridLayout
        self.ui.ui_upload_pushButton = RegularButton(self, icon = upload_icon, color=upload_color)
        self.ui.ui_upload_pushButton.setToolTip('Upload to SyncSketch Review Target')
        self.ui.ui_clipSelection_gridLayout.addWidget(self.ui.ui_upload_pushButton)


        # RIGHT PANEL
        # - - - - - - - - - -
        # download_layout
        self.ui.ui_download_pushButton = RegularButton(self, icon = download_icon, color=download_color)
        self.ui.ui_download_pushButton.setToolTip('Download from SyncSketch Review Target')
        self.ui.ui_download_pushButton.setText("DOWNLOAD")
        self.ui.ui_targetSelection_gridLayout.addWidget(self.ui.ui_download_pushButton,  10, 0)


        self.ui.ui_login_label = QtWidgets.QLabel()
        self.ui.ui_login_label.setText("You are not logged into SyncSketch")
        self.ui.ui_login_label.setMinimumHeight(header_size)
        self.ui.ui_login_label.setIndent(indent)
        self.ui.ui_login_label.setStyleSheet("background-color: rgba(255,255,255,.1);)")

        self.ui.syncsketchGUI_pushButton = RegularHeaderButton()
        self.ui.syncsketchGUI_pushButton.setIcon(logo_icon)
        self.ui.signup_pushButton = RegularHeaderButton()
        self.ui.signup_pushButton.setText("Sign Up")
        self.ui.logout_pushButton = RegularHeaderButton()
        self.ui.logout_pushButton.setText("Log Out")
        self.ui.login_pushButton = RegularHeaderButton()
        self.ui.login_pushButton.setText("Log In")
        self.ui.help_pushButton = RegularHeaderButton()
        self.ui.help_pushButton.setIcon(help_icon)
        self.ui.settings_pushButton = RegularHeaderButton()
        self.ui.settings_pushButton.setIcon(settings_icon)

        self.ui.ui_login_layout.addWidget(self.ui.syncsketchGUI_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.ui_login_label)
        self.ui.ui_login_layout.addWidget(self.ui.login_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.logout_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.signup_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.help_pushButton)
        self.ui.ui_login_layout.addWidget(self.ui.settings_pushButton)

        self.ui.ui_status_label = RegularStatusLabel()
        # self.ui.ui_status_label.setStyleSheet("background-color: rgba(255,255,255,.1); border-top: 1px solid red ;")
        # self.ui.logged_in_groupBox = QtWidgets.QGroupBox()
        # self.ui.logged_in_groupBox.setMinimumHeight(header_size)
        self.ui.ui_status_layout.addWidget(self.ui.ui_status_label)


        # populate UI
        filepath = os.path.expanduser('~/Desktop/playblasts')
        filepath = path.sanitize(filepath)
        self.ui.ps_directory_lineEdit.setText(filepath)

        self.ui.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, DEFAULT_PRESET)
        self.ui.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, DEFAULT_VIEWPORT_PRESET)
        self.update_last_recorded()

        self.ui.ui_range_comboBox.set_combobox_index( selection='Start / End')

        self.set_rangeFromComboBox()
        populate_review_panel(self, force=True)


    def disconnect_account(self):
        self.current_user.logout()
        isloggedIn(self)
        populate_review_panel(self,  force=True)

    def refresh(self):
        populate_review_panel(self, force=True)
        self.repaint()

    def open_target_url(self):
        url = sanitize(self.ui.target_lineEdit.text())
        if url:
            webbrowser.open(url)


    def update_clip_thumb(self, imageWidget):
        last_recorded_file = database.read_cache('last_recorded')["filename"]
        imageWidget.setStyleSheet("background-color: rgba(0.2,0.2,0.2,1); border: none;")
        clippath = path.sanitize(last_recorded_file)
        fname = None
        try:
            fname = video.get_thumb(clippath)
        except:
            pass
        if not fname:
            imageWidget.setIcon(logo_icon)
        else:
            icon = _get_qicon(fname)
            imageWidget.setIcon(icon)
        imageWidget.setIconSize(QtCore.QSize(320, 180))
        self.setWindowIcon(logo_icon)


    def get_directory_from_browser(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.Directory
        options |= QtWidgets.QFileDialog.ShowDirsOnly
        options |= QtWidgets.QFileDialog.DontUseNativeDialog

        filePath = QtWidgets.QFileDialog.getExistingDirectory(self, options=options)

        if filePath:
            self.ui.ps_directory_lineEdit.setText(filePath)
            return filePath

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_filters = "All Files(*);; "
        # file_filters = file_filters +  "Videos(*.mp4, *.mov, *.pdf) "
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_filters, options=options)
        self.ui.ps_lastfile_comboBox.set_combobox_index(selection=fileName)

    def validate_review_url(self, target = None):
        # self.populate_upload_settings()
        targetdata = update_target_from_tree(self.ui.browser_treeWidget)
        self.ui.target_lineEdit.setText(database.read_cache('upload_to_value'))

        if target or targetdata:
            target = targetdata['target_url_type']

        ui_to_toggle = [
            self.ui.ui_download_pushButton,
            self.ui.ui_upload_pushButton,
            self.ui.ui_open_pushButton,
            self.ui.ui_copyURL_pushButton,
            self.ui.ui_reviewSelection_hBoxLayout
        ]

        if (target == "review") or (target == "media") or (target == uploadPlaceHolderStr):
            enable_interface(ui_to_toggle, True)
            self.ui.ui_status_label.update('Valid Review Selected.', color='LightGreen')
        else:
            enable_interface(ui_to_toggle, False)
            self.ui.ui_status_label.update('Please select a review to upload to, using the tree widget or by entering a SyncSketch link', color=warning_color)
            self.ui.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)

        if target == "review":
            self.ui.ui_upload_pushButton.setText("UPLOAD\n Clip to Review '%s'"%targetdata["name"])
            # self.ui.us_ui_upload_pushButton.setStyleSheet(upload_color)

        elif target == "media":
            self.ui.ui_upload_pushButton.setText("UPLOAD\n Clip as new Version of '%s'"%targetdata["name"])
            # self.ui.us_ui_upload_pushButton.setStyleSheet(upload_color)x

            self.ui.thumbnail_itemPreview.set_icon_from_url(self.current_user.get_item_info(targetdata['media_id'])['objects'][0]['thumb'])


        else:
            self.ui.ui_upload_pushButton.setText("CANNOT UPLOAD\nSelect a target to upload to(right panel)")
            # self.ui.us_ui_upload_pushButton.setStyleSheet(disabled_color)


    # ==================================================================
    # Menu Item Functions

    def connect_account(self):
        if is_connected():
            _maya_delete_ui(WebLoginWindow.window_name)
            weblogin_window = WebLoginWindow(self)

        else:
            title = 'Not able to reach SyncSketch'
            message = 'Having trouble to connect to SyncSketch.\nMake sure you have an internet connection!'
            WarningDialog(self, title, message)

    def open_support(self):
        webbrowser.open(path.support_url)

    def open_contact(self):
        webbrowser.open(path.contact_url)

    # def open_terms_of_service(self):
    #     webbrowser.open(path.terms_url)

    def open_landing(self):
        webbrowser.open(path.home_url)

    def open_signup(self):
        webbrowser.open(path.signup_url)

    # ==================================================================
    # Reviews Tab Functions
    def open_player(self,url):
        OpenPlayer(self,url)

    def select_item_from_target_input(self):
        link = sanitize(self.ui.target_lineEdit.text())
        if not link:
            link = database.read_cache('upload_to_value')
        ids = get_ids_from_link(link)
        if not get_current_item_from_ids(self.ui.browser_treeWidget, ids):
            print "Review does not exist: %s"%ids

    # ==================================================================
    # Video Tab Functions

    def manage_preset(self):
        _maya_delete_ui(FormatPresetWindow.window_name)
        preset_window = FormatPresetWindow(self)
        preset_window.show()

    def manage_viewport_preset(self):
        _maya_delete_ui(ViewportPresetWindow.window_name)
        preset_viewport_window = ViewportPresetWindow(self)
        preset_viewport_window.show()

    # to do - should be able to wrap all of this in a single function
    # including synchronization

    def update_last_recorded(self, clips = None):
        try:
            clips = [clip["filename"] for clip in [database.read_cache('last_recorded')]]
        except:
            pass

        if clips:
            with suppressedUI(self.ui.ps_lastfile_comboBox):
                self.ui.ps_lastfile_comboBox.clear()
                self.ui.ps_lastfile_comboBox.addItems(clips)
                self.ui.ps_lastfile_comboBox.set_combobox_index( selection = database.read_cache('last_recorded')['filename'], default=r"")
            self.update_clip_info()


    def update_current_clip(self):
        val = self.ui.ps_lastfile_comboBox.currentText()
        database.dump_cache({'selected_clip': val})

        info_string = 'Please select a format preset'
        info_string = self.ui.ui_formatPreset_comboBox.currentText()
        format_preset_file = path.get_config_yaml(PRESET_YAML)
        data = database._parse_yaml(yaml_file = format_preset_file)[val]
        self.ui.ps_preset_description.setText("%s | %s | %sx%s "%(data["encoding"],data["format"],data["width"],data["height"]))


    def update_current_preset(self):
        val = self.ui.ui_formatPreset_comboBox.currentText()
        database.dump_cache({'current_preset': val})
        format_preset_file = path.get_config_yaml(PRESET_YAML)
        data = database._parse_yaml(yaml_file = format_preset_file)
        if data.has_key(val):
            data = data[val]
            text = "%s | %s | %sx%s " %(data["encoding"], data["format"], data["width"], data["height"])
        else:
            text = "no valid preset selected"
        self.ui.ps_preset_description.setText(text)


    def update_current_viewport_preset(self):
        val = self.ui.ui_viewportpreset_comboBox.currentText()
        database.dump_cache({'current_viewport_preset': val})


    def populate_camera_comboBox(self):
        value = database.read_cache('selected_camera')
        self.ui.ui_cameraPreset_comboBox.clear()
        active_cam = r"Active(%s)"%maya_scene.get_current_camera()
        self.cameras = [active_cam]
        self.cameras += maya_scene.get_available_cameras()
        self.ui.ui_cameraPreset_comboBox.addItems(self.cameras)
        self.ui.ui_cameraPreset_comboBox.set_combobox_index(selection=value, default=maya_scene.get_current_camera())


    def update_current_camera(self):
        print "updating Camera"
        value = self.ui.ui_cameraPreset_comboBox.currentText()
        if not value or not len(value) or value == 'null':
            value = database.read_cache('selected_camera')
        if not value or value.startswith(r"Active"):
            camera = maya_scene.get_current_camera()
            database.dump_cache({'selected_camera': camera})
        else:
            database.dump_cache({'selected_camera': value})


    def store_frame(self):
        database.dump_cache({'frame_start': self.ui.ui_rangeIn_textEdit.text()})
        database.dump_cache({'frame_end': self.ui.ui_rangeOut_textEdit.text()})


    def open_upload_to_url(self):
        self.validate_review_url()
        url = database.read_cache('upload_to_value')
        if url:
            webbrowser.open(url)

    def playblast(self):
        # store current preset since subsequent calls will use that data exclusively
        # savedata
        self.save_ui_state()

        if not MAYA:
            title = 'Maya Only Function'
            message = 'Recording is not yet functional outside of Maya.'
            WarningDialog(self.parent_ui, title, message)
            return

        recordData = syncsketchGUI.record()
        playblast_file = recordData["playblast_file"]
        if not playblast_file:
            self.ui.ui_status_label.update('Playblast failed. %s'%message_is_not_connected , color=error_color)
            return

        playblast_filename = os.path.split(playblast_file)[-1]
        # self.ui.ps_clipname_lineEdit.setText(playblast_filename)
        self.ui.ui_status_label.update('Playblast file [{}] is created.'.format(playblast_filename))

        # Update the last recorded file and save the ui state
        # To do - need to update and selc the target url when item is updated
        if recordData.has_key('uploaded_item'):
            print "uploaded_item %s"%recordData["uploaded_item"]["id"]
        # To do - do we really have to do this?
        if database.read_cache('ps_upload_after_creation_checkBox') == 'true':
            self.update_target_from_upload(recordData["uploaded_item"]['reviewURL'])

        self.restore_ui_state()
        self.update_last_recorded()


    def set_active_camera(self):
        self.populate_camera_comboBox()
        self.ui.ui_cameraPreset_comboBox.set_combobox_index(selection=maya_scene.get_current_camera())

    def set_in_out(self, type="Time Slider"):
        range = maya_scene.get_InOutFrames(type)
        self.ui.ui_rangeIn_textEdit.setText(str(range[0]))
        self.ui.ui_rangeOut_textEdit.setText(str(range[1]))

    def manual_set_range(self, show=True):
        interface = [
            self.ui.ui_rangeIn_textEdit,
            self.ui.ui_rangeOut_textEdit,
            self.ui.ui_range_toolButton
        ]
        enable_interface(interface, show)

    def set_rangeFromComboBox(self):
        sel = self.ui.ui_range_comboBox.currentText()
        self.set_in_out(sel)
        if sel == r"Start / End":
            self.manual_set_range(True)
        else:
            self.manual_set_range(False)



    def update_clip_info(self):
        last_recorded_file = database.read_cache('last_recorded_selection')
        last_recorded_data = database.read_cache('last_recorded')
        # last_recorded_file = last_recorded_data["filename"]
        # last_recorded_file = path.sanitize(last_recorded_file)
        # Update Date / Time
        date_created = video.get_creation_date(last_recorded_file)
        if not date_created:
            date_created = str()
        
        # Update Info
        clip_info = video.probe(last_recorded_file)

        info_string = str()
        if not clip_info:
            error_message = 'N/A. Please check if the file exists.'
            self.ui.cs_info_label.setText(error_message)
            return

        if 'start_frame' in last_recorded_data.keys() and \
                        'end_frame' in last_recorded_data.keys():
            info_string += '[{} to {}]'.format(last_recorded_data['start_frame'],
                                             last_recorded_data['end_frame'])



        if 'avg_frame_rate' in clip_info['streams'][0].keys() and 'duration' in clip_info["format"].keys():
            base, diviser = clip_info["streams"][0]["avg_frame_rate"].split('/')
            duration = float(clip_info["format"]["duration"])
            fps =(float(base) / float(diviser))
            frames = int(duration * fps)
            info_string += ' {} Frames'.format(frames)

        if 'codec_name' in clip_info['streams'][0].keys():
            info_string += ' | {}'.format(clip_info['streams'][0]['codec_name'])
        
        if  'width' in clip_info['streams'][0].keys() and \
            'height' in clip_info['streams'][0].keys():
            info_string += ' | {}x{}'.format( clip_info['streams'][0]['width'],
                                                clip_info['streams'][0]['height'])

        self.ui.cs_info_label.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.ui.cs_info_label.setText(info_string + ' | ' +  date_created)

        self.ui.cs_info_label.setMinimumHeight(20)
        self.ui.setStyleSheet("QLabel {font-font-size : 10px; color: rgba(255,255,255,0.45)} ")
        self.update_clip_thumb(self.ui.video_thumb_pushButton)

    def play(self):
        syncsketchGUI.play()


    def update_target_from_upload(self, uploaded_media_url):
        if 'none' in uploaded_media_url.lower():
            uploaded_media_url = str()

        if uploaded_media_url:
            uploaded_media_url.replace(path.playground_url, path.playground_display_url)

        print 'u\Uploaded_media_url: %s'%uploaded_media_url
        database.dump_cache({'us_last_upload_url_pushButton' : uploaded_media_url})
        # self.ui.us_last_upload_url_pushButton.setText(uploaded_media_url)

        database.dump_cache({'upload_to_value' : uploaded_media_url})
        self.refresh()

    # Upload Settings
    def upload(self):

        # savedata
        self.save_ui_state()

        uploaded_item = syncsketchGUI.upload()

        if not uploaded_item:
            self.ui.ui_status_label.update('Upload Failed, please check log', color=error_color)
            return

        self.update_target_from_upload(uploaded_item['reviewURL'])

    # Upload Settings
    def download(self):
        self.validate_review_url()
        show_download_window()
        return
        # review_id = item_data.get('id')



    def copy_to_clipboard(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        link =  self.ui.target_lineEdit.text()
        # link = database.read_cache('us_last_upload_url_pushButton')
        cb.setText(link, mode=cb.Clipboard)


    def populate_upload_settings(self):
        if database.read_cache('target_url_type') not in ['account', 'project']:
            self.ui.target_lineEdit.setText(database.read_cache('upload_to_value'))
        else:
            self.ui.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)
            self.ui.target_lineEdit.setText(None)
        self.validate_review_url()
        # self.ui.us_name_lineEdit.setText(database.read_cache('target_url_type'))
        # self.ui.us_artist_lineEdit.setText(database.read_cache('target_url_username'))
        # self.ui.us_upload_to_pushButton.setText(database.read_cache('upload_to_value'))

    # ==================================================================
    # Tooltip Area Functions


# Packaged Functions

def confirm_upload_to_playground():
    title = 'Confirm Upload'
    message = 'The file will be uploaded to the Playground.'
    info_message = 'Everyone with the link can view your upload.'
    
    confirm_dialog = QtWidgets.QMessageBox()
    confirm_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
    confirm_dialog.setText(message + '\n' + info_message)
    confirm_dialog.setDefaultButton(QtWidgets.QMessageBox.Ok)
    confirm_dialog.setIcon(QtWidgets.QMessageBox.Question)
    confirm_dialog.setWindowTitle(title)
    
    response = confirm_dialog.exec_()
    
    if response == QtWidgets.QMessageBox.Ok:
        return True


# tree function
def update_target_from_tree(treeWidget):
    selected_item = treeWidget.currentItem()
    if not selected_item:
        return
    else:
        item_data = selected_item.data(1, QtCore.Qt.EditRole)
        item_type = selected_item.data(2, QtCore.Qt.EditRole)

    review_base_url = "https://syncsketch.com/sketch/"
    current_data={}
    current_data['upload_to_value'] = str()
    current_data['breadcrumb'] = str()
    current_data['target_url_type'] = item_type
    current_data['review_id'] = str()
    current_data['media_id'] = str()
    current_data['target_url'] = None
    current_data['name'] = item_data.get('name')

    if item_type == 'project':
        review_url = '{}{}'.format(path.project_url, item_data.get('id'))
    elif item_type == 'review': # and not item_data.get('reviewURL'):
        current_data['review_id'] = item_data.get('id')
        current_data['target_url'] = review_base_url + str(current_data['review_id'])

    elif item_type == 'media':
        parent_item = selected_item.parent()
        parent_data = parent_item.data(1, QtCore.Qt.EditRole)
        current_data['review_id'] = parent_data.get('id')
        current_data['media_id'] = item_data.get('id')
        current_data['target_url'] = '{}#{}'.format(review_base_url + str(current_data['review_id']), current_data['media_id'])

    if selected_item.text(0) == 'Playground':
        current_data['upload_to_value'] = 'Playground'
    else:
        while selected_item.parent():
            current_data['breadcrumb'] = ' > '.join([selected_item.text(0), current_data['upload_to_value']])
            selected_item = selected_item.parent()

        if current_data['breadcrumb'].split(' > ')[-1] == '':
            current_data['breadcrumb'] = current_data['upload_to_value'].rsplit(' > ', 1)[0]


    database.dump_cache({'breadcrumb': current_data['breadcrumb']})
    database.dump_cache({'upload_to_value': current_data['target_url']})
    database.dump_cache({'target_url_type': current_data['target_url_type']})
    # Name
    item_name = selected_item.text(0)
    database.dump_cache({'target_url_item_name': item_name})

    # Username
    # Todo -  this should not be the current user but the creator of the item
    try:
        username = self.current_user.get_name()
    except:
        username = str()

    database.dump_cache({'target_url_username': username})

    # Description
    description = item_data.get('description')
    database.dump_cache({'target_url_description': description})
    database.dump_cache({'target_review_id': current_data['review_id']})
    database.dump_cache({'target_media_id': current_data['media_id']})

    # Upload to Value - this is really the 'breadcrumb')
    database.dump_cache({'upload_to_value': current_data['target_url']})
    # url =  database.read_cache('breadcrumb')

    return current_data




def show_web_login_window():

    if STANDALONE:
        _call_ui_for_standalone(WebLoginWindow)

    elif MAYA:
        _maya_delete_ui(WebLoginWindow.window_name)
        _call_ui_for_maya(WebLoginWindow)

def show_menu_window():

    if STANDALONE:
        app = _call_ui_for_standalone(MenuWindow)

        time.sleep(WAIT_TIME)
        panel_is_populated = populate_review_panel(app)

        if not panel_is_populated:
            app.update_tooltip(message_is_not_loggedin, color=error_color)

    elif MAYA:
        _maya_delete_ui(MenuWindow.window_name)
        app = _call_ui_for_maya(MenuWindow)


def show_download_window():
    if MAYA:
        _maya_delete_ui(DownloadWindow.window_name)
        _call_ui_for_maya(DownloadWindow)


def show_viewport_preset_window():
    if MAYA:
        _maya_delete_ui(ViewportPresetWindow.window_name)
        _call_ui_for_maya(ViewportPresetWindow)


def show_syncsketchGUI_browser_window():
    current_user = user.SyncSketchUser()
    if not current_user:
        show_web_login_window()
        return

    if STANDALONE:
        _call_ui_for_standalone(SyncSketchBrowserWindow)
        time.sleep(WAIT_TIME)
        panel_is_populated = populate_review_panel(app)


    if MAYA:
        _maya_delete_ui(SyncSketchBrowserWindow.window_name)
        app = _call_ui_for_maya(SyncSketchBrowserWindow)
        time.sleep(WAIT_TIME)
        panel_is_populated = populate_review_panel(app)


