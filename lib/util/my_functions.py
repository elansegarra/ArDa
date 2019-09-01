''' This file holds several useful custom functions '''

def title_except(sentence, exceptions = "normal"):
	# This function capitalizes ever word except for those in exceptions
    #    (exceptions is a set of str)
	if exceptions == "normal":
		exceptions = {'a', 'an', 'of', 'the', 'and', 'but', 'for', 'at', 'by',
						'from', 'in', 'to'}
	word_list = sentence.split(' ')       # re.split behaves as expected
	final = [word_list[0].title()] #capitalize()]
	for word in word_list[1:]:
		word = word.lower()
		final.append(word if word in exceptions else word.title()) #capitalize())
	return " ".join(final)
