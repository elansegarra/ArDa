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

def getAncestry(df, id_val, id_col, parent_col, text_col):
	''' Returns a list of the 'address' of the id item '''
	root_id = 0 # Indicates it has no parents
	parent_list = [df[df[id_col]==id_val].iloc[0][text_col]]
	curr_parent = df[df[id_col]==id_val].iloc[0][parent_col]
	while curr_parent != root_id:
		parent_list.insert(0, df[df[id_col]==curr_parent].iloc[0][text_col])
		curr_parent = df[df[id_col]==curr_parent].iloc[0][parent_col]
	return parent_list
