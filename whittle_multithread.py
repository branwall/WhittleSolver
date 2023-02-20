import copy
from itertools import permutations, repeat
import json
import math
import multiprocessing
from operator import itemgetter
import os
import sys
import time
import solutions_cached

# -------------------------
# This code solves [Whittle](https://whittlegame.com) by brute force.
# It takes a grid (pattern of playable vs. unplayable squares), determines
# where "words" go (i.e., contiguous playable squares in a straight line),
# and tests every permutation of dictionary words that could fit in the "word"
# of appropriate length.  Finally, it scores them (using solutions_cached.py) by
# number of overlapping words in dictionary definitions, to predict the likelihood
# that a given "solution" (set of required number of words) is the theme answer.
#
#
# Sorry it's all in one long python file!
# -------------------------

grid = []
letters = []
printEvery = 100000

wordLists = {}
## Grid globals
pulledFromFile = False
gridSerialized = []
wordsSerialized = []
wordsSerializedHorizontal = []
wordsSerializedVertical = []
overlaps = []
overlappingWords = []

## Length globals
wordsByLength = {2: [], 3: [], 4: [], 5: [], 6: []}
validLengths = []
letterDict = {}
solutionsByStartingWord = {}
startTime = time.time()


def import_wordLists(reduced=True):
	"""Opens the dictionary, saves to Wordlists.

	Args:
			reduced (bool, optional): Whether to use the reduced wordlists (if False, uses the full 
			wordlist, which is much longer and will require much more time and memory to compute). 
			Defaults to True.
	"""
	prepend = 'reduced' if reduced else ''
	global wordLists
	with open(prepend + '2.json') as wol2:
		with open(prepend + '3.json') as wol3:
			with open(prepend + '4.json') as wol4:
				with open(prepend + '5.json') as wol5:
					with open(prepend + '6.json') as wol6:
						wordLists[2] = json.load(wol2)
						wordLists[3] = json.load(wol3)
						wordLists[4] = json.load(wol4)
						wordLists[5] = json.load(wol5)
						wordLists[6] = json.load(wol6)


# -------------------------
# Collect the grid from user; process it to identify what words we need to create
# -------------------------


def inputProcess():
	"""Receives one line of grid as input and checks for validity.

	Returns:
			Formatted string like 'XOXXO' (or 'LAST') when input was valid. Else, returns False.
	"""
	i = input().upper()
	if i == "LAST":
		return i
	for ch in i:
		if len(i) != 5 or ((ch != "X") and (ch != "O") and (ch != "0")):
			print("Error: invalid input. Please start over.")
			return (False)
	return (i)


def getObjFromFile(letters=False):
	"""Returns the last used grid or set of letters.

	Args:
			letters (bool, optional): Whether to pull from the lastLetters file or not. Defaults to False.

	Returns:
			Either a grid object (array of strings) or a letters object (array of 1-char strings)
	"""
	global pulledFromFile
	if letters:
		if not os.path.exists("lastLetters"):
			print("No previous input found.")
			return None
		with open("lastLetters") as li:
			j = json.loads((li.read()))
			li.close()
			return j
	else:
		if not os.path.exists("lastGrid"):
			print("No previous input found.")
			return None
		with open("lastGrid") as li:
			j = json.loads((li.read()))
			li.close()
			pulledFromFile = True
			return j


def save_obj_to_file(obj, letters=False):
	"""Saves the user-inputted grid or letters to file for future use.

	Args:
			obj ([Str]): Either the active grid, or active list of letters.
			letters (bool, optional): Whether this object is letters. Defaults to False.
	"""
	if letters:
		with open("lastLetters", "w") as li:
			j = json.dump(obj, li)
			li.close()
	else:
		with open("lastGrid", "w") as li:
			j = json.dump(obj, li)
			li.close()


def import_grid():
	"""Gets a grid via user input or a file; writes it to globals.

	If user enters "last", it will pull from file.  
	Else, reads user input to format and serialize the grid.
	"""
	global grid, gridSerialized
	print('Enter grid, one line at a time, or enter "LAST" to ' +
	      'use a the grid and letters you entered previously.')
	while grid == []:
		print(
		    "Use an o, O, or 0 for playable spaces.  Use an x or X for blocked spaces."
		)
		for n in range(6):
			i = inputProcess()
			if i == "LAST":
				grid = getObjFromFile()
				if grid == None:
					grid = []
					break
				else:
					break
			elif i:
				grid.append(i)
			else:
				grid = []
				break
	save_obj_to_file(grid)
	for i, line in enumerate(grid):
		for j, letter in enumerate(line):
			if letter == "O" or letter == "0":
				gridSerialized.append((i, j))


def nextHCoord(coord):
	"""Increments the coordinate in the horizontal direction.

	Args:
			coord (tuple): The coordinate to increment (2-element tuple of integers)

	Returns:
			Coordinate: incremented coordinate.  Note: Does not check boundaries.
	"""
	return (coord[0], coord[1] + 1)


def nextVCoord(coord):
	"""Increments the coordinate in the vertical direction.

	Args:
			coord (tuple): The coordinate to increment (2-element tuple of integers)

	Returns:
			Coordinate: incremented coordinate.  Note: Does not check boundaries.
	"""
	return (coord[0] + 1, coord[1])


def inside(coord, wordCoords):
	"""Tests whether a coordinate falls within the range of coordinates that defines a 'word'

	Args:
			coord (tuple(int,int)): The coordinate to test for inclusion
			wordCoords (tuple(coord,coord)): The word (coordinate pair for start & end letter)
			to check against.

	Returns:
			bool: Whether the coordinate is inside the word.
	"""
	startCoord = wordCoords[0]
	endCoord = wordCoords[1]
	return (coord[0] >= startCoord[0] and coord[1] >= startCoord[1]
	        and coord[0] <= endCoord[0] and coord[1] <= endCoord[1])


def alreadyCaputred(coord, listOfWords):
	"""Tests whether we've already looked at this coordinate to determine words from grid.

	Args:
			coord (tuple(int,int)): The coordinate to check for already being caputred
			listOfWords ([tuple(coord,coord)]): The list of words we've already determined to exist.

	Returns:
			bool: Whether this coord has been seen already.
	"""
	for word in listOfWords:
		if inside(coord, word):
			return True
	return False


def serialize_words():
	"""Put the words in order.

	Using global variables, reads the serialized grid and determines the order of words.
	Horizontal words come first (from top to bottom), followed by vertical words sorted by highest 
	point in the word, with ties broken by left-to-right.

	Example:
  - - - - T
	F - - - H 
	O - - - R
	U - - - E 
	R - O N E 
	- T W O -

	"""
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
	"""Returns a list of grid coordinates that are part of more than one word.

	Using the global grid and word variables 
	(where "word" refers to a contiguous chunk of playable squares),
	walks through every playable square and sees whether it belongs to more than one word.  
	
	If so, there are overlapping words, and both words need to be
	checked at this index when testing a potential solution.

	Returns Tuple(int, int, int, int):
	(Index of Word A in which the coord appears;
	Index within Word A in which that letter appears;
	Index of Word B in which the coord appears;
	Index within Word B in which that letter appears)

	Raises:
			Exception when it can't find the word belonging to a given coordinate.
			Shouldn't ever occur with a valid grid.
	"""
	global overlaps, overlappingWords, gridSerialized, wordsSerializedVertical
	global wordsSerializedHorizontal, overlaps, wordsSerialized
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


def fastCheckOverlap(solution, overlappingWords):
	"""Given a potential solution, checks the spots where letters overlap to ensure equality.

	Args:
			solution ([str]): The list of words in the solution
			overlappingWords ([tuple(int,int,int,int)]): List of overlaps generated by find_overlaps()

	Returns:
			 bool: Whether all overlapping letters are equal (as is required for valid solution)
	"""
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
	if pulledFromFile:
		letters = getObjFromFile(True)
	else:
		while letters == []:
			ls = input("Enter usable letters\n").upper()
			if len(ls) == len(gridSerialized):
				letters = [*ls]
			else:
				print("Error: you entered the wrong number of letters")
		save_obj_to_file(letters, True)

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


def timeString(timeD):
	h, rem = divmod(round(timeD), 3600)
	m, s = divmod(rem, 60)
	if h < 10 and h != 0:
		h = "0" + str(h)
	if h == 0:
		h = ""
	if m < 10 and m != 0:
		m = "0" + str(m)
	if s < 10:
		s = "0" + str(s)
	if h != "":
		return (str(h) + ":" + str(m) + ":" + str(s))
	else:
		return (str(m) + ":" + str(s))


def emojiGrid(timeD):
	global grid
	emojistr = "Whittle #_ ("
	emojistr += timeString(timeD)
	emojistr += ")\n"
	for line in grid:
		for char in line:
			if char.upper() != "O" and char.upper() != "0":
				emojistr += "⬛"
			else:
				emojistr += "🟥"
		emojistr += "\n"
	print(emojistr)


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


def solutionIsValid(solution, letterDict, wordsSerialized, overlaps,
                    overlappingWords):
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
	if solutionIsValid(s, letterDict, wordsSerialized, overlaps,
	                   overlappingWords):
		return s
	else:
		return None


if __name__ == "__main__":
	useReducedWordlist = True
	for arg in sys.argv:
		if arg == "--full" or arg == "-full":
			useReducedWordlist = False
	import_wordLists(useReducedWordlist)
	import_grid()
	serialize_words()
	find_overlaps()
	handleWordLengths()
	handleLetters()
	cullWordlist()
	startTime = time.time()

	if useReducedWordlist:
		print("Using a reduced wordbank to optimize efficiency.")
	else:
		print("Using complete wordbank to definitively get the answer.")

	print("Permutations to test:",
	      "{:,}".format(totalSolutions(wordsSerialized, wordLists)))

	with multiprocessing.Pool() as pool:
		ts = totalSolutions(wordsSerialized, wordLists)
		args = (wordsSerialized, wordLists, letterDict, overlaps, overlappingWords)
		results = pool.starmap(testSolution, zip(range(ts), repeat(args)))

	et = time.time()

	print()
	print("Completed in", round(et - startTime, 2), "seconds.")
	time.sleep(1)
	all_solutions = [r for r in results if r != None]
	print("Solutions (", len(all_solutions), ")")
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

	for key, value in sbsw.items():
		print(key.upper())
		for sol in value:
			print('\t\t', sol)
		print()

	emojiGrid(et - startTime)

	print("Scoring solutions by likelihood of comprising theme answers")
	with multiprocessing.Pool() as p:
		scores = p.starmap(solutions_cached.score_solution,
		                   zip(all_solutions, repeat(wordLists)))

	scoredSolutions = {}
	solutionDefWords = {}
	for i, sol in enumerate(all_solutions):
		scoredSolutions[str(sol)] = scores[i][0]
		solutionDefWords[str(sol)] = scores[i][1]

	print()

	sortedSolutions = sorted(((v, k) for k, v in scoredSolutions.items()),
	                         reverse=True)
	for s in sortedSolutions:
		print(str(round(s[0], 2)) + ":\t", end='')
		solStrWords = s[1].strip('][').split(', ')
		olWords = solutionDefWords[s[1]]
		for w in solStrWords[:-1]:
			print(w.upper().strip("'") + ', ', end='')
		print(solStrWords[-1].upper().strip("'"), end='')
		if len(olWords) > 0:
			print('\t(', end='')
			for ww in olWords[:-1]:
				print(ww, end=', ')
			print(olWords[-1], end=")")
		print()

	if len(sortedSolutions) == 0:
		print("No solutions found! Try again with --full to use the full wordlist.")
		exit()

	print("Best Guess:", max(sortedSolutions, key=itemgetter(0))[1])
	print("Solution found from among", totalSolutions(wordsSerialized, wordLists),
	      "permutations and", len(all_solutions), "solutions.")

	with multiprocessing.Pool() as p:
		scrabbleScores = p.map(solutions_cached.scrabble_score_solution,
		                       all_solutions)

	scrabbledSolutions = {}
	for i, sol in enumerate(all_solutions):
		scrabbledSolutions[str(sol)] = scrabbleScores[i]

	print()

	sortedSolutions = sorted(((v, k) for k, v in scrabbledSolutions.items()),
	                         reverse=True)
	for s in sortedSolutions:
		print(str(round(s[0], 2)) + ":\t", end='')
		solStrWords = s[1].strip('][').split(', ')
		for w in solStrWords[:-1]:
			print(w.upper().strip("'") + ', ', end='')
		print(solStrWords[-1].upper().strip("'"))

	print("Best Guess (Scrabble Rules):",
	      max(sortedSolutions, key=itemgetter(0))[1])
