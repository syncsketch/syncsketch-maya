
import codecs
import json
import os
import platform
import socket
import sys
import time
import tempfile
import yaml
import re
from functools import partial

from vendor.Qt.QtWidgets import QApplication

import syncsketchGUI

from lib.gui.qt_widgets import *
from lib.gui import qt_utils
from lib.gui.qt_utils import *


from lib.connection import *
from vendor import mayapalette
from vendor.Qt import QtCompat
from vendor.Qt import QtCore
from vendor.Qt import QtGui
from vendor.Qt import QtWidgets

import logging
logger = logging.getLogger("syncsketchGUI")


from lib.gui.syncsketchWidgets.web import LoginView
import maya.cmds as cmds

PALETTE_YAML = 'syncsketch_palette.yaml'

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

def _call_ui_for_maya(ui_object):
    app_ui = ui_object(parent = _maya_main_window())
    app_ui.show()
    return app_ui

def _call_web_ui_for_maya(ui_object):
    app_ui = ui_object(parent=_maya_web_window())
    app_ui.show()
    return app_ui

# def trigger_load_expanded(tree, id):
#     """
#     Given a unique item'id set's the selection on the treeview
#     """
#     if not id:
#         return
#     iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)
#     while iterator.value():
#         item = iterator.value()
#         itemData = item.data(1, QtCore.Qt.EditRole)
#         if itemData.get('id') == id:
#             tree.setCurrentItem(item, 1)
#             tree.scrollToItem(item)
#         iterator += 1
#     return itemData


def set_tree_selection(tree, id):
    """
    Given a unique item'id set's the selection on the treeview
    """
    if not id:
        return
    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)
    while iterator.value():
        item = iterator.value()
        itemData = item.data(1, QtCore.Qt.EditRole)
        if itemData.get('id') == id:
            logger.info("tree.setCurrentItem{} itemData: {}".format(id, itemData))
            tree.setCurrentItem(item, 1)
            tree.scrollToItem(item)
        iterator += 1
    return itemData

def getReviewById(tree, reviewId):
    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)

    while iterator.value():
        item = iterator.value()
        item_data = item.data(1, QtCore.Qt.EditRole)
        if item_data.get('id') == reviewId:
            return item
        iterator +=1


def get_current_item_from_ids(tree, payload=None, setCurrentItem=True):
    logger.info("payload: {}".format(payload))
    searchValue = ''
    searchType = ''

    if not payload:
        return

    #Got both uuid and id, we are dealing with an item
    if payload['uuid'] and payload['id']:
        searchType = 'id'
        searchValue = int(payload['id'])
        logger.info("both payload['uuid'] and payload['id'] set {}".format(payload['uuid'], payload['id']))

    #Got only uuid, it's a review
    elif payload['uuid']:
        searchType = 'uuid'
        searchValue = payload['uuid']
        logger.info("payload['uuid'] set: {}".format(payload['uuid']))

    #Nothing useful found return
    else:
        logger.info("No uuid or id in payload, aborting")
        return


    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)

    while iterator.value():
        item = iterator.value()
        item_data = item.data(1, QtCore.Qt.EditRole)
        if item_data.get(searchType) == searchValue:
            if setCurrentItem:
                tree.setCurrentItem(item, 1)
                tree.scrollToItem(item)
                logger.info("Setting current Item : {} text:{} setCurrentItem: {}".format(item, item.text(0), setCurrentItem))
            return item_data
        iterator +=1

    logger.info("Item not found while iterating, no item set, setCurrentItem: {}".format(setCurrentItem))


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

    data = {"uuid":0, "id":0, "revision_id":0}
    #Add a slash so we don't need to chase two different cases
    if not link.split("#")[0][-1] == "/":
        link = "/#".join(link.split("#"))
        logger.info("Modified link: {}".format(link))


    if not link[0:len(baseUrl)] == baseUrl:
        logger.info("URL need's to start with: {}".format(baseUrl))
        return data


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



# tree function
def update_target_from_tree(self, treeWidget):
    logger.info("update_target_from_tree")
    selected_item = treeWidget.currentItem()
    if not selected_item:
        logger.info("Nothing selected returning")
        return
    else:
        item_data = selected_item.data(1, QtCore.Qt.EditRole)
        item_type = selected_item.data(2, QtCore.Qt.EditRole)
    logger.info("update_target_from_tree: item_data {} item_type {}".format(item_data, item_type))

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
        self.ui.thumbnail_itemPreview.clear()
        logger.info("in  item_type == 'project'")

    elif item_type == 'review': # and not item_data.get('reviewURL'):
        current_data['review_id'] = item_data.get('id')
        current_data['target_url'] = '{0}{1}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
        self.ui.thumbnail_itemPreview.clear()
        logger.info("in  item_type == 'review'")

    elif item_type == 'media':
        parent_item = selected_item.parent()
        parent_data = parent_item.data(1, QtCore.Qt.EditRole)
        current_data['review_id'] = parent_data.get('id')
        current_data['media_id'] = item_data.get('id')
        # * Expected url links
        #https://syncsketch.com/sketch/300639#692936
        #https://www.syncsketch.com/sketch/5a8d634c8447#692936/619482
        #current_data['target_url'] = '{}#{}'.format(review_base_url + str(current_data['review_id']), current_data['media_id'])
        current_data['target_url'] = '{0}{1}#{2}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
        logger.info("current_data['target_url'] {}".format(current_data['target_url']))


    while selected_item.parent():
        logger.info("selected_item.parent() {}".format(selected_item))
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
    logger.info("upload_to_value :{} ".format(current_data['upload_to_value']))

    return current_data



def show_web_login_window():
    _maya_delete_ui(LoginView.window_name)
    _call_ui_for_maya(LoginView)


def show_menu_window():
    from syncsketchGUI.lib.gui.syncsketchWidgets.mainWidget import MenuWindow
    _maya_delete_ui(MenuWindow.window_name)
    app = _call_ui_for_maya(MenuWindow)
    logger.info("app: {}".format(app))
    return app


def show_download_window():
    from syncsketchGUI.lib.gui.syncsketchWidgets.downloadWidget import DownloadWindow
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
    panel_is_populated = populate_review_panel(app)


