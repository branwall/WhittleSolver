from PyDictionary import PyDictionary

d = PyDictionary()
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
    "will": 1,
    "having": 1,
}


def score_solution(solution, wordLists=None):
	
	score = 0
	wordNet = {}
	for word in solution:
		if wordLists != None:

			wordlist = list(
			    wordLists[len(word)].keys())  
			firstThird = wordlist[:int(len(wordlist) / 3)]
			secondThird = wordlist[int(len(wordlist) / 3):int(2 * len(wordlist) / 3)]
			thirdThird = wordlist[int(2 * len(wordlist) / 3):]

			if word in firstThird:
				score += 4
			elif word in secondThird:
				score += 1
			elif word in thirdThird:
				score += 0

		localWordNet = {}
		definition = d.meaning(word, disable_errors=True)
		if definition != None:
			definition = definition.items()
			if len(list(definition)) > 0 and len(list(definition)[0]) > 0 and len(
			    list(definition)[0][1]) > 0:
				for part_of_speech in list(definition):
					for meaning in part_of_speech[1]:
						for definitionWord in meaning.split():
							if definitionWord not in banned_words:
								localWordNet[definitionWord] = 1
				for key in list(localWordNet.keys()):
					if key in wordNet:
						wordNet[key] += 1
					else:
						wordNet[key] = 1
	wordnet_reduced = {k:(v*v) for (k,v) in wordNet.items() if v >= 2}

	# print(solution, wordnet_reduced)
	for count in wordnet_reduced.values():
		score += count
	return score

