
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

def remedyxml(filename, position ) :
    text = ''
    with open(filename) as file:
        count = 1
        while True :
            line = file.readline()
            if line :
                if count == position[0] :
                    failed_char = line[position[1]]
                    line[position[1]] = ' '
                text += line
            else :
                break
    return text