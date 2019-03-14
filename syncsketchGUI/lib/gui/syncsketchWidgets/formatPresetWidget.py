
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

    def populate_ui(self):
        """
        Populate the UI based on the available values
        depending on what the user has installed and what the DCC tool has to offer
        """
        # Get the values from the host DCC
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
        format = self.ui.format_comboBox.currentText()
        encodings = maya_scene.get_available_compressions(format)
        self.ui.encoding_comboBox.clear()
        self.ui.encoding_comboBox.addItems(encodings)

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
            logger.info(preset)
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
