import os
import sys
import re
import math
import json
import linecache

from nltk.stem.porter import *

# tokenize and stemming the text

def analyze_text(text):
	regex = re.compile('[^a-z0-9A-Z]')
	text = regex.sub(' ', text).lower()
	stemmer = PorterStemmer()

	terms = [stemmer.stem(i) for i in text.split() if len(i) >= 2]
	return terms

# write the term and its line number in terms_to_postings.json

def write_term_line_relationship(config):
	if(os.path.exists(config.postings_file_name) is True):
		with open(config.postings_file_name, 'r') as infile:
			term_line_relationship = dict()

			while True:
				off_set = infile.tell()

				line = infile.readline().strip()

				if not line:
					break
				else:
					if len(line) > 0:
						data = json.loads(line)
					term_line_relationship[data["term"]] = off_set

			with open(config.term_line_relationship_file_name, 'w') as outfile:
				json.dump(term_line_relationship, outfile)


# read term_line_relationships.json for the line number of each term in terms_to_postings.json for faster retrieval

def read_term_line_relationship(config):
	if(os.path.exists(config.term_line_relationship_file_name) is True):
		with open(config.term_line_relationship_file_name, 'r') as file:
			term_line_relationship = json.load(file)
			return term_line_relationship

	return None


# read doc_id.json for doc_id and name of the files

def read_doc_ids_file(config):
	if(os.path.exists(config.doc_id_file_name) is True):
		with open(config.doc_id_file_name) as f:
			doc_ids = json.load(f)
			return doc_ids
	return dict()


#directly read at a specific line in terms_to_postings.json for term_posting information without storing large data in memory

def get_posting_at_specific_line(config,off_set):
	if(os.path.exists(config.postings_file_name) is True):
		with open(config.postings_file_name) as f:
			f.seek(off_set,0)
			line = f.readline().strip()
			resource_term_posting = json.loads(line)
			return resource_term_posting

	return None


# get terms - postings from inverted index list according to query terms

def get_query_postings(config,query_terms,term_line_relationship):
	if len(query_terms) == 0:
		return None

	query_postings = []

	for term in query_terms:
		if term not in term_line_relationship:
			return None
		else:
			line_num = term_line_relationship[term]

			resource_term_posting = get_posting_at_specific_line(config,line_num)
			if resource_term_posting is None:
				print("There is no term ",term,"in the indexer file")
			else:
				query_postings.append(resource_term_posting)

	return query_postings



# print query result to console output

def print_query_doc_name(config,query,doc_ids,query_result,time):
	time = round(time,2)

	if query_result is not None:
		print("Retrieved a total of " + str(len(query_result)) +  " documents of '" + str(query)+"' in "+str(time)+"ms.")

		query_ids = list(query_result.keys())

		for i in range(len(query_ids)):
			if i < int(config.max_num_urls_per_query):
				print(doc_ids[str(query_ids[i])])
			else:
				break
	else:
		print("Retrieved a total of " + "0" +  " documents of '" + str(query)+"' in "+str(time)+"ms.")

	print("")


# return all tokens as json format for terms_to_postings.json

# with the format:
#	{'term' : term1, 'posting' : posting1}
#	{'term' : term2, 'posting' : posting2}
#	{'term' : term3, 'posting' : posting3}

# and posting1,posting2,posting3 format is {'doc_id': doc_id, 'freq' : freq, 'tf_idf': tf_idf, 'positions' : positions}

def write_postings_file(config,total_tokens):
	outfile = open(config.postings_file_name,'w')

	json_str = ""

	for token,posting in total_tokens.items():
		print( "{ \"term\" : \"" + str(token)+ "\", \"posting\": [",end = "",file = outfile)
		for i in range(len(posting)):
			print(posting[i]._to_str(),end = "",file = outfile)
			if i < len(posting) - 1:
				print(",",end = "",file = outfile)
		print("]}",file = outfile)

	outfile.close()

	return json_str

