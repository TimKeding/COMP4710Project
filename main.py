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


ARB_CONST = 768
CONST_MAKER = Constant_Maker(ARB_CONST)

import codecs

ENCODING = 'utf-8'


def get_values(htmlText, handle):

    rValues =list()

    FINDING_TRIGGER, COLLECTING_VAL, COLLECTING_HERO_MARKER, COLLECTING_HERO_ID =range(4)
    HERO_MARKER ='svg#0x02E0000000000'

    mode =FINDING_TRIGGER
    currString =''
    collectedMarker =''
    markerIndex =0
    currID =''
    foundHandle =False

    for c in htmlText:

        if FINDING_TRIGGER ==mode:
            # value displayed on screen
            if '>' ==c:
                mode =COLLECTING_VAL
                currString =''
            
            # possibly the HERO_MARKER
            elif '.' ==c:
                # else branch saves space
                if foundHandle:
                    mode =COLLECTING_HERO_MARKER
                    collectedMarker =''
                    markerIndex =0

        elif COLLECTING_VAL ==mode:
            # closes collected val
            if '<' ==c:
                mode =FINDING_TRIGGER
                # else branch saves space
                if foundHandle:
                    currString =currString.strip()
                    # ignores blanks
                    if len(currString) ==0:
                        continue
                    rValues.append(currString)
                    # skips following if
                if handle ==currString:
                    foundHandle =True
                    rValues.append(currString)
            else:
                currString +=c

        elif COLLECTING_HERO_MARKER ==mode:
            # matching the marker
            if HERO_MARKER[markerIndex] ==c:
                markerIndex +=1
                # last character trigger
                if len(HERO_MARKER) ==markerIndex:
                    mode =COLLECTING_HERO_ID
                    currID =''

            # sudden mismatch -> reset
            else:
                mode =FINDING_TRIGGER

        elif COLLECTING_HERO_ID ==mode:
            # fill up the ID
            currID +=c
            # ID is two characters long
            if len(currID) ==3:
                rValues.append('HeroID={0}'.format(currID))
                mode =FINDING_TRIGGER

    return rValues

class PlayerNotFound(KeyError):
    def __init__(self, player):
        message ='{0} has likely been deleted/banned; cannot retrieve'.format(player)
        super(PlayerNotFound, self).__init__(message)

SECTION_LABELS =['Hero Specific', 'Combat', 'Assists', 'Best', 'Average']
SECTION_LABELS.extend(['Deaths', 'Match Awards', 'Game', 'Miscellaneous'])

SECTION_TO_INDEX =dict()
for idx in range(len(SECTION_LABELS)):
    SECTION_TO_INDEX[SECTION_LABELS[idx]] =idx

FINDING_QUICKPLAY, FINDING_HERO_DATA, READING_HEROES =range(3)
HERO_DATA_MARKER ='Featured Stats'
ENDING_MARKER ='Achievements'
def get_player_bag(htmlText, handle):

    valueList =get_values(htmlText, handle)
    # handles deleted/banned
    if 0 ==len(valueList):
        raise PlayerNotFound(handle)

    quickplayBag =dict()
    competitiveBag =dict()
    playerBags =[quickplayBag, competitiveBag]
    targetBag =quickplayBag
    currSection =None
    encounteredDeaths =False
    heroID =None

    mode =FINDING_QUICKPLAY
    valIdx =0
    while valIdx <len(valueList):

        val =valueList[valIdx]

        if FINDING_QUICKPLAY ==mode:
            if HERO_DATA_MARKER ==val:
                mode =FINDING_HERO_DATA

            valIdx +=1

        elif FINDING_HERO_DATA ==mode:
            # denotes beginning of Competitive data
            if HERO_DATA_MARKER ==val:
                targetBag =competitiveBag

            # denotes end of hero data
            elif ENDING_MARKER ==val:
                break

            elif 'HeroID=' in val:
                mode =READING_HEROES
                heroID =val[-3:]
                targetBag[heroID] =list()

            valIdx +=1

        elif READING_HEROES ==mode:
            # denotes Competitive Section
            if HERO_DATA_MARKER ==val:
                targetBag =competitiveBag
                mode =FINDING_HERO_DATA

                valIdx +=1

            # denotes end of all hero data
            elif ENDING_MARKER ==val:
                break

            elif 'HeroID' in val:
                heroID =val[-3:]
                targetBag[heroID] =list()

                valIdx +=1

            # could be section or value label
            elif 'Deaths' ==val:
                # is a section
                if not encounteredDeaths:
                    encounteredDeaths =True

                    thisSection =val
                    thisSectionIndex =SECTION_TO_INDEX[thisSection]

                    # first section
                    if not currSection:
                        currSection =thisSection

                        valIdx +=1
                        continue

                    # indicates new hero
                    currSectionIndex =SECTION_TO_INDEX[currSection]
                    if thisSectionIndex <currSectionIndex:
                        mode =FINDING_HERO_DATA
                        currSection =thisSection
                        encounteredDeaths =False

                        valIdx +=1

                    else:
                        currSection =thisSection

                        valIdx +=1

                # is a label
                else:
                    labelValue =(val, valueList[valIdx +1])
                    targetBag[heroID].append(labelValue)

                    valIdx +=2

            elif val in SECTION_LABELS:
                thisSection =val
                thisSectionIndex =SECTION_TO_INDEX[thisSection]

                # first section encountered
                if not currSection:
                    currSection =thisSection
                    valIdx +=1
                    continue

                # indicates new hero
                currSectionIndex =SECTION_TO_INDEX[currSection]
                if thisSectionIndex <currSectionIndex:
                    currSection =thisSection
                    encounteredDeaths =False

                    valIdx +=1

                else:
                    currSection =thisSection

                    valIdx +=1
            else:
                labelValue =(val, valueList[valIdx +1])
                targetBag[heroID].append(labelValue)

                valIdx +=2

    return playerBags

import requests


def main(username, platform, region, export_file):
    if region:
        count_sharp = len(username.split('-')) - 1
        if count_sharp == 0:
            print('err: no number on PC battletag')
            print('aborting...')
            exit()
        elif count_sharp > 1:
            print('err: battletag has too many #')
            print('aborting...')
            exit()

        name, number = username.split('-')
        try:
            n = int(number)
        except ValueError as v:
            print('err: given battletag has no number')
            exit()

        url = 'https://playoverwatch.com/en-us/career/pc/' + region.lower() + '/' + name + '-' + number

    else:
        name = username
        url = 'https://playoverwatch.com/en-us/career/' + platform.lower() + '/' + username

    r = requests.get(url)
    html_text = r.text
    try:
        player_bags = get_player_bag(html_text, name)

        bag_and_label = list()
        bag_and_label.append(('Quick Play', player_bags[0]))
        bag_and_label.append(('Competitive', player_bags[1]))

        write_results = open(export_file, 'a')

        write_results.write(username + '\n')
        for label, bag in bag_and_label:
            write_results.write(label + '\n')

            for hero in bag:
                write_results.write('\t{0}'.format(hero) + '\n')

                for label, val in bag[hero]:
                    write_results.write('\t\t{0} | {1}'.format(label, val) + '\n')
        write_results.write('-----------------\n')
        write_results.close()
    except IndexError:
            print('Player not found:' + username + " " + platform + " " + region)
# ---

def complain(prob_string):
    print(prob_string)
    print('Aborting...')


# handle different platforms
import sys

if __name__ == '__main__':

    pc_us_file = open('res/pc_us.txt', 'r')
    with open('res/pc_us_results', 'w'): pass
    for line in pc_us_file:
        main(line.strip('\n'), 'PC', 'US', 'res/pc_us_results')
    pc_us_file.close()

    # pc_eu_file = open('res/pc_eu.txt', 'r')
    # with open('res/pc_eu_results', 'w'): pass
    # for line in pc_eu_file:
    #     main(line.strip('\n'), 'PC', 'EU', 'res/pc_eu_results')
    #
    # pc_kr_file = open('res/pc_kr.txt', 'r')
    # with open('res/pc_kr_results', 'w'): pass
    # for line in pc_kr_file:
    #     main(line.strip('\n'), 'PC', 'KR', 'res/pc_kr_results')
    #
    # xbl_file = open('res/xbl.txt', 'r')
    # with open('res/xbl_results', 'w'): pass
    # for line in xbl_file:
    #     main(line.strip('\n'), 'XBL', 'US', 'res/xbl_results')
    #
    # psn_file = open('res/psn.txt', 'r')
    # with open('res/psn_results', 'w'): pass
    # for line in psn_file:
    #     main(line.strip('\n'), 'PSN', 'US', 'res/psn_results')

