import logging
import webbrowser
import re

from ..path import get_syncsketch_url, parse_url_data

logger = logging.getLogger("syncsketchGUI")

from syncsketchGUI.vendor.Qt import QtCore, QtGui, QtWidgets
from syncsketchGUI.lib import video, user, database, path
from syncsketchGUI.literals import uploadPlaceHolderStr

from syncsketchGUI import actions

from . import qt_regulars
from . import qt_presets
from . import qt_utils

# FIXME
USER_ACCOUNT_DATA = None


class ReviewBrowserWidget(QtWidgets.QWidget):
    title = "ReviewBrowser"
    target_changed = QtCore.Signal(dict)  # dict: target_data

    def __init__(self, *args, **kwargs):
        super(ReviewBrowserWidget, self).__init__(*args, **kwargs)

        self.reviewData = None
        self.mediaItemParent = None

        self._is_logged_in = False
        self._cache_user()

        self._create_ui()
        self._layout_ui()
        self._build_connections()
        self._populate_tree()
        self._restore_ui_state()
        self._update_thumbnail()
        self._update_pb_download()

    def refresh(self):
        logger.info("Refresh Clicked, trying to refresh if logged in")
        self._cache_user()
        if self._is_logged_in:
            self._populate_tree()
            self._update_target_from_cache()
        else:
            self._clear()

        self._update_pb_download()
        self._update_thumbnail()

    def update_target_from_url(self, url):
        url = self._sanitize(url)

        url_payload = parse_url_data(url)  # FIXME
        logger.debug("url_payload: {} ".format(url_payload))

        if not url_payload:
            return

        media_item = get_current_item_from_ids(self._tree, url_payload)  # FIXME

        if not media_item:

            logger.debug("Cant find Media Item. Try to find Review Item and repopulate, then try again.")

            review_url_payload = {
                "uuid": url_payload["uuid"],
                "id": None,
            }

            review_item = get_current_item_from_ids(self._tree, review_url_payload)

            if not review_item:
                logger.warning("Cant find Media and Review Item with payload: {}".format(url_payload))
                return
            else:
                logger.debug("Found Review Item: {}".format(review_item))

            self._populate_review_item(review_item)

            media_item = get_current_item_from_ids(self._tree, url_payload)

        self._tree.setCurrentItem(media_item, 1)
        self._tree.scrollToItem(media_item)
        logger.debug("Selected Media Item: {}".format(media_item))

    def _cache_user(self):
        self.current_user = user.SyncSketchUser()
        if self.current_user.is_logged_in():
            self._is_logged_in = True
        else:
            self._is_logged_in = False
        logger.debug("Cache login status for user: {}".format(self._is_logged_in))

    def _clear(self):
        logger.debug("Clear Browser Widget")
        self._tree.clear()
        self._ui_line_target.clear()
        self._ui_thumbnail_item_preview.clear()

    def _create_ui(self):

        self._tree = self._create_tree()
        self._ui_line_target = qt_regulars.LineEdit()
        self._ui_pb_open_url = qt_regulars.ToolButton(self, qt_presets.open_icon)
        self._ui_pb_copy_url = qt_regulars.ToolButton(self, qt_presets.copy_icon)
        self._ui_thumbnail_item_preview = qt_regulars.Thumbnail(width=320, height=180)
        self._ui_pb_download = self._create_pb_download()

    def _layout_ui(self):

        lay_hbox_review_sel = QtWidgets.QHBoxLayout()
        lay_hbox_review_sel.addWidget(self._ui_line_target)
        lay_hbox_review_sel.addWidget(self._ui_pb_open_url)
        lay_hbox_review_sel.addWidget(self._ui_pb_copy_url)

        lay_vbox_tree = QtWidgets.QVBoxLayout()
        lay_vbox_tree.addWidget(self._tree)
        lay_vbox_tree.addLayout(lay_hbox_review_sel)
        lay_vbox_tree.addWidget(self._ui_thumbnail_item_preview)
        lay_vbox_tree.addWidget(self._ui_pb_download, 10)

        lay_groupbox = QtWidgets.QGroupBox()
        lay_groupbox.setTitle('TARGET FOR UPLOAD')
        lay_groupbox.setLayout(lay_vbox_tree)

        lay_main = QtWidgets.QVBoxLayout()
        lay_main.setSpacing(3)
        lay_main.addWidget(lay_groupbox)

        self.setLayout(lay_main)

    def _build_connections(self):

        # tree widget functions
        self._tree.currentItemChanged.connect(self._update_target_from_item_callback)

        self._tree.doubleClicked.connect(self._open_url_callback)

        # Videos / Playblast Settings
        self._ui_line_target.textEdited.connect(self.update_target_from_url)

        self._tree.itemExpanded.connect(self._expand_item_callback)
        self._tree.header().sectionClicked.connect(self.refresh)

        # Videos / Upload Settings
        self._ui_pb_open_url.clicked.connect(self._open_url_callback)
        self._ui_pb_copy_url.clicked.connect(self._copy_to_clipboard)

        self._ui_pb_download.clicked.connect(self._download_callback)

        self.target_changed.connect(self._update_ui_from_target_data)
        self.target_changed.connect(self._cache_target_data)

    def _create_tree(self):
        tree = QtWidgets.QTreeWidget()
        tree.header().setStyleSheet("color: %s" % qt_presets.success_color)
        highlight_palette = tree.palette()
        highlight_palette.setColor(QtGui.QPalette.Highlight, qt_presets.highlight_color)
        tree.setPalette(highlight_palette)
        tree.setHeaderLabel('refresh')
        tree.header().setSectionsClickable(True)
        tree.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
        tree.setSelectionMode(QtWidgets.QTreeWidget.SingleSelection)
        return tree

    def _create_pb_download(self):
        pb = qt_regulars.Button(self, icon=qt_presets.download_icon, color=qt_presets.download_color)
        pb.setToolTip('Download from SyncSketch Review Target')
        pb.setText("DOWNLOAD")
        return pb

    def _restore_ui_state(self):
        if self._is_logged_in:
            self._update_target_from_cache()

    def _populate_tree(self, account_data=None, item_to_add=None, force=False):

        if not self._is_logged_in:
            logger.info("User not logged in, returning")
            return

        self._tree.clear()

        account_data = self.current_user.get_account_data(withItems=False)

        if not account_data:
            logger.warning("No account_data found")
            return

        logger.debug("account_data: {}".format(account_data))
        for account in account_data:
            account_treeWidgetItem = self._build_widget_item(parent=self._tree,
                                                             item_name=account.get('name'),
                                                             item_type='account',
                                                             item_icon=qt_presets.account_icon,
                                                             item_data=account)
            # Add projects
            projects = account.get('projects')
            for project in projects:
                project_treeWidgetItem = self._build_widget_item(parent=account_treeWidgetItem,
                                                                 item_name=project.get('name'),
                                                                 item_type='project',
                                                                 item_icon=qt_presets.project_icon,
                                                                 item_data=project)
                # Add reviews
                reviews = project.get('reviews')

                for review in reviews:
                    review_treeWidgetItem = self._build_widget_item(parent=project_treeWidgetItem,
                                                                    item_name=review.get('name'),
                                                                    item_type='review',
                                                                    item_icon=qt_presets.review_icon,
                                                                    item_data=review)
                    # Add items
                    items = review.get('items')
                    # * If there are no reviews, create still a dumy element to get an arrow icon
                    # * to visualize that the item needs to be expanded
                    for media in items or [{'uuid': '', 'type': 'video'}]:
                        # add UUID of the review container to the media, so we can use it in itemdata
                        media['uuid'] = review['uuid']
                        if not media.get('type'):
                            specified_media_icon = qt_presets.media_unknown_icon
                        elif 'video' in media.get('type').lower():
                            specified_media_icon = qt_presets.media_video_icon
                        elif 'image' in media.get('type').lower():
                            specified_media_icon = qt_presets.media_image_icon
                        elif 'sketchfab' in media.get('type').lower():
                            specified_media_icon = qt_presets.media_sketchfab_icon
                        else:
                            specified_media_icon = qt_presets.media_unknown_icon

                        media_treeWidgetItem = self._build_widget_item(parent=review_treeWidgetItem,
                                                                       item_name=media.get('name'),
                                                                       item_type='media',
                                                                       item_icon=specified_media_icon,
                                                                       item_data=media)

                        media_treeWidgetItem.sizeHint(80)

    def _populate_review_item(self, review_item):

        if not self._is_logged_in:
            return

        review = review_item.data(1, QtCore.Qt.EditRole)

        review_id = review['id']
        items = self.current_user.host_data.getMediaByReviewId(review_id)['objects']

        # Removes current child items
        review_item.takeChildren()

        for media in items:
            # add UUID of the review container to the media, so we can use it in itemdata
            media['uuid'] = review['uuid']
            if not media.get('type'):
                specified_media_icon = qt_presets.media_unknown_icon
            elif 'video' in media.get('type').lower():
                specified_media_icon = qt_presets.media_video_icon
            elif 'image' in media.get('type').lower():
                specified_media_icon = qt_presets.media_image_icon
            elif 'sketchfab' in media.get('type').lower():
                specified_media_icon = qt_presets.media_sketchfab_icon
            else:
                specified_media_icon = qt_presets.media_unknown_icon

            media_treeWidgetItem = self._build_widget_item(parent=review_item,
                                                           item_name=media.get('name'),
                                                           item_type='media',
                                                           item_icon=specified_media_icon,
                                                           item_data=media)

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

        logger.debug("Expanding treewidget: {}".format(target))
        selected_item = target
        # convert qmodelindex into a treewidget item
        item = target  # self.ui.browser_treeWidget.itemFromIndex(selected_item)
        try:
            logger.debug("item.text {} selected_item {}".format(item.data(0, QtCore.Qt.EditRole),
                                                                item.data(1, QtCore.Qt.EditRole)))
        except Exception as e:
            logger.debug("Exception: ".format(e))

        item_type = item.data(2, QtCore.Qt.EditRole)
        if item_type == "review":
            logger.debug("item_type is a review, expanding")
            if item.childCount() == 1 and not item.child(0).data(0, QtCore.Qt.EditRole):
                logger.debug("Only single empty dummy item, delete and load childs")
                item.takeChildren()
                self._populate_review_item(item)
        else:
            logger.debug("Not a review, nothing to expand")

            # User keeps pressing expand, so let's reload
            # * consolidate

            # item.setSelected(True)

    def _update_target_from_item_callback(self, current_item, previous_item):
        logger.debug("Browser Target changed. Signal emitted.")
        target_data = self._get_target_data(current_item)
        self.target_changed.emit(target_data)

    def _update_ui_from_target_data(self, target_data):

        target_url = target_data["target_url"]
        self._ui_line_target.setText(target_url)
        logger.debug("Set target_lineEdit to {}".format(target_url))

        ui_to_toggle = [
            self._ui_pb_copy_url,
        ]

        target_type = target_data['target_url_type']

        if (target_type == "review") or (target_type == "media"):
            qt_utils.enable_interface(ui_to_toggle, True)
        else:
            qt_utils.enable_interface(ui_to_toggle, False)
            self._ui_line_target.setPlaceholderText(uploadPlaceHolderStr)

        self._update_pb_download()
        self._update_thumbnail()

    def _update_thumbnail(self):
        current_item = self._tree.currentItem()

        if not current_item:
            self._ui_thumbnail_item_preview.clear()
            return

        item_data = self._get_target_data(current_item)
        target_type = item_data['target_url_type']

        if target_type == "media":
            thumbURL = self.current_user.get_item_info(item_data['media_id'])['objects'][0]['thumbnail_url']
            logger.debug("thumbURL: {}".format(thumbURL))
            self._ui_thumbnail_item_preview.set_icon_from_url(thumbURL)

        else:
            self._ui_thumbnail_item_preview.clear()

    def _update_pb_download(self):

        if not self._is_logged_in:
            self._ui_pb_download.setEnabled(False)
            return

        current_item = self._tree.currentItem()
        if not current_item:
            self._ui_pb_download.setEnabled(False)
            return

        item_data = self._get_target_data(current_item)
        target_type = item_data['target_url_type']

        if (target_type == "media"):
            self._ui_pb_download.setEnabled(True)
        else:
            self._ui_pb_download.setEnabled(False)

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
        logger.debug("Download pressed")
        # self.validate_review_url()
        actions.show_download_window()
        return

    def _open_url_callback(self, selected_item=None):
        if not selected_item:
            selected_item = self._tree.currentItem()

        target_data = self._get_target_data(selected_item)
        offline_url = path.make_url_offlineMode(target_data["target_url"])
        logger.debug("Opening Url: {} ".format(offline_url))
        if offline_url:
            webbrowser.open(offline_url)

    def _sanitize(self, val):
        return val.rstrip().lstrip()

    def _copy_to_clipboard(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        link = self._ui_line_target.text()
        # link = database.read_cache('us_last_upload_url_pushButton')
        cb.setText(link, mode=cb.Clipboard)

    def _update_target_from_cache(self):
        link = database.read_cache('upload_to_value')
        if not link:
            logger.debug("Cache for 'upload_to_value' doesnt exist")
            return
        logger.debug("Update Target from URL: {} ".format(link))
        self.update_target_from_url(link)

    def _get_target_data(self, item):

        if not item:
            logger.info("Nothing selected returning")
            return
        else:
            item_data = item.data(1, QtCore.Qt.EditRole)
            item_type = item.data(2, QtCore.Qt.EditRole)
        logger.debug("get data for item: item_data {} item_type {}".format(item_data, item_type))

        review_base_url = "{}/sketch/".format(get_syncsketch_url())
        current_data = {
            'upload_to_value': str(),
            'breadcrumb': str(),
            'target_url_type': item_type,
            'review_id': str(),
            'media_id': str(),
            'target_url': None,
            'name': item_data.get('name'),
            'target_url_item_name': item.text(0),
            'description': item_data.get('description')
        }

        if item_type == 'project':
            review_url = '{}{}'.format(path.project_url, item_data.get('id'))
            logger.info("in  item_type == 'project'")

        elif item_type == 'review':  # and not item_data.get('reviewURL'):
            current_data['review_id'] = item_data.get('id')
            current_data['target_url'] = '{0}{1}'.format(review_base_url, item_data.get('uuid'), item_data.get('id'))
            logger.info("in  item_type == 'review'")

        elif item_type == 'media':
            parent_item = item.parent()
            parent_data = parent_item.data(1, QtCore.Qt.EditRole)
            current_data['review_id'] = parent_data.get('id')
            current_data['media_id'] = item_data.get('id')
            # * Expected url links
            # https://syncsketch.com/sketch/300639#692936
            # https://www.syncsketch.com/sketch/5a8d634c8447#692936/619482
            # current_data['target_url'] = '{}#{}'.format(review_base_url + str(current_data['review_id']), current_data['media_id'])
            current_data['target_url'] = '{0}{1}#{2}'.format(review_base_url, item_data.get('uuid'),
                                                             item_data.get('id'))
            logger.debug("current_data['target_url'] {}".format(current_data['target_url']))

        while item.parent():
            current_data['breadcrumb'] = ' > '.join([item.text(0), current_data['upload_to_value']])
            item = item.parent()

        if current_data['breadcrumb'].split(' > ')[-1] == '':
            current_data['breadcrumb'] = current_data['upload_to_value'].rsplit(' > ', 1)[0]

        logger.debug("upload_to_value :{} ".format(current_data['upload_to_value']))

        return current_data


def get_current_item_from_ids(tree, payload=None):
    logger.debug("payload: {}".format(payload))
    searchValue = ''
    searchType = ''

    if not payload:
        return

    # Got both uuid and id, we are dealing with an item
    if payload['uuid'] and payload['id']:
        searchType = 'id'
        searchValue = int(payload['id'])
        logger.debug("both payload['uuid'] and payload['id'] set {}".format(payload['uuid'], payload['id']))

    # Got only uuid, it's a review
    elif payload['uuid']:
        searchType = 'uuid'
        searchValue = payload['uuid']
        logger.debug("payload['uuid'] set: {}".format(payload['uuid']))

    # Nothing useful found return
    else:
        logger.debug("No uuid or id in payload, aborting")
        return

    iterator = QtWidgets.QTreeWidgetItemIterator(tree, QtWidgets.QTreeWidgetItemIterator.All)

    while iterator.value():
        item = iterator.value()
        item_data = item.data(1, QtCore.Qt.EditRole)
        if item_data.get(searchType) == searchValue:
            return item
        iterator += 1

    logger.info("Item not found while iterating")
