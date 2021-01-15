# TMX Converter

tmxconverter reads tmx-files from an input folder and saves the outcome either
* as csv-files to an output folder or
* stores them into a database table


The language code is mapped to the 2-character code based on the given file 'language_code_mapping.csv' (specified in 'config.yaml')

The application is using a yaml-configuration file **config.yaml** to control the behaviour read from the working directory. 

## Command line options



## Mapping

* ```<tmx><header srclang="en-US"> ```: source_lang
* ```<body><tu creationdate``` : created
* ```<body><tu creationid``` : creation_id
* ```<body><tu changeid``` : change_id
* ```<body><tu changedate``` : changed
* ```<body><tu lastusagedate``` : lastusage
* From filename substring until '_' : domain
* Filename : origin
* ```<body><tu><tuv xml:lang``` : target_lang if different from source_lang using the language mapping
*  ```<body><tu><tuv><seg>```: source_text or target_text depending lang-attribute

## Files Output

If the parameter FILES_OUTPUT is ```true all``` tmx-files are written to the OUTPUT_FOLDER taking the same filename but replacing the suffix. 
The output is using a comma-separator and double quotes strings (pandas.to_csv used)

## Database Output

If the parameter HDB_OUTPUT is ````True```` then the data is stored to the HANA Database for which the details are given in the 
config.yaml-file.

The current table structure: 

```
CREATE COLUMN TABLE "TMX"."DATA"(
	"SOURCE_LANG" NVARCHAR(2),
	"SOURCE_TEXT" NVARCHAR(5000),
	"TARGET_LANG" NVARCHAR(2),
	"TARGET_TEXT" NVARCHAR(5000),
	"DOMAIN" NVARCHAR(15),
	"ORIGIN" NVARCHAR(30),
	"CREATION_ID" NVARCHAR(30),
	"CREATED" LONGDATE,
	"CHANGE_ID" NVARCHAR(30),
	"CHANGED" LONGDATE,
	"LAST_USAGE" LONGDATE,
	"USAGE_COUNT" INTEGER
)
```

## Example Config.YAML
```
# input folder
input_folder : /Users/Shared/data/tmx/input

#language coding map
lang_map_file : language_code_mapping.csv

# output files
OUTPUT_FILES : true # save to output folder
OUTPUT_FOLDER : /Users/Shared/data/tmx/output

# HANA DB
OUTPUT_HDB : false  # Save to db
HDB_HOST : 'xxx.com'
HDB_USER : 'TMXUSER'
HDB_PWD : 'PassWord'
HDB_PORT : 111

# Test Parameter
TEST : true
MAX_NUMBER_FILES : 100  # max number of files processed. NOT used when EXCLUSIVE_FILE given
EXCLUSIVE_FILE : reviews.tmx  # If not used leave empty
#EXCLUSIVE_FILE :
```
