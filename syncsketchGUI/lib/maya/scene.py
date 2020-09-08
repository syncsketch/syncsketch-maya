# -*- coding: UTF-8 -*-
# ======================================================================
# @Author   : SyncSketch LLC
# @Email    : dev@syncsketch.com
# @Version  : 1.0.0
# ======================================================================
import contextlib
import os
import sys
# ======================================================================
# Module Utilities
import tempfile
import zipfile
import xml.etree.ElementTree as ET

from maya import cmds
from maya import mel

from syncsketchGUI.lib import database
from syncsketchGUI.lib import path
from syncsketchGUI.vendor.capture import capture

import logging
logger = logging.getLogger("syncsketchGUI")

# ======================================================================
# Module Functions

def get_available_compressions(format = None):
    '''
    Get currently available compression formats in maya
    '''
    if not format:
        if sys.platform == 'darwin':
            format = 'qt'
        elif sys.platform == 'linux2':
            format = 'movie'
        elif sys.platform == 'win32':
            format = 'avi'
        else:
            format = 'movie'

    mel_command = 'playblast -format "{}" -query -compression'.format(format)
    return mel.eval(mel_command)

def get_available_formats():
    return cmds.playblast(query=True, format=True)

def get_available_cameras():
    return cmds.listCameras()

def confirm_overwrite_dialogue(message):
    result = cmds.confirmDialog(title='Confirm Overwrite',
                                button=['Yes', 'No'],
                                defaultButton='Yes',
                                dismissString='No',
                                cancelButton='No',
                                message=message,
                                icon='warning')

    return result.lower()


def get_current_camera(panel=None):
    """
    From BigRoy's Capture GUI
    Returns the currently active camera.

    Searched in the order of:
        1. Active Panel
        2. Selected Camera Shape
        3. Selected Camera Transform

    Returns:
        str: name of active camera transform

    """

    # Get camera from active modelPanel (if any)
    if not panel:
        panel = get_active_editor()
    if cmds.getPanel(typeOf=panel) == "modelPanel":
        cam = cmds.modelEditor(panel, q=1, camera=1)
        # In some cases above returns the shape, but most often it returns the
        # transform. Still we need to make sure we return the transform.
        if cam:
            if cmds.nodeType(cam) == "transform":
                return cam
            # camera shape is a shape type
            elif cmds.objectType(cam, isAType="shape"):
                parent = cmds.listRelatives(cam ,
                                          parent=True,
                                          fullPath=True)
                if parent:
                    return parent[0]

    # Check if a camShape is selected(if so use that)
    cam_shapes = cmds.ls(sl=1, type="camera")
    if cam_shapes:
        return cmds.listRelatives(cam_shapes,
                                parent=True,
                                fullPath=True)[0]

    # Check if a transform of a camShape is selected
    #(return cam transform if any)
    transforms = cmds.ls(sl=1, type="transform")
    if transforms:
        cam_shapes = cmds.listRelatives(transforms,
                                      shapes=True,
                                      type="camera")
        if cam_shapes:
            return cmds.listRelatives(cam_shapes,
                                    parent=True,
                                    fullPath=True)[0]

def get_all_modelPanels():
    return cmds.getPanel(type="modelPanel")

def get_active_editor():
    """
    From BigRoy's Capture GUI
    Return the active editor panel to playblast with
    """
    cmds.currentTime(cmds.currentTime(q=True))     # fixes `cmds.playblast` undo bug
    panel = cmds.playblast(activeEditor=True)
    #logger.info("panel %s" %panel.split('|')[-1])
    return panel.split('|')[-1]



def get_InOutFrames(type = 'Time Slider'):
    '''
    Get Frame Range from maya
    '''
    in_out = []
    if type == r"Highlighted":
        slider = mel.eval('$tmpVal=$gPlayBackSlider')
        in_out = cmds.timeControl(slider, query=True, rangeArray = True)
        in_out[1] = in_out[1]-1

    elif type == r"Start / End":
        in_out.append(cmds.playbackOptions(q=True, minTime = True))
        in_out.append(cmds.playbackOptions(q=True, maxTime = True))

    elif type == r"Time Slider":
        in_out.append(cmds.playbackOptions(q=True, animationStartTime = True))
        in_out.append(cmds.playbackOptions(q=True, animationEndTime = True))

    elif type == r"Current Frame":
        cf = cmds.currentTime(query=True)
        in_out = [cf,cf]
    else:
        start_frame = database.read_cache('frame_start')
        end_frame = database.read_cache('frame_end')
        in_out = [start_frame, end_frame]
    try:
        in_out = [str(int(val)) for val in in_out]
    except:
        pass
    return in_out

def modifyXMLData(xmlFile, xmlFileSaved, offsetFrames):
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    for neighbor in root.iter('frame'):
        current_frame = int(neighbor.attrib.get('time'))
        neighbor.set('time', str(current_frame + offsetFrames))
    tree.write(xmlFileSaved)

def updateZip(zipname, filename, data):
    # generate a temp file
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
    os.close(tmpfd)

    # create a temp copy of the archive without filename
    with zipfile.ZipFile(zipname, 'r') as zin:
        with zipfile.ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment  # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    # replace with the temp archive
    os.remove(zipname)
    os.rename(tmpname, zipname)

    # now add filename with its new data
    with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)


def modifyGreasePencil(zipname, offset=0):
    print(zipname)
    if not offset:
        return zipname
    xmlfileName = 'greasePencil.xml'
    with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in zf.namelist():
            logger.info(f)
            print(f)
        zipFileXML = zf.open(xmlfileName)
        # Generate temp file name for modified zml file
        tmpname = tempfile.TemporaryFile()
        # modify existing xml file and write to temp file
        modifyXMLData(zipFileXML, tmpname, offset)
        tmpname.seek(0)
        updateZip(zipname, xmlfileName, tmpname.read())
        tmpname.close()
    return path.sanitize(zipname)


def apply_greasepencil(filename, clear_existing_frames=False):
    import pymel.core as pm
    ctxName = 'syncSketchGreasePencil'

    # file path must be unix style otherwise IO Error by Maya Python zip.py
    filename = path.sanitize(filename)

    # create grease pencil if it doesn't exist
    if not pm.greasePencilCtx(ctxName, exists=True):
        ctx = pm.greasePencilCtx(ctxName)
        pm.setToolTo(ctx)
    else:
        nodeNames = pm.greasePencilCtx(ctxName,sequenceNodeName=True, query=True)
        if nodeNames and clear_existing_frames:
            pm.delete(nodeNames)
            logger.info('Deleted Existing Greasepencil frames ...')
    active_panel = get_active_editor()
    cmds.modelEditor(active_panel, edit=True, greasePencils=True)

    pm.greasePencilCtx(ctxName, edit = True, importArchive =  filename )


def apply_imageplane(filename, camera=None):
    import maya.cmds as cmds
    #Get Camera Shapes
    if not camera:
        ssCamera = cmds.camera()[1]

    else:
        # todo: there might be another camera in this hierarchy
        ssCamera = filter((lambda x: x if "Shape" in x else None), cmds.ls(camera, dag=True))[0]

    imagePlane = cmds.imagePlane(camera=ssCamera)
    cmds.setAttr("{}.type".format(imagePlane[1], 2), 2)
    cmds.setAttr("{}.imageName".format(imagePlane[1], 2), filename, type='string')



def add_extension(file):
    '''
    Find out the file extension manually because maya wouldn't
    return the extension if the the viewer is turned off
    '''
    extension = None
    #Assumptions that might not hold up, we should maybe consider setting
    #mov as a default for all
    if '.' in file:
        extension = file.rsplit('.', 1)[-1]

    if not extension:
        if sys.platform == 'darwin':
            extension = 'mov'
        elif sys.platform == 'linux2':
            extension = 'mov'
        elif sys.platform == 'win32':
            extension = 'mov'
        else:
            extension = 'mov'

    file = '{}.{}'.format(file.rsplit('.', 1)[0], extension)
    return path.sanitize(file)


def playblast_with_settings( viewport_preset = None, viewport_preset_yaml = None, **recArgs):
    '''
    Playblast with the user-defined settings
    recArgs are the arguments needed for the capture command
    '''

    # get default viewport preset config
    if viewport_preset and viewport_preset_yaml:
        cache_file = path.get_config_yaml(viewport_preset_yaml)
        viewportArgs = database.read_cache(viewport_preset, cache_file)
    else:
        viewportArgs = {}


    # process filenames
    filepath = recArgs["filename"]

    if not filepath:
        filepath = path.get_default_playblast_folder()

    filepath = path.sanitize(filepath)
    if os.path.isfile(filepath) and not recArgs["force_overwrite"]:
        filename = os.path.split(filepath)[-1]
        message = '[{}] already exists.\nDo you want to replace it?'.format(filename)
        if not confirm_overwrite_dialogue(message) == 'yes':
            return

    recArgs["show_ornaments"] = False
    recArgs["viewer"] = False

    # merge with viewport args
    viewport_options = viewportArgs.copy()
    viewport_options.update(recArgs)

    logger.info("viewport_options: {}".format(viewport_options))

    playblast_file = capture.capture(**viewport_options)

    if playblast_file:
        playblast_file = add_extension(playblast_file)
        recArgs["filename"] = playblast_file
        database.save_last_recorded(recArgs)
        database.dump_cache({"last_recorded_selection": playblast_file})
        logger.info('Find your recorded file here: {}'.format(playblast_file))
        return playblast_file
    else:
        logger.info("playblast_with_settings failed")


def playblast(filepath = None, width = 1280, height = 720, start_frame = 0, end_frame = 0, view_afterward = False, force_overwrite=False):
    '''
    Playblast with the pre-defined settings based on the user's OS
    '''
    logger.info("Playblast this:")
    if not filepath:
        filepath = path.get_default_playblast_folder()


    if filepath:
        filepath = path.sanitize(filepath)
        if os.path.isfile(filepath) and not force_overwrite:
            filename = os.path.split(filepath)[-1]
            message = '[{}] already exists.\nDo you want to replace it?'.format(filename)

            if not confirm_overwrite_dialogue(message) == 'yes':
                return


    recArgs = {
        "width": width,
        "height": height,
        "start_frame": start_frame,
        "end_frame": end_frame
    }
    logger.info("recargsplayblast (): {}".format(recArgs))
    # record with OS specific Fallback Settings
    os_settings = {
        "darwin": [
            {
                "format": 'qt',
                "compression": 'H.264',
            },
            {
                "format": 'avfoundation',
                "compression": 'H.264',
            }
        ],
        "linux2": [
            {
                "format": 'movie',
                "compression": 'H.264',
            },
            {
                "format": 'movie',
                "compression": '',
            }
        ],
        "linux2": [
            {
                "win32": 'qt',
                "compression": 'H.264',
            },
            {
                "format": 'movie',
                "compression": '',
            }
        ]
    }

    for platform, settingsList in os_settings.iteritems():
        if sys.platform == platform:
            for setting in settingsList:
                recArgs["compression"]  = setting["compression"]
                try:
                    logger.info("recArgs playblast(): {}".format(**recArgs))
                    playblast_file = _playblast_with_settings(**recArgs)
                    return playblast_file

                except Exception as err:
                    logger.info(u'%s' %(err))

# save active panel as a preset
def save_viewport_preset(cache_file, presetName, panel=None):
    if not panel:
        panel = get_active_editor()
    data = {}
    data[presetName] = capture.parse_view(panel)
    database.dump_cache(data, cache_file)

# save active panel as a preset
def delete_viewport_preset(cache_file, presetName):
    database.delete_key_from_cache(presetName, cache_file)

# save active panel as a preset
def rename_viewport_preset(cache_file, old_preset_name, new_preset_name):
    return database.rename_key_in_cache(old_preset_name, new_preset_name, cache_file)

def create_unique_name(existing_keys=[], new_key=None, suffix = None):
    if not new_key:
        strList = filter(None, ['New',suffix])
        new_key = ' '.join(strList)
    if existing_keys and len(existing_keys):
        while new_key in existing_keys:
            logger.info("key exists")
            strList = filter(None, ['Copy of',new_key])
            new_key = ' '.join(strList)
    return new_key

# save active panel as a preset
def new_viewport_preset(cache_file, preset_name=None, source_preset=None, panel=None):

    preset_data = database._parse_yaml(cache_file)

    if not preset_data:
        preset_data = {}
    existing_keys = preset_data.keys()

    if source_preset and source_preset in existing_keys:
        options = database.read_cache(source_preset, cache_file)
        if not preset_name:
            preset_name = 'Copy of ' + source_preset
    else:
        if not panel:
            panel = get_active_editor()
            options = capture.parse_view(panel)

    if not preset_name or preset_name in existing_keys:
        logger.info('key exists')
        preset_name = create_unique_name(existing_keys, new_key = preset_name, suffix = 'Preset')
        logger.info(preset_name)

    if not options:
        options = capture.parse_view(panel)
    else:
        preset_data[preset_name] = options

    logger.info("preset_name %s" + preset_name)

    preset_data[preset_name] = options
    database.dump_cache(preset_data, cache_file)
    return preset_name

# apply preset to panel
def apply_viewport_preset(cache_file, presetName, panels=[]):
    options = database.read_cache(presetName, cache_file)
    if not options:
        logger.info("No preset found")
        return
    if not len(panels):
        panels = [get_active_editor()]
    for panel in panels:
        capture.apply_view(panel, **options)
        logger.info("Applies preset %s to modelpanel %s"%(presetName,panel))


def screenshot_current_editor(cache_file, presetName, panel=None, camera=None):
    # Nice little screentshot function from BigRoy
    if not panel:
        panel = get_active_editor()

    options = database.read_cache(presetName, cache_file)
    if not options:
        logger.info("No preset found")
        return
    frame = cmds.currentTime(q=1)
    # When playblasting outside of an undo queue it seems that undoing
    # actually triggers a reset to frame 0. As such we sneak in the current
    # time into the undo queue to enforce correct undoing.
    cmds.currentTime(frame, update=True)
    with no_undo():
        tempdir = tempfile.mkdtemp()
        # override some settings
        options = options.copy()
        options['complete_filename'] = os.path.join(tempdir, "temp.jpg")
        options['width'] = 960
        options['height'] = 960
        options['viewer'] = False
        options['frame'] = frame
        options['off_screen'] = True
        options['format'] = "image"
        options['compression'] = "jpg"
        options['sound'] = None

        if camera:
            options['camera'] = camera

        fname = capture.snap(**options)

        if not fname:
            logger.warning("Preview failed")
            return
        return fname


@contextlib.contextmanager
def no_undo():
    """Disable undo during the context"""
    try:
        cmds.undoInfo(stateWithoutFlush=False)
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)

def get_maya_main_window():
    """Return Maya's main window"""
    for obj in QtWidgets.qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj


def getShapeNodes(obj):
    howManyShapes = 0
    getShape = maya.cmds.listRelatives(obj, shapes=True)
    if(getShape == None):
        logger.info('ERROR:: getShapeNodes : No Shape Nodes Connected to ' + obj + ' /n')
    else:
        howManyShapes = len(getShape[0])
    return(getShape, howManyShapes)

def get_render_resolution():
    '''
    Returns resolution (widht, height) in current render settings
    '''
    width = cmds.getAttr("defaultResolution.width")
    height = cmds.getAttr("defaultResolution.height")
    return (width, height)

def get_playblast_format():
    '''
    Returns the currently selected format in mayas playblast settings.
    '''
    return cmds.optionVar(query="playblastFormat")

def get_playblast_encoding():
    '''
    Returns the encoding setting used for the last playblast.
    Unfortunately it doesnt return the currently selected setting in the playblast menu.
    '''
    return cmds.optionVar(query="playblastCompression")