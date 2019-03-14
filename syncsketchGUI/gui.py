# -*- coding: UTF-8 -*-
# ======================================================================
# @Author   : SyncSketch LLC
# @Email    : dev@syncsketch.com
# @Version  : 1.0.0
# ======================================================================
import codecs
import json
import os
import platform
import socket
import sys
import time
import webbrowser
import tempfile
import yaml
import re
from functools import partial

from vendor.Qt.QtWebKit import *
from vendor.Qt.QtWebKitWidgets import *
from vendor.Qt.QtWidgets import QApplication

import syncsketchGUI
from lib import video, user, database
from lib.gui.qt_widgets import *
from lib.gui import qt_utils
from lib.gui.qt_utils import *

from lib.gui.icons import *
from lib.gui.icons import _get_qicon
from lib.connection import *
from vendor import mayapalette
from vendor.Qt import QtCompat
from vendor.Qt import QtCore
from vendor.Qt import QtGui
from vendor.Qt import QtWidgets

import logging
logger = logging.getLogger(__name__)

from lib.gui.syncsketchWidgets.webLoginWindow import WebLoginWindow

# ======================================================================
# Environment Detection

PLATFORM = platform.system()
BINDING = QtCompat.__binding__

try:
    from maya import cmds
    import maya.mel as mel
    MAYA = True
except ImportError:
    MAYA = False



STANDALONE = False

from lib.maya import scene as maya_scene

# ======================================================================
# Global Variables

PALETTE_YAML = 'syncsketch_palette.yaml'
PRESET_YAML = 'syncsketch_preset.yaml'
VIEWPORT_YAML = 'syncsketch_viewport.yaml'


DEFAULT_PRESET = 'Default(for speedy upload)'
DEFAULT_VIEWPORT_PRESET = database.read_cache('current_viewport_preset')

uploadPlaceHolderStr = "Pick a review/item or paste a SyncSketch URL here"
message_is_not_loggedin = "Please sign into your account by clicking 'Log-In' or create a free Account by clicking 'Sign up'."
message_is_not_connected = "WARNING: Could not connect to SyncSketch. It looks like you may not have an internet connection?"

WAIT_TIME = 0.00 # seconds

USER_ACCOUNT_DATA = None

# ======================================================================
# DCC application helper functions

def _maya_delete_ui(ui_name):
    """
    Delete existing UI in Maya
    """
    if cmds.control(ui_name, exists=True):
        cmds.deleteUI(ui_name)

def _maya_main_window():
    """
    Return Maya's main window
    """
    for obj in QtWidgets.qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')

def _maya_web_window():
    """
    Return Maya's main window
    """
    for obj in QtWidgets.qApp.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')


# ======================================================================
# Module Utilities

def _call_ui_for_standalone(ui_object):
    app = QtWidgets.QApplication(sys.argv)
    app_ui = ui_object(None)

    if not PLATFORM == 'Darwin' and BINDING == 'PySide' or BINDING == 'PyQt4':
        palette_file = path.get_config_yaml(PALETTE_YAML)
        style_data = database._parse_yaml(palette_file)
        mayapalette.set_palette_from_dict(style_data)
        mayapalette.set_style()
        mayapalette.set_maya_tweaks()

    app_ui.show()
    sys.exit(app.exec_())
    return app_ui

def _call_ui_for_maya(ui_object):
    app_ui = ui_object(parent = _maya_main_window())
    app_ui.show()
    return app_ui

def _call_web_ui_for_maya(ui_object):
    app_ui = ui_object(parent=_maya_web_window())
    app_ui.show()
    return app_ui

def _build_widget_item(parent, item_name, item_type, item_icon, item_data):
    treewidget_item = QtWidgets.QTreeWidgetItem(parent, [item_name])
    treewidget_item.setData(1, QtCore.Qt.EditRole, item_data)
    treewidget_item.setData(2, QtCore.Qt.EditRole, item_type)
    treewidget_item.setIcon(0, item_icon)
    return treewidget_item

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
# ======================================================================
# Module Classes

class OpenPlayer(QWebView):
    """
    Login Window Class
    """
    window_name = 'Login'
    window_label = 'Login to SyncSketch'

    def __init__(self, parent, url='https://syncsketch.com/pro'):
        super(OpenPlayer, self).__init__(parent)

        self.parent = parent
        self.current_user = user.SyncSketchUser()


        self.setWindowTitle(self.window_label)
        self.setObjectName(self.window_name)
        self.setWindowFlags(QtCore.Qt.Window)

        self.load(QtCore.QUrl(url))


        self.show()
        self.activateWindow()
        self._myBindingFunction()
        qt_utils.align_to_center(self, self.parent)

        self.setProperty('saveWindowPref', True)


def set_tree_selection(tree, id):
    """
    Given a uniqute item'id set's the selection on the treeview
    """
    if not id:
        return
    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)
    while iterator.value():
        item = iterator.value()
        itemData = item.data(1, QtCore.Qt.EditRole)
        if itemData.get('id') == id:
            tree.setCurrentItem(item, 1)
            tree.scrollToItem(item)
        iterator +=1
    return itemData


def get_current_item_from_ids(tree, payload=None):
    logging.info("payload: {}".format(payload))
    searchValue = ''
    searchType = ''

    if not payload:
        return

    #Got both uuid and id, we are dealing with an item
    if payload['uuid'] and payload['id']:
        searchType = 'id'
        searchValue = int(payload['id'])

    #Got only uuid, it's a review
    elif payload['uuid']:
        searchType = 'uuid'
        searchValue = payload['uuid']

    #Nothing useful found return
    else:
        return


    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)
    # by default select first item(playground)
    # todo: make sure we're not parsing for the correct review id
    while iterator.value():
        item = iterator.value()
        item_data = item.data(1, QtCore.Qt.EditRole)
        if item_data.get(searchType) == searchValue:
            tree.setCurrentItem(item, 1)
            tree.scrollToItem(item)
            return item_data
        iterator +=1


def parse_url_data(link=database.read_cache('upload_to_value')):
    '''
    simple url parser that extract uuid, review_id and revision_id
    '''
    #url = 'https://www.syncsketch.com/sketch/bff609f9cbac/#711273/637821'
    #       https://syncsketch.com/sketch/bff609f9cbac#711680

    #Remove reduntant path and check if it's expected
    logger.info("link parser: {}".format(link))
    if not link:
        logger.info("Link isn't a link: {}".format(link))
        return

    baseUrl = 'https://syncsketch.com/sketch/'

    #Remove leading forward slash
    if link[-1] == "/":
        link = link[:-1]

    #Remove www
    link = link.replace("www.", "")

    #Add a slash so we don't need to chase two different cases
    if not link.split("#")[0][-1] == "/":
        link = "/#".join(link.split("#"))
        logger.info("Modified link: {}".format(link))


    if not link[0:len(baseUrl)] == baseUrl:
        print("URL need's to start with: {}".format(baseUrl))
        return

    data = {"uuid":0, "id":0, "revision_id":0}

    #Find UUID
    payload = link[len(baseUrl):].split("/")

    if len(link) > 0:
        uuidPart = (re.findall(r"([a-fA-F\d]{12})", payload[0]))
        if uuidPart:
            data['uuid'] = uuidPart[0]
        else:
            print("link need's to be of the form https://www.syncsketch.com/sketch/bff609f9cbac/ got {}".format(link))
    #Find ID
    if len(payload) > 1:
        if payload[1].startswith("#"):
            data['id'] = payload[1][1:]
        else:
            print("link need's to be of the form https://www.syncsketch.com/sketch/bff609f9cbac/#711273 got {}".format(link))

    if len(payload) > 3:
        pass
        #handle revision
    return data



def get_ids_from_link(link = database.read_cache('upload_to_value')):
    #link: https://www.syncsketch.com/sketch/0a5546b336de/
    #uploaded_to_value: https://syncsketch.com/sketch/0854aaba81fb#705832
    #https://syncsketch.com/sketch/0854aaba81fb#705832
    logger.info("link: {0}".format(link))
    if not link:
        return
    return link.split('/')[-1].split('#')


def confirm_upload_to_playground():
    title = 'Confirm Upload'
    message = 'The file will be uploaded to the Playground.'
    info_message = 'Everyone with the link can view your upload.'

    confirm_dialog = QtWidgets.QMessageBox()
    confirm_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
    confirm_dialog.setText(message + '\n' + info_message)
    confirm_dialog.setDefaultButton(QtWidgets.QMessageBox.Ok)
    confirm_dialog.setIcon(QtWidgets.QMessageBox.Question)
    confirm_dialog.setWindowTitle(title)

    response = confirm_dialog.exec_()

    if response == QtWidgets.QMessageBox.Ok:
        return True



# tree function
def update_target_from_tree(self, treeWidget):
    logger.debug("update_target_from_tree")
    selected_item = treeWidget.currentItem()
    if not selected_item:
        return
    else:
        item_data = selected_item.data(1, QtCore.Qt.EditRole)
        item_type = selected_item.data(2, QtCore.Qt.EditRole)

    review_base_url = "https://syncsketch.com/sketch/"
    current_data={}
    current_data['upload_to_value'] = str()
    current_data['breadcrumb'] = str()
    current_data['target_url_type'] = item_type
    current_data['review_id'] = str()
    current_data['media_id'] = str()
    current_data['target_url'] = None
    current_data['name'] = item_data.get('name')




    if item_type == 'project':
        review_url = '{}{}'.format(path.project_url, item_data.get('id'))
        #todo: is there a shorter way?
        self.ui.thumbnail_itemPreview.clear()
    elif item_type == 'review': # and not item_data.get('reviewURL'):
        current_data['review_id'] = item_data.get('id')
        current_data['target_url'] = '{0}{1}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
        self.ui.thumbnail_itemPreview.clear()

    elif item_type == 'media':
        parent_item = selected_item.parent()
        parent_data = parent_item.data(1, QtCore.Qt.EditRole)
        current_data['review_id'] = parent_data.get('id')
        current_data['media_id'] = item_data.get('id')
        #todo: yfs: clean this
        #https://syncsketch.com/sketch/300639#692936
        #https://www.syncsketch.com/sketch/5a8d634c8447#692936/619482
        #current_data['target_url'] = '{}#{}'.format(review_base_url + str(current_data['review_id']), current_data['media_id'])
        current_data['target_url'] = '{0}{1}#{2}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
        logger.info(current_data['target_url'])

    if selected_item.text(0) == 'Playground':
        current_data['upload_to_value'] = 'Playground'
    else:
        while selected_item.parent():
            current_data['breadcrumb'] = ' > '.join([selected_item.text(0), current_data['upload_to_value']])
            selected_item = selected_item.parent()

        if current_data['breadcrumb'].split(' > ')[-1] == '':
            current_data['breadcrumb'] = current_data['upload_to_value'].rsplit(' > ', 1)[0]


    database.dump_cache({'breadcrumb': current_data['breadcrumb']})
    database.dump_cache({'upload_to_value': current_data['target_url']})
    database.dump_cache({'target_url_type': current_data['target_url_type']})
    # Name
    item_name = selected_item.text(0)
    database.dump_cache({'target_url_item_name': item_name})

    # Username
    # Todo -  this should not be the current user but the creator of the item
    try:
        username = self.current_user.get_name()
    except:
        username = str()

    database.dump_cache({'target_url_username': username})

    # Description
    description = item_data.get('description')
    database.dump_cache({'target_url_description': description})
    database.dump_cache({'target_review_id': current_data['review_id']})
    database.dump_cache({'target_media_id': current_data['media_id']})

    # Upload to Value - this is really the 'breadcrumb')
    database.dump_cache({'upload_to_value': current_data['target_url']})



    return current_data



def show_web_login_window():
    _maya_delete_ui(WebLoginWindow.window_name)
    _call_ui_for_maya(WebLoginWindow)


def show_menu_window():
    from syncsketchGUI.lib.gui.syncsketchWidgets.mainWidget import MenuWindow
    _maya_delete_ui(MenuWindow.window_name)
    app = _call_ui_for_maya(MenuWindow)
    logger.info("app: {}".format(app))
    return app


def show_download_window():
    from syncsketchGUI.lib.gui.syncsketchWidgets.webLoginWindow import DownloadWindow
    _maya_delete_ui(DownloadWindow.window_name)
    _call_ui_for_maya(DownloadWindow)


def show_viewport_preset_window():
    from syncsketchGUI.lib.gui.syncsketchWidgets.viewportPresetWidget import ViewportPresetWindow
    _maya_delete_ui(ViewportPresetWindow.window_name)
    _call_ui_for_maya(ViewportPresetWindow)


def show_syncsketch_browser_window():
    current_user = user.SyncSketchUser()
    if not current_user:
        show_web_login_window()
        return

    _maya_delete_ui(SyncSketchBrowserWindow.window_name)
    app = _call_ui_for_maya(SyncSketchBrowserWindow)
    time.sleep(WAIT_TIME)
    panel_is_populated = populate_review_panel(app)


