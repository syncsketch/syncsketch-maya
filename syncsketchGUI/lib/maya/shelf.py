import codecs
import os

from maya import cmds
from maya import mel

from syncsketchGUI.lib import path
import yaml

# ======================================================================
# Global Variables

yaml_shelf = 'syncsketch_shelf.yaml'
shelf_name = 'SyncSketch'

# ======================================================================
# Module Utilities

def _sanitize_path(raw_path):
    '''
    Replace the backslashes in the path with the forward slashes
    '''
    sanitized_path = raw_path.replace('\\', '/')
    return sanitized_path
    
def _shorten_icon_path(icon_fullname):
    '''
    Cut the filepath of the icon short and return only the filename
    '''
    if not icon_fullname:
        return icon_fullname
    
    return os.path.split(icon_fullname)[-1]
    
def _resolve_icon_path(icon_shortname):
    '''
    Connect the icon path with the icon name
    WARNING: This one works only when you have a pre-defined icon path
    '''
    if not icon_shortname:
        return icon_shortname
    
    icon_path = path.get_image_folder()
    icon_fullname = os.path.join(icon_path, icon_shortname)
    icon_fullname = _sanitize_path(icon_fullname)
    
    return icon_fullname
    
def _get_yaml_shelves():
    '''
    Get all the yaml files from the MAYA_SHELF_PATH
    '''
    shelf_paths = os.environ.get('MAYA_SHELF_PATH')
    if not shelf_paths:
        return
    
    shelves = list()
    for shelf_path in shelf_paths.split(';'):
        for root, dirs, files in os.walk(shelf_path):
            for name in files:
                if name.endswith(('.yaml', '.yml')):
                    shelf = os.path.join(root, name)
                    shelf = _sanitize_path(shelf)
                    shelves.append(shelf)
    
    for root, dirs, files in os.walk(cmds.internalVar(userShelfDir = True)):
        for name in files:
            if name.endswith(('.yaml', '.yml')):
                shelf = os.path.join(root, name)
                shelf = _sanitize_path(shelf)
                shelves.append(shelf)
    
    return shelves
    
def _parse_shelf_item(shelf_item):
    '''
    Get shelf item's arguments and their parameters.
    Return a dictionary with the default value if the user doesn't provide certain values.
    '''
    item_data = shelf_item.values()[0]
    parsed_item_data = {'enableCommandRepeat'   : True,             # 2015+
                        'enable'                : True,
                        'width'                 : 35,
                        'height'                : 35,
                        'manage'                : True,
                        'visible'               : True,
                        'preventOverride'       : False,
                        'annotation'            : '',
                        'enableBackground'      : False,
                        'align'                 : 'center',
                        'label'                 : '',
                        'labelOffset'           : 0,
                        'rotation'              : False,            # 2015+
                        'flipX'                 : False,            # 2015+
                        'flipY'                 : False,            # 2015+
                        'useAlpha'              : True,             # 2015+
                        'font'                  : 'plainLabelFont', # 2015+
                        'imageOverlayLabel'     : '',
                        'overlayLabelColor'     : [0.8, 0.8, 0.8],
                        'overlayLabelBackColor' : [0, 0, 0, 0.5],
                        'image'                 : '',
                        'image1'                : '',
                        'image2'                : '',
                        'image3'                : '',
                        'style'                 : 'iconOnly',
                        'marginWidth'           : 1,
                        'marginHeight'          : 1,
                        'command'               : '',
                        'sourceType'            : 'mel',
                        'commandRepeatable'     : True,
                        'flat'                  : True}
    
    if 'enableCommandRepeat' in item_data.keys():
        parsed_item_data['enableCommandRepeat'] = item_data.get('enableCommandRepeat')
    
    if 'enable' in item_data.keys():
        parsed_item_data['enable'] = item_data.get('enable')
    
    if 'width' in item_data.keys():
        parsed_item_data['width'] = item_data.get('width')
    
    if 'height' in item_data.keys():
        parsed_item_data['height'] = item_data.get('height')
    
    if 'manage' in item_data.keys():
        parsed_item_data['manage'] = item_data.get('manage')
    
    if 'visible' in item_data.keys():
        parsed_item_data['visible'] = item_data.get('visible')
    
    if 'preventOverride' in item_data.keys():
        parsed_item_data['preventOverride'] = item_data.get('preventOverride')
    
    if 'annotation' in item_data.keys():
        parsed_item_data['annotation'] = item_data.get('annotation')
    
    if 'enableBackground' in item_data.keys():
        parsed_item_data['enableBackground'] = item_data.get('enableBackground')
    
    if 'align' in item_data.keys():
        parsed_item_data['align'] = item_data.get('align')
    
    if 'label' in item_data.keys():
        parsed_item_data['label'] = item_data.get('label')
    
    if 'labelOffset' in item_data.keys():
        parsed_item_data['labelOffset'] = item_data.get('labelOffset')
    
    if 'rotation' in item_data.keys():
        parsed_item_data['rotation'] = item_data.get('rotation')
    
    if 'flipX' in item_data.keys():
        parsed_item_data['flipX'] = item_data.get('flipX')
    
    if 'flipY' in item_data.keys():
        parsed_item_data['flipY'] = item_data.get('flipY')
    
    if 'useAlpha' in item_data.keys():
        parsed_item_data['useAlpha'] = item_data.get('useAlpha')
    
    if 'font' in item_data.keys():
        parsed_item_data['font'] = item_data.get('font')
    
    if 'imageOverlayLabel' in item_data.keys():
        parsed_item_data['imageOverlayLabel'] = item_data.get('imageOverlayLabel')
    
    if 'overlayLabelColor' in item_data.keys():
        parsed_item_data['overlayLabelColor'] = item_data.get('overlayLabelColor')
    
    if 'overlayLabelBackColor' in item_data.keys():
        parsed_item_data['overlayLabelBackColor'] = item_data.get('overlayLabelBackColor')
    
    if 'image' in item_data.keys():
        parsed_item_data['image'] = _resolve_icon_path(item_data.get('image'))
    
    # Get the same image from the "image" if nothing is provided
    if 'image1' in item_data.keys():
        parsed_item_data['image1'] = _resolve_icon_path(item_data.get('image1'))
    
    elif 'image' in item_data.keys():
        parsed_item_data['image1'] = _resolve_icon_path(item_data.get('image'))
    
    # Get the same image from the "image" if nothing is provided
    if 'image2' in item_data.keys():
        parsed_item_data['image2'] = _resolve_icon_path(item_data.get('image2'))
    
    elif 'image' in item_data.keys():
        parsed_item_data['image2'] = _resolve_icon_path(item_data.get('image'))
    
    # Get the same image from the "image" if nothing is provided
    if 'image3' in item_data.keys():
        parsed_item_data['image3'] = _resolve_icon_path(item_data.get('image3'))
    
    elif 'image' in item_data.keys():
        parsed_item_data['image3'] = _resolve_icon_path(item_data.get('image'))
    
    if 'style' in item_data.keys():
        parsed_item_data['style'] = item_data.get('style')
    
    if 'marginWidth' in item_data.keys():
        parsed_item_data['marginWidth'] = item_data.get('marginWidth')
    
    if 'marginHeight' in item_data.keys():
        parsed_item_data['marginHeight'] = item_data.get('marginHeight')
    
    if 'command' in item_data.keys():
        parsed_item_data['command'] = item_data.get('command')
    
    if 'sourceType' in item_data.keys():
        parsed_item_data['sourceType'] = item_data.get('sourceType')
    
    if 'commandRepeatable' in item_data.keys():
        parsed_item_data['commandRepeatable'] = item_data.get('commandRepeatable')
    
    if 'flat' in item_data.keys():
        parsed_item_data['flat'] = item_data.get('flat')
    
    return parsed_item_data
    
def _parse_shelf_separator(shelf_separator):
    '''
    Get shelf separator's arguments and their parameters.
    Return a dictionary with the default value if the user doesn't provide certain values.
    '''
    item_data = shelf_separator.values()[0]
    parsed_item_data = {'enable'            : True,
                        'width'             : 12,
                        'height'            : 35,
                        'manage'            : True,
                        'visible'           : True,
                        'preventOverride'   : False,
                        'enableBackground'  : False,
                        'highlightColor'    : [0.321569, 0.521569, 0.65098],
                        'style'             : 'shelf',
                        'horizontal'        : False}
    
    if 'enable' in item_data.keys():
        parsed_item_data['enable'] = item_data.get('enable')
    
    if 'width' in item_data.keys():
        parsed_item_data['width'] = item_data.get('width')
    
    if 'height' in item_data.keys():
        parsed_item_data['height'] = item_data.get('height')
    
    if 'manage' in item_data.keys():
        parsed_item_data['manage'] = item_data.get('manage')
    
    if 'visible' in item_data.keys():
        parsed_item_data['visible'] = item_data.get('visible')
    
    if 'preventOverride' in item_data.keys():
        parsed_item_data['preventOverride'] = item_data.get('preventOverride')
    
    if 'enableBackground' in item_data.keys():
        parsed_item_data['enableBackground'] = item_data.get('enableBackground')
    
    if 'highlightColor' in item_data.keys():
        parsed_item_data['highlightColor'] = item_data.get('highlightColor')
    
    if 'style' in item_data.keys():
        parsed_item_data['style'] = item_data.get('style')
    
    if 'horizontal' in item_data.keys():
        parsed_item_data['horizontal'] = item_data.get('horizontal')
    
    return parsed_item_data
    
def _build_shelf_item(shelf_item_data, shelf):
    '''
    Add shelf button based on current maya version
    '''
    if cmds.about(apiVersion = True) >= 201600:
        # Maya 2016 and later
        cmds.shelfButton(  enableCommandRepeat     = shelf_item_data['enableCommandRepeat'],   # 2015+
                            enable                  = shelf_item_data['enable'],
                            width                   = shelf_item_data['width'],
                            height                  = shelf_item_data['height'],
                            manage                  = shelf_item_data['manage'],
                            visible                 = shelf_item_data['visible'],
                            preventOverride         = shelf_item_data['preventOverride'],
                            annotation              = shelf_item_data['annotation'],
                            enableBackground        = shelf_item_data['enableBackground'],
                            align                   = shelf_item_data['align'],
                            label                   = shelf_item_data['label'],
                            labelOffset             = shelf_item_data['labelOffset'],
                            rotation                = shelf_item_data['rotation'],              # 2015+
                            flipX                   = shelf_item_data['flipX'],                 # 2015+
                            flipY                   = shelf_item_data['flipY'],                 # 2015+
                            useAlpha                = shelf_item_data['useAlpha'],              # 2015+
                            font                    = shelf_item_data['font'],                  # 2015+
                            imageOverlayLabel       = shelf_item_data['imageOverlayLabel'],
                            overlayLabelColor       = shelf_item_data['overlayLabelColor'],
                            overlayLabelBackColor   = shelf_item_data['overlayLabelBackColor'],
                            image                   = shelf_item_data['image'],
                            image1                  = shelf_item_data['image1'],
                            image2                  = shelf_item_data['image2'],
                            image3                  = shelf_item_data['image3'],
                            style                   = shelf_item_data['style'],
                            marginWidth             = shelf_item_data['marginWidth'],
                            marginHeight            = shelf_item_data['marginHeight'],
                            command                 = shelf_item_data['command'],
                            sourceType              = shelf_item_data['sourceType'],
                            commandRepeatable       = shelf_item_data['commandRepeatable'],
                            flat                    = shelf_item_data['flat'],
                            parent                  = shelf)
    else:
        # Maya 2015 and earlier
        cmds.shelfButton(  enable                  = shelf_item_data['enable'],
                            width                   = shelf_item_data['width'],
                            height                  = shelf_item_data['height'],
                            manage                  = shelf_item_data['manage'],
                            visible                 = shelf_item_data['visible'],
                            preventOverride         = shelf_item_data['preventOverride'],
                            annotation              = shelf_item_data['annotation'],
                            enableBackground        = shelf_item_data['enableBackground'],
                            align                   = shelf_item_data['align'],
                            label                   = shelf_item_data['label'],
                            labelOffset             = shelf_item_data['labelOffset'],
                            imageOverlayLabel       = shelf_item_data['imageOverlayLabel'],
                            overlayLabelColor       = shelf_item_data['overlayLabelColor'],
                            overlayLabelBackColor   = shelf_item_data['overlayLabelBackColor'],
                            image                   = shelf_item_data['image'],
                            image1                  = shelf_item_data['image1'],
                            image2                  = shelf_item_data['image2'],
                            image3                  = shelf_item_data['image3'],
                            style                   = shelf_item_data['style'],
                            marginWidth             = shelf_item_data['marginWidth'],
                            marginHeight            = shelf_item_data['marginHeight'],
                            command                 = shelf_item_data['command'],
                            sourceType              = shelf_item_data['sourceType'],
                            commandRepeatable       = shelf_item_data['commandRepeatable'],
                            flat                    = shelf_item_data['flat'],
                            parent                  = shelf)
    
def _build_shelf_separator(shelf_separator_data, shelf):
    '''
    Add a seperator in the shelf based on current maya version
    '''
    # Exit if the maya version is earlier than 2016
    # because shelves have no separator function before 2016
    if not cmds.about(apiVersion = True) >= 201600:
        return
    
    cmds.separator(enable              = shelf_item_data['enable'],
                    width               = shelf_item_data['width'],
                    height              = shelf_item_data['height'],
                    manage              = shelf_item_data['manage'],
                    visible             = shelf_item_data['visible'],
                    preventOverride     = shelf_item_data['preventOverride'],
                    enableBackground    = shelf_item_data['enableBackground'],
                    highlightColor      = shelf_item_data['highlightColor'],
                    style               = shelf_item_data['style'],
                    horizontal          = shelf_item_data['horizontal'],
                    parent              = shelf)
    
def _get_shelf_item_data(shelf_button):
    shelf_item_data = dict()
    
    if 'separator' in shelf_button:
        if cmds.about(apiVersion = True) >= 201650:
            # Maya 2016.5 and later
            shelf_item_data['enable'] = \
                cmds.separator(shelf_button, query = True, enable = True)
            shelf_item_data['width'] = \
                cmds.separator(shelf_button, query = True, width = True)
            shelf_item_data['height'] = \
                cmds.separator(shelf_button, query = True, height = True)
            shelf_item_data['manage'] = \
                cmds.separator(shelf_button, query = True, manage = True)
            shelf_item_data['visible'] = \
                cmds.separator(shelf_button, query = True, visible = True)
            shelf_item_data['preventOverride'] = \
                cmds.separator(shelf_button, query = True, preventOverride = True)
            shelf_item_data['enableBackground'] = \
                cmds.separator(shelf_button, query = True, enableBackground = True)
            shelf_item_data['highlightColor'] = \
                cmds.separator(shelf_button, query = True, highlightColor = True)
            shelf_item_data['style'] = \
                cmds.separator(shelf_button, query = True, style = True)
            shelf_item_data['horizontal'] = \
                cmds.separator(shelf_button, query = True, horizontal = True)
        else:
            # Maya 2016 and earlier
            shelf_item_data['enable'] = \
                cmds.separator(shelf_button, query = True, enable = True)
            shelf_item_data['width'] = \
                cmds.separator(shelf_button, query = True, width = True)
            shelf_item_data['height'] = \
                cmds.separator(shelf_button, query = True, height = True)
            shelf_item_data['manage'] = \
                cmds.separator(shelf_button, query = True, manage = True)
            shelf_item_data['visible'] = \
                cmds.separator(shelf_button, query = True, visible = True)
            shelf_item_data['preventOverride'] = \
                cmds.separator(shelf_button, query = True, preventOverride = True)
            shelf_item_data['enableBackground'] = \
                cmds.separator(shelf_button, query = True, enableBackground = True)
            shelf_item_data['style'] = \
                cmds.separator(shelf_button, query = True, style = True)
            shelf_item_data['horizontal'] = \
                cmds.separator(shelf_button, query = True, horizontal = True)
        
        return {'separator' : shelf_item_data}
    
    if cmds.about(apiVersion = True) >= 201600:
        # Maya 2016 and later
        shelf_item_data['enableCommandRepeat'] = \
            cmds.shelfButton(shelf_button, query = True, enableCommandRepeat = True) # 2015+
        shelf_item_data['enable'] = \
            cmds.shelfButton(shelf_button, query = True, enable = True)
        shelf_item_data['width'] = \
            cmds.shelfButton(shelf_button, query = True, width = True)
        shelf_item_data['height'] = \
            cmds.shelfButton(shelf_button, query = True, height = True)
        shelf_item_data['manage'] = \
            cmds.shelfButton(shelf_button, query = True, manage = True)
        shelf_item_data['visible'] = \
            cmds.shelfButton(shelf_button, query = True, visible = True)
        shelf_item_data['preventOverride'] = \
            cmds.shelfButton(shelf_button, query = True, preventOverride = True)
        shelf_item_data['annotation'] = \
            cmds.shelfButton(shelf_button, query = True, annotation = True)
        shelf_item_data['enableBackground'] = \
            cmds.shelfButton(shelf_button, query = True, enableBackground = True)
        shelf_item_data['align'] = \
            cmds.shelfButton(shelf_button, query = True, align = True)
        shelf_item_data['label'] = \
            cmds.shelfButton(shelf_button, query = True, label = True)
        shelf_item_data['labelOffset'] = \
            cmds.shelfButton(shelf_button, query = True, labelOffset = True)
        shelf_item_data['rotation'] = \
            cmds.shelfButton(shelf_button, query = True, rotation = True) # 2015+
        shelf_item_data['flipX'] = \
            cmds.shelfButton(shelf_button, query = True, flipX = True) # 2015+
        shelf_item_data['flipY'] = \
            cmds.shelfButton(shelf_button, query = True, flipY = True) # 2015+
        shelf_item_data['useAlpha'] = \
            cmds.shelfButton(shelf_button, query = True, useAlpha = True) # 2015+
        shelf_item_data['font'] = \
            cmds.shelfButton(shelf_button, query = True, font = True) # 2015+
        shelf_item_data['imageOverlayLabel'] = \
            cmds.shelfButton(shelf_button, query = True, imageOverlayLabel = True)
        shelf_item_data['overlayLabelColor'] = \
            cmds.shelfButton(shelf_button, query = True, overlayLabelColor = True)
        shelf_item_data['overlayLabelBackColor'] = \
            cmds.shelfButton(shelf_button, query = True, overlayLabelBackColor = True)
        
        # Resolve the image paths to just get the names if possible
        shelf_item_data['image'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image = True))
        shelf_item_data['image1'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image1 = True))
        shelf_item_data['image2'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image2 = True))
        shelf_item_data['image3'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image3 = True))
        
        shelf_item_data['style'] = \
            cmds.shelfButton(shelf_button, query = True, style = True)
        shelf_item_data['marginWidth'] = \
            cmds.shelfButton(shelf_button, query = True, marginWidth = True)
        shelf_item_data['marginHeight'] = \
            cmds.shelfButton(shelf_button, query = True, marginHeight = True)
        shelf_item_data['command'] = \
            cmds.shelfButton(shelf_button, query = True, command = True)
        shelf_item_data['sourceType'] = \
            cmds.shelfButton(shelf_button, query = True, sourceType = True)
        shelf_item_data['commandRepeatable'] = \
            cmds.shelfButton(shelf_button, query = True, commandRepeatable = True)
        shelf_item_data['flat'] = \
            cmds.shelfButton(shelf_button, query = True, flat = True)
    else:
        # Maya 2015 and earlier
        shelf_item_data['enable'] = \
            cmds.shelfButton(shelf_button, query = True, enable = True)
        shelf_item_data['width'] = \
            cmds.shelfButton(shelf_button, query = True, width = True)
        shelf_item_data['height'] = \
            cmds.shelfButton(shelf_button, query = True, height = True)
        shelf_item_data['manage'] = \
            cmds.shelfButton(shelf_button, query = True, manage = True)
        shelf_item_data['visible'] = \
            cmds.shelfButton(shelf_button, query = True, visible = True)
        shelf_item_data['preventOverride'] = \
            cmds.shelfButton(shelf_button, query = True, preventOverride = True)
        shelf_item_data['annotation'] = \
            cmds.shelfButton(shelf_button, query = True, annotation = True)
        shelf_item_data['enableBackground'] = \
            cmds.shelfButton(shelf_button, query = True, enableBackground = True)
        shelf_item_data['align'] = \
            cmds.shelfButton(shelf_button, query = True, align = True)
        shelf_item_data['label'] = \
            cmds.shelfButton(shelf_button, query = True, label = True)
        shelf_item_data['labelOffset'] = \
            cmds.shelfButton(shelf_button, query = True, labelOffset = True)
        shelf_item_data['imageOverlayLabel'] = \
            cmds.shelfButton(shelf_button, query = True, imageOverlayLabel = True)
        shelf_item_data['overlayLabelColor'] = \
            cmds.shelfButton(shelf_button, query = True, overlayLabelColor = True)
        shelf_item_data['overlayLabelBackColor'] = \
            cmds.shelfButton(shelf_button, query = True, overlayLabelBackColor = True)
        
        # Resolve the image paths to just get the names if possible
        shelf_item_data['image'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image = True))
        shelf_item_data['image1'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image1 = True))
        shelf_item_data['image2'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image2 = True))
        shelf_item_data['image3'] = \
            _shorten_icon_path(cmds.shelfButton(shelf_button, query = True, image3 = True))
        
        shelf_item_data['style'] = \
            cmds.shelfButton(shelf_button, query = True, style = True)
        shelf_item_data['marginWidth'] = \
            cmds.shelfButton(shelf_button, query = True, marginWidth = True)
        shelf_item_data['marginHeight'] = \
            cmds.shelfButton(shelf_button, query = True, marginHeight = True)
        shelf_item_data['command'] = \
            cmds.shelfButton(shelf_button, query = True, command = True)
        shelf_item_data['sourceType'] = \
            cmds.shelfButton(shelf_button, query = True, sourceType = True)
        shelf_item_data['commandRepeatable'] = \
            cmds.shelfButton(shelf_button, query = True, commandRepeatable = True)
        shelf_item_data['flat'] = \
            cmds.shelfButton(shelf_button, query = True, flat = True)
    
    return {'shelfButton' : shelf_item_data}
    
# ======================================================================
# Module Functions

def install():
    '''
    Dynamically create and load the shelf in maya
    '''
    yaml_shelf_file = path.get_config_yaml(yaml_shelf)
    icon_path = path.get_image_folder()
    
    load(yaml_shelf_file, shelf_name)
    
def uninstall(shelf_name=shelf_name):
    '''
    Delete a previously created shelf created
    '''
    if cmds.shelfLayout(shelf_name, exists = True):
        cmds.deleteUI(shelf_name)
    
def load(yaml_shelf_file, custom_shelf_name = None):
    '''
    Dynamically create and load the shelf in maya
    '''
    if custom_shelf_name:
        shelf_name = custom_shelf_name
    else:
        shelf_name = yaml_shelf_file.split('/')[-1]
        shelf_name = shelf_name.split('shelf_')[-1]
        shelf_name = shelf_name.rsplit('.')[0]
    
    # Parse the yaml_shelf
    with codecs.open(yaml_shelf_file, encoding="utf-8") as f_in:
        shelf_data = yaml.safe_load(f_in)
    
    if not shelf_data:
        raise RuntimeError('Could not get config data from {}.'.format(yaml_shelf))
    
    shelf_items = list()
    for item in shelf_data:
        shelf_items.append(item)
    
    if len(shelf_items) < 1:
        raise RuntimeError('Not enough shelf item in the config file: {}'.format(yaml_shelf))
    
    # This is a fix for the automatically saved shelf function
    # It will delete a previously shelf created with the plugin if any exist
    if cmds.shelfLayout(shelf_name, exists = True):
        cmds.deleteUI(shelf_name)
    
    # Declare the $gShelfTopLevel variable as a python variable
    # The $gShelfTopLevel mel variable is the Maya default variable for the shelves bar UI
    shelf_top_level = mel.eval('$temp_mel_var = $gShelfTopLevel;')
    
    # Create a new shelfLayout in $gShelfTopLevel
    custom_shelf = cmds.shelfLayout(shelf_name, parent = shelf_top_level)
    
    # Create shelf items
    for shelf_item in shelf_items:
        if 'separator' in shelf_item.keys()[0]:
            shelf_separator_data = _parse_shelf_separator(shelf_item)
            _build_shelf_separator(shelf_separator_data, custom_shelf)
        else:
            shelf_item_data = _parse_shelf_item(shelf_item)
            _build_shelf_item(shelf_item_data, custom_shelf)
            
    # Give a name and save the shelf
    cmds.tabLayout(shelf_top_level, edit = True, tabLabel = [custom_shelf, shelf_name])
    
    user_shelf_dir = cmds.internalVar(userShelfDir = True)
    user_shelf_fullname = os.path.join(user_shelf_dir, 'shelf_' + shelf_name)
    user_shelf_fullname = _sanitize_path(user_shelf_fullname)
    cmds.saveShelf(custom_shelf, user_shelf_fullname)
    
def import_shelf():
    '''
    Import the user selected YAML shelf
    '''
    yaml_file = cmds.fileDialog2(fileFilter = 'YAML Shelves(*.yaml *.yml)', fileMode = 1)
    if not yaml_file:
        return
    
    load(yaml_file[0])
    
def export_active_shelf():
    '''
    Export the currently active shelf as a yaml file
    '''
    shelf_top_level = mel.eval('$temp_mel_var = $gShelfTopLevel;')
    active_shelf = cmds.shelfTabLayout(shelf_top_level, query = True, selectTab = True)
    active_shelf_buttons = cmds.shelfLayout(active_shelf, query = True, childArray = True)
    
    shelf_data = list()
    for button in active_shelf_buttons:
        shelf_data.append(_get_shelf_item_data(button))
    
    yaml_file = cmds.fileDialog2(fileFilter = 'YAML Shelves(*.yaml *.yml)', fileMode = 0)
    if not yaml_file:
        return
    
    yaml_file = _sanitize_path(yaml_file[0])
    with codecs.open(yaml_file, 'w', encoding = 'utf-8') as f_out:
        yaml.safe_dump(shelf_data, f_out)
    
def load_all():
    '''
    Load all the yaml shelves from the MAYA_SHELF_PATH
    '''
    shelves = _get_yaml_shelves()
    for shelf in shelves:
        shelf_name = os.path.split(shelf)[-1]
        
        try:
            load(shelf)
            print('[{}] loaded successfully.'.format(shelf_name))
        except Exception as err:
            print (u'%s' %(err))
    