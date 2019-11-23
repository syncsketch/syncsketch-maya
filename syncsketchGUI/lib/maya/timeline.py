from maya import cmds
from maya import mel


def _add_context_menu_item(menu_name = 'TimeSliderMenu'):
    '''
    Add the checkbox into the timeline right click option
    so that the user can turn on and off the undo function
    with a checkbox
    '''
    if not cmds.menu(menu_name, query = True, exists = True):
        print(menu_name, 'doesn\'t exist. SyncSketch menuitem is not added.')
        return

    # To add menu item into the TimeSliderMenu,
    # we need to initialize it first
    # Unless the menu items don't exist
    mel.eval('updateTimeSliderMenu TimeSliderMenu;')
    
    if cmds.menuItem('ssPlayblast', query = True, exists = True):
        cmds.deleteUI('ssPlayblast', menuItem = True)

    if cmds.menuItem('ssPlayblastOB', query = True, exists = True):
        cmds.deleteUI('ssPlayblastOB', menuItem = True)
    

    menu_items = cmds.menu(menu_name, query = True, itemArray = True)
    if not menu_items:
        return
    
    cmds.menuItem('ssPlayblast', p='TimeSliderMenu', label='Playblast with Syncsketch', 
                    annotation='Starts playblast for syncsketch', 
                    command='import syncsketchGUI; syncsketchGUI.record()')
    cmds.menuItem('ssPlayblastOB', p='TimeSliderMenu', optionBox=True,  
                command='from syncsketchGUI import standalone; reload(standalone)')

    
def _remove_context_menu_item():
    '''
    Remove the checkbox from the timeline right click option
    To be used when the plugin is uninitialized
    '''
    if cmds.menuItem('playblast_to_syncsketch', query = True, exists = True):
        cmds.deleteUI('ssPlayblast', menuItem = True)
    if cmds.menuItem('playblast_to_syncsketch', query = True, exists = True):
        cmds.deleteUI('ssPlayblastOB', menuItem = True)
    
# ======================================================================
# Module Functions

def add_context_menu_item():
    
    cmds.evalDeferred(_add_context_menu_item)
    
def remove_context_menu_item():
    
    cmds.evalDeferred(_remove_context_menu_item)
    
