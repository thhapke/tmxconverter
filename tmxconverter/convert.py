import xml.etree.ElementTree as ET
from os import path, listdir
from _datetime import datetime
import csv

import yaml


from tmxconverter.save2files import save_file
from tmxconverter.save2hdb import save_db

###
# configuration
###
with open('config.yaml') as yamls :
    params = yaml.safe_load(yamls)

# directories
input_folder = params['input_folder']
if params['OUTPUT_FILES'] :
    output_folder = params['OUTPUT_FOLDER']
lang_map_file = params['lang_map_file']

# language mapping file
langmapcodes = dict()
with open(lang_map_file) as filename :
    for line in csv.reader(filename):
        langmapcodes[line[0]] = line[1]

# db config
db = {'host':params['HDB_HOST'],
      'user':params['HDB_USER'],
      'pwd':params['HDB_PWD'],
      'port':params['HDB_PORT']}

# files to be processed
tmxfiles = listdir(input_folder)

# test parameters
if params['TEST'] :
    exclusive_file = params['EXCLUSIVE_FILE']
    #exclusive_filename = None
    max_number_files = params['MAX_NUMBER_FILES']
    if exclusive_file :
        max_number_files = 0
max_number_files = len(tmxfiles) if max_number_files == 0 else max_number_files


for i, filename in enumerate(tmxfiles):

    if params['TEST'] :
        # for development only
        if exclusive_file and not filename == exclusive_file:
            continue
        if i > max_number_files :
            break

    ###
    # tmx parsing
    ###
    # check suffix
    if  not filename.endswith('.tmx') :
        continue

    print('{}/{}: {}'.format(i,max_number_files, filename))
    tree = ET.parse(path.join(input_folder, filename))
    root = tree.getroot()
    if root.tag != 'tmx' :
        raise UserWarning('Root is not <tmx> tag for file: {}'.format(filename))
        continue

    domain = filename.split('_')[0]

    # header
    header = root.find('header')
    src_lang = langmapcodes[header.attrib['srclang']]

    # body
    tu_records = list()
    body = root.find('body')
    for tu in body :
        rec = dict()
        rec['creation_id'] =  tu.attrib.get('creationid')
        rec['change_id'] = tu.attrib.get('changeid')
        uc = tu.attrib.get('usagecount')
        rec['usage_count'] = None if uc == None else int(uc)
        rec['created'] = datetime.strptime(tu.attrib.get('creationdate'), '%Y%m%dT%H%M%SZ')
        rec['changed'] = datetime.strptime(tu.attrib.get('changedate'), '%Y%m%dT%H%M%SZ')
        rec['last_usage'] = datetime.strptime(tu.attrib.get('lastusagedate'), '%Y%m%dT%H%M%SZ')
        rec['origin'] = filename.split('.')[0]
        rec['source_lang'] = src_lang
        rec['domain'] = domain

        tuvs = tu.findall("./tuv")
        for tl in tuvs :
            lang = langmapcodes[list(tl.attrib.values())[0]]
            segtext = tl.find('.seg').text
            if lang == src_lang :
                rec['source_text'] = segtext
            else :
                rec['target_text'] = segtext
                rec['target_lang']  = lang


        tu_records.append(rec)

    if  params['OUTPUT_FILES'] :
        csvfilename = filename.replace('.tmx', '.csv')
        outfile = path.join(output_folder,csvfilename)
        save_file(tu_records,outfile)

    if params['OUTPUT_HDB'] :
        save_db(tu_records,db)



