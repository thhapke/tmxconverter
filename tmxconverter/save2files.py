import pandas as pd

### Output routines
def save_file(records,filename) :
    df = pd.DataFrame(records)
    #remove newlines
    df.source_text = df.source_text.apply(lambda  x : x.replace('\n',' '))
    df.target_text = df.target_text.apply(lambda x: x.replace('\n', ''))
    df = df[['source_lang', 'source_text', 'target_lang', 'target_text', 'domain', 'origin', 'creation_id', 'created',
             'change_id', 'changed', 'last_usage', 'usage_count']]
    df.to_csv(filename, index=False, line_terminator='\n')