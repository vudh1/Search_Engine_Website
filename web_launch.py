# #!/usr/bin/python3
import os, sys, time, logging, pickle
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
from threading import Thread
from pickle import UnpicklingError
from forms import QueryTerm
from search import search
from indexer import inverted_index
from helper import get_configurations
from helper import get_terms_from_query
from helper import update_query_cache
from helper import read_doc_ids_file
from helper import read_term_line_relationship_file
from helper import read_strong_index_file

config = get_configurations()

if config is None:
	print("No config file. Exit now")
	sys.exit()

if(os.path.exists(config.output_folder_name) is False):
	os.mkdir(config.output_folder_name)


app = Flask(__name__)
app.config['SECRET_KEY'] = '012345678998765433210'
app.config['SQLALCHEMY_DATABASE_URI'] = config.result_database_file_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

log = logging.getLogger('werkzeug')

log.disabled = True
# app.logger.disabled = True


class QueryResult(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	url = db.Column(db.String(120), nullable = False)
	title = db.Column(db.String(120), nullable = False)
	def __repr__(self):
		return str(self.title)

# #################################################################################################################################


doc_ids = dict()
term_line_relationship = dict()
strong_index = dict()

num_documents = 0
num_terms = 0

query = ""
query_terms = []

time_start = 0
time_end = 0

query_ids_results = []

cache = defaultdict(lambda : False)

# #################################################################################################################################

def search_ui():
	global config
	global query
	global query_terms
	global term_line_relationship
	global cache
	global query_ids_results
	global doc_ids
	global strong_index

	# try:
	query_terms = get_terms_from_query(query)

	query_ids_results = search(config, query_terms, doc_ids,term_line_relationship, cache, strong_index)
	# except Exception:
		# query_ids_results = []


def update_database():
	global config
	global db
	global query_ids_results

	db.drop_all()

	db.create_all()

	for i in range(len(query_ids_results)):
		db.session.add(QueryResult(title = doc_ids[query_ids_results[i]][0],url = doc_ids[query_ids_results[i]][1]))

	db.session.commit()


def update_statistics():
	global config
	global doc_ids
	global term_line_relationship
	global num_documents
	global num_terms
	global cache
	global strong_index

	doc_ids = read_doc_ids_file(config)

	if doc_ids is None:
		doc_ids = dict()

	num_documents = len(doc_ids)

	strong_index = read_strong_index_file(config)

	if strong_index is None:
		strong_index = dict()

	term_line_relationship = read_term_line_relationship_file(config)

	if term_line_relationship is None:
		term_line_relationship = dict()

	num_terms = len(term_line_relationship)

# #################################################################################################################################

@app.route("/",methods = ['GET', 'POST'])
@app.route("/home",methods = ['GET', 'POST'])
def home():
	global query
	global time_start
	global time_end
	global config

	form = QueryTerm()

	if form.validate_on_submit():
		time_start = time.process_time()

		query = str(form.query.data)

		search_ui()

		time_end = time.process_time()

		return redirect(url_for('result'))
	return render_template('home.html', title ='Home', num_documents = num_documents, num_terms = num_terms, form = form)

@app.route("/about")
def about():
	return render_template('about.html', title='About')

@app.route("/update")
def update():
	global config
	global num_documents
	global num_terms

	time_start = time.process_time()

	num_documents, num_terms = inverted_index(config)

	if num_documents == 0:
		print("No files to index.")

	time_end = time.process_time()

	indexer_time = round((time_end - time_start),2)

	update_statistics()

	return render_template('update.html', title ='Update', indexer_time = indexer_time, num_documents = num_documents, num_terms = num_terms)

@app.route("/result")
def result():
	global config
	global query
	global time_start
	global time_end
	global query_ids_results

	update_database()

	page = request.args.get('page', 1, type = int)

	result_info = QueryResult.query.paginate(page = page, per_page = config.max_num_urls_per_page)

	query_time = round((time_end-time_start)*(10**3),2)

	return render_template('result.html', title='Result', query = query,
					 result_info = result_info, length = len(query_ids_results) , query_time = query_time)

# #################################################################################################################################

def initial_indexer():
	global config

	print("\nIndexing document ...")
	time_start = time.process_time()

	num_documents, num_terms = inverted_index(config)

	if num_documents == 0:
		print("No files to index.")

	time_end = time.process_time()

	print("Complete indexing",num_documents, "documents in", (time_end - time_start),"s\n")

	update_statistics()

	print("WebUI is ready to use ... \n")


# #################################################################################################################################

update_statistics()

if __name__ == '__main__':
	initial_indexer()

