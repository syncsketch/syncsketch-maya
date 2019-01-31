# -*- coding: UTF-8 -*-
# ======================================================================
# @Author   : SyncSketch LLC
# @Email    : dev@syncsketch.com
# @Version  : 1.0.0
# ======================================================================
import getpass
import os

from syncsketchGUI.vendor import yaml
import syncsketch
import requests

from syncsketchGUI.lib import database
from syncsketchGUI.lib import path

# ======================================================================
# Global Variables

yaml_file = 'syncsketch_user.yaml'

# ======================================================================
# Module Utilities

    
def _merge_dictionaries(*dictionaries):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result_dictionary = dict()
    for dictionary in dictionaries:
        result_dictionary.update(dictionary)
    return result_dictionary


def _set_to_yaml_user(key, value):
    '''
    Set the given dictionary to the user's local yaml file
    '''
    yaml_path = path.get_config_yaml(yaml_file)
    
    if not os.path.isfile(yaml_path):
        yaml_path = open(yaml_path, 'w')
    
    existing_data = dict()
    user_data = {str(key) : str(value)}
    
    if os.path.isfile(yaml_path):
        existing_data = database._parse_yaml(yaml_path)
    
    if existing_data:
        user_data = _merge_dictionaries(existing_data, user_data)
    
    with open(yaml_path, 'w') as outfile:
        new_data = yaml.dump(user_data, default_flow_style = False)
        outfile.write(new_data)
    
def _get_from_yaml_user(key):
    '''
    Get the given key's value from the user's local yaml file
    '''
    yaml_path = path.get_config_yaml(yaml_file)
    if not os.path.isfile(yaml_path):
        return
    
    user_data = database._parse_yaml(yaml_path)
    return user_data.get(key)



def _upload_to_playground(filepath, user_email = ''):
    files = {'file': open(filepath, 'rb')}
    print "Uploading %s for user %s"%(files,user_email)
    response = requests.post(path.playground_url,
                              files = files,
                              data = {'userEmail' : user_email,
                                        "creator": user_email,
                                        'noConvertFlag' : no_convert})

    # for k, v in response.__dict__.items():
    #     print k.ljust(10), ':', v

    return response.json()


def download_file(url, fileName):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(fileName, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() if it works well without flush leave it...
    return fileName


# ======================================================================
# Module Classes

class SyncSketchUser():
    '''
    Class to store all user data
    '''
    # Class Variables
    name        = None
    os_user     = None
    api_key     = None
    password    = None
    host_data   = None
    token       = None

    api_host    = path.api_host_url

    # Set Functions
    def set_name(self, name):
        self.name = name
        _set_to_yaml_user('username', self.name)

    def set_os_user(self):
        self.os_user = getpass.getuser()
        _set_to_yaml_user('os_user', self.os_user)

    # Set Functions
    def set_token(self, token):
        self.token = token
        _set_to_yaml_user('token', self.token)

    def set_api_key(self, api_key):
        self.api_key = api_key
        _set_to_yaml_user('api_key', self.api_key)

    def set_password(self, password):
        self.password = password
        _set_to_yaml_user('password', self.password)

    # Get Functions
    def get_name(self):
        self.name = _get_from_yaml_user('username')
        return self.name

    def get_os_user(self):
        self.os_user = _get_from_yaml_user('os_user')
        return self.os_user

    def get_api_key(self):
        self.api_key = _get_from_yaml_user('api_key')
        return self.api_key

    def get_token(self):
        self.token = _get_from_yaml_user('token')
        return self.token

    def get_password(self):
        self.password = _get_from_yaml_user('password')
        return self.password

    # Auto Login
    def auto_login(self):
        # print " doing autologin: %s"%self.api_host
        if not self.host_data:
            self.host_data = syncsketch.SyncSketchAPI(self.get_name(),
                                                       self.get_api_key(),
                                                       useExpiringToken=True,
                                                       host = self.api_host,
                                                       debug=True)

    def is_logged_in(self):
        if self.get_name() and self.get_token():
            return True
        else:
            return False


    def logout(self):

        r = requests.get('%s/app/logmeout/' %(self.api_host))
        result = r.text

        # resetting the yaml file
        self.set_name('')
        self.set_api_key('')
        self.set_token('')


    def get_account_data(self, match_user_with_os = False):
        self.auto_login()

        if not self.host_data:
            print 'Please login first.'
            return


        if match_user_with_os and not self.get_os_user() == getpass.getuser():
            print 'Please login first.'
            return


        account_data = dict()
        account_data['projects'] = list()
        account_data['reviews'] = list()
        account_data['media'] = list()


        tree_data = self.host_data.getTree(withItems = True)

        return tree_data

        if not tree_data:
            print 'Fail to obtain tree data from the server.'
            return

        for tree in tree_data:
            projects = tree.get('projects')
            account_data['projects'] = projects

            for project in projects:
                reviews = project.get('reviews')
                account_data['reviews'] = reviews

                for review in reviews:
                    items = review.get('items')
                    account_data['media'] = items

        return account_data

    def get_review_data_from_id(self, review_id):
        self.auto_login()
        review_data = self.host_data.getReviewById(review_id)
        return review_data


    def get_media_data_from_id(self, media_id):
        self.auto_login()
        media_data = self.host_data.getAnnotations(media_id)
        return media_data

    def get_item_info(self, media_id):
        '''
        Get the item / media info
        '''
        self.auto_login()
        if not self.host_data:
            print 'Please login first.'
            return
        return self.host_data.getMedia({'id': media_id})


    def upload_media_to_review(self, review_id, filepath, noConvertFlag = False, itemParentId = False, data={}):
        if review_id == 'playground':
            return _upload_to_playground(filepath, user_email)

        self.auto_login()
        if not self.host_data:
            print 'Please login first.'
            return

        uploaded_item = self.host_data.addMedia(review_id, filepath, noConvertFlag = noConvertFlag, itemParentId = itemParentId)
        uploaded_item = self.host_data.updateItem(uploaded_item["id"], data )
        return uploaded_item

    def update_item(self, item_id, filepath, data = None):
        files = {'reviewFile': open(filepath)}
        if data:
            data.update(files)
        else:
            data = files

        self.auto_login()
        if not self.host_data:
            print 'Please login first.'
            return

        return self.host_data.updateItem(item_id, data)

    # Todo set path properly
    def download_greasepencil(self, reviewId, itemId, filepath = '/Users/bern/Downloads/sycnsketch.greasepencil.zip'):

        # currently we bail if user is using playground or is
        # not logged in
        """
            Download overlay sketches for Maya Greasepencil. Function will download a zip file which contains
            an XML and the sketches as png files. Maya can load the zip file to overlay the sketches over the 3D model!

            For more information visit:
            https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2015/ENU/Maya/files/Grease-Pencil-Tool-htm.html
        :param reviewId:
        :param itemId:
        :return: filePath to the zip file with the greasePencil data. PLEASE make sure that /tmp is writable
        """

        if reviewId == 'playground':
            print "No greasepencil download from playground(yet)"
            return

        self.auto_login()
        if not self.host_data:
            print 'Please login first.'
            return

        return self.host_data.getGreasePencilOverlays(reviewId, itemId, local_filename=filepath)




# ======================================================================
# Module Functions

def upload_to_playground(filepath, user_email):
    uploaded_media_url = _upload_to_playground(filepath, user_email)
    return uploaded_media_url

