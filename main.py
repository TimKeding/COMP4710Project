import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

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
    srRanking = 0

    mode =FINDING_QUICKPLAY
    valIdx =0
    while valIdx <len(valueList):

        val =valueList[valIdx]

        if valIdx == 2:
            srRanking = val

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
                targetBag[heroID] = list()
                targetBag[heroID].append(('SR', srRanking))
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
    heroes = {'040': 'roadhog', '002': 'reaper', '003': 'tracer', '004': 'mercy', '005': 'hanzo', '006': 'torbjorn', '007': 'reinhardt', '008': 'pharah', '009': 'winston', '00A': 'widowmaker', '015': 'bastion',
              '016': 'symmetra', '020': 'zenyatta', '029': 'genji', '042': 'mccree', '065': 'junkrat', '068': 'zarya', '06E': 'soldier76', '079': 'lucio', '07A': 'd.va', '0DD': 'mei', '13B': 'ana'}
    try:

        player_bags = get_player_bag(html_text, name)


        for hero in player_bags[1]:
            export = export_file + heroes[hero] + '_results'

            write_results = open(export, 'a')
            write_results.write(username + '\n')

            for label, val in player_bags[1][hero]:
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

def clearFiles():
    consoles = {'pc', 'psn', 'xbl'}
    heroes = {'ana', 'bastion', 'd.va', 'genji', 'hanzo', 'lucio', 'mccree', 'mei', 'mercy', 'pharah', 'reaper', 'reinhardt', 'roadhog', 'soldier76', 'sombra', 'tracer', 'winston', 'widowmaker', 'zarya', 'zenyatta'}

    for console in consoles:
        for hero in heroes:
            open('res/competitive/' + console + '/' + hero + '_results', 'w').close()

def performClustering():
    raw_data = 'out/us_ana'
    dataset = pd.read_csv(raw_data, delimiter=';', header=1, usecols=(*range(1, 55), *range(64, 75)))

    dataset = np.nan_to_num(dataset)
    dataset = StandardScaler().fit_transform(dataset)



    db = DBSCAN(eps=10, min_samples=200, algorithm='auto').fit(dataset)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = 'k'

        class_member_mask = (labels == k)

        xy = dataset[class_member_mask & core_samples_mask]
        plt.plot(xy[:, 0], xy[:, 55], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=14)

        xy = dataset[class_member_mask & ~core_samples_mask]
        plt.plot(xy[:, 0], xy[:, 55], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=6)

    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

if __name__ == '__main__':

    performClustering()
    # clearFiles()
    #
    # pc_us_file = open('res/pc_us.txt', 'r')
    # for line in pc_us_file:
    #     try:
    #         main(line.strip('\n'), 'PC', 'US', 'res/competitive/pc/')
    #     except:
    #         pass
    # pc_us_file.close()
    #
    # pc_eu_file = open('res/pc_eu.txt', 'r')
    # for line in pc_eu_file:
    #     try:
    #         main(line.strip('\n'), 'PC', 'US', 'res/competitive/pc/')
    #     except:
    #         pass
    #
    #
    # pc_kr_file = open('res/pc_kr.txt', 'r')
    # for line in pc_kr_file:
    #     try:
    #         main(line.strip('\n'), 'PC', 'US', 'res/competitive/pc/')
    #     except:
    #         pass
    #
    # xbl_file = open('res/xbl.txt', 'r')
    # for line in xbl_file:
    #     try:
    #         main(line.strip('\n'), 'XBL', None, 'res/competitive/xbl/')
    #     except:
    #         pass
    #
    # psn_file = open('res/psn.txt', 'r')
    # for line in psn_file:
    #     try:
    #         main(line.strip('\n'), 'PSN', None, 'res/competitive/psn/')
    #     except:
    #         pass