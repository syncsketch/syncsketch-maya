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
        self.populateTree()

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
        self.browser_treeWidget.currentItemChanged.connect(self.validate_review_url)
        self.browser_treeWidget.currentItemChanged.connect(self.currentItemChanged)
        self.browser_treeWidget.doubleClicked.connect(self.open_upload_to_url)

        # Videos / Playblast Settings
        self.target_lineEdit.editingFinished.connect(self.select_item_from_target_input)


        self.browser_treeWidget.itemExpanded.connect(self.expandedTest)
        self.browser_treeWidget.header().sectionClicked.connect(self.refresh)

                # Videos / Upload Settings
        self.ui_open_pushButton.clicked.connect(self.open_upload_to_url)
        self.ui_copyURL_pushButton.clicked.connect(self.copy_to_clipboard)
        
        self.ui_download_pushButton.clicked.connect(self.download)

    @QtCore.Slot(str)
    def update_upload(self, url):
        logger.debug('Update Upload Slot triggered with URL [{}]'.format(url))
        self.update_target_from_upload(url)

    def download(self):
        logger.info("Download pressed")
        self.validate_review_url()
        show_download_window()
        return



    def refresh(self):
        logger.info("Refresh Clicked, trying to refresh if logged in")
        #self.populate_review_panel(self, force=True)
        #self.asyncPopulateTree(withItems=False)
        self.populateTree()
        #self.repaint()
    
    def populateTree(self):
        #Only called at the beginning of a sessions
        self.current_user = user.SyncSketchUser()
        if not self.current_user.is_logged_in():
            logger.info("User not logged in, returning")
            return

        logger.info("Trying to fetch data and co")
        #self.fetchData(user=self.current_user)
        self.accountData = self.current_user.get_account_data(withItems=False)

        self.populateReviewPanel()
        # * those two next commands might be switched
        self.loadLeafs()
        self.populateReviewItems()
    

    def populateReviewPanel(self):
        self.browser_treeWidget.clear()
        if self.accountData:
            self.populate_review_panel(self.accountData, force=True)
        else:
            logger.warning("No Accountdata found")
        
    def populate_review_panel(self, account_data=None, item_to_add = None, force = False):
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

        logger.info("uploaded_to_value: {}".format(database.read_cache('upload_to_value')))
        url_payload = parse_url_data(database.read_cache('upload_to_value')) #FIXME
        logger.info("url_payload: {}".format(url_payload))
        get_current_item_from_ids(self.browser_treeWidget, url_payload, setCurrentItem=True) #FIXME

        USER_ACCOUNT_DATA = account_data #FIXME

        self.populate_upload_settings()
        return account_data
    
    def update_target_from_upload(self, uploaded_media_url):
        logger.info("update_target_from_upload uploaded_media_url: {}".format(uploaded_media_url))
        if 'none' in uploaded_media_url.lower():
            uploaded_media_url = str()

        logger.info('Uploaded_media_url: %s'%uploaded_media_url)
        database.dump_cache({'us_last_upload_url_pushButton' : uploaded_media_url})
        self.target_lineEdit.setText(uploaded_media_url)
        logger.info("target_lineEdit.setText {}".format(uploaded_media_url))

        self.select_item_from_target_input()
        #getReviewById(self.ui.browser_treeWidget, reviewId=reviewId)
        #self.ui.us_last_upload_url_pushButton.setText(uploaded_media_url)

        database.dump_cache({'upload_to_value' : uploaded_media_url})
        # todo this shouldn't be abstracted
        #self.refresh()
    
    def populate_upload_settings(self):
        if database.read_cache('target_url_type') not in ['account', 'project']:
            #todo yafes
            pass
            #self.ui.target_lineEdit.setText(database.read_cache('upload_to_value'))
            logger.info("database.read_cache('target_url_type') not in ['account', 'project']".format())
        else:
            self.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)
            self.target_lineEdit.setText(None)
            logger.info("target_lineEdit.setText: NONE".format())
        self.validate_review_url()
        # self.ui.us_name_lineEdit.setText(database.read_cache('target_url_type'))
        # self.ui.us_artist_lineEdit.setText(database.read_cache('target_url_username'))
        # self.ui.us_upload_to_pushButton.setText(database.read_cache('upload_to_value'))
    
    def currentItemChanged(self):
        pass


    def open_upload_to_url(self):
        self.validate_review_url()
        url = path.make_url_offlineMode(database.read_cache('upload_to_value')) #FIXME
        logger.info("Opening Url: {} ".format(url))
        if url:
            webbrowser.open(url)
    
    # FIXME: where needed ?
    def open_target_url(self):
        url = self.sanitize(self.target_lineEdit.text())
        if url:
            webbrowser.open(path.make_url_offlineMode(url))
        
    def copy_to_clipboard(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        link =  self.target_lineEdit.text()
        # link = database.read_cache('us_last_upload_url_pushButton')
        cb.setText(link, mode=cb.Clipboard)
    

    def select_item_from_target_input(self, event=None):
        link = self.sanitize(self.target_lineEdit.text())
        logger.info("Got Link from lineEdit: {}".format(link))

        if not link:
            link = database.read_cache('upload_to_value')
            logger.info("No link, reading from cache: {} ".format(link))
        #ids = get_ids_from_link(link)
        url_payload = parse_url_data(link)  #FIXME
        logger.info("url_payload: {} ".format(url_payload))


        currentItem = get_current_item_from_ids(self.browser_treeWidget, url_payload, setCurrentItem=True) #FIXME
        logger.info("current Item: {}".format(currentItem))

        if not currentItem:
            logger.info("Reviewitem does not exist, trying to load review and it's items{}".format(url_payload))

            iterator = QtWidgets.QTreeWidgetItemIterator(self.browser_treeWidget, QtWidgets.QTreeWidgetItemIterator.All)

            while iterator.value():
                item = iterator.value()
                item_data = item.data(1, QtCore.Qt.EditRole)
                if item_data.get('uuid') == url_payload['uuid']:
                    logger.info("Found review with item_data: {} loading reviewItems ...".format(item_data))
                    #self.ui.browser_treeWidget.setCurrentItem(item, 1)
                    #self.ui.browser_treeWidget.scrollToItem(item)
                    self.loadLeafs(item)
                    break
                iterator +=1
            currentItem = get_current_item_from_ids(self.browser_treeWidget, url_payload, setCurrentItem=True)
    

    # todo: remove last line call to remove sideffect
    def loadLeafs(self, target=None):
        '''
        '''
        if not target:
            logger.info("No Target")
            reviewId = database.read_cache('target_review_id')
            if reviewId:
                logger.info("Restoring reviewId section for : {} ".format(reviewId))
                target = getReviewById(self.browser_treeWidget, reviewId=reviewId) #FIXME
            else:
                return

        logger.info("target: {} target name: {}".format(type(target), target.text(0)))

        selected_item = target
        review = selected_item.data(1, QtCore.Qt.EditRole)
        item_type = selected_item.data(2, QtCore.Qt.EditRole)


        if item_type == "review":
            current_user = user.SyncSketchUser()
            current_user.auto_login()
            if not current_user.is_logged_in():
                return

            self.review = review
            self.reviewData = self.load_leafs(user=current_user, reviewId=review['id'])[0]
            logger.info("review['id']: {} reviewData: {}".format(review['id'], self.reviewData))
            self.mediaItemParent = target
            self.populateReviewItems()
    
    def load_leafs(self, user, reviewId=None):
        items = user.host_data.getMediaByReviewId(reviewId)['objects']
        return (items, reviewId)

    def sanitize(self, val):
        return val.rstrip().lstrip()
    

    # * double check last item selected, looks like after this func, it stopped
    def expandedTest(self, target):

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
                self.loadLeafs(item)
        else:
            logger.info("Not a review, nothing to expand")

            #User keeps pressing expand, so let's reload
            # * consolidate


            #item.setSelected(True)


    def populateReviewItems(self):
        items = self.reviewData
        if not self.mediaItemParent:
            logger.info("No Review Item parent, returning")
            return
        self.mediaItemParent.takeChildren()
        logger.info("takeChildren and populating reviewItems {} ".format(items))

        for media in items or []:
            #add UUID of the review container to the media, so we can use it in itemdata
            media['uuid'] = self.review['uuid']
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

            media_treeWidgetItem = self._build_widget_item(parent = self.mediaItemParent,
                                                        item_name = media.get('name'),
                                                        item_type='media',
                                                        item_icon = specified_media_icon,
                                                        item_data = media)

            media_treeWidgetItem.sizeHint(80)
            # * this is an obsolute call
            #set_tree_selection(self.ui.browser_treeWidget, None)

            #Make sure we select the last uploaded item
        if database.read_cache("upload_to_value"):
            logger.info("true upload_to_value: {}".format(database.read_cache("upload_to_value")))
            #logger.info("upload_to_value is set, updating lineEdit")
            self.target_lineEdit.setText(database.read_cache("upload_to_value"))
            self.select_item_from_target_input() #FIXME circular dependency
        else:
            logger.info("Nothing to set in the lineedit")
            logger.info('false upload_to_value')


    def _build_widget_item(self, parent, item_name, item_type, item_icon, item_data):
        treewidget_item = QtWidgets.QTreeWidgetItem(parent, [item_name])
        treewidget_item.setData(1, QtCore.Qt.EditRole, item_data)
        treewidget_item.setData(2, QtCore.Qt.EditRole, item_type)
        treewidget_item.setIcon(0, item_icon)
        return treewidget_item

    #FIXME: needed?
    def storeReviewData(self, s):
        logger.info("storereviewData {}".format(s[0]))
        logger.info("storereviewData {}".format(s[1]))
        self.reviewData = s[0]
    
        # todo refactor: this function does more than validation
    def validate_review_url(self, target = None):
        # self.populate_upload_settings()
        logger.info("Current Item changed")
        targetdata = self.update_target_from_tree(self.browser_treeWidget)
        #todo: don't do that, that's very slow put this in the caching at the beginning
        #if target:
        #    logger.warning(self.current_user.get_review_data_from_id(targetdata['review_id']))
        #{'target_url_type': u'media', 'media_id': 692936, 'review_id': 300639, 'breadcrumb': '', 'target_url': 'https://syncsketch.com/sketch/300639#692936', 'upload_to_value': '', 'name': u'playblast'}
        self.target_lineEdit.setText(database.read_cache('upload_to_value'))
        logger.info("target_lineEdit.setText validate_review_url: upload_to_value {}".format(database.read_cache('upload_to_value')))
        if target or targetdata:
            target = targetdata['target_url_type']

        ui_to_toggle = [
            self.ui_download_pushButton,
            self.ui_copyURL_pushButton,
            self.ui_reviewSelection_hBoxLayout
        ]

        #todo remove sideffect
        if (target == "review") or (target == "media"):
            enable_interface(ui_to_toggle, True)
        else:
            enable_interface(ui_to_toggle, False)
            self.target_lineEdit.setPlaceholderText(uploadPlaceHolderStr)

        if target == "media":
            thumbURL = self.current_user.get_item_info(targetdata['media_id'])['objects'][0]['thumbnail_url']
            logger.info("thumbURL: {}".format(thumbURL))
            self.thumbnail_itemPreview.set_icon_from_url(thumbURL)


        self.target_changed.emit(targetdata)
    

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
            self.thumbnail_itemPreview.clear()
            logger.info("in  item_type == 'project'")

        elif item_type == 'review': # and not item_data.get('reviewURL'):
            current_data['review_id'] = item_data.get('id')
            current_data['target_url'] = '{0}{1}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
            self.thumbnail_itemPreview.clear()
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


