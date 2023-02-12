import copy
from itertools import permutations
import json
import math
import multiprocessing
import sys
import time

# -------------------------
# Open the dictionary, set up filters to sort by length
# -------------------------

wordLists = {}

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


grid = ['XXOXO', 'XOOOO', 'XXOXO', 'XXOXO', 'XXOXX', 'OOOOX']
# grid = [] ##! Change back!
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

gridSerialized = []
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


wordsSerializedHorizontal = []
for coord in gridSerialized:
	if not alreadyCaputred(coord, wordsSerializedHorizontal):
		terminalCoord = coord
		while nextHCoord(terminalCoord) in gridSerialized:
			terminalCoord = nextHCoord(terminalCoord)
		if terminalCoord[1] > coord[1]:
			wordsSerializedHorizontal.append((coord, terminalCoord))
	else:
		continue

wordsSerializedVertical = []
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

overlaps = []
for coord in gridSerialized:
	if (alreadyCaputred(coord, wordsSerializedVertical)
	    and alreadyCaputred(coord, wordsSerializedHorizontal)):
		overlaps.append(coord)

overlappingWords = []
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


def fastCheckOverlap(solution):
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


wordsByLength = {2: [], 3: [], 4: [], 5: [], 6: []}
for word in wordsSerialized:
	wordsByLength[getWordLength(word)].append(word)

validLengths = []
for key in wordsByLength.keys():
	if len(wordsByLength[key]) > 0:
		validLengths.append(key)

letters = [
    "I", "A", "B", "G", "T", "A", "P", "T", "S", "U", "R", "B", "S", "A", "H"
]
# letters = []  ##! FIX TO EMPTY ARRAY
while letters == []:
	ls = input("Enter usable letters\n").upper()
	if len(ls) == len(gridSerialized):
		letters = [*ls]
	else:
		print("Error: you entered the wrong number of letters")

letterDict = {}
for letter in letters:
	if letter in letterDict:
		letterDict[letter] += 1
	else:
		letterDict[letter] = 1

# -------------------------
# Cull the wordlist to only plausible solutions (right length; right letters).
# -------------------------
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


def totalSolutions():
	n = 1
	for word in wordsSerialized:
		n = n * len(wordLists[getWordLength(word)])
	return n


print("Permutations to test:", "{:,}".format(totalSolutions()))

# -------------------------
# Print Utils
# -------------------------


def printGrid():
	for line in grid:
		for char in line:
			if char.upper() != "O" and char.upper() != "0":
				print("▩ ", end='')
			else:
				print("▢ ", end='')
		print()


def letterAtCoord(coord, solution):
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


def prettyPrint(solution):
	#For every spot on the grid . . .
	for line in range(6):
		for column in range(5):
			coord = (line, column)
			print(letterAtCoord(coord, solution), " ", end='')
		print()
		sys.stdout.flush()
	print("***************")
	print()


# -------------------------
# Test every permutation of plausible words to see if it's a valid solution
# -------------------------


def checkCoordConsistency(coord, solution):
	target = ""
	for wordIndex, wordRange in enumerate(wordsSerialized):
		startCoord = wordRange[0]
		endCoord = wordRange[1]
		if (coord[0] >= startCoord[0] and coord[1] >= startCoord[1]
		    and coord[0] <= endCoord[0] and coord[1] <= endCoord[1]):
			# if the coordinate we're checking is contained in this word,
			# make sure the letter in this word either matches the target,
			# or set the target to the current word.
			charIndex = max(coord[0] - startCoord[0], coord[1] - startCoord[1])
			if target == "":
				target = solution[wordIndex][charIndex]
			else:
				if target != solution[wordIndex][charIndex]:
					return False
	else:
		return True


def solutionIsValid(solution):
	lettersInSolution = {}

	if not fastCheckOverlap(solution):
		return False

	for word in solution:
		for char in word.upper():
			if char in lettersInSolution:
				lettersInSolution[char] += 1
			else:
				lettersInSolution[char] = 1

	for coord in overlaps:
		lettersInSolution[letterAtCoord(coord, solution)] -= 1

	for key, value in lettersInSolution.items():
		if letterDict[key] != value:
			return False

	prettyPrint(solution)
	return True


solutionsByStartingWord = {}


def getSolutionNumber(i):
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


startTime = time.time()

# def testSolutionRecursively(wordsSoFar = [],slotNo = 0):
# 	if wordsSoFar != [] and (len(wordsSoFar) == len(wordsSerialized)):
# 		if solutionIsValid(wordsSoFar):
# 			if wordsSoFar[0] in solutionsByStartingWord:
# 				solutionsByStartingWord[wordsSoFar[0]].append(wordsSoFar)
# 			else:
# 				solutionsByStartingWord[wordsSoFar[0]] = [wordsSoFar]
# 			return True
# 		return solutionIsValid(wordsSoFar)
# 	else:
# 		length = getWordLength(wordsSerialized[slotNo])
# 		for testWord in wordLists[length]:
# 			if slotNo == 0:
# 				endTime = time.time()
# 				pct = list(wordLists[length]).index(testWord)/len(wordLists[length])*100
# 				print("Testing",testWord,"as the starting word. ",round(pct,2),"%",end=' *** ')
# 				if pct>0 and endTime>startTime:
# 					print("Elapsed: ",endTime-startTime,"ETC: ",round((endTime-startTime)/(pct/100),0)-round(endTime-startTime,0),"seconds.")
# 				else:
# 					print("")
# 			newWordsToTest = copy.deepcopy(wordsSoFar)
# 			newWordsToTest.append(testWord)
# 			testSolutionRecursively(newWordsToTest,slotNo+1)


def testSolution(i):
	s = getSolutionNumber(i)
	if solutionIsValid(s):
		if s[0] in solutionsByStartingWord:
			solutionsByStartingWord[s[0]].append(s)
		else:
			solutionsByStartingWord[s[0]] = [s]
	elif i % 10000 == 0:  ##! Change back to 10,000!
		et = time.time()
		timeDelta = round(et - startTime)
		prog = i / totalSolutions()
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
		      flush=True)  ## Change end back to '\r'


def testAllSolutions():
	ts = totalSolutions()
	for i in range(ts):
		testSolution(i)


testAllSolutions()

# if __name__ == "__main__":
# 	with multiprocessing.Pool(2) as pool:
# 		results = pool.map(solutionIsValid, range(1000))

print()
print("Completed in", round(time.time() - startTime, 2), "seconds.")
for s in solutionsByStartingWord.items():
	print(s)
