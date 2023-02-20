from nltk.corpus import wordnet as wn

banned_words = {
    "a": 1,
    "of": 1,
    "to": 1,
    "in": 1,
    "is": 1,
    "on": 1,
    "by": 1,
    "it": 1,
    "or": 1,
    "be": 1,
    "at": 1,
    "as": 1,
    "an": 1,
    "we": 1,
    "us": 1,
    "if": 1,
    "my": 1,
    "do": 1,
    "the": 1,
    "and": 1,
    "for": 1,
    "you": 1,
    "not": 1,
    "are": 1,
    "all": 1,
    "new": 1,
    "was": 1,
    "can": 1,
    "has": 1,
    "but": 1,
    "our": 1,
    "one": 1,
    "may": 1,
    "out": 1,
    "use": 1,
    "any": 1,
    "that": 1,
    "this": 1,
    "with": 1,
    "from": 1,
    "your": 1,
    "have": 1,
    "more": 1,
    "some": 1,
    "very": 1,
    "used": 1,
    "who": 1,
    "will": 1,
    "having": 1,
    "usually": 1
}


def prettyPrintSolutionScore(solution, score, overlappingDefinitionWords):
	out = ""
	if len(solution) > 0 and len(overlappingDefinitionWords) > 0:
		for word in solution[:-1]:
			out += word.upper() + ', '
		out += solution[-1].upper() + ":\t"
		out += str(score) + '\t'
		out += "("
		for word in overlappingDefinitionWords[:-1]:
			out += word + ", "
		out += overlappingDefinitionWords[-1] + ")"
	return out


def score_solution(solution, wordLists=None):
	score = 0
	all_words = {}
	for word in solution:
		if wordLists != None:
			wordlist = list(wordLists[len(word)].keys())
			firstThird = wordlist[:int(len(wordlist) / 3)]
			secondThird = wordlist[int(len(wordlist) / 3):int(2 * len(wordlist) / 3)]
			thirdThird = wordlist[int(2 * len(wordlist) / 3):]

			if word in firstThird:
				score += 4
			elif word in secondThird:
				score += 1
			elif word in thirdThird:
				score += 0
		unique_words = {}
		sysnet_array = wn.synsets(word)
		for meaning in sysnet_array:
			for word in meaning.definition().strip("123456789-").replace(
			    ')', '').replace('(', '').lower().split():
				unique_words[word] = 1
		for key in list(unique_words.keys()):
			if key in all_words and key not in banned_words:
				all_words[key] += 1
			else:
				all_words[key] = 1

	all_words_reduced = {k: (v * v) for (k, v) in all_words.items() if v >= 2}

	for count in all_words_reduced.values():
		score += count

	overlappingDefWords = []
	if len(list(all_words_reduced)) > 0:
		mv = max(all_words_reduced.values())
		for k, v in all_words_reduced.items():
			if v == mv:
				overlappingDefWords.append(k)

	# pps = prettyPrintSolutionScore(solution, score, overlappingDefWords)
	return (score, overlappingDefWords)


scrabbles = {
    'a': 1,
    'b': 3,
    'c': 3,
    'd': 2,
    'e': 1,
    'f': 4,
    'g': 2,
    'h': 4,
    'i': 1,
    'j': 8,
    'k': 5,
    'l': 1,
    'm': 3,
    'n': 1,
    'o': 1,
    'p': 3,
    'q': 10,
    'r': 1,
    's': 1,
    't': 1,
    'u': 1,
    'v': 8,
    'w': 4,
    'x': 8,
    'y': 4,
    'z': 10
}


def scrabble_score_solution(solution):
	score = 0
	all_words = {}
	for word in solution:
		for letter in word:
			score += scrabbles[letter]
	return (score)

