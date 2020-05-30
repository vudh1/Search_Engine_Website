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

		# index file : this is all inverted_index list
		self.index_file_name = self.output_folder_name + config["FILE_NAME"]["INDEX_FILE_NAME"]

		# anchor terms file : this is all anchor terms dictionary
		self.anchor_terms_file_name = self.output_folder_name + config["FILE_NAME"]["ANCHOR_TERMS_FILE_NAME"]

		# strong terms file : this is has strong index dictionary
		self.strong_terms_file_name = self.output_folder_name + config["FILE_NAME"]["STRONG_TERMS_FILE_NAME"]

		# term_line_relationship file: this file store the line number of the term which can be found in postings_file_name
		self.term_line_relationship_file_name = self.output_folder_name + config["FILE_NAME"]["TERM_LINE_RELATIONSHIP_FILE_NAME"]

		# query_cache file : this file stores previously queried terms_to_postings and count (num times queried)
		self.query_cache_file_name = self.output_folder_name + config["FILE_NAME"]["QUERY_CACHE_FILE_NAME"]

		# result database file to store the result of query
		self.result_database_file_name = 'sqlite:///' +  self.output_folder_name + config["FILE_NAME"]["RESULT_DATABASE_FILENAME"]

		# number of iterations for ranking
		self.num_iterations_for_page_ranking = int(config["NUMBERS"]["NUM_ITERATIONS_FOR_PAGE_RANKING"])
		# the number of urls printed to console after query
		self.max_num_urls_per_query = int(config["NUMBERS"]["MAX_NUM_URLS_PER_QUERY"])

		# the number of urls for a page
		self.max_num_urls_per_page = int(config["NUMBERS"]["MAX_NUM_URLS_PER_PAGE"])

		# the number of entries in the query cache
		self.max_num_query_cache_terms = int(config["NUMBERS"]["MAX_QUERY_CACHE_TERMS"])

		# the number of documents per batch
		self.max_documents_per_batch = int(config["NUMBERS"]["MAX_DOCUMENTS_PER_BATCH"])

		# the number of different bits in sim hash
		self.threshold_sim_hash_value  = int(config["NUMBERS"]["THRESHOLD_SIM_HASH_VALUE"])

		# max length for title
		self.max_length_for_title = int(config["NUMBERS"]["MAX_LENGTH_FOR_TITLE"])

		# default score for boolean AND
		self.default_score_boolean_and = float(config["NUMBERS"]["DEFAULT_SCORE_BOOLEAN_AND"])

		# default score for boolean AND
		self.default_score_boolean_and_position = float(config["NUMBERS"]["DEFAULT_SCORE_BOOLEAN_AND_POSITION"])

		# default score for anchor text
		self.default_score_anchor_text = float(config["NUMBERS"]["DEFAULT_SCORE_ANCHOR_TEXT"])

		# default score for strong index (title, bold)
		self.default_score_strong_terms = float(config["NUMBERS"]["DEFAULT_SCORE_STRONG_TERMS"])

		# threshold for important terms
		self.threshold_high_idf_terms = float(config["NUMBERS"]["THRESHOLD_HIGH_IDF_TERMS"])

		# threshold for percent of terms in docs
		self.threshold_percent_of_terms_in_docs = float(config["NUMBERS"]["THRESHOLD_PERCENT_OF_TERMS_IN_DOCS"])

		# percent of threshold increasing until at least found 1 high idf terms
		self.threshold_increase_percent = float(config["NUMBERS"]["THRESHOLD_INCREASE_PERCENT"])


def read_config_file(config_file):
	cparser = ConfigParser()
	cparser.read(config_file)
	config = Config(cparser)
	return config
