class Constant_Maker:
    def __init__(self, seed):
        self.curr_id = seed

    def generate_id(self, count=1):
        if count == 1:
            r = self.curr_id
            self.curr_id +=1
            return r

        start = self.curr_id
        ex_end = self.curr_id + count
        self.curr_id += count

        return range(start, ex_end)


ARB_CONST = 768
CONST_MAKER = Constant_Maker(ARB_CONST)

import codecs

ENCODING = 'utf-8'


def get_values(html_text, handle):

    rValues = list()
    FINDING_TRIGGER, COLLECTING_VAL, COLLECTING_HERO_MARKER, COLLECTING_HERO_ID = range(4)
    HERO_MARKER ='svg#0x02E00000000000'


    mode = FINDING_TRIGGER
    currString =''
    collectedMarker =''
    markerIndex =0
    currID =''
    foundHandle =False

    for c in html_text:

        if FINDING_TRIGGER == mode:
            if '>' == c:
                mode = COLLECTING_VAL
                currString =''
            elif '.' == c:
                if not foundHandle:
                    continue
                mode = COLLECTING_HERO_MARKER
                collectedMarker =''
                markerIndex =0

        elif COLLECTING_VAL == mode:
            if '<' == c:
                mode = FINDING_TRIGGER
                if foundHandle:
                    currString = currString.strip()
                    if len(currString) ==0:
                        continue
                    rValues.append(currString)
                    continue
                if handle == currString:
                    foundHandle =True
                    rValues.append(currString)
            else:
                currString += c

        elif COLLECTING_HERO_MARKER == mode:
            if HERO_MARKER[markerIndex] == c:
                markerIndex +=1
                # if at last character
                if len(HERO_MARKER) == markerIndex:
                    mode = COLLECTING_HERO_ID
                    currID =''
            else:
                mode =FINDING_TRIGGER

        elif COLLECTING_HERO_ID == mode:
            currID += c
            # IDs are 2chars long
            if len(currID) ==2:
                rValues.append('HeroID={0}'.format(currID))
                mode =FINDING_TRIGGER

    return rValues

class PlayerNotFound(KeyError):
    def __init__(self, player):
        message = '{0} has likely been deleted or banned and cannot be retrieved'.format(player)
        super(PlayerNotFound, self).__init__(message)

def get_player_bag(htmlText, handle):

    valuesList = get_values(htmlText, handle)
    # to handle deleted / banned players
    if len(valuesList) == 0:
        raise PlayerNotFound(handle)

    quickplayBag = dict()
    competitiveBag = dict()
    playerBags = [quickplayBag, competitiveBag]

    sectionLabels = ['Hero Specific', 'Combat', 'Assists', 'Best', 'Average', 'Deaths', 'Match Awards', 'Game', 'Miscellaneous']
    sectionToIdx = dict()
    for idx in range(len(sectionLabels)):
        sectionToIdx[sectionLabels[idx]] =idx

    FINDING_FIRST_HERO, READING_VALUES = CONST_MAKER.generate_id(2)
    FINISH_MARKER_VALUE = 'Achievements'

    currValIdx = 0
    currVal = valuesList[currValIdx]
    currHeroIdx = -1
    currSectionIdx = None
    currBag = quickplayBag
    mode = FINDING_FIRST_HERO
    encountered_deaths = False
    while( FINISH_MARKER_VALUE != currVal ):

        if FINDING_FIRST_HERO == mode:
            currVal = valuesList[currValIdx]

            if currVal not in sectionLabels:
                currValIdx +=1
                continue
            currSectionIdx = sectionToIdx[currVal]
            if 'Deaths' == currVal:
                encountered_deaths = True
                
            # the first hero is encountered
            currValIdx +=1
            currHeroIdx +=1
            currBag[currHeroIdx] = list()
            mode = READING_VALUES

        elif READING_VALUES == mode:
            currVal = valuesList[currValIdx]

            # handle double Deaths labels
            if 'Deaths' == currVal and (not encountered_deaths):
                encountered_deaths = True
                currValIdx +=1

            # handle section labels
            # - and not deaths to let the else handle the Deaths field value
            elif currVal in sectionLabels and (currVal != 'Deaths'):
                newSectionIdx = sectionToIdx[currVal]

                # this new section <= miscellaneous -> same hero
                if newSectionIdx > currSectionIdx:
                    currSectionIdx = newSectionIdx
                    currValIdx +=1

                # this new section past miscellaneous of current hero -> next hero
                else:
                    currSectionIdx = newSectionIdx
                    currHeroIdx +=1
                    currBag[currHeroIdx] = list()
                    currValIdx +=1
                    encountered_deaths = False

            # past here is competitive
            elif 'Featured Stats' == currVal:
                currBag = competitiveBag
                currValIdx +=1
                currHeroIdx =-1
                encountered_deaths = False
                mode = FINDING_FIRST_HERO

            # no more heroes past here
            elif 'Achievements' == currVal:
                break

            else:
                label, val = valuesList[currValIdx : currValIdx +2]
                currBag[currHeroIdx].append((label, val))
                currValIdx +=2

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

# importable main
def requestPlayerBag(username, platform, region, delimiter='-'):
    if region:
        countSharp = len(username.split(delimiter)) -1
        if countSharp == 0:
            print('err: no number on PC battletag')
            print('aborting...')
            exit()
        elif countSharp >1:
            print('err: battletag has too many #')
            print('aborting...')
            exit()

        name, number = username.split(delimiter)
        try:
            n = int(number)
        except ValueError as v:
            print('err: given battletag has no number')
            print('aborting...')
            exit()

        url = 'https://playoverwatch.com/en-us/career/pc/' +region.lower() +'/' +name +'-' +number
    
    else:
        name = username
        url = 'https://playoverwatch.com/en-us/career/' +platform.lower() +'/' +username

    r = requests.get(url)
    htmlText = r.text
    playerBags = get_player_bag(htmlText, name)
    quickplayBag, competitiveBag = playerBags

    return quickplayBag, competitiveBag

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

