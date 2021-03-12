import logging
import webbrowser

from syncsketchGUI.vendor.Qt import QtCore, QtGui, QtWidgets

import syncsketchGUI
from syncsketchGUI.lib import video, user, database, path


from . import qt_utils
from . import qt_regulars
from . import qt_presets


logger = logging.getLogger("syncsketchGUI")

class UploadWidget(QtWidgets.QWidget):

    uploaded = QtCore.Signal(dict)

    def __init__(self, *args, **kwargs):
        super(UploadWidget, self).__init__(*args, **kwargs)

        self._decorate_ui()
        self._build_connections()
        self.update_last_recorded()
        self._restore_ui_state()


    def _decorate_ui(self):
        file_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        #directory_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)


        self.video_thumb_pushButton = QtWidgets.QPushButton()
        self.video_thumb_pushButton.setContentsMargins(0, 0, 0, 0)
        
        # Used ?
        self.ui_lastfile_layout = QtWidgets.QHBoxLayout()


        self.cs_info_label = QtWidgets.QLabel()
        self.cs_info_label.setStyleSheet("font: 9pt")

        self.ps_lastfile_line_edit = qt_regulars.LineEdit(self)
        self.ps_lastfile_line_edit.setReadOnly(1)
        
        self.ps_filename_toolButton = qt_regulars.ToolButton(self, icon=file_icon)
        

        self.ui_lastfileSelection_layout = QtWidgets.QHBoxLayout()
        self.ui_lastfileSelection_layout.addWidget(self.ps_lastfile_line_edit)
        self.ui_lastfileSelection_layout.addWidget(self.ps_filename_toolButton)


        # To DO should be cleaner
        self.video_thumbOverlay_pushButton = qt_regulars.HoverButton(icon=qt_presets.play_icon)
        self.video_thumbOverlay_pushButton.setIconSize(QtCore.QSize(320, 180))
        self.video_thumbOverlay_pushButton.setToolTip('Play Clip')
       

        # upload_layout - after upload
        self.ps_open_afterUpload_checkBox = QtWidgets.QCheckBox()
        self.ps_open_afterUpload_checkBox.setChecked(True)
        self.ps_open_afterUpload_checkBox.setText('Open SyncSketch')

        self.ps_afterUpload_label = QtWidgets.QLabel("After Upload")

        self.ps_record_after_layout = qt_regulars.GridLayout(self, label='After Upload')
        self.ps_record_after_layout.addWidget(self.ps_open_afterUpload_checkBox, 0, 1)
        
        self.ui_upload_pushButton = qt_regulars.Button(self, icon = qt_presets.upload_icon, color=qt_presets.upload_color)
        self.ui_upload_pushButton.setToolTip('Upload to SyncSketch Review Target')
        

        self.ui_thumb_gridLayout = QtWidgets.QGridLayout()
        self.ui_thumb_gridLayout.setSpacing(3)
        self.ui_thumb_gridLayout.addLayout(self.ui_lastfileSelection_layout, 0, 0)
        self.ui_thumb_gridLayout.addLayout(self.ui_lastfile_layout,  1, 0)
        self.ui_thumb_gridLayout.addWidget(self.video_thumb_pushButton, 2, 0)
        self.ui_thumb_gridLayout.addWidget(self.video_thumbOverlay_pushButton, 2, 0)
        self.ui_thumb_gridLayout.addWidget(self.cs_info_label, 3, 0)

        # Adding ui_mainLeft_gridLayout
        self.ui_clipSelection_gridLayout = QtWidgets.QVBoxLayout()
        self.ui_clipSelection_gridLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.ui_clipSelection_gridLayout.addLayout(self.ui_thumb_gridLayout)
        self.ui_clipSelection_gridLayout.addWidget(self.ui_upload_pushButton)
        self.ui_clipSelection_gridLayout.addLayout(self.ps_record_after_layout, 10)

        self.ui_upload_groupbox = QtWidgets.QGroupBox()
        self.ui_upload_groupbox.setTitle('FILE TO UPLOAD')
        self.ui_upload_groupbox.setLayout(self.ui_clipSelection_gridLayout)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.ui_upload_groupbox)

        self.setLayout(main_layout)  

    def _build_connections(self):
        self.video_thumb_pushButton.clicked.connect(self.update_clip_thumb)
        self.ui_upload_pushButton.clicked.connect(self.upload)
        self.ps_filename_toolButton.clicked.connect(self.openFileNameDialog)
        self.video_thumbOverlay_pushButton.clicked.connect(self.play)

    def _restore_ui_state(self):
        value = database.read_cache('ps_open_afterUpload_checkBox')
        self.ps_open_afterUpload_checkBox.setChecked(
            True if value == 'true' else False)

    
    def _save_ui_state(self):
        ui_setting = {
            'ps_open_afterUpload_checkBox':
                self.bool_to_str(self.ps_open_afterUpload_checkBox.isChecked())}
        database.dump_cache(ui_setting)

    def upload(self):
        logger.info("Upload only function")
        self._save_ui_state()
        uploaded_item = syncsketchGUI.upload()
        self.uploaded.emit(uploaded_item)

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_filters = "All Files(*);; "

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", file_filters, options=options)
        self.ps_lastfile_line_edit.setText(fileName)
        database.dump_cache({"last_recorded_selection": fileName})

    def play(self):
        syncsketchGUI.play()
    
    def update_last_recorded(self, clips = None):
        try:
            clips = [clip["filename"] for clip in [database.read_cache('last_recorded')]]
        except:
            pass

        if clips:
            with qt_utils.suppressedUI(self.ps_lastfile_line_edit):
                self.ps_lastfile_line_edit.clear()
                self.ps_lastfile_line_edit.setText(database.read_cache('last_recorded')['filename'])
            self.update_clip_info()

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
            error_message='N/A. Please check if the file exists.'
            self.cs_info_label.setText(error_message)
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
            info_string += ' | {}x{}'.format(clip_info['streams'][0]['width'],
                                                clip_info['streams'][0]['height'])

        self.cs_info_label.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.cs_info_label.setText(info_string + ' | ' +  date_created)

        self.cs_info_label.setMinimumHeight(20)
        #self.ui.setStyleSheet("QLabel {font-font-size : 10px; color: rgba(255,255,255,0.45)} ")
        self.update_clip_thumb(self.video_thumb_pushButton)


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
            imageWidget.setIcon(qt_presets.logo_icon)
        else:
            icon = qt_presets._get_qicon(fname)
            imageWidget.setIcon(icon)
        imageWidget.setIconSize(QtCore.QSize(320, 180))


    def closeEvent(self, event):
        logger.info("UploadWidget closed.")
        self._save_ui_state()

    def bool_to_str(self, val):
        strVal='true' if val else 'false'
        return strVal


