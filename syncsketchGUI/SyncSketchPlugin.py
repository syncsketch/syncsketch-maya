# -*- coding: UTF-8 -*-
# ======================================================================
author  = 'SyncSketch LLC'
email   = 'dev@syncsketchGUI.com'
version = '1.0.0'
# ======================================================================
from maya import OpenMayaMPx as ommpx
from maya import OpenMaya as om

import logging
logger = logging.getLogger("syncsketchGUI")

# ======================================================================
# Call Command List

playblast_cmd_name = 'ssPlayblast'
playblast_option_cmd_name = 'ssPlayblastOption'
playblast_and_upload_cmd_name =  'ssPlayblastAndUpload'
playblast_and_upload_option_cmd_name = 'ssplayblastAndUploadOption'

export_fbx_cmd_name = 'ssExportFBX'
export_obj_cmd_name = 'ssExportObj'

browser_menu_cmd_name = 'ssBrowserMenu'

login_cmd_name = 'ssLogin'

# ======================================================================
# Module Utilities

def _show_info(message):
    '''
    Show given message in the output bar
    '''
    om.MGlobal.displayInfo(message)
    
def _show_warning(message):
    '''
    Show given warning in the output bar
    '''
    om.MGlobal.displayWarning(message)
    
def _show_error(message):
    '''
    Show given error in the output bar
    '''
    om.MGlobal.displayError(message)
    
def _register_command(mplugin_object, command_name, command_creator):
    '''
    Register the command based on the mplugin object,
    command name and command creator
    '''
    try:
        mplugin_object.registerCommand(command_name, command_creator)
    except:
        message = 'Failed to register command: ' + command_name
        _show_error(message)
    
def _deregister_command(mplugin_object, command_name):
    '''
    Deregister the command based on the given command name
    '''
    try:
        mplugin_object.deregisterCommand(command_name)
    except:
        message = 'Failed to register command: ' + command_name
        _show_error(message)
    
def _get_command_pairs():
    '''
    Get the command pairs from the global variables in the script.
    A command pair is made up of a command name and a command creator.
    Returns a list of tuples. Each tuple has a string and a command object.
    '''
    command_pairs = list()
    for item in globals().keys():
        if not item.endswith('_cmd_name'):
            continue
        
        command_name = globals().get(item)
        command_creator = item.replace('cmd_name', 'cmd_creator')
        command_creator = globals().get(command_creator)
        
        if command_name and command_creator:
            command_pairs.append((command_name, command_creator))
    
    return command_pairs
    
# ======================================================================
# Command Classes

class Playblast(ommpx.MPxCommand):
    '''
    SyncSketch Playblast
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        import syncsketchGUI;
        reload(syncsketchGUI);
        syncsketchGUI.reload_toolkit();
        syncsketchGUI.playblast()
    
class PlayblastOption(ommpx.MPxCommand):
    '''
    SyncSketch Playblast Options
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        # TO DO: Replace with syncsketchGUI custom command
        from maya import mel
        mel.eval('performPlayblast 4')
    
class PlayblastAndUpload(ommpx.MPxCommand):
    '''
    SyncSketch Playblast And Upload
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        import syncsketchGUI;
        reload(syncsketchGUI);
        syncsketchGUI.reload_toolkit();
        syncsketchGUI.playblast_and_upload()
    
class PlayblastAndUploadOption(ommpx.MPxCommand):
    '''
    SyncSketch Playblast And Upload Option
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        import syncsketchGUI;
        reload(syncsketchGUI);
        syncsketchGUI.reload_toolkit();
        syncsketchGUI.show_menu_window()
    
class ExportFBX(ommpx.MPxCommand):
    '''
    SyncSketch Export FBX
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        # TO DO: Replace with syncsketchGUI custom command
        logger.info('Exporting to FBX ...')
    
class ExportObj(ommpx.MPxCommand):
    '''
    SyncSketch Export Obj
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        # TO DO: Replace with syncsketchGUI custom command
        logger.info('Exporting to Obj ...')
    
class BrowserMenu(ommpx.MPxCommand):
    '''
    SyncSketch Main Browser Menu UI
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        import syncsketchGUI
        syncsketchGUI.show_menu_window()
    
class Login(ommpx.MPxCommand):
    '''
    SyncSketch Login To Server
    '''
    def __init__(self):
        ommpx.MPxCommand.__init__(self)
    
    def doIt(self, *arg):
        # TO DO: Replace with syncsketchGUI custom command
        import syncsketchGUI
        syncsketchGUI.show_login_dialog()
    
# ======================================================================
# Command Creators

def playblast_cmd_creator():
    return ommpx.asMPxPtr(Playblast())
    
def playblast_option_cmd_creator():
    return ommpx.asMPxPtr(PlayblastOption())
    
def playblast_and_upload_cmd_creator():
    return ommpx.asMPxPtr(PlayblastAndUpload())
    
def playblast_and_upload_option_cmd_creator():
    return ommpx.asMPxPtr(PlayblastAndUploadOption())
    
def export_fbx_cmd_creator():
    return ommpx.asMPxPtr(ExportFBX())
    
def export_obj_cmd_creator():
    return ommpx.asMPxPtr(ExportObj())
    
def browser_menu_cmd_creator():
    return ommpx.asMPxPtr(BrowserMenu())
    
def login_cmd_creator():
    return ommpx.asMPxPtr(Login())

# ======================================================================
# Plugin Initializer

def initializePlugin(mobject):
    
    # Add the menu
    import syncsketchGUI
    syncsketchGUI.build_menu()
    syncsketchGUI.refresh_menu_state()
    syncsketchGUI.add_timeline_context_menu()
    
    # Register command pairs
    mplugin = ommpx.MFnPlugin( mobject,
                                author,
                                version)
    
    command_pairs = _get_command_pairs()
    for pair in command_pairs:
        _register_command(mplugin, pair[0], pair[1])
    
# ======================================================================
# Plugin Uninitializer

def uninitializePlugin(mobject):
    
    # Remove the menu
    import syncsketchGUI
    syncsketchGUI.delete_menu()
    
    # Deregister command pairs
    mplugin = ommpx.MFnPlugin(mobject)
    
    command_pairs = _get_command_pairs()
    for pair in command_pairs:
        _deregister_command(mplugin, pair[0])
    