# get all competitive Mercy data

# first, for each given file, get username, platform, region
# usage:
#
#		python N mercyAggregator.py A1 A2 A3 ...
#			such that N is a natural number
#			such that An = (filename PC KR|US|EU) | (filename PSN|XBL)
#
#		file output format
#
#			label!value|label2!value
#			- commas in html values
#			- : in html values
#
import sys
from main import Constant_Maker
from main import requestPlayerBag
from main import PlayerNotFound

if __name__=='__main__':

	args = sys.argv[1:]

	# how much users to pull
	try:
		NUM_ACCOUNTS_TO_LOAD = int(sys.argv[1])
	except ValueError as v:
		print(sys.argv[1], ' is not an integer')
		print('aborting...')
		exit()
	if NUM_ACCOUNTS_TO_LOAD <= 0:
		print(sys.argv[1], ' is not useful to run with')
		print('aborting...')
		exit()

	# read as stream
	# - 2 possibilities
	#	1 - triplet: (filename PC KR|US|EU)
	#	2 - couplet: (filename PSN|XBL)
	ARB_FIRST_CONST = 99
	CONSTANTS = Constant_Maker(ARB_FIRST_CONST)
	NUM_MODES = 4
	READ_FILENAME, READ_PLATFORM, READ_REGION, GET_BAG = CONSTANTS.generate_id(NUM_MODES)
	VALID_PLATFORMS = ['PC', 'PSN', 'XBL']
	VALID_REGIONS = ['KR', 'US', 'EU']
	FILE_DELIMITER = '-'

	mode = READ_FILENAME
	currPackage = None

	# go through the given files
	for arg in args:

		if READ_FILENAME == mode:
			currPackage = list()
			filename = arg
			currPackage.append(filename)
			mode = READ_PLATFORM

		elif READ_PLATFORM == mode:
			platform = arg
			
			# bad platform guard
			if platform not in VALID_PLATFORMS:
				print('err: ', platform, ' not in [PC, PSN, XBL]')
				print('aborting...')
				break
			currPackage.append(platform)

			# triplet
			if 'PC' == platform:
				mode = READ_REGION

			# couplet
			else:
				# no region
				currPackage.append(None)
				mode = GET_BAG

		elif READ_REGION == mode:
			region = arg

			# bad region guard
			if region not in VALID_REGIONS:
				print('err: ', region, ' not in [KR, US, EU]')
				print('aborting...')
				break

			currPackage.append(region)
			mode = GET_BAG

		if GET_BAG == mode:
			numAccountsLoaded = 0

			filename, platform, region = currPackage
			currPackage = list()

			with open(filename) as source:
				for name in source:
					# try to fetch
					try:
						_, competitiveBag = requestPlayerBag(name, platform, region, FILE_DELIMITER)
					except PlayerNotFound as p:
						print(str(p))
						continue

					# player does not play mercy -> move on
					mercyIdx = None
					for currHeroIdx in competitiveBag:
						for label, _ in competitiveBag[currHeroIdx]:
							if 'Players Resurrected' != label:
								continue
							mercyIdx = currHeroIdx
							break
						if None != mercyIdx:
							break
					if None == mercyIdx:
						continue

					# DEBUG - progress printer
					name = name.strip()
					print(name)
					sys.stdout.flush()

					# write mercy stats to file - Pipe Separated Value Format ; commas exist
					with open('mercyStats.txt', 'a') as destFile:
						numAccountsLoaded +=1

						# collect vals
						labelAndValueList = list()
						labelAndValueList.append(('player',name))
						for label, value in competitiveBag[mercyIdx]:
							labelAndValueList.append((label,value))

						# write labels and vals
						for label, value in labelAndValueList[:-1]:
							destFile.write('{0}!{1}|'.format(label, value))
						lastTuple = labelAndValueList[-1]
						destFile.write('{0}!{1}\n'.format(lastTuple[0], lastTuple[1]))

						# check if collected desired amount
						if numAccountsLoaded > NUM_ACCOUNTS_TO_LOAD:
							exit()