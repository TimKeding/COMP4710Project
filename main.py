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


def get_values(html_text, handle):
    r_values = list()

    LOOKING_FOR_GT, LOOKING_FOR_C, LOOKING_FOR_ID = range(3)

    id_name = 'data-category-id="0'

    read_mode = LOOKING_FOR_GT
    encountered_handle = False

    curr_string = ''
    for c in html_text:

        if LOOKING_FOR_GT == read_mode:
            if '>' == c:
                curr_string = ''
                read_mode = LOOKING_FOR_C
            elif 'd' == c:
                curr_string = ''
                pos = 1
                read_mode = LOOKING_FOR_ID

        elif LOOKING_FOR_C == read_mode:

            if c != '<':
                curr_string += c

            else:

                read_mode = LOOKING_FOR_GT

                if len(curr_string) == 0: continue

                if encountered_handle:
                    #print(curr_string)
                    r_values.append(curr_string)

                else:

                    if handle == curr_string:
                        encountered_handle = True
                        #print(curr_string)
                        r_values.append(curr_string)

                    else:
                        continue

        elif LOOKING_FOR_ID == read_mode:

            if pos < len(id_name) and c == id_name[pos]:
                pos += 1

            elif pos == len(id_name) and c != '"':
                curr_string += c

            else:

                read_mode = LOOKING_FOR_GT

                if len(curr_string) == 0: continue

                if encountered_handle:
                    #print(curr_string)
                    r_values.append('0' + curr_string)

                else:

                    if handle == curr_string:
                        encountered_handle = True
                        #print(curr_string)
                        r_values.append('0' + curr_string)

                    else:
                        continue

    return r_values


def get_player_bag(html_text, handle):
    fields_after_handle = get_values(html_text, handle)

    quickplay_bag = dict()
    competitive_bag = dict()
    player_bags = [quickplay_bag, competitive_bag]

    LOOKING_FOR_HERO, READING_STATS = CONST_MAKER.generate_id(2)

    current_hero = -1
    read_mode = LOOKING_FOR_HERO
    curr_idx = 0
    # section_labels = [ 'Combat', 'Assists', 'Best', 'Average', 'Deaths', 'Match Awards', 'Game', 'Miscellaneous' ]
    section_labels = ['Combat', 'Assists', 'Best', 'Average', 'Match Awards', 'Game', 'Miscellaneous']
    encountered_deaths = False
    curr_val = fields_after_handle[curr_idx]
    all_hero_ids = ['0x02E0000000000002', '0x02E0000000000003', '0x02E0000000000004', '0x02E0000000000005', '0x02E0000000000006', '0x02E0000000000007', '0x02E0000000000008', '0x02E0000000000009',
                  '0x02E000000000000A', '0x02E0000000000015', '0x02E0000000000016', '0x02E0000000000020', '0x02E0000000000029', '0x02E0000000000040', '0x02E0000000000042', '0x02E0000000000065',
                  '0x02E0000000000068', '0x02E000000000006E', '0x02E0000000000079', '0x02E000000000007A', '0x02E00000000000DD', '0x02E000000000013B']
    all_heroes = ['Reaper', 'Tracer', 'Mercy', 'Hanzo', 'Torbjorn', 'Reinhardt', 'Pharah', 'Winston', 'Widowmaker', 'Bastion', 'Symmetra', 'Zenyatta', 'Genji', 'Roadhog', 'McCree', 'Junkrat',
                  'Zarya', 'Soldier 76', 'Lucio', 'D.Va', 'Mei', 'Ana']
    for hero in range(len(all_heroes)):
        quickplay_bag[hero] = list()
        competitive_bag[hero] = list()
        quickplay_bag[hero].append(('Hero:', all_heroes[hero]))
        competitive_bag[hero].append(('Hero:', all_heroes[hero]))

    destination_bag = quickplay_bag
    while (curr_val != 'Achievements'):

        try:
            curr_val = fields_after_handle[curr_idx]
            if 'Achievements' == curr_val:
                break
        except IndexError as i:
            print('error with', curr_idx)
            break

        if READING_STATS == read_mode:

            if 'Hero Specific' == curr_val:
                #current_hero += 1
                #destination_bag[current_hero] = list()
                curr_idx += 1

            # throws off the 2-val pull in the else-branch
            elif curr_val in section_labels:
                curr_idx += 1

            # Deaths is a field AND a section label
            # Throws off the indexing otherwise
            elif 'Deaths' == curr_val and (not encountered_deaths):
                encountered_deaths = True
                curr_idx += 1

            # marks the competitive data
            elif 'Featured Stats' == curr_val:
                read_mode = LOOKING_FOR_HERO
                #current_hero = -1
                destination_bag = competitive_bag
                continue

            else:
                label, val = fields_after_handle[curr_idx: curr_idx + 2]
                destination_bag[current_hero].append((label, val))
                curr_idx += 2

        elif LOOKING_FOR_HERO == read_mode:

            if '0x02E' == curr_val[0:5] and curr_val[-1] != 'F':
                read_mode = READING_STATS
                current_hero = all_hero_ids.index(curr_val)
                #current_hero += 1
                destination_bag[current_hero] = list()
                encountered_deaths = False
            curr_idx += 1

    return player_bags


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

