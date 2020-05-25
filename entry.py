
# each Entry is a class/object contains variables in a specific doc_id that a term is found

class Entry:
	def __init__(self, freq,tf,tf_idf, positions):
		self.freq = freq
		self.tf = tf
		self.tf_idf = tf_idf
		self.positions = positions

	def get_freq(self):
		return self.freq

	def get_tf(self):
		return self.tf

	def get_tf_idf(self):
		return self.tf_idf

	def get_positions(self):
		return self.positions

	def set_tf_idf(self, tf_idf):
		self.tf_idf = tf_idf