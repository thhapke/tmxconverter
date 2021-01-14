import pandas as pd

### Output routines
def save_file(records,filename) :
    df = pd.DataFrame(records)
    df = df[['source_lang', 'source_text', 'target_lang', 'target_text', 'domain', 'origin', 'creation_id', 'created',
             'change_id', 'changed', 'last_usage', 'usage_count']]
    df.to_csv(filename, index=False)