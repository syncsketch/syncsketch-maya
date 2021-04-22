import os 
import logging

from syncsketchGUI.vendor.Qt import QtWidgets, QtCore, QtGui

import syncsketchGUI

from syncsketchGUI.lib import path
from syncsketchGUI.lib import database


from syncsketchGUI.lib.maya import scene as maya_scene

from . import qt_regulars
from . import qt_presets
from . import qt_utils

from .literals import DEFAULT_VIEWPORT_PRESET, PRESET_YAML, VIEWPORT_YAML, DEFAULT_PRESET, message_is_not_connected

logger = logging.getLogger("syncsketchGUI")

class MayaPlayblastRecorderWidget(QtWidgets.QWidget):
    title = "RECORD"

    recorded = QtCore.Signal(str) # str: recorded File
    uploaded = QtCore.Signal(str) # str: Url

    def __init__(self, *args, **kwargs):
        super(MayaPlayblastRecorderWidget, self).__init__(*args, **kwargs)
        
        self.decorate_ui()
        self.populate_ui()
        self.restore_ui_state()
        self.connect_ui()
        

    def closeEvent(self, event):
        logger.info("Closing MayaCaptureWidget")
        self.save_ui_state()
        event.accept()

    def decorate_ui(self):

        file_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        directory_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        self.lay_main = QtWidgets.QVBoxLayout()
        self.grp_box = QtWidgets.QGroupBox()
        self.grp_box.setTitle('RECORD')
        self.lay_main.addWidget(self.grp_box)
        self.setLayout(self.lay_main)

        self.lay_grid_main = QtWidgets.QVBoxLayout()
        self.grp_box.setLayout(self.lay_grid_main)
        

         # record_layout_layout -  format preset
        self.upload_formatPreset_layout = qt_regulars.GridLayout(self, label='Format Preset')
        self.lay_grid_main.addLayout(self.upload_formatPreset_layout)
        self.ui_formatPreset_comboBox = qt_regulars.ComboBox(self)
        self.ps_preset_description = QtWidgets.QLabel()
        self.ps_preset_description.setStyleSheet("font: 9pt")
        self.ps_preset_description.setIndent(5)
        self.ps_format_toolButton = qt_regulars.ToolButton(self, icon = file_icon)
        self.upload_formatPreset_layout.addWidget(self.ui_formatPreset_comboBox, 0, 1)
        self.upload_formatPreset_layout.addWidget(self.ps_format_toolButton, 0, 2)
        self.upload_formatPreset_layout.addWidget(self.ps_preset_description,  1, 1, 1, 2)

        # record_layout - viewport preset
        self.upload_viewportPreset_layout = qt_regulars.GridLayout(self, label='Viewport Preset')
        self.lay_grid_main.addLayout(self.upload_viewportPreset_layout)
        self.ui_viewportpreset_comboBox = qt_regulars.ComboBox(self)
        self.ui_viewport_toolButton = qt_regulars.ToolButton(self, icon = qt_presets.preset_icon)
        self.upload_viewportPreset_layout.addWidget(self.ui_viewportpreset_comboBox, 0, 1)
        self.upload_viewportPreset_layout.addWidget(self.ui_viewport_toolButton, 0, 2)

        # record_layout - camera
        self.upload_cameraPreset_layout = qt_regulars.GridLayout(self, label='Camera')
        self.lay_grid_main.addLayout(self.upload_cameraPreset_layout)
        self.ui_cameraPreset_comboBox = qt_regulars.ComboBox(self)
        self.ui_camera_toolButton = qt_regulars.ToolButton(self, icon = file_icon)
        self.upload_cameraPreset_layout.addWidget(self.ui_cameraPreset_comboBox, 0, 1)
        self.upload_cameraPreset_layout.addWidget(self.ui_camera_toolButton, 0, 2)

        # record_layout - range
        self.upload_range_layout = qt_regulars.GridLayout(self, label='Frame Range')
        self.lay_grid_main.addLayout(self.upload_range_layout)
        self.ui_range_comboBox = qt_regulars.ComboBox(self)
        self.ui_range_comboBox.addItems(["Start / End", "Time Slider","Highlighted","Current Frame"])
        self.ui_range_toolButton = qt_regulars.ToolButton(self, icon = file_icon)
        self.ui_rangeIn_textEdit  = qt_regulars.LineEdit()
        self.ui_rangeOut_textEdit  = qt_regulars.LineEdit()
        self.upload_range_layout.addWidget(self.ui_range_comboBox, 0, 1)
        self.upload_range_layout.addWidget(self.ui_rangeIn_textEdit, 0, 2)
        self.upload_range_layout.setColumnStretch(2,0)
        self.upload_range_layout.addWidget(self.ui_rangeOut_textEdit, 0, 3)
        self.upload_range_layout.setColumnStretch(3,0)
        self.ui_rangeIn_textEdit.setFixedWidth(40)
        self.ui_rangeOut_textEdit.setFixedWidth(40)

        self.ui_rangeIn_textEdit.setAlignment(QtCore.Qt.AlignRight)
        self.ui_rangeOut_textEdit.setAlignment(QtCore.Qt.AlignRight)
        self.upload_range_layout.addWidget(self.ui_range_toolButton, 0, 4)

        self.onlyInt = QtGui.QIntValidator()
        self.ui_rangeIn_textEdit.setValidator(self.onlyInt)
        self.ui_rangeIn_textEdit.setPlaceholderText('Start')
        self.ui_rangeOut_textEdit.setValidator(self.onlyInt)
        self.ui_rangeOut_textEdit.setPlaceholderText('End')

        # record_layout - Directory
        self.upload_directory_layout = qt_regulars.GridLayout(self, label='Directory')
        self.lay_grid_main.addLayout(self.upload_directory_layout)
        self.ps_directory_lineEdit = QtWidgets.QLineEdit()
        self.ps_directory_lineEdit.setPlaceholderText('Output Directory')
        self.ps_directory_toolButton = qt_regulars.ToolButton(self, icon = directory_icon)
        self.upload_directory_layout.addWidget(self.ps_directory_lineEdit, 0, 1)
        self.upload_directory_layout.addWidget(self.ps_directory_toolButton, 0, 2)

        # record_layout - filename
        self.upload_filename_layout = qt_regulars.GridLayout(self, label='Clip Name')
        self.lay_grid_main.addLayout(self.upload_filename_layout)
        self.us_filename_lineEdit = QtWidgets.QLineEdit()
        self.us_filename_lineEdit.setPlaceholderText('File Name or Prefix')
        self.ps_filename_toolButton = qt_regulars.ToolButton(self)   ######    self.ps_filename_toolButton used twice  

        self.ps_filename_toolButton.setEnabled(0)
        self.upload_filename_layout.addWidget(self.us_filename_lineEdit, 0, 1)
        self.upload_filename_layout.addWidget(self.ps_filename_toolButton, 0, 2)

        # record_layout - clipname
        self.upload_clipname_layout = qt_regulars.GridLayout(self, label='Clip Suffix ')
        self.lay_grid_main.addLayout(self.upload_clipname_layout)
        self.ps_clipname_lineEdit = QtWidgets.QLineEdit()
        self.ps_clipname_lineEdit.setPlaceholderText('Clip Suffix (optional)')
        self.ps_clipname_toolButton = qt_regulars.ToolButton(self)
        self.ps_clipname_toolButton.setEnabled(0)
        self.upload_clipname_layout.addWidget(self.ps_clipname_lineEdit, 0, 1)
        self.upload_clipname_layout.addWidget(self.ps_clipname_toolButton, 0, 2)

        # record_layout - after record
        self.upload_after_layout = qt_regulars.GridLayout(self, label='After Record')
        self.ps_play_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ps_play_after_creation_checkBox.setChecked(True)
        self.ps_play_after_creation_checkBox.setText('Play')
        self.ps_upload_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ps_upload_after_creation_checkBox.setText('Upload')
        self.upload_after_layout.addWidget(self.ps_play_after_creation_checkBox, 0, 1)
        self.upload_after_layout.addWidget(self.ps_upload_after_creation_checkBox, 0, 2)
        self.lay_grid_main.addLayout(self.upload_after_layout)
        # record_layout - record button
        self.ui_record_pushButton = qt_regulars.Button(self, icon=qt_presets.record_icon, color=qt_presets.record_color)
        self.ui_record_pushButton.setText("RECORD")

        self.lay_grid_main.addWidget(self.ui_record_pushButton)
    

    def populate_ui(self):
        # filepath = os.path.expanduser('~/Desktop/playblasts')
        # filepath = path.sanitize(filepath)
        # self.ps_directory_lineEdit.setText(filepath)

        self.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, DEFAULT_PRESET)
        self.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, DEFAULT_VIEWPORT_PRESET)

        #self.update_last_recorded()

        self.ui_range_comboBox.set_combobox_index(selection='Start / End')

        self.set_rangeFromComboBox()
    
    def connect_ui(self):

        self.ui_record_pushButton.clicked.connect(self.record_playblast)
        self.ui_formatPreset_comboBox.currentIndexChanged.connect(self.update_current_preset)
        self.ui_viewportpreset_comboBox.currentIndexChanged.connect(self.update_current_viewport_preset)
        self.ui_cameraPreset_comboBox.currentIndexChanged.connect(self.update_current_camera)


        self.ps_format_toolButton.clicked.connect(self.manage_preset)
        self.ps_directory_toolButton.clicked.connect(self.get_directory_from_browser)

        self.ui_viewport_toolButton.clicked.connect(self.manage_viewport_preset)

        self.ui_range_toolButton.clicked.connect(self.set_in_out)
        self.ui_camera_toolButton.clicked.connect(self.set_active_camera)

        self.ui_range_comboBox.currentIndexChanged.connect(self.set_rangeFromComboBox)

        self.ui_rangeIn_textEdit.textChanged.connect(self.store_frame)
        self.ui_rangeOut_textEdit.textChanged.connect(self.store_frame)


    def save_ui_state(self):
        ui_setting = {
            # Playblast Settings
            'ps_directory_lineEdit':
                self.sanitize(self.ps_directory_lineEdit.text()),
            'ps_clipname_lineEdit':
                self.sanitize(self.ps_clipname_lineEdit.text()),
            'current_range_type':
                self.ui_range_comboBox.currentText(),
            'ps_play_after_creation_checkBox':
                self.bool_to_str(self.ps_play_after_creation_checkBox.isChecked()),
            'ps_upload_after_creation_checkBox':
                self.bool_to_str(self.ps_upload_after_creation_checkBox.isChecked()),
            'us_filename_lineEdit':
                self.us_filename_lineEdit.text(),
                            }
        database.dump_cache(ui_setting)
    
    def restore_ui_state(self):
        value = self.sanitize(database.read_cache('ps_directory_lineEdit'))
        self.ps_directory_lineEdit.setText(
            value if value else os.path.expanduser('~/Desktop/playblasts'))

        value = self.sanitize(database.read_cache('ps_clipname_lineEdit'))
        self.ps_clipname_lineEdit.setText(value)

        value = database.read_cache('ps_play_after_creation_checkBox')
        self.ps_play_after_creation_checkBox.setChecked(
            True if value == 'true' else False)

        self.populate_camera_comboBox()

        value = database.read_cache('current_preset')
        self.ui_formatPreset_comboBox.set_combobox_index(selection=value)

        value = database.read_cache('current_range_type')
        self.ui_range_comboBox.set_combobox_index(selection=value)

        # value = database.read_cache('ps_upload_after_creation_checkBox')
        # self.ps_upload_after_creation_checkBox.setChecked(
        #     True if value == 'true' and self.current_user.is_logged_in() else False)

        value = database.read_cache('us_filename_lineEdit')
        self.us_filename_lineEdit.setText(
            value if value else 'playblast')



        #Set FrameRange from the lider
        database.dump_cache({"frame_start":self.ui_rangeIn_textEdit.text()})
        database.dump_cache({"frame_end":self.ui_rangeOut_textEdit.text()})

    def populate_camera_comboBox(self):
        value = database.read_cache('selected_camera')
        self.ui_cameraPreset_comboBox.clear()
        active_cam = r"Active(%s)"%maya_scene.get_current_camera()
        self.cameras = [active_cam]
        self.cameras += maya_scene.get_available_cameras()
        self.ui_cameraPreset_comboBox.addItems(self.cameras)
        logger.info("maya_scene.get_current_camera(): {}".format(maya_scene.get_current_camera()))
        self.ui_cameraPreset_comboBox.set_combobox_index(selection=value, default=maya_scene.get_current_camera())
    
    def set_rangeFromComboBox(self):
        sel = self.ui_range_comboBox.currentText()
        self.set_in_out(sel)
        if sel == r"Start / End":
            self.manual_set_range(True)
        else:
            self.manual_set_range(False)
    
    def set_in_out(self, type="Time Slider"):
        range = maya_scene.get_InOutFrames(type)
        self.ui_rangeIn_textEdit.setText(str(range[0]))
        self.ui_rangeOut_textEdit.setText(str(range[1]))

    def manual_set_range(self, show=True):
        interface = [
            self.ui_rangeIn_textEdit,
            self.ui_rangeOut_textEdit,
            self.ui_range_toolButton
        ]
        qt_utils.enable_interface(interface, show) 
    
    def record_playblast(self):
        # store current preset since subsequent calls will use that data exclusively
        # savedata
        self.save_ui_state()
        recordData = syncsketchGUI.record()
        playblast_file = recordData["playblast_file"]

        if not playblast_file:
            self.recorded.emit(None)
            return

        # self.ui.ps_clipname_lineEdit.setText(playblast_filename)
        self.recorded.emit(playblast_file)
        

        if self.ps_upload_after_creation_checkBox.isChecked() and self.ps_upload_after_creation_checkBox.isEnabled() :
            self.uploaded.emit("update_target_from_upload = {}".format(recordData["uploaded_item"]['reviewURL']))
            logger.info("update_target_from_upload = {}".format(recordData["uploaded_item"]['reviewURL']))
        else:
            logger.info("Upload checkbox was not selected, returning here")
            return

        # Update the last recorded file and save the ui state
        # To do - need to update and selc the target url when item is updated
        if recordData.has_key('uploaded_item'):
            logger.info("uploaded_item %s"%recordData["uploaded_item"]["id"])

        #self.restore_ui_state()

    def get_directory_from_browser(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.Directory
        options |= QtWidgets.QFileDialog.ShowDirsOnly
        options |= QtWidgets.QFileDialog.DontUseNativeDialog

        filePath = QtWidgets.QFileDialog.getExistingDirectory(self, options=options)

        if filePath:
            self.ps_directory_lineEdit.setText(filePath)
            return filePath

    def update_current_preset(self):
        val = self.ui_formatPreset_comboBox.currentText()
        database.dump_cache({'current_preset': val})
        format_preset_file = path.get_config_yaml(PRESET_YAML)
        data = database._parse_yaml(yaml_file = format_preset_file)
        logger.info("data: {}".format(data))
        if data.has_key(val):
            data = data[val]
            #text = "%s | %s | %sx%s " %(data["encoding"], data["format"], data["width"], data["height"])
            text = "{} | {} | {}x{}".format(data["encoding"], data["format"], data["width"], data["height"])
        else:
            text = "no valid preset selected"
        self.ps_preset_description.setText(text)

    def update_current_viewport_preset(self):
        val = self.ui_viewportpreset_comboBox.currentText()
        database.dump_cache({'current_viewport_preset': val})

    def manage_preset(self):
        from .qt_recorder_preset import FormatPresetWindow
        preset_window = qt_utils.get_persistent_widget(FormatPresetWindow)
        preset_window.show()
    
    def manage_viewport_preset(self):
        from .qt_viewport_preset import ViewportPresetWindow
        preset_viewport_window = qt_utils.get_persistent_widget(ViewportPresetWindow)
        preset_viewport_window.show()
    
    def update_current_camera(self):
        logger.info("updating Camera")
        value = self.ui_cameraPreset_comboBox.currentText()
        if not value or not len(value) or value == 'null':
            value = database.read_cache('selected_camera')
        if not value or value.startswith(r"Active"):
            camera = maya_scene.get_current_camera()
            database.dump_cache({'selected_camera': camera})
        else:
            database.dump_cache({'selected_camera': value})
    
    def set_active_camera(self):
        self.populate_camera_comboBox()
        self.ui_cameraPreset_comboBox.set_combobox_index(selection=maya_scene.get_current_camera())
    
    def store_frame(self):
        database.dump_cache({'frame_start': self.ui_rangeIn_textEdit.text()})
        database.dump_cache({'frame_end': self.ui_rangeOut_textEdit.text()})

    def sanitize(self, val):
        return val.rstrip().lstrip()

    def bool_to_str(self, val):
        strVal='true' if val else 'false'
        return strVal