# coding=utf-8

import os
from tools import load_json_file
HTTP_PROXY = None

api_config_file = 'config/api_config.json'
if os.path.exists(api_config_file):
    api_config = load_json_file(api_config_file)
    if 'http_proxy' in api_config and api_config['http_proxy']:
        HTTP_PROXY = api_config['http_proxy']

