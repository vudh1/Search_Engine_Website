import sys
import re
import math
import json
from bs4 import BeautifulSoup
from bs4.element import Comment
from os import listdir
import os
from nltk.stem import *
from nltk.stem.porter import *
from decimal import *
from math import ceil

total_tokens = dict()
file_id = dict()
num_documents = 0

output_folder_name = 'output/'
file_id_file_name = output_folder_name+'file_id.json'			# FIXED: .txt -> .json
indexes_file_name = output_folder_name+'index_list.txt'
index_info_file_name = output_folder_name+'report.txt'
posting_file_name = output_folder_name+'posting_per_index_info.txt'	

def tokenize(text):
	regex = re.compile('[^a-z0-9A-Z]')
	text = regex.sub(' ',text).lower()
	list_of_tokens = [i for i in text.split() if len(i) >= 2]
	return list_of_tokens

def stemming(list_of_tokens):
	stemmer = PorterStemmer()

	list_of_stem = [stemmer.stem(token) for token in tokens]

	return list_of_stem

def compute_word_frequencies(list_of_tokens):
	frequencies = {i : 0 for i in list_of_tokens}

	for token in list_of_tokens:
		frequencies[token] += 1

	return frequencies

def tf_score(frequencies):
	total = sum(frequencies.values())

	result = {i : (frequencies[i]/total) for i in frequencies.keys()}

	return result


def get_tf_idf_score(total_tokens):
	for token,posting in total_tokens.items():
		for value in posting:
			if value['tf'] > 0 and len(posting) > 1:
				value['tf_idf'] = value['tf'] * math.log(num_documents/len(posting))
			else:
				value['tf_idf'] = 0
				
def add_to_list(tokens,num_documents):
	frequencies = compute_word_frequencies(tokens)
	tf = tf_score(frequencies)
	for token, freq in frequencies.items():
		if token not in total_tokens:
			total_tokens[token] = list()

		temp = dict({'file_id' : num_documents, 'freq':freq,'tf' : tf[token], 'tf_idf': 0.00})
		total_tokens[token].append(temp)

def tag(element):
	if element.parent.name in ['head', 'title', 'meta', 'style', 'script', '[document]']:
		return False
	if isinstance(element, Comment):
		return False
	return True

if __name__ == '__main__':

	for root, directories, files in os.walk('DEV'):
		for dir in directories:
			files = listdir(root+'/'+dir)
			for f in files:				
				data = dict()

				with open(root+'/'+dir+'/'+f) as jf:
					data = json.load(jf)
					
					try:
						html = BeautifulSoup(data["content"], 'html.parser')
						text = ' '.join(filter(tag, html.find_all(text=True)))
						tokens = tokenize(text)
						tokens = stemming(tokens)
						file_id[num_documents] = str(data["url"])
						add_to_list(tokens,num_documents)
						num_documents +=1
					except Exception:
						continue

	get_tf_idf_score(total_tokens)

	os.mkdir(output_folder_name)

	with open(file_id_file_name, 'w') as outfile:		
		json.dump(file_id, outfile)			# FIXED: file_id_file_name -> file_id (dict)

	outfile = open(indexes_file_name,'w')

	for token,posting in total_tokens.items():
		print(token,file = outfile)

	outfile.close()

	outfile = open(posting_file_name,'w')

	for token,posting in total_tokens.items():

		print(token, ":",end = '',file = outfile)
		for tup in posting:
			print('[',tup['file_id'], ',', tup['freq'], ',',round(float(tup['tf_idf']),4),']',file = outfile,end ='')

		print("",file = outfile)
	
	outfile.close()

	outfile = open(index_info_file_name,'w')

	print("Number of documents =", num_documents,file = outfile)
	print("Number of unique tokens = ", len(total_tokens),file = outfile)
	print("Size of indexes on disk (KB) = ",((os.stat(posting_file_name)).st_size)/1000,file = outfile)

	outfile.close()
