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
from tmxconverter.readfiles import read_regex, read_language_code_mapping, remedyxml



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
    tmxfiles = listdir(input_folder)

    # test parameters
    max_number_files = 0
    if params['TEST'] :
        logging.info('Run in TEST-mode')
        exclusive_file = params['EXCLUSIVE_FILE']
        #exclusive_filename = None
        max_number_files = params['MAX_NUMBER_FILES']
        if exclusive_file :
            max_number_files = 0
    max_number_files = len(tmxfiles) if max_number_files == 0 or max_number_files > len(tmxfiles)  else max_number_files

    all_records = 0
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

        logging.info('{}/{}: {}'.format(i+1,max_number_files, filename))

        tu_elements = []
        domain = filename.split('_')[0]
        drop = False
        src_lang = ''
        lang = ''
        rec = dict()


        context = iter(ET.iterparse(path.join(input_folder, filename),events=("start","end")))
        event, elem = next(context)
        tu_count = 0
        tu_count_drop = 0
        while not elem == None:
            if event == 'start':
                if elem.tag == 'tuv' :
                    lang = langmapcodes[list(elem.attrib.values())[0]]
                elif elem.tag == 'tu':
                    drop = False
                    rec = dict()  # new dict
                elif elem.tag == 'header':
                    src_lang = langmapcodes[elem.attrib['srclang']]
            elif event == 'end' :
                if elem.tag == 'tu' :
                    tu_count += 1
                    if not drop :  # If sth went wrong do not save elem
                        rec['creation_id'] = elem.attrib.get('creationid')
                        rec['change_id'] = elem.attrib.get('changeid')
                        uc = elem.attrib.get('usagecount')
                        rec['usage_count'] = None if uc == None else int(uc)
                        created = elem.attrib.get('creationdate')
                        rec['created'] = None if not created else datetime.strptime(created, '%Y%m%dT%H%M%SZ')
                        changed = elem.attrib.get('changedate')
                        rec['changed'] = None if not changed else datetime.strptime(changed, '%Y%m%dT%H%M%SZ')
                        lastusage = elem.attrib.get('lastusagedate')
                        rec['last_usage'] = None if not lastusage else datetime.strptime(lastusage, '%Y%m%dT%H%M%SZ')
                        rec['origin'] = filename.split('.')[0]
                        rec['domain'] = domain
                        tu_elements.append(rec)
                        drop = False
                    else :
                        drop = False
                        tu_count_drop += 1
                elif elem.tag == 'seg':
                    if elem.text:
                        if params['REGEX']:
                            for r in regex_pattern:
                                if re.match(r, elem.text):
                                    drop = True
                                    dropout = (filename, r, elem.text)
                                    regex_dropouts.append(dropout)
                        if lang == src_lang:
                            rec['source_lang'] = lang
                            rec['source_text'] = elem.text
                        else:
                            rec['target_text'] = elem.text
                            rec['target_lang'] = lang
                    else :
                        drop = True
            try:
                event, elem = next(context)
            except ET.ParseError as e:
                logging.warning('XML ParseError in file {} #records: {}\n{}'.format(filename,len(tu_elements), e))
                drop = True
            except StopIteration :
                break

        logging.info('Number of Records: processed: {} - saved: {} - dropped: {}'.format(len(tu_elements),tu_count,tu_count_drop))
        all_records += len(tu_elements)
        if  params['OUTPUT_FILES'] :
            csvfilename = filename.replace('.tmx', '.csv')
            outfile = path.join(output_folder,csvfilename)
            save_file(tu_elements,outfile)
            logging.info('TMX data save as csv-file: {}'.format(csvfilename))

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


