#!/usr/bin/env python3
# FeedbackAligner.py


import re, sys, pickle
import os.path 
import itertools
import time, json
import pymysql

from TW_strongs_ref_lookup import TWs


class FeedbackAligner:
	def __init__(self,db,src,src_version,trg,trg_version):

		self.db = db
		
		cur = self.db.cursor()
		
		self.src_table_name = src+"_"+src_version+"_BibleWord"
		self.trg_table_name = trg+"_"+trg_version+"_BibleWord"

		self.alignment_table_name = src+"_"+src_version+"_"+trg+"_"+trg_version+"_Alignment"
		# self.FeedbackLookup_table_name = src+"_"+trg+"_FeedbackLookup"

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


		
	def __del__(self):
		
		self.db.commit()
		# self.db.close()
		


	def insert_into_lookup_table(self,src_word,trg_word):
		# decide on how to represent feedback info using type and stage
		# and implement this
		return


	def save_alignment_full_verse(self,lid,word_pairs,userId,type,Stage):
		cur = self.db.cursor()
		
		for pair in word_pairs:
			cur.execute("DELETE FROM "+self.alignment_table_name+" WHERE LidSrc = %s", (pair[0][0]))
		
			cur.execute("INSERT INTO "+self.alignment_table_name+" (LidSrc, LidTrg, PositionSrc, PositionTrg, Strongs, WordSrc, UserId, Stage) VALUES (%s, %s, %s, %s, %s, %s, 0, 1)",
				(pair[0][0], pair[1][0], pair[0][1], pair[1][1],pair[0][2], pair[1][2]))

		self.db.commit()


	


			
	def get_suggested_feedback_alignment_on_verse(self,lid_to_update):
		# decide on how to represent feedback info using type and stage
		# and implement this
		

		return replacement_options
		


		




	def fetch_alignment(self,lid):
		cur = self.db.cursor()

		print(type(lid))
		cur.execute("SELECT Word, Position FROM "+self.src_table_name+" WHERE LID = %s ORDER BY Position ",(lid))
		src_word_list = cur.fetchall()


		
		cur.execute("SELECT Strongs, Position, Word FROM "+self.trg_table_name+" WHERE LID = %s ORDER BY Position ",(lid))
		trg_word_list = cur.fetchall()
		
		cur.execute("SELECT EnglishNASB, Position FROM Grk_Eng_Aligned_Lexicon WHERE LID = %s ORDER BY Position",(lid))
		eng_word_list = cur.fetchall()

		count_trg = 0
		count_eng = 0
		trg_word_list_appended = []
		while count_trg<len(trg_word_list) and count_eng<len(eng_word_list):
			if(trg_word_list[count_trg][1] == eng_word_list[count_eng][1]):
				trg_word_list_appended.append((trg_word_list[count_trg][0],trg_word_list[count_trg][1],trg_word_list[count_trg][2],eng_word_list[count_eng][0]))
				count_trg += 1
				count_eng += 1
			elif (trg_word_list[count_trg][1] < eng_word_list[count_eng][1]):
				trg_word_list_appended.append((trg_word_list[count_trg][0],trg_word_list[count_trg][1],trg_word_list[count_trg][2],""))
				count_trg += 1
			else:
				count_eng +=1	
		if(count_trg<len(trg_word_list)):
			while (count_trg<len(trg_word_list)):
				trg_word_list_appended.append((trg_word_list[count_trg][0],trg_word_list[count_trg][1],trg_word_list[count_trg][2],""))
				count_trg += 1
		trg_word_list = trg_word_list_appended

		cur.execute("SELECT LidSrc, LidTrg, PositionSrc, PositionTrg, WordSrc, Strongs, UserID, Type, Stage from "+self.alignment_table_name+" WHERE LidSrc=%s",(lid))
		fetched_alignments = cur.fetchall()
		
		# # for all source_words get _FeedbackLookup entry
		# # and if entry present in trg_verse, add them to replacement_options
		# replacement_options=self.get_suggested_feedback_alignment_on_verse(lid)

		auto_alignments = [ ((row[0],row[2],row[4]),(row[1],row[3],row[5])) for row in fetched_alignments if row[6]==0]
		corrected_alignments = [ ((row[0],row[2],row[4]),(row[1],row[3],row[5])) for row in fetched_alignments if row[6]==11111]
		replacement_options = []
		
		return list(src_word_list), list(trg_word_list), auto_alignments, corrected_alignments, replacement_options
	


	def on_approve_feedback(self,corrected_src_trg_word_list):
		# decide on how to represent feedback info using type and stage
		# and implement this
		return


	def fetch_aligned_TWs(self,tw_index,strong_list,refs_list,cur):
		
		return_list = {}
		# required format of return_list
		# {
  #       "48004005": {
  #           "words": "('5206', 'मिले।')",
  #           "positions": ["('8', '16')"]
  #       }

		return return_list




	def fetch_all_TW_alignments(self):
		cur = self.db.cursor()

		return_dict_of_aligned_words = {}
		for tw in TWs:
			strong_list = TWs[tw]["strongs"]
			refs_list = TWs[tw]["References"]
			return_list = self.fetch_aligned_TWs(tw,strong_list,refs_list,cur)
			return_dict_of_aligned_words[str(tw)] = return_list

		cur.close()
		return json.dumps(return_dict_of_aligned_words,  ensure_ascii=False)

	def fetch_seleted_TW_alignments(self,tw_index_list):
		cur = self.db.cursor()

		return_dict_of_aligned_words = {}
		for tw in tw_index_list:
			strong_list = TWs[tw]["strongs"]
			refs_list = TWs[tw]["References"]
			return_list = self.fetch_aligned_TWs(tw,strong_list,refs_list,cur)
			return_dict_of_aligned_words[str(tw)] = return_list

		cur.close()
		return json.dumps(return_dict_of_aligned_words,  ensure_ascii=False)





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
	                     # database="itl_db",
	                     database = "AutographaMT_Staging",
	                     charset='utf8mb4')

	# connection =  pymysql.connect(host="103.196.222.37",    # your host, usually localhost
	#                     user="bcs_vo_owner",         # your username
	#                     password="bcs@0pen",  # your password
	#                     # database="bcs_vachan_engine_test",
	#                     database="bcs_vachan_engine_open",
	#                     port=13306,
	#                     charset='utf8mb4')
		
	src_version = "5"
	trg_version = "UGNT"
	if src in ["Hin","Mar","Guj","Mal"]:
		src_version = "4"
	if trg != 'Grk':
		if trg in ["Hin","Mar","Guj","Mal"]:
			trg_version = "4"
		else:
			trg_version = "5"


	obj = FeedbackAligner(connection,src,src_version,trg,trg_version)

	start = time.clock()
	
	#obj.on_approve_feedback([("2424 5547","यीशु मसीह"),("5207","सन्तान"),("5257 5547","मसीह . सेवक")])

	# src_word_list, trg_word_list, auto_alignments, corrected_alignments, replacement_options = obj.fetch_alignment('28830','grk_hin_sw_stm_ne_giza_tw__alignment')
	src_word_list, trg_word_list, auto_alignments, corrected_alignments, replacement_options = obj.fetch_alignment(28830)
	# print("src_word_list:"+str(src_word_list))
	# print("\n")
	print("trg_word_list:"+str(trg_word_list))
	print("\n")
	# print("auto_alignments:"+str(auto_alignments))
	# print("\n")
	# print("corrected_alignments:"+str(corrected_alignments))
	# print("\n")
	# print("replacement_options:"+str(replacement_options))




	# obj.update_alignment_on_verse('23146')
	
	# obj.save_alignment(123,[("xxx","YYY")],'testcase')

	# TW_alignments = obj.fetch_all_TW_alignments()
	# TW_alignments = obj.fetch_seleted_TW_alignments([1,2,3])
	#TW_alignments = obj.fetch_seleted_TW_alignments(range(17,22))

	# TW_alignments = obj.fetch_seleted_TW_alignments([18])

	# print(TW_alignments)

	print("Time taken:"+str(time.clock()-start))
	del obj
