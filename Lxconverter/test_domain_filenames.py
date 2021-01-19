
import logging
from os import path, listdir
import re

import yaml

from Lxconverter.readfiles import read_regex, read_code_mapping

###
# configuration
###
logging.info('Open configuraion file {}'.format('config.yaml'))
with open('config.yaml') as yamls:
    params = yaml.safe_load(yamls)

# directories
input_folder = params['TMX_INPUT_FOLDER']

tmxfiles = listdir(input_folder)
domains = list()

for f in tmxfiles :
    domains.append(re.search("(.+)_\w{4}_\w{4}\.tmx$",f).group(1))

# domain mapping file
domainmapcodes = read_code_mapping(params['DOMAIN_CODE_MAPPING'])

for d in domains :
    print('{} -> {}'.format(d,domainmapcodes[d]))