class Constant_Maker:

	def __init__( self, seed ):
		self.curr_id = seed

	def generate_id( self, count=1 ):

		if count == 1:
			r = self.curr_id
			self.curr_id += 1
			return r

		start = self.curr_id
		ex_end = self.curr_id +count
		self.curr_id += count

		return range( start, ex_end )

ARB_CONST = 768
CONST_MAKER = Constant_Maker( ARB_CONST )

import codecs
ENCODING = 'utf-8'
def get_values( html_text, handle ):

	r_values = list()

	LOOKING_FOR_GT, LOOKING_FOR_C = range( 2 )

	read_mode = LOOKING_FOR_GT
	encountered_handle = False

	curr_string = ''
	for c in html_text:

		if LOOKING_FOR_GT == read_mode:
			if '>' == c:
				curr_string = ''
				read_mode = LOOKING_FOR_C

		elif LOOKING_FOR_C == read_mode:

			if c != '<':
				curr_string += c

			else:

				read_mode = LOOKING_FOR_GT

				if len( curr_string ) == 0: continue

				if encountered_handle:
					r_values.append( curr_string )

				else:

					if handle == curr_string:
						encountered_handle = True
						r_values.append( curr_string )

					else: continue

	return r_values

def get_player_bag( html_text, handle ):

	fields_after_handle = get_values( html_text, handle )

	quickplay_bag = dict()
	competitive_bag = dict()
	player_bags = [ quickplay_bag, competitive_bag ]

	LOOKING_FOR_HERO, READING_STATS = CONST_MAKER.generate_id( 2 )

	current_hero = -1
	read_mode = LOOKING_FOR_HERO
	curr_idx = 0
	#section_labels = [ 'Combat', 'Assists', 'Best', 'Average', 'Deaths', 'Match Awards', 'Game', 'Miscellaneous' ]
	section_labels = [ 'Combat', 'Assists', 'Best', 'Average', 'Match Awards', 'Game', 'Miscellaneous' ]
	encountered_deaths = False
	curr_val = fields_after_handle[ curr_idx ]
	destination_bag = quickplay_bag
	while( curr_val != 'Achievements' ):

		try:
			curr_val = fields_after_handle[ curr_idx ]
			if 'Achievements' == curr_val:
				break
		except IndexError as i:
			print( 'error with', curr_idx )
			break

		if READING_STATS == read_mode:

			if 'Hero Specific' == curr_val:
				current_hero += 1
				destination_bag[ current_hero ] = list()
				curr_idx += 1

			# throws off the 2-val pull in the else-branch
			elif curr_val in section_labels:
				curr_idx += 1

			# Deaths is a field AND a section label
			# Throws off the indexing otherwise
			elif 'Deaths' == curr_val and ( not encountered_deaths ):
				encountered_deaths = True
				curr_idx += 1

			# marks the competitive data
			elif 'Featured Stats' == curr_val:
				read_mode = LOOKING_FOR_HERO
				current_hero = -1
				destination_bag = competitive_bag
				continue

			else:
				label, val = fields_after_handle[ curr_idx : curr_idx +2 ]
				destination_bag[ current_hero ].append( ( label, val ) )
				curr_idx += 2

		elif LOOKING_FOR_HERO == read_mode:

			if 'Hero Specific' == curr_val:
				read_mode = READING_STATS
				current_hero += 1
				destination_bag[ current_hero ] = list()
				encountered_deaths = False
			curr_idx += 1

	return player_bags

import requests
def main( username, platform, region ):

	if region:
		count_sharp = len( username.split( '#' ) ) -1
		if count_sharp == 0:
			print( 'err: no number on PC battletag' )
			print( 'aborting...' )
			exit()
		elif count_sharp > 1:
			print( 'err: battletag has too many #' )
			print( 'aborting...' )
			exit()

		name, number = username.split( '#' )
		try:
			n = int( number )
		except ValueError as v:
			print( 'err: given battletag has no number' )
			exit()

		url = 'https://playoverwatch.com/en-us/career/pc/' +region.lower() +'/' +name +'-' +number
	
	else:
		name = username
		url = 'https://playoverwatch.com/en-us/career/' +platform.lower() +'/' +username
		
	r = requests.get( url )
	html_text = r.text
	player_bags = get_player_bag( html_text, name )

	bag_and_label = list()
	bag_and_label.append( ( 'Quick Play', player_bags[ 0 ] ) )
	bag_and_label.append( ( 'Competitive', player_bags[ 1 ] ) )
	for label, bag in bag_and_label:
		print( label )
		
		for hero in bag:
			print( '\t{0}'.format( hero ) )

			for label, val in bag[ hero ]:
				print( '\t\t{0} | {1}'.format( label, val ) )
# ---

def complain( prob_string ):
	print( prob_string )
	print( 'Aborting...' )

# handle different platforms
import sys
if __name__=='__main__':
	MIN_ARG = 2
	MAX_ARG = 3
	region = None
	if len( sys.argv[ 1: ] ) < MIN_ARG:
		print( 'usage: main.py USERNAME(#NUMBER) PSN|XBL|( PC US|KR|EU )' )
		print( 'aborting...' )
		exit()

	elif len( sys.argv[ 1: ] ) == MIN_ARG:

		username = sys.argv[ 1 ]
		platform = sys.argv[ 2 ]
		if platform not in [ 'PSN', 'XBL' ]:
			print( 'err: 2-argument argument 2 not PSN or XBL' )
			print( 'usage: main.py USERNAME(#NUMBER) PSN|XBL|( PC US|KR|EU )' )
			print( 'aborting...' )
			exit()

	elif len( sys.argv[ 1: ] ) == MAX_ARG:

		username = sys.argv[ 1 ]
		platform = sys.argv[ 2 ]
		if platform != 'PC':
			print( 'err: 3-argument argument 2 not PC' )
			print( 'usage: main.py USERNAME(#NUMBER) PSN|XBL|( PC US|KR|EU )' )
			print( 'aborting...' )
			exit()
		region = sys.argv[ 3 ]
		if region not in [ 'US', 'KR', 'EU' ]:
			print( 'err: 3-argument argument 3 not US, KR, or EU' )
			print( 'usage: main.py USERNAME(#NUMBER) PSN|XBL|( PC US|KR|EU )' )
			print( 'aborting...' )
			exit()

	else:
		print( 'err: more than 3 arguments' )
		print( 'usage: main.py USERNAME(#NUMBER) PSN|XBL|( PC US|KR|EU )' )
		print( 'aborting...' )
		exit()

	main( username, platform, region )