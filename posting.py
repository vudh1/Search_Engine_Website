
# each EntryPosting is a class/object contains a doc_id and related variables that a term is found

class Entry_Posting:
	def __init__(self, doc_id, freq,tf_idf, positions):
		self.doc_id = doc_id
		self.freq = freq
		self.tf_idf = tf_idf
		self.positions = positions

	def get_doc_id(self):
		return self.doc_id

	def get_freq(self):
		return self.freqs

	def get_tf_idf(self):
		return self.tf_idf

	def get_positions(self):
		return self.positions

	def set_tf_idf(self, tf_idf):
		self.tf_idf = tf_idf


	# print positions as string
	# for example: [0,1,2,3,4,5]

	def positions_to_str(self):
		positions_str = "["

		for i in range(len(self.positions)):
			positions_str += str(self.positions[i])
			if i < len(self.positions) - 1:
				positions_str += ","

		return positions_str + "]"


	# print the entry_posting format
	# for example: {'doc_id':0,'freq':10,'tf_idf':0.4132,'positions':[0,1,2,3,4,5]}

	def _to_str(self):
		return "{\"doc_id\":" + str(self.doc_id) + ",\"freq\":" + str(self.freq) + ",\"tf_idf\":" + str(self.tf_idf) + ",\"positions\":" + self.positions_to_str()+"}"