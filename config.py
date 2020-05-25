import re

from configparser import ConfigParser

# adding more config variables here after adding in 'config.ini' file for using

class Config(object):

	#read configurations for file names and values
	def __init__(self, config):
		#folder names
		self.input_folder_name = config["FOLDER_NAME"]["INPUT_FOLDER_NAME"]
		self.output_folder_name = config["FOLDER_NAME"]["OUTPUT_FOLDER_NAME"]
		self.partial_index_folder_name = config["FOLDER_NAME"]["PARTIAL_INDEX_FOLDER_NAME"]

		# file names
		self.doc_id_file_name = self.output_folder_name + config["FILE_NAME"]["DOC_IDS_FILE_NAME"]

		# terms_to_postings file : this is all inverted_index list
		self.index_file_name = self.output_folder_name + config["FILE_NAME"]["INDEX_FILE_NAME"]

		# term_line_relationship file: this file store the line number of the term which can be found in postings_file_name
		self.term_line_relationship_file_name = self.output_folder_name + config["FILE_NAME"]["TERM_LINE_RELATIONSHIP_FILE_NAME"]

		# query_cache file : this file stores previously queried terms_to_postings and count (num times queried)
		self.query_cache_file_name = self.output_folder_name + config["FILE_NAME"]["QUERY_CACHE_FILE_NAME"]

		# the number of urls printed to console after query
		self.max_num_urls_per_query = int(config["NUMBERS"]["MAX_NUM_URLS_PER_QUERY"])

		# the number of entries in the query cache
		self.max_num_query_cache_entries = int(config["NUMBERS"]["MAX_QUERY_CACHE_ENTRIES"])

		# the number of documents per batch
		self.max_documents_per_batch = int(config["NUMBERS"]["MAX_DOCUMENTS_PER_BATCH"])

def read_config_file(config_file):
	cparser = ConfigParser()
	cparser.read(config_file)
	config = Config(cparser)
	return config
