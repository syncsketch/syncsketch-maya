import logging

from syncsketchGUI.vendor.Qt import QtWidgets, QtCore

from syncsketchGUI.lib import path, database
from syncsketchGUI.settings import VIEWPORT_YAML

from syncsketchGUI.lib.maya import scene as maya_scene

from . import qt_windows
from . import qt_regulars
from . import qt_presets
from . import qt_dialogs

logger = logging.getLogger("syncsketchGUI")


class ViewportPresetWindow(qt_windows.SyncSketchWindow):
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
        self.build_screenshot()

    def decorate_ui(self):
        self.ui.ps_thumb_horizontalLayout = QtWidgets.QGridLayout()
        self.ui.screenshot_pushButton = qt_regulars.Thumbnail(width=480, height=270)
        self.ui.ui_thumbcamera_label = qt_regulars.HoverButton(icon=qt_presets.refresh_icon)
        self.ui.ui_thumbcamera_label.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.ui.ui_thumbcamera_label.setMinimumSize(480, 270)
        self.ui.ps_thumb_horizontalLayout.addWidget(self.ui.screenshot_pushButton, 0, 0)
        self.ui.ps_thumb_horizontalLayout.addWidget(self.ui.ui_thumbcamera_label, 0, 0)

        # Viewport Preset Selection and Handling
        self.ui.ps_preset_horizontalLayout = QtWidgets.QHBoxLayout()
        self.ui.ui_viewportpreset_comboBox = qt_regulars.ComboBox()

        self.ui.ps_new_preset_pushButton = qt_regulars.ToolButton()
        self.ui.ps_new_preset_pushButton.setIcon(qt_presets.add_icon)

        self.ui.ps_rename_preset_pushButton = qt_regulars.ToolButton()
        self.ui.ps_rename_preset_pushButton.setIcon(qt_presets.edit_icon)

        self.ui.ps_delete_preset_pushButton = qt_regulars.ToolButton()
        self.ui.ps_delete_preset_pushButton.setIcon(qt_presets.delete_icon)

        self.ui.ps_refresh_pushButton = qt_regulars.ToolButton()
        self.ui.ps_refresh_pushButton.setIcon(qt_presets.refresh_icon)

        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_refresh_pushButton)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ui_viewportpreset_comboBox)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_rename_preset_pushButton)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_new_preset_pushButton)
        self.ui.ps_preset_horizontalLayout.addWidget(self.ui.ps_delete_preset_pushButton)

        # Viewport Preset Application
        self.ui.buttons_horizontalLayout = QtWidgets.QHBoxLayout()

        self.ui.ps_apply_preset_pushButton = qt_regulars.Button()
        self.ui.ps_apply_preset_pushButton.setText("Apply \nto current view")
        self.ui.buttons_horizontalLayout.addWidget(self.ui.ps_apply_preset_pushButton)

        self.ui.ps_applyToAll_preset_pushButton = qt_regulars.Button()
        self.ui.ps_applyToAll_preset_pushButton.setText("Apply\nto all views")
        self.ui.buttons_horizontalLayout.addWidget(self.ui.ps_applyToAll_preset_pushButton)

        self.ui.ps_save_preset_pushButton = qt_regulars.Button()
        self.ui.ps_save_preset_pushButton.setText("Override preset\nfrom view")
        self.ui.buttons_horizontalLayout.addWidget(self.ui.ps_save_preset_pushButton)

        self.ui.ui_status_label = qt_regulars.StatusLabel()

        self.ui.ui_status_label.setFixedHeight(30)
        self.lay_main.setSpacing(1)
        self.lay_main.addWidget(self.ui.ui_status_label)
        self.lay_main.addLayout(self.ui.ps_thumb_horizontalLayout)
        self.lay_main.addLayout(self.ui.ps_preset_horizontalLayout)
        self.lay_main.addLayout(self.ui.buttons_horizontalLayout)

    def build_connections(self):
        """Connects all widget's callbacks"""
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

    def new_preset(self, new_preset_name=None):
        """Create a new preset"""
        title = 'Creating Preset'
        message = 'Please choose a name for this preset.'
        user_input = qt_dialogs.InputDialog(self, title, message)
        if not user_input.response:
            return
        new_preset_name = user_input.response_text

        if not new_preset_name:
            return

        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        new_preset_name = maya_scene.new_viewport_preset(preset_file, new_preset_name)
        database.save_cache("current_viewport_preset", new_preset_name)
        self.populate_ui()
        self.build_screenshot()

    def delete_preset(self, preset_name=None):
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
        current_preset = self.ui.ui_viewportpreset_comboBox.currentText()
        new_preset_name, response = QtWidgets.QInputDialog.getText(self, "Rename this preset",
                                                                   "Please enter a new Name:",
                                                                   QtWidgets.QLineEdit.Normal, current_preset)
        logger.info(new_preset_name)
        if not new_preset_name:
            return
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = current_preset
            new_preset_name = maya_scene.rename_viewport_preset(preset_file, preset_name, new_preset_name)
        if not new_preset_name:
            title = 'Error Renaming'
            message = 'It appears this name already exists.'
            qt_dialogs.WarningDialog(self, title, message)
            return
        database.save_cache("current_viewport_preset", new_preset_name)
        self.populate_ui()
        self.setParent_preset()

    def apply_preset_to_all(self, preset_name=None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        panels = maya_scene.get_all_modelPanels()
        maya_scene.apply_viewport_preset(preset_file, preset_name, panels)

    def apply_preset(self, preset_name=None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        maya_scene.apply_viewport_preset(preset_file, preset_name)

    def override_preset(self, preset_name=None):
        preset_file = path.get_config_yaml(VIEWPORT_YAML)
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()
        maya_scene.save_viewport_preset(preset_file, preset_name)
        self.build_screenshot(preset_name)

    def build_screenshot(self, preset_name=None):
        if not preset_name:
            preset_name = self.ui.ui_viewportpreset_comboBox.currentText()

        preset_file = path.get_config_yaml(VIEWPORT_YAML)

        current_camera = self._get_current_camera()
        fname = maya_scene.screenshot_current_editor(preset_file, preset_name, camera=current_camera)
        self.ui.ui_status_label.update(preset_name)
        if not fname:
            self.ui.screenshot_pushButton.setIcon(qt_presets.logo_icon)
        else:
            icon = qt_presets._get_qicon(fname)
            self.ui.screenshot_pushButton.setIcon(icon)
            self.ui.ui_status_label.update("Previewing Preset '%s' - from camera '%s'" % (preset_name, current_camera))
        self.ui.screenshot_pushButton.setText('')
        self.ui.screenshot_pushButton.setIconSize(QtCore.QSize(480, 270))

        self.setWindowIcon(qt_presets.logo_icon)

    def _get_current_camera(self):
        cached_cam = database.read_cache('selected_camera')

        if cached_cam in maya_scene.get_available_cameras():
            return cached_cam
        else:
            return maya_scene.get_current_camera()

    def populate_ui(self):
        """
        Populate the UI based on the available values
        depending on what the user has installed and what the DCC tool has to offer
        """
        self.ui.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML, defaultValue=database.read_cache(
            'current_viewport_preset'))

    def set_to_current_preset(self):
        """
        Load the currently selected preset from the combobox list
        """
        self.setParent_preset()
        self.build_screenshot()

    def setParent_preset(self):
        database.save_cache("current_viewport_preset", self.ui.ui_viewportpreset_comboBox.currentText())
        try:
            self.parent.ui.ui_viewportpreset_comboBox.populate_combo_list(VIEWPORT_YAML,
                                                                          defaultValue=database.read_cache(
                                                                              'current_viewport_preset'))
        except:
            pass

    def closeEvent(self, event):
        self.setParent_preset()
        event.accept()
