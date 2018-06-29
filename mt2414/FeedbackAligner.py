#!/usr/bin/env python3
# FeedbackAligner.py


import re, sys, pickle
import os.path 
import pymysql


class FeedbackAligner:
	def __init__(db,self,src,trg):

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
				" (source_word VARCHAR(50) CHARACTER SET utf8mb4 NOT NULL,target_word VARCHAR(50) CHARACTER SET utf8mb4 NOT NULL,confidence_score INT)")
			cur.execute("ALTER TABLE "+self.FeedbackLookup_table_name+" ADD UNIQUE INDEX source_word_index(source_word)")
			cur.execute("ALTER TABLE "+self.FeedbackLookup_table_name+" ADD INDEX target_word_index(target_word)")
			self.db.commit()
		
	def __del__(self):
		
		self.db.commit()
		# self.db.close()
		


	def insert_into_lookup_table(self,src_word,trg_word):
		try:
			cur = self.db.cursor()
			cur.execute("INSERT INTO "+self.FeedbackLookup_table_name+" (source_word,target_word,confidence_score) VALUES (%s,%s,1)",
				(src_word,trg_word))
			self.db.commit()
			
		except Exception as e:
			print("Warning: word pair not inserted to look up table")

	def update_all_alignment_by_word(self,src_word_to_update):
		cur = self.db.cursor()

		trg_words_to_update = []
		cur.execute("SELECT target_word from "+self.FeedbackLookup_table_name+" WHERE source_word='"+src_word_to_update+"'")
		for row in cur.fetchall():
			trg_words_to_update.append(row[0])

		# print(trg_words_to_update)

		src_positions = []
		cur.execute("SELECT occurences from "+self.src_table_name+" WHERE word='"+src_word_to_update+"'")
		for row in cur.fetchall():
			src_positions.append(row[0])

		# print(src_positions)


		trg_positions = []
		temp = src_positions
		src_positions = []
		for pos in temp:
			flag = "Not found"
			verseID = re.split("_",pos)[0]
			cur.execute("SELECT target_wordID from "+self.alignment_table_name+" WHERE source_wordID like'"+verseID+"\_%' and corrected=0" )
			for target_wordID in cur.fetchall():
				if target_wordID[0].endswith("255"):
					continue
				cur2 = self.db.cursor()
				cur2.execute("SELECT word from "+self.trg_table_name+" WHERE occurences='"+target_wordID[0]+"'")
				if cur2.rowcount == 0:
					continue
				trg_word = cur2.fetchone()[0]
				# print("Checking "+trg_word+" at "+target_wordID[0])
				if trg_word in trg_words_to_update and target_wordID not in trg_positions:
						trg_positions.append(target_wordID[0])
						flag = "Found"
						# print("FOUND ONE")
						break
			if flag =="Found":
				src_positions.append(pos)

		print(src_positions)
		print(trg_positions)


		for sp,tp in zip(src_positions,trg_positions):
			print(sp)
			print(tp)
			verseID=re.split("_",sp)[0]
			cur.execute("DELETE FROM "+self.alignment_table_name+"  WHERE source_wordID='"+sp+"'")

			verseID=re.split("_",tp)[0]
			cur.execute("DELETE FROM "+self.alignment_table_name+"  WHERE target_wordID='"+tp+"'")

			cur.execute("INSERT INTO "+self.alignment_table_name+" (source_wordID,target_wordID,corrected) VALUES (%s,%s,0)",
				(sp,tp))

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
		for s_wrd in src_word_list:
			cur.execute("SELECT target_word FROM "+self.FeedbackLookup_table_name+" WHERE source_word='"+s_wrd[0]+"' ORDER BY confidence_score")
			for row in cur.fetchall():
				mapped_trg_word = row[0]
				flag = False
				for t_wrd in trg_word_list:
					if t_wrd[0]==mapped_trg_word:
						replacement_options.append((s_wrd[1],t_wrd[1]))
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





	def mark_alignment_as_verified(self,lid):
		cur = self.db.cursor()

		cur.execute("UPDATE "+self.alignment_table_name+" SET corrected=1 WHERE source_wordID LIKE '"+str(lid)+"\_%'")
		self.db.commit()



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
	                     charset='utf8')
		

	
	obj = FeedbackAligner(connection, src,trg)


	# obj.on_approve_feedback([("G24240","यीशु"),("G52070","सन्तान")])

	# obj.mark_alignment_as_verified(23147)

	obj.update_alignment_on_verse('23146')
	

	del obj