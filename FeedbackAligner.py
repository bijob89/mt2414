#!/usr/bin/env python3
# FeedbackAligner.py


import re, sys, pickle
import os.path 
import pymysql


class FeedbackAligner:
	def __init__(self,db,src,trg):

		self.db = db
		
		cur = self.db.cursor()
		
		self.src_table_name = src+"_bible_concordance"
		self.trg_table_name = trg+"_bible_concordance"

		self.alignment_table_name = src+"_"+trg+"_alignment"
		self.FeedbackLookup_table_name = src+"_"+trg+"_FeedbackLookup"

		cur.execute("SHOW TABLES LIKE '"+self.src_table_name+"'")
		if cur.rowcount==0:
			print("Table not found: "+self.src_table_name)
			sys.exit(0)


		cur.execute("SHOW TABLES LIKE '"+self.trg_table_name+"'")
		if cur.rowcount==0:
			print("Table not found: "+self.trg_table_name)
			sys.exit(0)
			
		cur.execute("SHOW TABLES LIKE '"+self.alignment_table_name+"'")
		if cur.rowcount==0:
			print("Table not found: "+self.alignment_table_name)
			sys.exit(0)


		cur.execute("SHOW TABLES LIKE '"+self.FeedbackLookup_table_name+"'")
		if cur.rowcount==0:
			cur.execute("CREATE TABLE "+self.FeedbackLookup_table_name+
				" (source_word VARCHAR(50) CHARACTER SET utf8mb4 NOT NULL,target_word VARCHAR(50) CHARACTER SET utf8mb4 NOT NULL,confidence_score FLOAT(6,5))")
			cur.execute("ALTER TABLE "+self.FeedbackLookup_table_name+" ADD INDEX source_word_index(source_word)")
			cur.execute("ALTER TABLE "+self.FeedbackLookup_table_name+" ADD INDEX target_word_index(target_word)")
			self.db.commit()
		
	# def __del__(self):
		
		self.db.commit()
		# self.db.close()
		


	def insert_into_lookup_table(self,src_word,trg_word):
		try:	
			cur = self.db.cursor()


			# for calculating confidence_score
			cur.execute("select count(distinct left(occurences,5)) from "+self.src_table_name+" where word='"+src_word+"'") 
			if cur.rowcount>0:
				total_verses_src_word_occured = cur.fetchone()[0]
				print(total_verses_src_word_occured)
			else:
				total_verses_src_word_occured = 1

			query = " select count(distinct left("+ self.trg_table_name +".occurences,5)) from "+ self.trg_table_name +" INNER JOIN "+ self.src_table_name +" on left("+self.trg_table_name+".occurences,5)=left("+self.src_table_name+".occurences,5) where "+self.src_table_name+".word=\'"+src_word+"\' and "+self.trg_table_name+".word=\'"+trg_word+"\'"
			print(query)
			cur.execute(query)
			if cur.rowcount>0:
				total_verses_trg_word_cooccured = cur.fetchone()[0]
				print(total_verses_trg_word_cooccured)
			else:
				total_verses_trg_word_cooccured = 0


			cur.execute("	select count(distinct b.lid) from "+self.src_table_name+" a, "+self.alignment_table_name+" b, "+self.trg_table_name+" c where a.occurences=b.source_wordID and c.occurences=b.target_wordID and a.word='"+src_word+"' and c.word='"+trg_word+"'")
			if cur.rowcount>0:
				total_verses_src_trg_aligned = cur.fetchone()[0]
				print(total_verses_src_trg_aligned)
			else:
				total_verses_src_trg_aligned = 1


			cur.execute("	select count(distinct b.lid) from "+self.src_table_name+" a, "+self.alignment_table_name+" b, "+self.trg_table_name+" c where a.occurences=b.source_wordID and c.occurences=b.target_wordID and a.word='"+src_word+"' and c.word!='"+trg_word+"'")
			if cur.rowcount>0:
				total_verses_src_trg_NOTaligned = cur.fetchone()[0]
				print(total_verses_src_trg_NOTaligned)
			else:
				total_verses_src_trg_NOTaligned = 0

			co_occurence_confidence = total_verses_trg_word_cooccured/total_verses_src_word_occured
			aligned_confidence = (total_verses_src_trg_aligned-total_verses_src_trg_NOTaligned) /(total_verses_src_trg_aligned+total_verses_src_trg_NOTaligned)


			confidence_score = 0.75*co_occurence_confidence + 0.25*aligned_confidence
	

			cur.execute("INSERT INTO "+self.FeedbackLookup_table_name+" (source_word,target_word,confidence_score) VALUES (%s,%s,%s)",
				(src_word,trg_word,confidence_score))
			self.db.commit()
			
		except Exception as e:
			print("Warning: word pair not inserted to look up table")
			print(e)



	def save_alignment(self,lid,word_pairs,user):
		cur = self.db.cursor()

		for pair in word_pairs:
			cur.execute("INSERT INTO "+self.alignment_table_name+" (lid,source_wordID,target_wordID,user) VALUES (%s,%s,%s,'default')",
				(lid, pair[0],pair[1]))

		self.db.commit()


	


	def update_alignment_on_verse(self,lid_to_update):
		cur = self.db.cursor()

		# get source_word list and target list for the verse from concordance table
		cur.execute("SELECT word,occurences FROM "+self.src_table_name+" WHERE occurences LIKE '"+lid_to_update+"\_%'")
		src_word_list = []
		for row in cur.fetchall():
			src_word_list.append((row[0],row[1]))
		cur.execute("SELECT word,occurences FROM "+self.trg_table_name+" WHERE occurences LIKE '"+lid_to_update+"\_%'")
		trg_word_list = []
		for row in cur.fetchall():
			trg_word_list.append((row[0],row[1]))

		# for all source_words get _FeedbackLookup entry
		# and if entry present in trg_verse, add them to replacement_options
		replacement_options=[]
		mapped = []
		for s_wrd in src_word_list:
			cur.execute("SELECT target_word FROM "+self.FeedbackLookup_table_name+" WHERE source_word='"+s_wrd[0]+"' ORDER BY confidence_score DESC")
			for row in cur.fetchall():
				mapped_trg_word = row[0]
				flag = False
				for t_wrd in trg_word_list:
					if t_wrd[0]==mapped_trg_word and t_wrd[1] not in mapped:
						replacement_options.append((s_wrd[1],t_wrd[1]))
						mapped.append(t_wrd[1])
						flag=True 
						break
				if flag==True:
					break
		print(replacement_options)



		#update the alignment table
		for pair in replacement_options:
			cur.execute("DELETE FROM "+self.alignment_table_name+"  WHERE source_wordID='"+pair[0]+"'")

			cur.execute("DELETE FROM "+self.alignment_table_name+"  WHERE target_wordID='"+pair[1]+"'")

		for pair in replacement_options:

			cur.execute("INSERT INTO "+self.alignment_table_name+" (lid,source_wordID,target_wordID,corrected) VALUES (%s,%s,%s,0)",
				(lid_to_update, pair[0],pair[1]))

		self.db.commit()

			

		# for word 




	def fetch_alignment(self,lid,auto_alignmenttable):
		cur = self.db.cursor()

		# get source_word list and target list for the verse from concordance table
		cur.execute("SELECT word,occurences FROM "+self.src_table_name+" WHERE occurences LIKE '"+lid+"\_%'")
		src_word_list = []
		for row in cur.fetchall():
			src_word_list.append((row[0],row[1]))
		# print("src_word_list")
		# print(src_word_list)


		cur.execute("SELECT word,occurences FROM "+self.trg_table_name+" WHERE occurences LIKE '"+lid+"\_%'")
		trg_word_list = []
		for row in cur.fetchall():
			trg_word_list.append((row[0],row[1]))
		# print("trg_word_list")
		# print(trg_word_list)


		# get the alignments from specified table
		cur.execute("SELECT * from "+auto_alignmenttable+" WHERE lid='"+lid+"'")
		auto_alignments = cur.fetchall()
		# print("auto_alignments")
		# print(auto_alignments)

		# get the alignments from master table, if present
		cur.execute("SELECT * from "+self.alignment_table_name+" WHERE lid='"+lid+"'")
		corrected_alignments = cur.fetchall()
		# print("corrected_alignments")
		# print(corrected_alignments)

		# for all source_words get _FeedbackLookup entry
		# and if entry present in trg_verse, add them to replacement_options
		replacement_options=[]
		mapped = []
		for s_wrd in src_word_list:
			cur.execute("SELECT target_word FROM "+self.FeedbackLookup_table_name+" WHERE source_word='"+s_wrd[0]+"' ORDER BY confidence_score DESC")
			for row in cur.fetchall():
				mapped_trg_word = row[0]
				flag = False
				for t_wrd in trg_word_list:
					if t_wrd[0]==mapped_trg_word and t_wrd[1] not in mapped:
						replacement_options.append((s_wrd[1],t_wrd[1]))
						mapped.append(t_wrd[1])
						flag=True 
						break
				if flag==True:
					break
		# print("replacement_options")
		# print(replacement_options)

		return src_word_list, trg_word_list, auto_alignments, corrected_alignments, replacement_options
	


	def on_approve_feedback(self,corrected_src_trg_word_list):
		for src_trg in corrected_src_trg_word_list:
			src_word_to_update=src_trg[0]
			trg_word_to_update=src_trg[1]

			self.insert_into_lookup_table(src_word_to_update,trg_word_to_update)

			# self.update_all_alignment_by_word(src_word_to_update)



if __name__ == '__main__':
	if len(sys.argv)==3:
		src = sys.argv[1]
		trg = sys.argv[2]

	else:
		print("Usage: python3 FeedbackAligner.py src trg\n(src,trg - 3 letter lang codes\n")
		sys.exit(0)


	connection =  pymysql.connect(host="localhost",    # your host, usually localhost
	                     user="root",         # your username
	                     password="password",  # your password
	                     database="itl_db",
	                     charset='utf8mb4')
		

	
	obj = FeedbackAligner(connection, src,trg)


	obj.on_approve_feedback([("G24240","यीशु"),("G52070","सन्तान")])

	obj.fetch_alignment('23146','grk_hin_sw_stm_ne_giza_tw__alignment')

	# obj.update_al
	

	del obj