import copy
from itertools import permutations, repeat
import json
import math
import multiprocessing
import sys
import time

# -------------------------
# Open the dictionary, set up filters to sort by length
# -------------------------

grid = [] ##! Change back!
letters = []  ##! FIX TO EMPTY ARRAY
printEvery = 10000  ##! Reset to 10,000
# grid = ['XXOXO', 'XOOOO', 'XXOXO', 'XXOXO', 'XXOXX', 'OOOOX']
# letters = [
#     "I", "A", "B", "G", "T", "A", "P", "T", "S", "U", "R", "B", "S", "A", "H"
# ]

wordLists = {}
## Grid stuff
gridSerialized = []
wordsSerialized = []
wordsSerializedHorizontal = []
wordsSerializedVertical = []
overlaps = []
overlappingWords = []

## Length stuff
wordsByLength = {2: [], 3: [], 4: [], 5: [], 6: []}
validLengths = []
letterDict = {}
solutionsByStartingWord = {}
startTime = time.time()


def import_wordLists():
	global wordLists
	with open('reduced2.json') as wol2:
		with open('reduced3.json') as wol3:
			with open('reduced4.json') as wol4:
				with open('reduced5.json') as wol5:
					with open('reduced6.json') as wol6:
						wordLists[2] = json.load(wol2)
						wordLists[3] = json.load(wol3)
						wordLists[4] = json.load(wol4)
						wordLists[5] = json.load(wol5)
						wordLists[6] = json.load(wol6)


def len2(pair):
	key, value = pair
	if len(key) != 2:
		return False
	return True


def len3(pair):
	key, value = pair
	if len(key) != 3:
		return False
	return True


def len4(pair):
	key, value = pair
	if len(key) != 4:
		return False
	return True


def len5(pair):
	key, value = pair
	if len(key) != 5:
		return False
	return True


def len6(pair):
	key, value = pair
	if len(key) != 6:
		return False
	return True


# -------------------------
# Collect the grid from user; process it to identify what words we need to create
# -------------------------


def inputProcess():
	i = input().upper()
	for ch in i:
		if len(i) != 5 or ((ch != "X") and (ch != "O") and (ch != "0")):
			print("Error: invalid input. Please start over.")
			return (False)
	return (i)


def import_grid():
	global grid, gridSerialized
	while grid == []:
		print("Enter grid, one line at a time.")
		print(
		    "Use an o, O, or 0 for playable spaces.  Use an x or X for blocked spaces."
		)
		for n in range(6):
			i = inputProcess()
			if i:
				grid.append(i)
			else:
				grid = []
				break

	for i, line in enumerate(grid):
		for j, letter in enumerate(line):
			if letter == "O" or letter == "0":
				gridSerialized.append((i, j))


def nextHCoord(coord):
	return (coord[0], coord[1] + 1)


def nextVCoord(coord):
	return (coord[0] + 1, coord[1])


def inside(coord, wordCoords):
	startCoord = wordCoords[0]
	endCoord = wordCoords[1]
	return (coord[0] >= startCoord[0] and coord[1] >= startCoord[1]
	        and coord[0] <= endCoord[0] and coord[1] <= endCoord[1])


def alreadyCaputred(coord, listOfWords):
	for word in listOfWords:
		if inside(coord, word):
			return True
	return False


def serialize_words():
	global wordsSerialized, gridSerialized, wordsSerializedHorizontal, wordsSerializedVertical

	for coord in gridSerialized:
		if not alreadyCaputred(coord, wordsSerializedHorizontal):
			terminalCoord = coord
			while nextHCoord(terminalCoord) in gridSerialized:
				terminalCoord = nextHCoord(terminalCoord)
			if terminalCoord[1] > coord[1]:
				wordsSerializedHorizontal.append((coord, terminalCoord))
		else:
			continue

	for coord in gridSerialized:
		if not alreadyCaputred(coord, wordsSerializedVertical):
			terminalCoord = coord
			while nextVCoord(terminalCoord) in gridSerialized:
				terminalCoord = nextVCoord(terminalCoord)
			if terminalCoord[0] > coord[0]:
				wordsSerializedVertical.append((coord, terminalCoord))
		else:
			continue

	wordsSerialized = wordsSerializedHorizontal + wordsSerializedVertical


def find_overlaps():
	global overlaps, overlappingWords, gridSerialized, wordsSerializedVertical, wordsSerializedHorizontal, overlaps, wordsSerialized
	for coord in gridSerialized:
		if (alreadyCaputred(coord, wordsSerializedVertical)
		    and alreadyCaputred(coord, wordsSerializedHorizontal)):
			overlaps.append(coord)

	for overlapCoord in overlaps:
		wordA = None
		wordB = None
		wordAIdx = None
		wordBIdx = None
		for wordIndex, wordRange in enumerate(wordsSerialized):
			startCoord = wordRange[0]
			endCoord = wordRange[1]
			if (overlapCoord[0] >= startCoord[0] and overlapCoord[1] >= startCoord[1]
			    and overlapCoord[0] <= endCoord[0] and overlapCoord[1] <= endCoord[1]):

				# if the coordinate we're checking is contained in this word,
				# make sure the letter in this word either matches the target,
				# or set the target to the current word.
				charIndex = max(overlapCoord[0] - startCoord[0],
				                overlapCoord[1] - startCoord[1])
				if wordA == None:
					wordA = wordIndex
					wordAIdx = charIndex
				else:
					wordB = wordIndex
					wordBIdx = charIndex
		if wordAIdx == None or wordBIdx == None:
			raise Exception("Couldn't find coordinate's parent words for", overlapCoord)
		overlappingWords.append((wordA, wordAIdx, wordB, wordBIdx))


def fastCheckOverlap(solution,overlappingWords):
	for ol in overlappingWords:
		wordA = ol[0]
		wordB = ol[2]
		wordAIdx = ol[1]
		wordBIdx = ol[3]
		if solution[wordA][wordAIdx] != solution[wordB][wordBIdx]:
			return False
		
	return True


# -------------------------
# Determine the length of each slot in the grid, so we know how long the target words are
# -------------------------


def getWordLength(word):
	sc = word[0]
	ec = word[1]
	if sc[0] == ec[0]:
		#if they're in the same row, treat it as horizontal word
		return ec[1] - sc[1] + 1
	else:
		#if they're not in the same row, it's vertical.
		return ec[0] - sc[0] + 1


def handleWordLengths():
	global wordsSerialized, wordsByLength, validLengths
	for word in wordsSerialized:
		wordsByLength[getWordLength(word)].append(word)
	for key in wordsByLength.keys():
		if len(wordsByLength[key]) > 0:
			validLengths.append(key)


def handleLetters():
	global letters, gridSerialized, letterDict
	while letters == []:
		ls = input("Enter usable letters\n").upper()
		if len(ls) == len(gridSerialized):
			letters = [*ls]
		else:
			print("Error: you entered the wrong number of letters")

	for letter in letters:
		if letter in letterDict:
			letterDict[letter] += 1
		else:
			letterDict[letter] = 1


# -------------------------
# Cull the wordlist to only plausible solutions (right length; right letters).
# -------------------------
def cullWordlist():
	global wordLists, letters

	dt = 0
	print("Full Dictionary Size:")
	for key in wordLists.keys():
		cl = len(wordLists[key])
		dt += cl
		print(key, ":", cl)
	print("(", dt, "total )")

	def wordCouldBeValid(word, letters):
		usableletters = copy.deepcopy(letters)
		if len(word) not in validLengths:
			return False
		for letter in word.upper():
			if letter not in usableletters:
				return False
			usableletters.remove(letter)
		return True

	deleteList = {2: [], 3: [], 4: [], 5: [], 6: []}
	## Trim out unusable words
	for i in range(5):
		for word in wordLists[i + 2].keys():
			if not wordCouldBeValid(word, letters):
				deleteList[len(word)].append(word)
	for key in deleteList.keys():
		for word in deleteList[key]:
			del wordLists[len(word)][word]

	dt = 0
	print("Dictionary Size After Culling:")
	for key in wordLists.keys():
		cl = len(wordLists[key])
		dt += cl
		print(key, ":", cl)
	print("(", dt, "total )")


def totalSolutions(wordsSerialized, wordLists):
	n = 1
	for word in wordsSerialized:
		n = n * len(wordLists[getWordLength(word)])
	return n


# -------------------------
# Print Utils
# -------------------------


def printGrid():
	global grid
	for line in grid:
		for char in line:
			if char.upper() != "O" and char.upper() != "0":
				print("▩ ", end='')
			else:
				print("▢ ", end='')
		print()


def letterAtCoord(coord, solution, wordsSerialized):
	for wordIndex, wordRange in enumerate(wordsSerialized):
		startCoord = wordRange[0]
		endCoord = wordRange[1]

		# Check if this word contains the coordinate from which we want to print
		if (coord[0] >= startCoord[0] and coord[1] >= startCoord[1]
		    and coord[0] <= endCoord[0] and coord[1] <= endCoord[1]):

			#If so, identify what position in the word it is.
			charIndex = max(coord[0] - startCoord[0], coord[1] - startCoord[1])

			return (solution[wordIndex][charIndex].upper())
	return ("▩")


def prettyPrint(solution, wordsSerialized):
	#For every spot on the grid . . .
	for line in range(6):
		for column in range(5):
			coord = (line, column)
			print(letterAtCoord(coord, solution, wordsSerialized), " ", end='')
		print()
		sys.stdout.flush()
	print("***************")
	print()


# -------------------------
# Test every permutation of plausible words to see if it's a valid solution
# -------------------------


def solutionIsValid(solution, letterDict, wordsSerialized,overlaps,overlappingWords):
	lettersInSolution = {}
	if not fastCheckOverlap(solution, overlappingWords):
		return False

	for word in solution:
		for char in word.upper():
			if char in lettersInSolution:
				lettersInSolution[char] += 1
			else:
				lettersInSolution[char] = 1

	for coord in overlaps:
		lettersInSolution[letterAtCoord(coord, solution, wordsSerialized)] -= 1

	for key, value in lettersInSolution.items():
		if letterDict[key] != value:
			return False
	# prettyPrint(solution, wordsSerialized)
	return True


def getSolutionNumber(i, wordsSerialized, wordLists):
	# return ['TUBA', 'HARP', 'GUITAR', 'BASS']  ##! Delete tis line
	solutionWords = []
	for slot in reversed(wordsSerialized):
		length = getWordLength(slot)
		totalNLengthWords = len(wordLists[length])
		product = 1
		for wordToTheRight in solutionWords:
			product *= len(wordLists[len(wordToTheRight)])
		x = math.floor(i / product)
		wordIndex = x % totalNLengthWords

		solutionWords.append(list(wordLists[length].keys())[wordIndex])
	return list(reversed(solutionWords))


def testSolution(i, args):
	wordsSerialized = args[0]
	wordLists = args[1]
	letterDict = args[2]
	overlaps = args[3]
	overlappingWords = args[4]
	s = getSolutionNumber(i, wordsSerialized, wordLists)
	if i % printEvery == 0:
		et = time.time()
		timeDelta = round(et - startTime)
		prog = i / totalSolutions(wordsSerialized, wordLists)
		pct = round(100 * prog, 2)
		etc = round(timeDelta / max(prog, 0.0000000000001) - timeDelta)
		etcStr = "{:,}".format(etc)
		etcMin = round(etc / 60, 1)
		etcMinStr = "{:,}".format(etcMin)
		its = round(i / max(timeDelta, 0.00000000000001), 1)
		print(pct,
		      "%",
		      "Elapsed:",
		      timeDelta,
		      "s",
		      "ETC: ",
		      etcStr,
		      "s",
		      etcMinStr,
		      "m",
		      "Currently testing",
		      s,
		      "(",
		      its,
		      "it/s)",
		      end='\r',
		      flush=True)
	if solutionIsValid(s, letterDict, wordsSerialized,overlaps,overlappingWords):
		return s
	else:
		return None


if __name__ == "__main__":
	import_wordLists()
	import_grid()
	serialize_words()
	find_overlaps()
	handleWordLengths()
	handleLetters()
	cullWordlist()
	startTime = time.time()

	
	print("Permutations to test:",
	      "{:,}".format(totalSolutions(wordsSerialized, wordLists)))

	
	

	with multiprocessing.Pool(15) as pool:
		ts = totalSolutions(wordsSerialized, wordLists)
		args = (wordsSerialized, wordLists, letterDict,overlaps,overlappingWords)
		results = pool.starmap(testSolution, zip(range(ts), repeat(args)))
		# for idx in range(ts):
		# 	results[idx] = (pool.apply_async(testSolution,args=(idx,args)))
		# 	pass

	
	print()
	print("Completed in", round(time.time() - startTime, 2), "seconds.")
	time.sleep(1)
	all_solutions = [r for r in results if r != None]
	print("Solutions (",len(all_solutions),")")
	time.sleep(1)
	for sol in all_solutions:
		prettyPrint(sol, wordsSerialized)
	
	sbsw = {}
	for sol in all_solutions:
		if sol[0] in sbsw:
			sbsw[sol[0]].append(sol)
		else:
			sbsw[sol[0]] = [sol]
	print()
	

	for key,value in sbsw.items():
		print(key.upper())
		for sol in value:
			print('\t\t',sol)
		print()
