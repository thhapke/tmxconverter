
from hdbcli import dbapi

def save_db(records,db) :
    conn = dbapi.connect(address=db['host'], port=db['port'], user=db['user'], password=db['pwd'], encrypt=True,
                         sslValidateCertificate=False)

    cursor = conn.cursor()
    sql = 'INSERT INTO TMX.DATA (SOURCE_LANG, SOURCE_TEXT, TARGET_LANG, TARGET_TEXT, DOMAIN, ORIGIN, CREATION_ID, '\
          'CREATED,CHANGE_ID,CHANGED, LAST_USAGE,USAGE_COUNT) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)'
    data = [(r['source_lang'], r['source_text'], r['target_lang'], r['target_text'],r['domain'],r['origin'],r['creation_id'],
             r['created'],r['change_id'],r['changed'],r['last_usage'],r['usage_count']) for r in records]
    cursor.executemany(sql, data)
    cursor.close()
    conn.close()