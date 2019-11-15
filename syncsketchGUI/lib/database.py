import codecs
import os
import yaml
import logging
import logging
logger = logging.getLogger("syncsketchGUI")
from syncsketchGUI.lib import path

# ======================================================================
# Global Variables

CACHE_YAML = 'syncsketch_cache.yaml'

# ======================================================================
# Module Utilities

def _parse_yaml(yaml_file = CACHE_YAML):
    '''
    Parse the given yaml file
    '''
    if not yaml_file:
        _show_error('Please provide valid yaml file.')
        return

    # cache_file = path.get_config_yaml(yaml_file)
    if not os.path.isfile(yaml_file):
        raise RuntimeError('Please provide valid yaml file.')

    with open(yaml_file, 'r') as stream:
        data = yaml.load(stream)

    return data


# ======================================================================
# Module Classes


def dump_cache(data, yaml_file = CACHE_YAML):
    '''
    Dump a dictionary data into the yaml_file
    '''

    cache_file = path.get_config_yaml(yaml_file)

    parsed_data = dict()
    if os.path.isfile(cache_file):
        parsed_data = _parse_yaml(cache_file)

    if not(isinstance(data, dict) or data == 'clear'):
        return

    if data == 'clear':
        logger.info( 'should clear')
        with codecs.open(cache_file, 'w', encoding = 'utf-8') as f_out:
            yaml.safe_dump(dict(), f_out, default_flow_style = False)
        return

    if parsed_data:
        parsed_data.update(data)
        data = parsed_data

    with codecs.open(cache_file, 'w', encoding = 'utf-8') as f_out:
        yaml.safe_dump(data, f_out, default_flow_style = False)


def rename_key_in_cache(old_key, new_key, yaml_file = CACHE_YAML):
    '''
    Delete the key value pair from the yaml_file
    '''
    cache_file = path.get_config_yaml(yaml_file)

    if os.path.isfile(cache_file):
        parsed_data = _parse_yaml(cache_file)
    else:
        raise RuntimeError('Please provide valid yaml file.')

    if not parsed_data:
        return

    if new_key in parsed_data.keys():
        return
        # raise RuntimeError('Key %s already exists in cache'%new_key)

    parsed_data[new_key] = parsed_data.pop(old_key)
    dump_cache('clear', yaml_file)
    dump_cache(parsed_data, yaml_file)
    return new_key

def delete_key_from_cache(key, yaml_file = CACHE_YAML):
    '''
    Delete the key value pair from the yaml_file
    '''
    cache_file = path.get_config_yaml(yaml_file)
    if os.path.isfile(cache_file):
        parsed_data = _parse_yaml(cache_file)
    else:
        raise RuntimeError('Please provide valid yaml file.')

    if key in parsed_data:
        del parsed_data[key]
        dump_cache('clear', yaml_file)
        dump_cache(parsed_data, yaml_file)
        logger.info( "Deleted preset %s from %s"%(key, CACHE_YAML))


def read_cache(key, yaml_file = CACHE_YAML):
    '''
    Get the value of a key from the yaml_file
    '''
    cache_file = path.get_config_yaml(yaml_file)
    if os.path.isfile(cache_file):
        parsed_data = _parse_yaml(cache_file)
    else:
        raise RuntimeError('Could not read or find %s\nPlease provide valid yaml file.'%cache_file)

    if isinstance(parsed_data, dict):
        return parsed_data.get(key)

def save_cache(key, value, yaml_file = CACHE_YAML):
    '''
    Set the value of a key from the yaml_file
    '''
    data = {key : value}

    cache_file = path.get_config_yaml(yaml_file)

    parsed_data = dict()
    if os.path.isfile(cache_file):
        parsed_data = _parse_yaml(cache_file)

    if not isinstance(data, dict) or data == 'clear':
        return

    if parsed_data:
        parsed_data.update(data)
        data = parsed_data

    with codecs.open(cache_file, 'w', encoding = 'utf-8') as f_out:
        yaml.safe_dump(data, f_out, default_flow_style = False)


def save_last_recorded(data=[]):
    '''
    Set the last_recorded key and value
    '''

    dump_cache({'last_recorded': data})