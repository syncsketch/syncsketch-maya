# -*- coding: UTF-8 -*-
# ======================================================================
# @Author   : SyncSketch LLC
# @Email    : dev@syncsketch.com
# @Version  : 1.0.0
# ======================================================================
from maya import cmds
from maya import mel

# ======================================================================
# Global Variables

menuitem_command = 'import syncsketch;'
menuitem_command += 'reload(syncsketch);'
menuitem_command += 'syncsketch.reload_toolkit();'
menuitem_command += 'syncsketch.playblast_and_upload();'

# ======================================================================
# Module Utilities

def _add_context_menu_item(menu_name = 'TimeSliderMenu'):
    '''
    Add the checkbox into the timeline right click option
    so that the user can turn on and off the undo function
    with a checkbox
    '''
    if not cmds.menu(menu_name, query = True, exists = True):
        print menu_name, 'doesn\'t exist. SyncSketch menuitem is not added.'
        return
    
    if cmds.menuItem('playblast_to_syncsketch', query = True, exists = True):
        cmds.deleteUI('playblast_to_syncsketch', menuItem = True)
    
    # To add menu item into the TimeSliderMenu,
    # we need to initialize it first
    # Unless the menu items don't exist
    mel.eval('updateTimeSliderMenu TimeSliderMenu;')
    
    enable_stepped_preview = None
    menu_items = cmds.menu(menu_name, query = True, itemArray = True)
    if not menu_items:
        return
    
    menu_label = 'Playblast To SyncSketch'
    for menu_item in menu_items:
        label =  cmds.menuItem(menu_item,
                                query = True,
                                label = True)
    
    cmds.menuItem( 'playblast_to_syncsketch',
                    parent = 'TimeSliderMenu',
                    label = menu_label,
                    command = menuitem_command)
    
def _remove_context_menu_item():
    '''
    Remove the checkbox from the timeline right click option
    To be used when the plugin is uninitialized
    '''
    if cmds.menuItem('playblast_to_syncsketch', query = True, exists = True):
        cmds.deleteUI('playblast_to_syncsketch', menuItem = True)
    
# ======================================================================
# Module Functions

def add_context_menu_item():
    
    cmds.evalDeferred(_add_context_menu_item)
    
def remove_context_menu_item():
    
    cmds.evalDeferred(_remove_context_menu_item)
    
