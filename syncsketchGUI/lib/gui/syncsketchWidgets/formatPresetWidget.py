# -*- coding: utf-8 -*-
import sys
import logging
import yaml
import codecs

from syncsketchGUI.lib.gui.qt_widgets import SyncSketch_Window
from syncsketchGUI.vendor.Qt import QtWidgets, QtCore
from syncsketchGUI.lib.gui.qt_widgets import RegularComboBox, RegularButton, RegularToolButton, RegularGridLayout, RegularQSpinBox, InputDialog, WarningDialog
from syncsketchGUI.lib.gui.icons import *
from syncsketchGUI.lib.gui.qt_utils import *
from syncsketchGUI.lib.gui import qt_utils
from functools import partial
from syncsketchGUI.lib.connection import is_connected, open_url
from syncsketchGUI.lib import database, user
from syncsketchGUI.lib.maya import scene as maya_scene
from syncsketchGUI.lib.gui.syncsketchWidgets.mainWidget import DEFAULT_PRESET, VIEWPORT_YAML, PRESET_YAML


logger = logging.getLogger("syncsketchGUI")


class FormatPresetWindow(SyncSketch_Window):
    """
    Video Preset Window Class
    """
    window_name = 'syncsketchGUI_preset_window'
    window_label = 'Recording Preset Manager'

    def __init__(self, parent=None, icon=None, color='white'):
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
            logger.info("key: %s\nfactor: %s"%(key, factor))
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

        self.ui.ps_new_preset_pushButton.clicked.connect(self.new_preset)
        self.ui.ps_rename_preset_pushButton.clicked.connect(self.rename_preset)
        self.ui.ps_delete_preset_pushButton.clicked.connect(self.delete_preset)

    def populate_ui(self):
        """
        Populate the UI based on the available values
        depending on what the user has installed and what the DCC tool has to offer
        """
        formats = maya_scene.get_available_formats()
        encodings = maya_scene.get_available_compressions()


        # Populate the preset names
        self.ui.ui_formatPreset_comboBox.clear()

        self.ui.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, defaultValue= DEFAULT_PRESET )

        # Populate the values to the fields based on the preset
        self.ui.format_comboBox.clear()
        self.ui.encoding_comboBox.clear()
        self.ui.width_spinBox.clear()
        self.ui.height_spinBox.clear()


        self.ui.format_comboBox.addItems(formats)
        self.ui.encoding_comboBox.addItems(encodings)
        self.ui.width_spinBox.setValue(1920)
        self.ui.height_spinBox.setValue(1080)


    def update_encoding_list(self):
        """
        Refresh the available compressions.
        """
        compressionFormat = self.ui.format_comboBox.currentText()
        encodings = maya_scene.get_available_compressions(compressionFormat)
        self.ui.encoding_comboBox.clear()
        self.ui.encoding_comboBox.addItems(encodings)


    def update_login_ui(self):
        #user Login
        self.currentUser = user.SyncSketchUser()
        if self.currentUser.is_logged_in() and is_connected():
            username = self.currentUser.get_name()
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


    def load_preset(self, presetName=None):
        """
        Load the user's current preset from yaml
        """
        presetFile = path.get_config_yaml(PRESET_YAML)
        logger.info("reading YAML: {}".format(presetFile))
        presetData = database._parse_yaml(presetFile)
        if not presetData:
            return
        if not presetName:
            self.ui.ui_formatPreset_comboBox.set_combobox_index(selection=database.read_cache('current_preset'))
            self.ui.format_comboBox.set_combobox_index(selection='avi')
            self.ui.encoding_comboBox.set_combobox_index(selection='none')
            self.ui.width_spinBox.setValue(1280)
            self.ui.height_spinBox.setValue(720)


        elif presetName == DEFAULT_PRESET:
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
            preset = presetData.get(presetName)
            logger.info("presetName: {}, preset: {} presetData: {}".format(presetName, preset, presetData))
            if not preset:
                return
            logger.info(preset)
            format = preset.get('format')
            encoding = preset.get('encoding')
            width = preset.get('width')
            height = preset.get('height')

            self.ui.ui_formatPreset_comboBox.set_combobox_index(selection=presetName)
            self.ui.format_comboBox.set_combobox_index(selection=format)
            self.ui.encoding_comboBox.set_combobox_index(selection=encoding)
            self.ui.width_spinBox.setValue(width)
            self.ui.height_spinBox.setValue(height)

    def load_preset_from_selection(self):
        """
        Load the currently selected preset from the combobox list
        """
        selected_preset = self.ui.ui_formatPreset_comboBox.currentText()
        self.load_preset(selected_preset)


    def save(self):
        presetFile = path.get_config_yaml(PRESET_YAML)

        presetName = self.ui.ui_formatPreset_comboBox.currentText()
        format = self.ui.format_comboBox.currentText()
        encoding = self.ui.encoding_comboBox.currentText()
        width = self.ui.width_spinBox.value()
        height = self.ui.height_spinBox.value()

        newData = {presetName:
                    {'encoding': encoding,
                    'format': format,
                    'height': height,
                    'width': width}}

        database.dump_cache(newData, presetFile)

        self._update_current_preset(presetName)

        self.close()

    def new_preset(self):
        """Create a new preset"""
        title = 'Creating Preset'
        message = 'Please choose a name for this preset.'
        user_input = InputDialog(self, title, message)
        if not user_input.response:
            return
        preset_name = user_input.response_text

        if not preset_name:
            logger.info("No new preset name specified")
            return

        preset_file = path.get_config_yaml(PRESET_YAML)
        current_preset_names = database._parse_yaml(preset_file).keys()        
        if preset_name in current_preset_names:
            title = 'Error Creating'
            message = 'It appears this name already exists.'
            WarningDialog(self, title, message)
            return
        
        width, height = maya_scene.get_render_resolution()
        encoding = maya_scene.get_playblast_encoding()
        format = maya_scene.get_playblast_format()

        preset_data = {preset_name:
                        {'encoding': encoding,
                        'format': format,
                        'height': height,
                        'width': width}}

        logger.info("Create Format Preset from {}".format(preset_name))
        database.dump_cache(preset_data, preset_file)

        self.populate_ui()
        self.ui.ui_formatPreset_comboBox.set_combobox_index(selection=preset_name)
    
    def rename_preset(self):
        title = 'Renaming Preset'
        message = 'Please choose a name for this preset.'
        old_preset_name = self.ui.ui_formatPreset_comboBox.currentText()
        new_preset_name, response =  QtWidgets.QInputDialog.getText(self, "Rename this preset",  "Please enter a new Name:", QtWidgets.QLineEdit.Normal, old_preset_name)

        

        if not new_preset_name:
            logger.info("No new preset name specified")
            return

        preset_file = path.get_config_yaml(PRESET_YAML)
        current_preset_names = database._parse_yaml(preset_file).keys()        

        if new_preset_name in current_preset_names:
            title = 'Error Renaming'
            message = 'It appears this name already exists.'
            WarningDialog(self, title, message)
            return
        
        
        logger.info("Rename Preset from {} to {}".format(old_preset_name, new_preset_name))
        database.rename_key_in_cache(old_preset_name, new_preset_name, preset_file)
        
        if database.read_cache("current_preset") == old_preset_name:
            self._update_current_preset(new_preset_name)

        self.populate_ui()
        self.ui.ui_formatPreset_comboBox.set_combobox_index(selection=new_preset_name)


    def delete_preset(self):
        preset_file = path.get_config_yaml(PRESET_YAML)
        preset_name = self.ui.ui_formatPreset_comboBox.currentText()
        database.delete_key_from_cache(preset_name, preset_file)
        current_preset = database.read_cache("current_preset")

        if current_preset == preset_name:
            current_preset_names = database._parse_yaml(preset_file).keys()
            new_preset_name = current_preset_names[0]
            self._update_current_preset(new_preset_name)
        else:
            self._update_current_preset(current_preset)
            
        self.populate_ui()
        self.ui.ui_formatPreset_comboBox.set_combobox_index(0)


    def _update_current_preset(self, preset_name):
        database.save_cache("current_preset", preset_name)
        self.parent.ui.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, preset_name)
