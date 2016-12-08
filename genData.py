class Constant_Maker:
    def __init__(self, seed):
        self.curr_id = seed

    def generate_id(self, count=1):
        if count == 1:
            r = self.curr_id
            self.curr_id += 1
            return r

        start = self.curr_id
        ex_end = self.curr_id + count
        self.curr_id += count

        return range(start, ex_end)

import sys
def dprint(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

ARB_CONST = 768
CONST_MAKER = Constant_Maker(ARB_CONST)

from fieldkit.fieldkit import FieldKeeper
ALL_HERO_STATS =FieldKeeper.getAllHeroStats()
import codecs

ENCODING = 'utf-8'


def get_values(htmlText, handle):
    rValues = list()

    FINDING_TRIGGER, COLLECTING_VAL, COLLECTING_HERO_MARKER, COLLECTING_HERO_ID = range(4)
    HERO_MARKER = 'svg#0x02E0000000000'

    mode = FINDING_TRIGGER
    currString = ''
    collectedMarker = ''
    markerIndex = 0
    currID = ''
    foundHandle = False

    for c in htmlText:

        if FINDING_TRIGGER == mode:
            # value displayed on screen
            if '>' == c:
                mode = COLLECTING_VAL
                currString = ''

            # possibly the HERO_MARKER
            elif '.' == c:
                # else branch saves space
                if foundHandle:
                    mode = COLLECTING_HERO_MARKER
                    collectedMarker = ''
                    markerIndex = 0

        elif COLLECTING_VAL == mode:
            # closes collected val
            if '<' == c:
                mode = FINDING_TRIGGER
                # else branch saves space
                if foundHandle:
                    currString = currString.strip()
                    # ignores blanks
                    if len(currString) == 0:
                        continue
                    rValues.append(currString)
                    # skips following if
                elif handle == currString:
                    foundHandle = True
                    rValues.append(currString)
            else:
                currString += c

        elif COLLECTING_HERO_MARKER == mode:
            # matching the marker
            if HERO_MARKER[markerIndex] == c:
                markerIndex += 1
                # last character trigger
                if len(HERO_MARKER) == markerIndex:
                    mode = COLLECTING_HERO_ID
                    currID = ''

            # sudden mismatch -> reset
            else:
                mode = FINDING_TRIGGER

        elif COLLECTING_HERO_ID == mode:
            # fill up the ID
            currID += c
            # ID is two characters long
            if len(currID) == 3:
                rValues.append('HeroID={0}'.format(currID))
                mode = FINDING_TRIGGER

    return rValues


class PlayerNotFound(KeyError):
    def __init__(self, player):
        message = '{0} has likely been deleted/banned; cannot retrieve'.format(player)
        super(PlayerNotFound, self).__init__(message)


SECTION_LABELS = ['Hero Specific', 'Combat', 'Assists', 'Best', 'Average']
SECTION_LABELS.extend(['Deaths', 'Match Awards', 'Game', 'Miscellaneous'])

SECTION_TO_INDEX = dict()
for idx in range(len(SECTION_LABELS)):
    SECTION_TO_INDEX[SECTION_LABELS[idx]] = idx

FINDING_QUICKPLAY, FINDING_HERO_DATA, READING_HEROES = range(3)
HERO_DATA_MARKER = 'Featured Stats'
ENDING_MARKER = 'Achievements'

ERROR_LOG ='ERR.LOG'
with open(ERROR_LOG, 'w') as sink: pass
def log(msg):
    with open(ERROR_LOG, 'a') as sink:
        sink.write('{0}\n'.format(msg))
    
SR_IDX =2
def get_player_bag(htmlText, handle):
    valueList = get_values(htmlText, handle)
    # handles deleted/banned
    if 0 == len(valueList):
        raise PlayerNotFound(handle)

    quickplayBag = dict()
    competitiveBag = dict()
    playerBags = [quickplayBag, competitiveBag]
    targetBag = quickplayBag
    currSection = None
    encounteredDeaths = False
    heroID = None
    srRanking = 0
    possibleSR =valueList[SR_IDX]
    if 1 ==len(possibleSR.split(' ')):
        try:
            srRanking =int(possibleSR)
        except TypeError as t:
            log('missing SR; setting SR to 0 - {0}'.format(handle)) 
    competitiveBag['SR'] =srRanking

    mode = FINDING_QUICKPLAY
    valIdx = 0
    while valIdx < len(valueList):

        val = valueList[valIdx]

        if FINDING_QUICKPLAY == mode:
            if HERO_DATA_MARKER == val:
                mode = FINDING_HERO_DATA

            valIdx += 1

        elif FINDING_HERO_DATA == mode:
            # denotes beginning of Competitive data
            if HERO_DATA_MARKER == val:
                targetBag = competitiveBag

            # denotes end of hero data
            elif ENDING_MARKER == val:
                break

            elif 'HeroID=' in val:
                mode = READING_HEROES
                heroID = val[-3:]
                targetBag[heroID] = list()

            valIdx += 1

        elif READING_HEROES == mode:
            # denotes Competitive Section
            if HERO_DATA_MARKER == val:
                targetBag = competitiveBag
                mode = FINDING_HERO_DATA

                valIdx += 1

            # denotes end of all hero data
            elif ENDING_MARKER == val:
                break

            elif 'HeroID' in val:
                heroID = val[-3:]
                targetBag[heroID] = list()
                valIdx += 1

            # could be section or value label
            elif 'Deaths' == val:
                # is a section
                if not encounteredDeaths:
                    encounteredDeaths = True

                    thisSection = val
                    thisSectionIndex = SECTION_TO_INDEX[thisSection]

                    # first section
                    if not currSection:
                        currSection = thisSection

                        valIdx += 1
                        continue

                    # indicates new hero
                    currSectionIndex = SECTION_TO_INDEX[currSection]
                    if thisSectionIndex < currSectionIndex:
                        mode = FINDING_HERO_DATA
                        currSection = thisSection
                        encounteredDeaths = False

                        valIdx += 1

                    else:
                        currSection = thisSection

                        valIdx += 1

                # is a label
                else:
                    labelValue = (val, valueList[valIdx + 1])
                    targetBag[heroID].append(labelValue)

                    valIdx += 2

            elif val in SECTION_LABELS:
                thisSection = val
                thisSectionIndex = SECTION_TO_INDEX[thisSection]

                # first section encountered
                if not currSection:
                    currSection = thisSection
                    valIdx += 1
                    continue

                # indicates new hero
                currSectionIndex = SECTION_TO_INDEX[currSection]
                if thisSectionIndex < currSectionIndex:
                    currSection = thisSection
                    encounteredDeaths = False

                    valIdx += 1

                else:
                    currSection = thisSection

                    valIdx += 1
            else:
                labelValue = (val, valueList[valIdx + 1])
                targetBag[heroID].append(labelValue)

                valIdx += 2

    return playerBags


import requests


def main(username, platform, region, exportFile):

    if not region:
        name =username
        url ='https://playoverwatch.com/en-us/career/{0}/{1}'.format(platform.lower(), username)
    else:
        name, _ =username.split('-')
        url ='https://playoverwatch.com/en-us/career/pc/{0}/{1}'.format(region.lower(), username)

    r = requests.get(url)
    html_text = r.text
    heroes = {'040': 'roadhog', '002': 'reaper', '003': 'tracer', '004': 'mercy', '005': 'hanzo', '006': 'torbjorn',
              '007': 'reinhardt', '008': 'pharah', '009': 'winston', '00A': 'widowmaker', '015': 'bastion',
              '016': 'symmetra', '020': 'zenyatta', '029': 'genji', '042': 'mccree', '065': 'junkrat', '068': 'zarya',
              '06E': 'soldier76', '079': 'lucio', '07A': 'd.va', '0DD': 'mei', '13B': 'ana', '12E': 'sombra'}
    try:
        player_bags = get_player_bag(html_text, name)
        competitiveBag =player_bags[1]
        sr =competitiveBag['SR']
        competitiveBag.pop('SR', None)
        for hero in competitiveBag:
            sinkFile ='{0}_{1}'.format(exportFile, heroes[hero])

            completeFieldList =ALL_HERO_STATS[heroes[hero]]

            # fill with defaults
            userFields =dict()
            for field in completeFieldList:
                userFields[field] =0

            # fill with user values
            for field, val in competitiveBag[hero]:
                if field not in userFields:
                    field =FieldKeeper.getLibraryForm(field, hero)
                if field not in userFields:
                    log('erroneous field - {0}'.format(field))
                    continue
                userFields[field] =val

            # fill with uservals
            line ='{0};{1};'.format(username, sr)
            orderedKeys =sorted(list(userFields.keys()))
            for key in orderedKeys:
                line +='{0};'.format(userFields[key])
            line =line[:-1]
            with open(sinkFile, 'a') as sink:
                sink.write(line+'\n')

    except IndexError:
        print('Player not found:' + username + " " + platform + " " + region)


# ---

def complain(prob_string):
    print(prob_string)
    print('Aborting...')

def clearFiles():
    consoles = {'pc', 'psn', 'xbl'}
    heroes = {'ana', 'bastion', 'd.va', 'genji', 'hanzo', 'junkrat', 'lucio', 'mccree', 'mei', 'mercy', 'pharah',
              'reaper', 'reinhardt', 'roadhog', 'soldier76', 'sombra', 'symmetra', 'torbjorn', 'tracer', 'widowmaker',
              'winston', 'zarya', 'zenyatta'}

    for console in consoles:
        for hero in heroes:
            open('res/competitive/' + console + '/' + hero + '_results', 'w').close()
            write_labels = open('res/competitive/' + console + '/' + hero + '_results', 'a')
            hero_stats = sorted(ALL_HERO_STATS[hero])
            outputLine ='Username;'
            for stat in hero_stats:
                outputLine +='{0};'.format(stat)
            outputLine =outputLine[:-1]
            write_labels.write('{0}\n'.format(outputLine))
            write_labels.close()

if __name__ == '__main__':
    args =sys.argv[1:]
    with open(args[0]) as source:
        for line in source:
            line =line.strip()
            if not line: continue

            
            dprint('processing {0}'.format(line), end='...')
            try:
                if 4 ==len(args):
                    main(line, args[1], args[2], args[3])
                elif 3 ==len(args):
                    with open(args[2], 'w') as sink: pass
                    main(line, args[1], None, args[2])
                else:
                    exit()
                dprint('done')
            except PlayerNotFound as p:
                dprint('missing')





