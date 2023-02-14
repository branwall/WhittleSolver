from PyDictionary import PyDictionary

d = PyDictionary()
banned_words = {
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
}


def score_solution(solution):
	# print("\rScoring",solution, end = '\r')
	wordNet = {}
	for word in solution:
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
	score = 0
	for count in wordNet.values():
		score += count
	if len(list(wordNet.values())) != 0:
		score /= len(list(wordNet.values()))
	else:
		score = 1
	
	score -= 1
	score *= 100
	return score
