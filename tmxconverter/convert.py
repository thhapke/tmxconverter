import xml.etree.ElementTree as ET
from os import path, listdir
from _datetime import datetime
import csv
import re
import logging
from datetime import datetime, timedelta
from argparse import ArgumentParser

import yaml

from tmxconverter.save2files import save_file
from tmxconverter.save2hdb import save_db


def main() : # encapsulated into main otherwise entrypoint is not working
    ### Command line
    parser = ArgumentParser(description='Converts tmx-files')
    parser.add_argument('--log','-l',help='Setting logging level \'warning\' (default), \'info\', \'debug\'')
    args = parser.parse_args()
    loglevelmap = {'warning':logging.WARNING,'debug':logging.DEBUG,'info':logging.INFO}
    loglevel = logging.WARNING if args.log == None else loglevelmap[args.log]

    ### Logging
    logging.basicConfig(format='%(levelname)s: %(asctime)s %(message)s',level=loglevel)

    start_timestamp = datetime.now()
    logging.info('Conversion started: {}'.format(start_timestamp.strftime('%H:%M:%S%f')))

    ###
    # configuration
    ###
    logging.info('Open configuraion file {}'.format('config.yaml'))
    with open('config.yaml') as yamls :
        params = yaml.safe_load(yamls)

    # directories
    input_folder = params['input_folder']
    if params['OUTPUT_FILES'] :
        logging.info('CSV Files stored to: {}'.format(params['OUTPUT_FOLDER']))
        output_folder = params['OUTPUT_FOLDER']
    lang_map_file = params['lang_map_file']

    # language mapping file
    langmapcodes = dict()
    with open(lang_map_file) as filename :
        for line in csv.reader(filename):
            langmapcodes[line[0]] = line[1]

    # db config
    if params['OUTPUT_HDB'] :
        logging.info('Setting DB connection parameter.')
        db = {'host':params['HDB_HOST'],
              'user':params['HDB_USER'],
              'pwd':params['HDB_PWD'],
              'port':params['HDB_PORT']}

    # regex
    regex_pattern = list()
    regex_dropouts = list()
    if params['REGEX'] :
        logging.info('Reading regex pattern file {}'.format(params['INPUT_REGEX']))
        with open(params['INPUT_REGEX']) as file:
            while True :
                line = file.readline().rstrip('\n')
                if line :
                    regex_pattern.append(line)
                else :
                    break
            file.close()
        # clean log file
        with open(params['OUTPUT_REGEX_LOG'], 'w') as file:
            csvwriter = csv.writer(file)
            file.close()


    # files to be processed
    tmxfiles = listdir(input_folder)

    # test parameters
    if params['TEST'] :
        logging.info('Run in TEST-mode')
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

        logging.debug('Convert file: {}'.format(filename))
        domain = filename.split('_')[0]

        # header
        header = root.find('header')
        src_lang = langmapcodes[header.attrib['srclang']]

        # body
        tu_records = list()
        body = root.find('body')
        for tu in body :
            drop = False
            rec = dict()
            rec['creation_id'] =  tu.attrib.get('creationid')
            rec['change_id'] = tu.attrib.get('changeid')
            uc = tu.attrib.get('usagecount')
            rec['usage_count'] = None if uc == None else int(uc)
            created = tu.attrib.get('creationdate')
            rec['created'] = None if not created else datetime.strptime(created,'%Y%m%dT%H%M%SZ')
            changed = tu.attrib.get('changedate')
            rec['changed'] = None if not changed else datetime.strptime(changed, '%Y%m%dT%H%M%SZ')
            lastusage = tu.attrib.get('lastusagedate')
            rec['last_usage'] = None if not lastusage else datetime.strptime(lastusage, '%Y%m%dT%H%M%SZ')
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

                if not segtext :
                    drop = True
                elif params['REGEX'] :
                    for r in regex_pattern :
                        if re.match(r,segtext) :
                            drop = True
                            dropout = (filename,r,segtext)
                            regex_dropouts.append(dropout)

            if not drop :
                tu_records.append(rec)

        if  params['OUTPUT_FILES'] :
            csvfilename = filename.replace('.tmx', '.csv')
            outfile = path.join(output_folder,csvfilename)
            save_file(tu_records,outfile)
            logging.debug('TMX data save as csv-file: {}'.format(csvfilename))

        if params['OUTPUT_HDB'] :
            save_db(tu_records,db)
            logging.debug('TMX data saved in DB: {}'.format(filename))

        if params['REGEX'] :
            with open(params['OUTPUT_REGEX_LOG'],'a') as file :
                csvwriter = csv.writer(file)
                for line in regex_dropouts :
                    csvwriter.writerow(line)

        logging.debug('File processed: {}'.format(filename))

    # time calculation
    end_timestamp = datetime.now()
    duration = end_timestamp - start_timestamp

    logging.info('Conversion ended: {} (Time: {})'.format(end_timestamp,str(duration)))


if __name__ == '__main__':
    main()


