
from hdbcli import dbapi
import logging
import pandas as pd

def save_db(source, records,db,batchsize = 0 ) :
    conn = dbapi.connect(address=db['host'], port=db['port'], user=db['user'], password=db['pwd'], encrypt=True,
                         sslValidateCertificate=False)


    if source == 'TMX' :
        data = [
            (r['source'], r['source_lang'], r['source_text'], r['target_lang'], r['target_text'], r['domain'], r['origin'],
             r['created'], r['changed'], r['last_usage'], r['usage_count']) for r in records]
        sql = 'UPSERT TMX.DATA (SOURCE,SOURCE_LANG, SOURCE_TEXT, TARGET_LANG, TARGET_TEXT, DOMAIN, ORIGIN, ' \
              'CREATED,CHANGED, LAST_USAGE,USAGE_COUNT) VALUES (?,?,?,?,?,?,?,?,?,?,?) WITH PRIMARY KEY;'
    elif source == 'ABAP' :
        data = records[['source','source_lang','source_text','target_lang','target_text','domain','origin','exported','changed',
                 'last_usage','transl_system','abap_package','central_system','objtype','objname','max_langth','ach_comp',
                 'sw_comp','sw_comp_version','pp_type','pp_qstatus','orig_lang']].to_records(index= False).tolist()
        sql =''
    else:
        raise ValueError('Unknown source: {}',format(source))

    cursor = conn.cursor()

    if batchsize == 0 :
        logging.debug('Uploading: {}'.format(len(data)))
        cursor.executemany(sql, data)
    else:
        logging.debug('Uploading in batches: {} of batch size: {} (#{})'.format(len(data),batchsize,int(len(data)/batchsize)+1))
        for i in range(0,len(data),batchsize) :
            logging.debug('Uploaded: {}/{} - Uploading: {}'.format(i,len(data),len(data[i:i+batchsize])))
            cursor.executemany(sql, data[i:i+batchsize])

    cursor.close()
    conn.close()