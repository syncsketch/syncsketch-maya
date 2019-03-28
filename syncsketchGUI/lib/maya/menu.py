import uuid

from maya import OpenMaya as om
from maya import cmds
from maya import mel
from syncsketchGUI.lib import user, path

from syncsketchGUI.lib import database

# ======================================================================
# Global Variables

yaml_file = 'syncsketch_menu.yaml'
menu_prefix = 'syncsketch'

# ======================================================================
# Module Utilities

def _show_info(message):
    om.MGlobal.displayInfo(message)

def _show_warning(message):
    om.MGlobal.displayWarning(message)

def _show_error(message):
    om.MGlobal.displayError(message)


def _sanitize_mel_command(mel_command_string):
    '''
    If the given MEL command has quotes,
    put escape slashes before each quotation
    '''
    if not isinstance(mel_command_string, str):
        return

    mel_command_string = mel_command_string.replace('"', '\"')
    mel_command_string = mel_command_string.replace('\'', '\"')
    return mel_command_string

def _get_main_menu_bar():
    '''
    Get maya's main menu bar
    '''
    main_menu_bar = 'MayaWindow'
    return main_menu_bar

def _remove_special_characters(string):
    '''
    Remove all the non alpha numeric characters from the string
    '''
    sanitized_string = ''.join(e for e in string if e.isalnum())
    return sanitized_string

def _make_object_name(string):
    '''
    Convert the given string into a python usable object name.
    If non ascii characters are found, generate a uuid
    and attach it behind the string 'MenuItem'
    '''
    if string:
        string = _remove_special_characters(string)
        string = string.encode('ascii', 'ignore')

    unique_id = str(uuid.uuid4())
    unique_id = _remove_special_characters(unique_id)

    if not string:
        string = '{}{}'.format('MenuItem_', unique_id)

    return '{}{}'.format(menu_prefix, string)

def _add_menu_top(menu_top_label):
    '''
    Check if the menu top already exist and create one if it doesn't
    '''
    main_menu_bar = _get_main_menu_bar()
    menu_top_object = _make_object_name(menu_top_label)

    if mel.eval('menu -exists {}'.format(menu_top_object)):
        cmds.deleteUI(menu_top_object, menu = True)

    menu_top = cmds.menu(  menu_top_object,
                            parent = main_menu_bar,
                            label = menu_top_label,
                            tearOff = True)
    return menu_top

def _delete_menu_top(menu_top_label):
    '''
    Check if the menu top already exist and create one if it doesn't
    '''
    main_menu_bar   = _get_main_menu_bar()
    menu_top_object = _make_object_name(menu_top_label)

    if mel.eval('menu -exists {}'.format(menu_top_object)):
        cmds.deleteUI(menu_top_object, menu = True)

def _add_menu(menu_label, menu_parent_label):
    menu_object = _make_object_name(menu_label)
    menu_parent_object = _make_object_name(menu_parent_label)

    if mel.eval('menuItem -exists {}'.format(menu_object)):
        cmds.deleteUI(menu_object, menuItem = True)

    menu = cmds.menuItem(  menu_object,
                            parent = menu_parent_object,
                            label = menu_label,
                            tearOff = True,
                            subMenu = True)
    return menu

def _add_divider(divider_label, divider_parent_label):
    divider_object = _make_object_name(divider_label)
    divider_parent_object = _make_object_name(divider_parent_label)

    if mel.eval('menuItem -exists {}'.format(divider_object)):
        cmds.deleteUI(divider_object, menuItem = True)

    divider = cmds.menuItem(   divider_object,
                                parent = divider_parent_object,
                                divider = True,
                                label = divider_label)
    return divider

def _add_menu_item(menu_item_label, menu_item_command, menu_item_parent_label):
    menu_item_object = _make_object_name(menu_item_label)
    menu_item_parent_object = _make_object_name(menu_item_parent_label)

    if mel.eval('menuItem -exists {}'.format(menu_item_object)):
        cmds.deleteUI(menu_item_object, menuItem = True)

    if not menu_item_command:
        menu_item = cmds.menuItem( menu_item_object,
                                    parent = menu_item_parent_object,
                                    label = menu_item_label,
                                    tearOff = True)
    else:
        menu_item = cmds.menuItem( menu_item_object,
                                    parent = menu_item_parent_object,
                                    command = menu_item_command,
                                    label = menu_item_label,
                                    tearOff = True)
    return menu_item

def _add_menu_item_option(menu_item_label, menu_item_command, menu_item_parent_label):
    menu_item_object = _make_object_name(menu_item_label)
    menu_item_parent_object = _make_object_name(menu_item_parent_label)

    if mel.eval('menuItem -exists {}'.format(menu_item_object)):
        cmds.deleteUI(menu_item_object, menuItem = True)

    if not menu_item_command:
        menu_item = cmds.menuItem( menu_item_object,
                                    parent = menu_item_parent_object,
                                    label = menu_item_label,
                                    optionBox = True,
                                    tearOff = True)
    else:
        menu_item = cmds.menuItem( menu_item_object,
                                    parent = menu_item_parent_object,
                                    command = menu_item_command,
                                    label = menu_item_label,
                                    optionBox = True,
                                    tearOff = True)
    return menu_item

def _populate_menus(menu_data, menu_parent):
    '''
    Populate the pre-existing menu tops with sub menus and menu items
    menu_data = Dictionary parsed from yaml
    '''
    if not isinstance(menu_data, list):
        return

    for item in menu_data:

        # If the value is a list, the item has submenu
        if isinstance(item.values()[0], list):
            menu_label = item.keys()[0]
            menu_parent_label = menu_parent
            _add_menu( menu_label,
                        menu_parent_label)

        # If the value is a string, the item has no submenu,
        # and if it's a divider, add a divider instead of a command
        elif isinstance(item.values()[0], str) and \
                item.values()[0].lower() == 'divider':
            divider_label = item.keys()[0]
            divider_parent_label = menu_parent
            _add_divider(divider_label, divider_parent_label)

        # If the value is a string, the item has no submenu.
        # Then just add it as a menu command with
        else:
            menu_item_label = item.keys()[0]
            menu_item_command = item.values()[0]
            menu_item_parent_label = menu_parent

            if 'option' in menu_item_label.lower():
                menu_item_object = _add_menu_item_option(  menu_item_label,
                                                            menu_item_command,
                                                            menu_item_parent_label)
            else:
                menu_item_object = _add_menu_item( menu_item_label,
                                                    menu_item_command,
                                                    menu_item_parent_label)

            # When the command was added in python command,
            # it's being interpreted as a python command
            # like cmds.somecommand(), but we want MEL command.
            # So, editing the menu item in MEL would
            # make maya interpret the command as a MEL command.
            menu_item_command = _sanitize_mel_command(menu_item_command)
            if menu_item_command:
                mel_command = 'menuItem -edit -command "{}" {}'\
                                .format(   menu_item_command,
                                            menu_item_object)
                mel.eval(mel_command)

# ======================================================================
# Module Functions

def delete_menu():
    '''
    Delete the menu tops based on the yaml file
    '''
    # Parse the yaml file and get the menu items as a dictionary
    yaml_path = path.get_config_yaml(yaml_file)
    data = database._parse_yaml(yaml_path)

    if not data:
        _show_error('Invalid YAML data.')
        return

    # Get menus from the parsed data
    menu_tops = data.keys()

    # Create the menu tops
    for menu_top in menu_tops:
        _delete_menu_top(menu_top)

def build_menu():
    '''
    Build and populate the menus based on the yaml file
    '''
    # Parse the yaml file and get the menu items as a dictionary
    yaml_path = path.get_config_yaml(yaml_file)
    data = database._parse_yaml(yaml_path)

    if not data:
        _show_error('Invalid YAML data.')
        return

    if not isinstance(data, dict):
        return

    # Build menus from the parsed data
    menu_tops = data.keys()

    # Create the menu tops
    for menu_top in menu_tops:
        _add_menu_top(menu_top)

    # Populate the first menus
    for menu_top in menu_tops:
        menu_data = data.get(menu_top)
        if menu_data:
            _populate_menus(menu_data, menu_top)

    # Populate the second menus
    second_menus = list()
    for menu_top in menu_tops:
        menu_data = data.get(menu_top)
        if not menu_data:
            continue

        for second_menu in menu_data:
            if isinstance(second_menu, dict):
                second_menus.append(second_menu)

    for second_menu in second_menus:
        second_menu_data = second_menu.values()[0]
        second_menu_parent = second_menu.keys()[0]

        if isinstance(second_menu_data, list):
            _populate_menus(second_menu_data, second_menu_parent)

    # Populate the third menus
    third_menus = list()
    for second_menu in second_menus:
        for third_menu_list in second_menu.values():
            for third_menu in third_menu_list:
                if isinstance(third_menu, dict):
                    third_menus.append(third_menu)

    for third_menu in third_menus:
        third_menu_data = third_menu.values()[0]
        third_menu_parent = third_menu.keys()[0]

        if isinstance(third_menu_data, list):
            _populate_menus(third_menu_data, third_menu_parent)

def refresh_menu_state():
    '''
    If before_login is the given state, some parts of the menu will be greyed out.
    If after_login, all parts of the menu will be enabled and accessible.
    '''
    current_user = user.SyncSketchUser()
    username = current_user.get_name()

    login_info = 'Currently not logged in'
    if username:
        login_info = 'Logged in as: [{}]'.format(username)

    # Parse the yaml file and get the menu items as a dictionary
    yaml_path = path.get_config_yaml(yaml_file)
    data = database._parse_yaml(yaml_path)

    if not data:
        return

    if not isinstance(data, dict):
        return

    # Build menus from the parsed data
    menu_tops = data.keys()

    for menu_top in menu_tops:
        menu_top_name = _make_object_name(menu_top)
        if not cmds.menuItem('logged_in_as', exists = True):
            cmds.menuItem( 'logged_in_as',
                            parent = menu_top_name)

        cmds.menuItem( 'logged_in_as',
                        edit = True,
                        enable = False,
                        label = login_info)
