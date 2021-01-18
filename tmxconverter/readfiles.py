
import csv

def read_regex(filename,outputfile) :
    regex_pattern = list()
    with open(filename) as file:
        while True :
            line = file.readline().rstrip('\n')
            if line :
                regex_pattern.append(line)
            else :
                break
        file.close()
    # clean log file
    with open(outputfile, 'w') as file:
        csvwriter = csv.writer(file)
        file.close()
    return regex_pattern


def read_language_code_mapping(filename) :
    # language mapping file
    langmapcodes = dict()
    with open(filename) as file :
        for line in csv.reader(file):
            langmapcodes[line[0]] = line[1]
    return langmapcodes
