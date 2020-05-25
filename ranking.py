#M3 part will be here


# ranking function

def ranking(config,query_doc_ids,query_postings):
	if len(query_doc_ids) == 0:
		return None

	query_doc_score = dict()

	for doc_id in query_doc_ids:
		score = 0

		for term,query_posting in query_postings.items():
			score += query_posting[doc_id].get_tf_idf()

		query_doc_score[doc_id] = score

	reverse_sorted_query_doc_score = sorted(query_doc_score.items(), key = lambda kv:(kv[1], kv[0]),reverse = True)

	query_result = dict(reverse_sorted_query_doc_score)

	return query_result