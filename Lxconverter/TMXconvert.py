import xml.etree.ElementTree as ET
from os import path, listdir
from _datetime import datetime
import csv
import re
import logging
from datetime import datetime, timedelta
from argparse import ArgumentParser

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

    # directories
    input_folder = params['TMX_INPUT_FOLDER']
    if params['TMX_OUTPUT_FILES'] :
        logging.info('CSV Files stored to: {}'.format(params['TMX_OUTPUT_FOLDER']))
        output_folder = params['TMX_OUTPUT_FOLDER']

    # language mapping file
    langmapcodes = read_language_code_mapping(params['lang_map_file'])

    # db config
    if params['OUTPUT_HDB'] :
        logging.info('Setting DB connection parameter.')
        db = {'host':params['HDB_HOST'],
              'user':params['HDB_USER'],
              'pwd':params['HDB_PWD'],
              'port':params['HDB_PORT']}
        batchsize = int(params['BATCHSIZE'])
        text_max_len = 100000 if params['MAX_LEN'] == 0 else params['MAX_LEN']

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
        domain = re.search("(.+)_\w{4}_\w{4}\.tmx$",filename).group(1)
        if not domain:
            logging.warning('Filename does not match regex pattern. Replaced by filename: {}'.format(filename))
            domain = filename.split('.')[0]
        drop = False
        src_lang = ''
        lang = ''
        rec = dict()


        context = iter(ET.iterparse(path.join(input_folder, filename),events=("start","end")))
        event, elem = next(context)
        tu_count = 0
        tu_count_drop = 0
        seg_branch = False
        while not elem == None:
            if event == 'start':
                if elem.tag == 'tuv' :
                    lang = langmapcodes[list(elem.attrib.values())[0]]
                elif elem.tag == 'tu':
                    drop = False
                    rec = dict()  # new dict
                elif elem.tag == 'header':
                    src_lang = langmapcodes[elem.attrib['srclang']]
                elif elem.tag == 'seg':
                    seg_branch = True
                    text = elem.text if elem.text else ''

            elif event == 'end' :
                if elem.tag == 'tu' :
                    tu_count += 1
                    if not drop :  # If sth went wrong do not save elem
                        rec['source'] = 'TMX'
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
                        seg_branch = False
                        if params['REGEX']:
                            for r in regex_pattern:
                                if re.match(r, text):
                                    drop = True
                                    dropout = (filename, r, text)
                                    regex_dropouts.append(dropout)
                        if lang == src_lang:
                            rec['source_lang'] = lang
                            rec['source_text'] = text[:text_max_len]
                        else:
                            rec['target_text'] = text[:text_max_len]
                            rec['target_lang'] = lang
                    else :
                        drop = True
                elif seg_branch :
                    if elem.text :
                        text += elem.text
                    if elem.tail :
                        text += elem.tail
            try:
                event, elem = next(context)
            except ET.ParseError as e:
                logging.warning('XML ParseError in file {} #records: {}\n{}'.format(filename,len(tu_elements), e))
                drop = True
            except StopIteration :
                break

        logging.info('Number of Records: processed: {} - saved: {} - dropped: {}'.format(len(tu_elements),tu_count,tu_count_drop))
        all_records += len(tu_elements)
        if  params['TMX_OUTPUT_FILES'] :
            csvfilename = filename.replace('.tmx', '.csv')
            outfile = path.join(output_folder,csvfilename)
            save_file(tu_elements,outfile)
            logging.info('TMX data save as csv-file: {}'.format(csvfilename))

        if params['OUTPUT_HDB'] :
            save_db(source = 'TMX',records=tu_elements,db=db,batchsize=batchsize)
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


