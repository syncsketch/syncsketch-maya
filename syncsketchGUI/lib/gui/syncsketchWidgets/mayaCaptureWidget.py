import webbrowser
from syncsketchGUI.vendor.Qt import QtCore
from syncsketchGUI.vendor.Qt import QtGui
from syncsketchGUI.vendor.Qt import QtWidgets
from syncsketchGUI.lib.gui.icons import *
from syncsketchGUI.lib.gui.qt_widgets import *
from syncsketchGUI.lib.gui.literals import DEFAULT_VIEWPORT_PRESET, PRESET_YAML, VIEWPORT_YAML, DEFAULT_PRESET, uploadPlaceHolderStr, message_is_not_loggedin, message_is_not_connected

#import logging
#logger = logging.getLogger("syncsketchGUI")

class MayaCaptureWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(MayaCaptureWidget, self).__init__(*args, **kwargs)

        self.textw = QtWidgets.QLineEdit()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.textw)
        self.ui_mainLeft_gridLayout = QtWidgets.QGridLayout()
        self.decorate_ui()
        self.layout.addLayout(self.ui_mainLeft_gridLayout)
        self.setLayout(self.layout)



    def decorate_ui(self):
        file_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        directory_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        # Adding the two colums to main_layout
        #self.ui_mainLeft_gridLayout = QtWidgets.QGridLayout()
        #self.ui_mainRight_gridLayout = QtWidgets.QVBoxLayout()
        self.ui_mainLeft_gridLayout.setSpacing(1)
        #self.ui_mainRight_gridLayout.setSpacing(2)
        self.ui_reviewSelection_hBoxLayout = QtWidgets.QHBoxLayout()

        #self.main_layout.addLayout(self.ui_mainLeft_gridLayout, 0, 0)
        #self.main_layout.addLayout(self.ui_mainRight_gridLayout, 0, 1)

        #self.main_layout.setColumnMinimumWidth(0, 320)
        #self.main_layout.setColumnMinimumWidth(1, 320)
        #self.main_layout.setColumnStretch(0, 1)
        #self.main_layout.setColumnStretch(1, 0)

        # Adding ui_mainLeft_gridLayout
        self.ui_record_gridLayout = QtWidgets.QVBoxLayout()
        self.ui_clipSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui_targetSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui_targetSelection_gridLayout.setSpacing(3)

        self.ui_record_groupbox = QtWidgets.QGroupBox()
        self.ui_mainLeft_gridLayout.addWidget(self.ui_record_groupbox)
        self.ui_record_groupbox.setTitle('RECORD')
        self.ui_record_groupbox.setLayout(self.ui_record_gridLayout)

        self.ui_upload_groupbox = QtWidgets.QGroupBox()
        self.ui_mainLeft_gridLayout.addWidget(self.ui_upload_groupbox)
        self.ui_upload_groupbox.setTitle('FILE TO UPLOAD')
        self.ui_upload_groupbox.setLayout(self.ui_clipSelection_gridLayout)

        self.ui_targetSelection_groupbox = QtWidgets.QGroupBox()
        self.ui_targetSelection_groupbox.setTitle('TARGET FOR UPLOAD')
        self.ui_targetSelection_groupbox.setLayout(self.ui_targetSelection_gridLayout)


        self.ui_mainLeft_gridLayout.addLayout(self.ui_record_gridLayout, 0, 0)
        self.ui_mainLeft_gridLayout.addLayout(self.ui_clipSelection_gridLayout, 1, 0)


        # upload_layout -  format preset
        self.upload_formatPreset_layout = RegularGridLayout(self, label='Format Preset')
        self.ui_record_gridLayout.addLayout(self.upload_formatPreset_layout)
        self.ui_formatPreset_comboBox = RegularComboBox(self)
        self.ps_preset_description = QtWidgets.QLabel()
        self.ps_preset_description.setStyleSheet("font: 9pt")
        self.ps_preset_description.setIndent(5)
        self.ps_format_toolButton = RegularToolButton(self, icon = file_icon)
        self.upload_formatPreset_layout.addWidget(self.ui_formatPreset_comboBox, 0, 1)
        self.upload_formatPreset_layout.addWidget(self.ps_format_toolButton, 0, 2)
        self.upload_formatPreset_layout.addWidget(self.ps_preset_description,  1, 1, 1, 2)

        # upload_layout - viewport preset
        self.upload_viewportPreset_layout = RegularGridLayout(self, label='Viewport Preset')
        self.ui_record_gridLayout.addLayout(self.upload_viewportPreset_layout)
        self.ui_viewportpreset_comboBox = RegularComboBox(self)
        self.ui_viewport_toolButton = RegularToolButton(self, icon = preset_icon)
        self.upload_viewportPreset_layout.addWidget(self.ui_viewportpreset_comboBox, 0, 1)
        self.upload_viewportPreset_layout.addWidget(self.ui_viewport_toolButton, 0, 2)

        # upload_layout - camera
        self.upload_cameraPreset_layout = RegularGridLayout(self, label='Camera')
        self.ui_record_gridLayout.addLayout(self.upload_cameraPreset_layout)
        self.ui_cameraPreset_comboBox = RegularComboBox(self)
        self.ui_camera_toolButton = RegularToolButton(self, icon = fill_icon)
        self.upload_cameraPreset_layout.addWidget(self.ui_cameraPreset_comboBox, 0, 1)
        self.upload_cameraPreset_layout.addWidget(self.ui_camera_toolButton, 0, 2)

        # upload_layout - range
        self.upload_range_layout = RegularGridLayout(self, label='Frame Range')
        self.ui_record_gridLayout.addLayout(self.upload_range_layout)
        self.ui_range_comboBox = RegularComboBox(self)
        self.ui_range_comboBox.addItems(["Start / End", "Time Slider","Highlighted","Current Frame"])
        self.ui_range_toolButton = RegularToolButton(self, icon = fill_icon)
        self.ui_rangeIn_textEdit  = RegularLineEdit()
        self.ui_rangeOut_textEdit  = RegularLineEdit()
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

        # upload_layout - Directory
        self.upload_directory_layout = RegularGridLayout(self, label='Directory')
        self.ui_record_gridLayout.addLayout(self.upload_directory_layout)
        self.ps_directory_lineEdit = QtWidgets.QLineEdit()
        self.ps_directory_lineEdit.setPlaceholderText('Output Directory')
        self.ps_directory_toolButton = RegularToolButton(self, icon = directory_icon)
        self.upload_directory_layout.addWidget(self.ps_directory_lineEdit, 0, 1)
        self.upload_directory_layout.addWidget(self.ps_directory_toolButton, 0, 2)

        # record_layout - filename
        self.upload_filename_layout = RegularGridLayout(self, label='Clip Name')
        self.ui_record_gridLayout.addLayout(self.upload_filename_layout)
        self.us_filename_lineEdit = QtWidgets.QLineEdit()
        self.us_filename_lineEdit.setPlaceholderText('File Name or Prefix')
        self.ps_filename_toolButton = RegularToolButton(self)

        self.ps_filename_toolButton.setEnabled(0)
        self.upload_filename_layout.addWidget(self.us_filename_lineEdit, 0, 1)
        self.upload_filename_layout.addWidget(self.ps_filename_toolButton, 0, 2)

        # record_layout - clipname
        self.upload_clipname_layout = RegularGridLayout(self, label='Clip Suffix ')
        self.ui_record_gridLayout.addLayout(self.upload_clipname_layout)
        self.ps_clipname_lineEdit = QtWidgets.QLineEdit()
        self.ps_clipname_lineEdit.setPlaceholderText('Clip Suffix (optional)')
        self.ps_clipname_toolButton = RegularToolButton(self)
        self.ps_clipname_toolButton.setEnabled(0)
        self.upload_clipname_layout.addWidget(self.ps_clipname_lineEdit, 0, 1)
        self.upload_clipname_layout.addWidget(self.ps_clipname_toolButton, 0, 2)

        # record_layout - after record
        self.upload_after_layout = RegularGridLayout(self, label='After Record')
        self.ps_play_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ps_play_after_creation_checkBox.setChecked(True)
        self.ps_play_after_creation_checkBox.setText('Play')
        self.ps_upload_after_creation_checkBox = QtWidgets.QCheckBox()
        self.ps_upload_after_creation_checkBox.setText('Upload')
        self.upload_after_layout.addWidget(self.ps_play_after_creation_checkBox, 0, 1)
        self.upload_after_layout.addWidget(self.ps_upload_after_creation_checkBox, 0, 2)
        self.ui_record_gridLayout.addLayout(self.upload_after_layout)
        # record_layout - record button
        self.ui_record_pushButton = RegularButton(self, icon=record_icon, color=record_color)
        self.ui_record_pushButton.setText("RECORD")
        self.ui_record_gridLayout.addWidget(self.ui_record_pushButton)

        self.ui_formatPreset_comboBox.populate_combo_list(PRESET_YAML, DEFAULT_PRESET)
        self.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, DEFAULT_VIEWPORT_PRESET)
        #self.update_last_recorded()
