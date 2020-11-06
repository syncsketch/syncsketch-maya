import logging
import webbrowser

logger = logging.getLogger("syncsketchGUI")

from syncsketchGUI.vendor.Qt import QtCore, QtGui, QtWidgets
from syncsketchGUI.lib import video, user, database

from syncsketchGUI.gui import show_download_window

# FIXME
from syncsketchGUI.lib.gui.qt_widgets import *
from syncsketchGUI.lib.gui.qt_utils import *

from syncsketchGUI.gui import parse_url_data, get_current_item_from_ids, set_tree_selection, getReviewById
from syncsketchGUI.lib.gui.literals import uploadPlaceHolderStr


# FIXME
USER_ACCOUNT_DATA = None

class BrowserWidget(QtWidgets.QWidget):

    target_changed = QtCore.Signal(dict) # dict: target_data

    def __init__(self, *args, **kwargs):
        super(BrowserWidget, self).__init__(*args, **kwargs)

        self.reviewData = None
        self.mediaItemParent = None

        self._decorate_ui()
        self._build_connections()

        #Populate Treewidget sparse
        #self.asyncProcessRunning = False
        self._populate_tree()

        self._restore_ui_state()

    def _decorate_ui(self):

        self.browser_treeWidget = QtWidgets. QTreeWidget()
        self.browser_treeWidget.header().setStyleSheet("color: %s"%success_color)
        highlight_palette = self.browser_treeWidget.palette()
        highlight_palette.setColor(QtGui.QPalette.Highlight, highlight_color)
        self.browser_treeWidget.setPalette(highlight_palette)
        self.browser_treeWidget.setHeaderLabel('refresh')
        self.browser_treeWidget.header().setSectionsClickable(True)

        self.browser_treeWidget.header().setDefaultAlignment(QtCore.Qt.AlignCenter)


        
        self.target_lineEdit = RegularLineEdit() #FIXME
        self.ui_open_pushButton = RegularToolButton(self, open_icon) #FIXME
        self.ui_copyURL_pushButton = RegularToolButton(self, copy_icon) #FIXME

        self.ui_reviewSelection_hBoxLayout = QtWidgets.QHBoxLayout()
        self.ui_reviewSelection_hBoxLayout.addWidget(self.target_lineEdit)
        self.ui_reviewSelection_hBoxLayout.addWidget(self.ui_open_pushButton)
        self.ui_reviewSelection_hBoxLayout.addWidget(self.ui_copyURL_pushButton)

        self.thumbnail_itemPreview = RegularThumbnail(width=320, height=180) #FIXME
        
        # Download Button
        self.ui_download_pushButton = RegularButton(self, icon = download_icon, color=download_color)
        self.ui_download_pushButton.setToolTip('Download from SyncSketch Review Target')
        self.ui_download_pushButton.setText("DOWNLOAD")
        
        
        self.review_ui_treeWidget_layout = QtWidgets.QVBoxLayout()
        self.review_ui_treeWidget_layout.addWidget(self.browser_treeWidget)
        self.review_ui_treeWidget_layout.addLayout(self.ui_reviewSelection_hBoxLayout)
        self.review_ui_treeWidget_layout.addWidget(self.thumbnail_itemPreview)
        self.review_ui_treeWidget_layout.addWidget(self.ui_download_pushButton, 10)

    
        self.ui_targetSelection_groupbox = QtWidgets.QGroupBox()
        self.ui_targetSelection_groupbox.setTitle('TARGET FOR UPLOAD')
        self.ui_targetSelection_groupbox.setLayout(self.review_ui_treeWidget_layout)


        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setSpacing(3)
        self.main_layout.addWidget(self.ui_targetSelection_groupbox)

        self.setLayout(self.main_layout)
    
    def _build_connections(self):
        
        #tree widget functions
        self.browser_treeWidget.currentItemChanged.connect(self._update_target_from_item_callback)

        self.browser_treeWidget.doubleClicked.connect(self._open_url_callback)

        # Videos / Playblast Settings
        self.target_lineEdit.textChanged.connect(self.update_target_from_url)


        self.browser_treeWidget.itemExpanded.connect(self._expand_item_callback)
        self.browser_treeWidget.header().sectionClicked.connect(self.refresh)

        # Videos / Upload Settings
        self.ui_open_pushButton.clicked.connect(self._open_url_callback)
        self.ui_copyURL_pushButton.clicked.connect(self.copy_to_clipboard)
        
        self.ui_download_pushButton.clicked.connect(self._download_callback)

        self.target_changed.connect(self._update_ui_from_target_data)
        self.target_changed.connect(self._cache_target_data)

    def _restore_ui_state(self):
        current_user = user.SyncSketchUser()
        if current_user.is_logged_in() :
            self.update_target_from_cache()

    def _populate_tree(self, account_data=None, item_to_add = None, force = False):

        self.current_user = user.SyncSketchUser()
        if not self.current_user.is_logged_in():
            logger.info("User not logged in, returning")
            return

        self.browser_treeWidget.clear()
    
        account_data = self.current_user.get_account_data(withItems=False)
    
        if not account_data:
            logger.info("No account_data found")
            return

        logger.info("account_data: {}".format(account_data))
        for account in account_data:
            account_treeWidgetItem = self._build_widget_item(parent = self.browser_treeWidget,
                                                            item_name = account.get('name'),
                                                            item_type='account',
                                                            item_icon = account_icon, #FIXME
                                                            item_data = account)
            # Add projects
            projects = account.get('projects')
            for project in projects:
                project_treeWidgetItem = self._build_widget_item(parent = account_treeWidgetItem,
                                                                item_name = project.get('name'),
                                                                item_type='project',
                                                                item_icon = project_icon, #FIXME
                                                                item_data = project)
                # Add reviews
                reviews = project.get('reviews')

                for review in reviews:
                    review_treeWidgetItem = self._build_widget_item(parent = project_treeWidgetItem,
                                                                item_name = review.get('name'),
                                                                item_type='review',
                                                                item_icon = review_icon, #FIXME
                                                                item_data = review)
                    # Add items
                    items = review.get('items')
                    # * If there are no reviews, create still a dumy element to get an arrow icon
                    # * to visualize that the item needs to be expanded
                    for media in items or [{'uuid':'', 'type':'video'}]:
                        #add UUID of the review container to the media, so we can use it in itemdata
                        media['uuid'] = review['uuid']
                        if not media.get('type'):
                            specified_media_icon = media_unknown_icon #FIXME
                        elif 'video' in media.get('type').lower():
                            specified_media_icon = media_video_icon #FIXME
                        elif 'image' in media.get('type').lower():
                            specified_media_icon = media_image_icon #FIXME
                        elif 'sketchfab' in media.get('type').lower():
                            specified_media_icon = media_sketchfab_icon #FIXME
                        else:
                            specified_media_icon = media_unknown_icon

                        media_treeWidgetItem = self._build_widget_item(parent = review_treeWidgetItem,
                                                                    item_name = media.get('name'),
                                                                    item_type='media',
                                                                    item_icon = specified_media_icon, #FIXME
                                                                    item_data = media)

                        media_treeWidgetItem.sizeHint(80)

    def _populate_review_item(self, review_item):
        
        current_user = user.SyncSketchUser()
        current_user.auto_login()
        if not current_user.is_logged_in():
            return

        review = review_item.data(1, QtCore.Qt.EditRole)

        review_id = review['id']
        items = current_user.host_data.getMediaByReviewId(review_id)['objects']

        # Removes current child items
        review_item.takeChildren()

        for media in items:
            #add UUID of the review container to the media, so we can use it in itemdata
            media['uuid'] = review['uuid']
            if not media.get('type'):
                specified_media_icon = media_unknown_icon #FIXME 
            elif 'video' in media.get('type').lower():
                specified_media_icon = media_video_icon  #FIXME
            elif 'image' in media.get('type').lower():
                specified_media_icon = media_image_icon  #FIXME
            elif 'sketchfab' in media.get('type').lower():
                specified_media_icon = media_sketchfab_icon  #FIXME
            else:
                specified_media_icon = media_unknown_icon   #FIXME

            media_treeWidgetItem = self._build_widget_item(parent = review_item,
                                                        item_name = media.get('name'),
                                                        item_type='media',
                                                        item_icon = specified_media_icon,
                                                        item_data = media)

            media_treeWidgetItem.sizeHint(80)

    def _build_widget_item(self, parent, item_name, item_type, item_icon, item_data):
        treewidget_item = QtWidgets.QTreeWidgetItem(parent, [item_name])
        treewidget_item.setData(1, QtCore.Qt.EditRole, item_data)
        treewidget_item.setData(2, QtCore.Qt.EditRole, item_type)
        treewidget_item.setIcon(0, item_icon)
        return treewidget_item

    def _expand_item_callback(self, target):

        """
        Select the item that is in the expanded hierarchy
        which triggers the load of items.
        """

        logger.info("Expanding treewidget: {}".format(target))
        selected_item = target
        #convert qmodelindex into a treewidget item
        item =  target #self.ui.browser_treeWidget.itemFromIndex(selected_item)
        try:
            logger.info("item.text {} selected_item {}".format(item.data(0, QtCore.Qt.EditRole), item.data(1, QtCore.Qt.EditRole)))
        except Exception as e:
            logger.info("Exception: ".format(e))
        item_type = item.data(2, QtCore.Qt.EditRole)
        if item_type == "review":
            logger.info("item_type is a review, expanding")
            if item.childCount() == 1 and not item.child(0).data(0, QtCore.Qt.EditRole):
                logger.info("Only single empty dummy item, delete and load childs")
                item.takeChildren()
                self._populate_review_item(item)
        else:
            logger.info("Not a review, nothing to expand")

            #User keeps pressing expand, so let's reload
            # * consolidate


            #item.setSelected(True)

    def _update_target_from_item_callback(self, current_item, previous_item):
 
        target_data = self.get_target_data(current_item)
        self.target_changed.emit(target_data)

    def _update_ui_from_target_data(self, target_data):
        
        target_url = target_data["target_url"]
        self.target_lineEdit.setText(target_url)
        logger.info("Set target_lineEdit to {}".format(target_url))

        ui_to_toggle = [
            self.ui_download_pushButton,
            self.ui_copyURL_pushButton,
            self.ui_reviewSelection_hBoxLayout
        ]

        target_type = target_data['target_url_type']

        if (target_type == "review") or (target_type == "media"):
            enable_interface(ui_to_toggle, True)
        else:
            enable_interface(ui_to_toggle, False)
            self.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)

        if target_type == "media":
            current_user = user.SyncSketchUser()
            thumbURL = current_user.get_item_info(target_data['media_id'])['objects'][0]['thumbnail_url']
            logger.info("thumbURL: {}".format(thumbURL))
            self.thumbnail_itemPreview.set_icon_from_url(thumbURL)

    def _cache_target_data(self, target_data):
        logger.info("Cache Target Data: {}".format(target_data))
        database.dump_cache({'breadcrumb': target_data['breadcrumb']})
        database.dump_cache({'upload_to_value': target_data['target_url']})
        database.dump_cache({'target_url_type': target_data['target_url_type']})
        database.dump_cache({'target_url_item_name': target_data['target_url_item_name']})

        # Username
        # Todo -  this should not be the current user but the creator of the item
        try:
            username = self.current_user.get_name()
        except:
            username = str()

        database.dump_cache({'target_url_username': username})

        # Description
        database.dump_cache({'target_url_description': target_data['description']})
        database.dump_cache({'target_review_id': target_data['review_id']})
        database.dump_cache({'target_media_id': target_data['media_id']})

        # Upload to Value - this is really the 'breadcrumb')
        database.dump_cache({'upload_to_value': target_data['target_url']})

    def _download_callback(self):
        logger.info("Download pressed")
        #self.validate_review_url()
        show_download_window()
        return

    def _open_url_callback(self, selected_item= None):
        if not selected_item:
            selected_item = self.browser_treeWidget.currentItem()
        
        target_data = self.get_target_data(selected_item)
        offline_url = path.make_url_offlineMode(target_data["target_url"])
        logger.info("Opening Url: {} ".format(offline_url))
        if offline_url:
            webbrowser.open(offline_url)
    
    def _sanitize(self, val):
        return val.rstrip().lstrip()

    def refresh(self):
        logger.info("Refresh Clicked, trying to refresh if logged in")
        current_user = user.SyncSketchUser()
        if current_user.is_logged_in():
            self._populate_tree()
            self.update_target_from_cache()
        
    def copy_to_clipboard(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        link =  self.target_lineEdit.text()
        #link = database.read_cache('us_last_upload_url_pushButton')
        cb.setText(link, mode=cb.Clipboard)
    
    def update_target_from_url(self, url):
        url = self._sanitize(url)

        url_payload = parse_url_data(url)  #FIXME
        logger.info("url_payload: {} ".format(url_payload))

        if not url_payload:
            return

        media_item = get_current_item_from_ids(self.browser_treeWidget, url_payload, setCurrentItem=False) #FIXME
        
        if not media_item:

            logger.info("Cant find Media Item. Try to find Review Item and repopulate, then try again.")

            review_url_payload = {
                "uuid" : url_payload["uuid"],
                "id" : None,
            } 

            review_item = get_current_item_from_ids(self.browser_treeWidget, review_url_payload, setCurrentItem=False)

            if not review_item:
                logger.warning("Cant find Media and Review Item with payload: {}".format(url_payload))
                return
            else:
                logger.info("Found Review Item: {}".format(review_item))
            
            self._populate_review_item(review_item)

            media_item = get_current_item_from_ids(self.browser_treeWidget, url_payload, setCurrentItem=False)
        

        self.browser_treeWidget.setCurrentItem(media_item, 1)
        self.browser_treeWidget.scrollToItem(media_item)
        logger.info("Selected Media Item: {}".format(media_item))

    def update_target_from_cache(self):
        link = database.read_cache('upload_to_value')
        if not link:
            logger.info("Cache for 'upload_to_value' doesnt exist")
            return
        logger.info("Update Target from URL: {} ".format(link))
        self.update_target_from_url(link)
    
    def get_target_data(self, item):

        if not item:
            logger.info("Nothing selected returning")
            return
        else:
            item_data = item.data(1, QtCore.Qt.EditRole)
            item_type = item.data(2, QtCore.Qt.EditRole)
        logger.info("get data for item: item_data {} item_type {}".format(item_data, item_type))

        review_base_url = "https://syncsketch.com/sketch/"
        current_data={}
        current_data['upload_to_value'] = str()
        current_data['breadcrumb'] = str()
        current_data['target_url_type'] = item_type
        current_data['review_id'] = str()
        current_data['media_id'] = str()
        current_data['target_url'] = None
        current_data['name'] = item_data.get('name')
        current_data['target_url_item_name'] = item.text(0)
        current_data['description'] = item_data.get('description')

        if item_type == 'project':
            review_url = '{}{}'.format(path.project_url, item_data.get('id'))
            logger.info("in  item_type == 'project'")

        elif item_type == 'review': # and not item_data.get('reviewURL'):
            current_data['review_id'] = item_data.get('id')
            current_data['target_url'] = '{0}{1}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
            logger.info("in  item_type == 'review'")

        elif item_type == 'media':
            parent_item = item.parent()
            parent_data = parent_item.data(1, QtCore.Qt.EditRole)
            current_data['review_id'] = parent_data.get('id')
            current_data['media_id'] = item_data.get('id')
            # * Expected url links
            #https://syncsketch.com/sketch/300639#692936
            #https://www.syncsketch.com/sketch/5a8d634c8447#692936/619482
            #current_data['target_url'] = '{}#{}'.format(review_base_url + str(current_data['review_id']), current_data['media_id'])
            current_data['target_url'] = '{0}{1}#{2}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
            logger.info("current_data['target_url'] {}".format(current_data['target_url']))


        while item.parent():
            logger.info("item.parent() {}".format(item))
            current_data['breadcrumb'] = ' > '.join([item.text(0), current_data['upload_to_value']])
            item = item.parent()

        if current_data['breadcrumb'].split(' > ')[-1] == '':
            current_data['breadcrumb'] = current_data['upload_to_value'].rsplit(' > ', 1)[0]

        logger.info("upload_to_value :{} ".format(current_data['upload_to_value']))

        return current_data

    def clear(self):
        logger.info("Clear Browser Widget")
        self.browser_treeWidget.clear()
        self.target_lineEdit.clear()
        self.thumbnail_itemPreview.clear()

