import xml.etree.ElementTree as ET
from os import path, listdir
from _datetime import datetime
import csv
import re
import logging
from datetime import datetime, timedelta
from argparse import ArgumentParser
import pandas as pd

import yaml

from Lxconverter.save2files import save_file
from Lxconverter.save2hdb import save_db
from Lxconverter.readfiles import read_regex, read_language_code_mapping



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


    # language mapping file
    langmapcodes = read_language_code_mapping(params['lang_map_file'])

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
        regex_pattern = read_regex(params['INPUT_REGEX'],params['OUTPUT_REGEX_LOG'])

    # files to be processed
    files = listdir(params['ABAP_INPUT_FOLDER'])

    # test parameters
    max_number_files = 0
    if params['TEST'] :
        logging.info('Run in TEST-mode')
        exclusive_file = params['EXCLUSIVE_FILE']
        #exclusive_filename = None
        max_number_files = params['MAX_NUMBER_FILES']
        if exclusive_file :
            max_number_files = 0
    max_number_files = len(files) if max_number_files == 0 or max_number_files > len(files)  else max_number_files

    all_records = 0
    for i, filename in enumerate(files):

        if params['TEST'] :
            # for development only
            if exclusive_file and not filename == exclusive_file:
                continue
            if i > max_number_files :
                break

        df = pd.read_csv(filename)



        if params['OUTPUT_HDB'] :
            save_db(tu_elements,db)
            logging.info('TMX data saved in DB: {}'.format(filename))

        if params['REGEX'] :
            with open(params['OUTPUT_REGEX_LOG'],'a') as file :
                csvwriter = csv.writer(file)
                for line in regex_dropouts :
                    csvwriter.writerow(line)


    # time calculation
    end_timestamp = datetime.now()
    duration = end_timestamp - start_timestamp

    logging.info('Number of all records: {}'.format(all_records))
    logging.info('Conversion ended: {} (Time: {})'.format(end_timestamp,str(duration)))


if __name__ == '__main__':
    main()


