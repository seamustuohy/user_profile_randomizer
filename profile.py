#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2017 seamus tuohy, <code@seamustuohy.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the included LICENSE file for details.

import argparse

import logging
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)
from os import path, listdir, getcwd
import subprocess

import random
import requests
from time import sleep
import re
import csv

def main():
    args = parse_arguments()
    set_logging(args.verbose, args.debug)

    converted_profile = []
    if path.isdir(args.profile):
        output_path = None
        # Check that output is correct
        if (args.converted) and not (path.isdir(args.converted)):
            print("If you select a directory for profile you must select a directory for the output as well.")
            exit(1)
        elif args.converted is None:
            output_path = False # Output should be std out
        for f in listdir(args.profile):
            pathname = path.join(args.profile, f)
            log.info("Converting {0}".format(pathname))
            if output_path is None:
                # Output is a directory to write the file to
                output_path = path.join(args.converted, f)
            profile = get_profile(args.randomize_pronoun)
            convert_profile(pathname,
                            output_path,
                            profile.get("name"),
                            profile.get("pronouns"))
            create_pdf(output_path,
                       profile.get("gender"),
                       args.license_path,
                       image_path=args.image_path,
                       template_path=args.template_path,
                       output_directory=args.output_directory)
            output_path = None
    else:
        profile = get_profile(args.randomize_pronoun)
        convert_profile(args.profile,
                        args.converted,
                        profile.get("name"),
                        profile.get("pronouns"))
        create_pdf(args.converted,
                   profile.get("gender"),
                   args.license_path,
                   image_path=args.image_path,
                   template_path=args.template_path,
                   output_directory=args.output_directory)

def create_pdf(converted_profile, gender, license_path,
               image_path='images', template_path='templates/basic.tex',
               output_directory='outputs'):
    """ Create a pdf

    args:
        converted_profile: path to the converted profile
        gender: the sub_directory used to split images
        license_path: the path to the license file.
    """
    working_dir = getcwd()
    images = path.join(working_dir, image_path, gender)
    image = random.choice(listdir(images))
    licenses = get_licenses(license_path)
    # Split license string off images
    # e.g. WOCinTech_photo001.jpg to get WOCinTech
    image_string = image.split("_")[0]
    image_license = licenses.get(image_string)
    image_path = path.join(working_dir, image_path,
                           gender, image)
    subprocess.check_call(['./make_pdf.sh',
                           converted_profile,
                           image_path,
                           image_license,
                           template_path,
                           output_directory])

def get_licenses(license_path):
    """ Read a csv license file and return the data.

    A license file should have two columns:
        Col 1: license file prefixes
        Col 2: the corresponding license string to put in the doc
    """
    licenses = {}
    with open(license_path, 'r') as licefile:
        lread = csv.reader(licefile)
        for lpair in lread:
            licenses.setdefault(lpair[0], lpair[1])
    return licenses


def get_profile(randomize_pronoun, name_language=None):
    """ Query Wikidata to get a name, language, gender, and pronoun.

    TODO: Add unit test for missing names
        name_language=('Esperanto', 'Q143')
    """
    gender_of_name = {"female":'Q11879590', "male":'Q12308941'}
    gender = random.choice(list(gender_of_name.keys()))
    gender_query = gender_of_name.get(gender)
    full_name = None
    # Only get language list if needed,
    # Only get it once
    if name_language is None:
        languages = get_languages(gender_query)
    # Name loop
    while full_name is None:
        try:
            if name_language is None:
                name_language = random.choice(languages)
            name = []
            # 'Q101352' == Surname
            for name_type in [gender_query, 'Q101352']:
                name.append(get_random_name(name_type, name_language[1]))
                sleep(1)
            if is_a_real_person(name):
                log.info("{0} was a real person. Starting again.".format(" ".join([i[0] for i in name])))
                name_language = None
            else:
                full_name = " ".join([i[0] for i in name])
                log.info("[{0},{1},{2}]".format(gender,
                                                name_language[0],
                                                full_name))
        except (ValueError, IndexError) as _e:
            log.debug(_e)
            log.info("No {0} names were found. Trying another.".format(name_language[0]))
            name_language = None
    if randomize_pronoun is True:
        gender = None
    pronouns = get_pronoun(gender=gender)
    log.debug(pronouns)
    return {"name":name,
            "language":name_language,
            "gender":gender,
            "pronouns":pronouns}

def is_a_real_person(name):
    """Checks if a name is a person who exists on WikiData
    """
    query = """
SELECT ?person
WHERE
{{
  ?person wdt:P735 wd:{0};
          wdt:P734 wd:{1}.
}}""".format(name[0][1], name[1][1])
    payload = {"format":"json", "query":query}
    r = requests.get("https://query.wikidata.org/sparql?format=json",
                     params=payload)
    return_json = r.json()
    humans = len(return_json['results']['bindings'])
    if humans > 0:
        log.info("There are {0} {1} {2}'s in the world".format(humans, name[0][0], name[1][0]))
        return True
    else:
        return False

def convert_profile(prof_path, output_path, name, pronouns):
    """Takes a template and creates a filled out profile
    """
    converted_file = []
    with open(prof_path, 'r') as profile_pointer:
        for line in profile_pointer:
            pronoun_converted = replace_pronouns(line, new=pronouns)
            name_converted = replace_name(pronoun_converted, name)
            converted_file.append(name_converted)
    if output_path is False:
        for line in converted_file:
            print(line)
    else:
        log.debug(output_path)
        with open(output_path, 'w+') as write_file:
            for line in converted_file:
                write_file.write(line)

def replace_name(line, name):
    """Replaces template name strings with the supplied name
    """
    rep_strings = {"name": name[0][0],
                   "full name": " ".join([i[0] for i in name])}
    rep_line = line.format(**rep_strings)
    return rep_line

def replace_pronouns(text, new, old=["xey","xem","xyr","xyrs","xemself"]):
    """Replaces all pronouns in the provided text with a new set of pronouns
    """
    for i,pronoun in enumerate(new):
        pattern = re.compile("(?<![a-zA-Z])([{0}{1}])({2})(?=[\.,;\:'\"\?\-\)!0-9 ])".format(old[i][0].lower(),
                                                           old[i][0].upper(),
                                                           old[i][1:]))

        text = pattern.sub((lambda x: replace_pronoun(x, pronoun)),
                          text)
    return text

def replace_pronoun(match, repl):
    """Sub-function for replacing pronouns that handles capitalization
    """
    replacement = ''
    if match.group(1).isupper() is True:
        replacement += repl[0].upper()
    else:
        replacement += repl[0]
    replacement += repl[1:]
    #replacement += match.group(4)
    return replacement

def get_pronoun(gender=None):
    """Get pronouns to use.

    Pronoun list taken from pronoun.is.
    The code from pronoun.is is GNU Affero General Public License v3.0
    I didn't use their code, but we went with a compliant license nonetheless
    https://github.com/witch-house/pronoun.is/blob/develop/COPYING
    """
    gender_pronoun_pairs = {"male":3, "female":2}
    pronouns = [["ze","hir","hir","hirs","hirself"],
                ["ze","zir","zir","zirs","zirself"],
                ["she","her","her","hers","herself"],
                ["he","him","his","his","himself"],
                ["they","them","their","theirs","themselves"],
                ["they","them","their","theirs","themself"],
                ["xey","xem","xyr","xyrs","xemself"],
                ["sie","hir","hir","hirs","hirself"],
                ["it","it","its","its","itself"],
                ["ey","em","eir","eirs","eirself"],
                ["e","em","eir","eirs","emself"],
                ["hu","hum","hus","hus","humself"],
                ["peh","pehm","peh's","peh's","pehself"],
                ["per","per","per","pers","perself"],
                ["thon","thon","thons","thons","thonself"],
                ["jee","jem","jeir","jeirs","jemself"],
                ["ve","ver","vis","vis","verself"],
                ["xe","xem","xyr","xyrs","xemself"],
                ["zie","zir","zir","zirs","zirself"],
                ["ze","zem","zes","zes","zirself"],
                ["zie","zem","zes","zes","zirself"],
                ["ze","mer","zer","zers","zemself"],
                ["se","sim","ser","sers","serself"],
                ["zme","zmyr","zmyr","zmyrs","zmyrself"],
                ["ve","vem","vir","virs","vemself"],
                ["zee","zed","zeta","zetas","zedself"],
                ["fae","faer","faer","faers","faerself"],
                ["zie","hir","hir","hirs","hirself"],
                ["si","hyr","hyr","hyrs","hyrself"],
                ["kit","kit","kits","kits","kitself"],
                ["ne","nem","nir","nirs","nemself"],
                ["fey","feym","feir","feirs","feirself"],
                ["xie","xer","xer","xers","xerself"]]
    if gender is not None:
        if gender.lower() in gender_pronoun_pairs:
            return pronouns[gender_pronoun_pairs.get(gender)]
    return random.choice(pronouns)

def get_languages(gender_query):
    """Get a list of the top 50 languages based by number of given names with a specific gender
    """
    language_query="""
  SELECT ?native ?nativeLabel (count(?native) as ?count)
  WHERE
  {{
    ?given_name wdt:P31 wd:{0};
                wdt:P407 ?native .
    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
  }}
  GROUP BY ?nativeLabel ?native
  ORDER BY DESC(?count)
  LIMIT 50
  """.format(gender_query)
    payload = {"format":"json", "query":language_query}
    r = requests.get("https://query.wikidata.org/sparql?format=json", params=payload)
    languages = []
    return_json = r.json()

    for item in return_json['results']['bindings']:
        languages.append((item['nativeLabel']['value'], item["native"]["value"].split("/")[-1]))
    return languages


def get_random_name(gender_query, language):
    """ Get a random name that fits the gender and language provided
    """
    name = []
    query='''
SELECT DISTINCT ?name ?nameLabel (SHA256(CONCAT(str(?s),str(RAND()))) as ?random)
WHERE
{{
  ?name wdt:P31 wd:{0};
        wdt:P407 wd:{1} . # LANGUAGE ID == wd:Q......
  ?name rdfs:label ?label .
  FILTER(LANG(?label) = "en")
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
 }}
ORDER BY ?random
LIMIT 20
'''.format(gender_query, language)
    payload = {"format":"json", "query":query}
    r = requests.get("https://query.wikidata.org/sparql?format=json", params=payload)
    return_json = r.json()
    #print(return_json)
    names = []
    for item in return_json['results']['bindings']:
        names.append((item['nameLabel']['value'],
                      item['name']['value'].split("/")[-1]))
    random_part = random.choice(names)
    return random_part

def set_logging(verbose=False, debug=False):
    if debug == True:
        log.setLevel("DEBUG")
    elif verbose == True:
        log.setLevel("INFO")

def parse_arguments():
    parser = argparse.ArgumentParser("Get a summary of some text")
    parser.add_argument("--verbose", "-v",
                        help="Turn verbosity on",
                        action='store_true')
    parser.add_argument("--debug", "-d",
                        help="Turn debugging on",
                        action='store_true')
    parser.add_argument("--profile", "-p",
                        help="select profile to modify")
    parser.add_argument("--converted", "-c",
                        help="select file/directory to output convered profile text into")
    parser.add_argument("--randomize_pronoun", "-r",
                        help="Randomize pronoun usage",
                        action='store_true')
    parser.add_argument("--license_path", "-l",
                        help="the path to the license file to use for photos")
    parser.add_argument("--image_path", "-i",
                        help="the path to the images directory")
    parser.add_argument("--template_path", "-t",
                        help="the path to the pdf template")
    parser.add_argument("--output_directory", "-o",
                        help="select file to output profile into")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main()
