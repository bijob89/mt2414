#!/usr/bin/env python3
# FeedbackAligner.py


import re, sys, pickle
import os.path 
import itertools
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
		
	def __del__(self):
		
		self.db.commit()
		# self.db.close()
		


	def insert_into_lookup_table(self,src_word,trg_word):
		try:	
			cur = self.db.cursor()

			src_word_array = src_word.split(" ")
			trg_word_array = trg_word.split(" ")


			# for calculating confidence_score

			#handling multi-word src phrases and multi-word non-contiguous phrases
			#multi-words inputed as, a single string with "space" seperating the words
			#non-contigious words, as a single string with "." for every word in between and all words and dots separated by "space"
			cur.execute("select occurences  from "+self.src_table_name+" where word='"+src_word_array[0]+"'")
			src_word_occurences = [x[0] for x in cur.fetchall()]
			for i,src_word in enumerate(src_word_array):
				if src_word == ".":
					continue
				for fetched_pos in src_word_occurences:
					lid = fetched_pos.split("_")[0]
					pos = int(fetched_pos.split("_")[1])
					pos = pos + i
					check_occurance = lid+"_"+str(pos)
					cur.execute("select word from "+self.src_table_name+" where word='"+src_word+"' and occurences='"+check_occurance+"'")
					if cur.rowcount==0:
						src_word_occurences.remove(fetched_pos)

			total_verses_src_word_occured = len(src_word_occurences)
			if total_verses_src_word_occured==0:
				total_verses_src_word_occured = 1

			

			cur.execute("select occurences  from "+self.trg_table_name+" where word='"+trg_word_array[0]+"'")
			trg_word_occurences = [x[0] for x in cur.fetchall()]
			for i,trg_word in enumerate(trg_word_array):
				if trg_word == ".":
					continue
				for fetched_pos in trg_word_occurences:
					lid = fetched_pos.split("_")[0]
					pos = int(fetched_pos.split("_")[1])
					pos = pos + i
					check_occurance = lid+"_"+str(pos)
					cur.execute("select word from "+self.trg_table_name+" where word='"+trg_word+"' and occurences='"+check_occurance+"'")
					if cur.rowcount==0:
						trg_word_occurences.remove(fetched_pos)

			src_lids = [x.split("_")[0] for x in src_word_occurences]
			trg_lids = [x.split("_")[0] for x in trg_word_occurences]
			
			co_occurence_lid_set = set(src_lids).intersection(set(trg_lids))
			total_verses_trg_word_cooccured = len(co_occurence_lid_set)
			
			co_occurence_pospair_set =[]
			for x,y in itertools.product(src_word_occurences,trg_word_occurences):
				if x.split("_")[0]==y.split("_")[0]:
					co_occurence_pospair_set.append((x,y))
			


			cur.execute("SELECT distinct lid from "+self.alignment_table_name)
			verses_in_aligned_table = [str(x[0]) for x in cur.fetchall()]
			total_cooccurance_verses_INalignedtable = len(co_occurence_lid_set.intersection(set(verses_in_aligned_table)))

			
			if total_cooccurance_verses_INalignedtable==0:
				total_cooccurance_verses_INalignedtable = 1
			
			total_verses_src_trg_aligned = 0
			verses_src_trg_aligned = []
			for pos_pair in co_occurence_pospair_set:
				cur.execute("SELECT lid from "+self.alignment_table_name+" WHERE source_wordID='"+pos_pair[0]+"' and target_wordID='"+pos_pair[1]+"'")
				if cur.rowcount>0:
					verses_src_trg_aligned.append(cur.fetchone()[0])
			total_verses_src_trg_aligned = len(set(verses_src_trg_aligned))
			
			co_occurence_confidence = total_verses_trg_word_cooccured/total_verses_src_word_occured
			aligned_confidence = total_verses_src_trg_aligned / total_cooccurance_verses_INalignedtable
			confidence_score = 0.75*co_occurence_confidence + 0.25*aligned_confidence
	
			print(" ".join(src_word_array)+"---"+" ".join(trg_word_array)+":"+str(confidence_score))
			cur.execute("INSERT INTO "+self.FeedbackLookup_table_name+" (source_word,target_word,confidence_score) VALUES (%s,%s,%s)",
				(" ".join(src_word_array)," ".join(trg_word_array),confidence_score))
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
		for i,s_wrd in enumerate(src_word_list):

			cur.execute("SELECT source_word, target_word FROM "+self.FeedbackLookup_table_name+" WHERE source_word like '"+s_wrd[0]+"%' ORDER BY  confidence_score DESC, CHAR_LENGTH(source_word) DESC")
			for row in cur.fetchall():
				drop = False
				mapped_src_word = row[0]
				mapped_trg_word = row[1]
				src_pos = []
				src_multiword_list = mapped_src_word.split(" ")
				for j,w in enumerate(src_multiword_list):
					if (i+j)<len(src_word_list) and  src_word_list[i+j][0]==w :
						src_pos.append(src_word_list[i+j][1])
					elif (i+j)<len(src_word_list) and w==".":
						pass
					else:
						drop=True
				
				if drop:
					break

				trg_multiword_list = mapped_trg_word.split(" ")
				trg_pos = []
				for i,t_wrd in enumerate(trg_word_list):
					if t_wrd[1] in mapped:
						continue
					temp_trg_pos = []
					drop = False
					for j,w in enumerate(trg_multiword_list):
						if (i+j)<len(trg_word_list) and  trg_word_list[i+j][0] == w :
							temp_trg_pos.append(trg_word_list[i+j][1])
						elif (i+j)<len(trg_word_list) and w==".":
							pass
						else:
							temp_trg_pos = []
							drop = True
							break
					if not drop:
						trg_pos = temp_trg_pos
						break
				if drop:
					break



				for i,j in itertools.product(src_pos,trg_pos):
					replacement_options.append((i,j))
					mapped.append(j)
					drop = True
				# print('replacement_options'+str(replacement_options))
				if drop:
					break

		print(replacement_options)



		#update the alignment table
		for pair in replacement_options:
			cur.execute("DELETE FROM "+self.alignment_table_name+"  WHERE source_wordID='"+pair[0]+"'")

			cur.execute("DELETE FROM "+self.alignment_table_name+"  WHERE target_wordID='"+pair[1]+"'")

		for pair in replacement_options:

			cur.execute("INSERT INTO "+self.alignment_table_name+" (lid,source_wordID,target_wordID,user) VALUES (%s,%s,%s,'default')",
				(lid_to_update, pair[0],pair[1]))

		self.db.commit()

			

		




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


	# obj.on_approve_feedback([("2424 5547","यीशु मसीह"),("5207","सन्तान"),("5257 5547","मसीह . सेवक")])

	# obj.fetch_alignment('23146','grk_hin_sw_stm_ne_giza_tw__alignment')

	obj.update_alignment_on_verse('23146')
	

	del obj