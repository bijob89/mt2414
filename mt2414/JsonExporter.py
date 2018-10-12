import time
import json

class JsonExporter:

    def __init__(self, db, src, trg, bookcode, book, tablename, usfmFlag):
        self.db = db.cursor()
        self.src = src
        self.trg = trg
        self.tablename = tablename
        self.src_bible_words_table = self.src.capitalize() + '_4_BibleWord'
        self.trg_bible_words_table = self.trg.capitalize() + '_UGNT_BibleWord'
        self.src_text_table = 'Hin_4_Text'
        self.grk_table = 'Grk_UGNT_Text'
        self.book = book
        self.bc = int(bookcode)
        self.usfmFlag = usfmFlag
        if self.usfmFlag:
            self.usfm_table = self.src + '_IRV_Text_USFM'
            self.db.execute("SELECT bcv, verse FROM " + self.usfm_table)
            usfm_rst = self.db.fetchall()
            self.src_usfm_dict = {}
            for u in usfm_rst:
                self.src_usfm_dict[u[0]] = u[1]


    def alignmentarrayelements(self, a_list):
        '''Alignment Array for a verse'''
        alignmentArrayList = []
        for i in range(len(a_list[0])):
            alignmentArrayelement = {
                "score": a_list[0][i],
                "r0": a_list[1][i][0],
                "r1": a_list[1][i][1],
                "verified": a_list[2][i]
            }
            alignmentArrayList.append(alignmentArrayelement)
        return alignmentArrayList


    def segmentResourceValue(self, r_list):
        '''Individual resource element'''
        metadata = {
            "contextId": r_list[0]
        }
        if r_list[2] == []:
            value = {
                "text": r_list[1],
                "tokens": r_list[1].split(' '),
                "metadata": metadata
            }
        else:
            value = {
                "text": r_list[1],
                "tokens": r_list[1].split(' '),
                "metadata": metadata,
                "usfm": r_list[2]
            }

        return value


    def segmentResourceArray(self, r_list):
        '''Resource Array for a verse'''
        resources = {
            "r0": self.segmentResourceValue([r_list[0], r_list[1], []]),
            "r1": self.segmentResourceValue([r_list[0], r_list[2], r_list[3]])
        }
        return resources


    def generateSegmentList(self, s_list):
        '''Argument contains verse id, resource texts, alignments list and alignment verified list'''
        resources = self.segmentResourceArray(s_list[0])
        alignments = self.alignmentarrayelements(s_list[1])
        return (resources, alignments)


    def segmentArrayElements(self, s_list):
        '''List of resources and alignment tuple'''
        segmentArrayList = []
        for item in s_list:
            value = self.generateSegmentList(item)
            segmentArrayelement = {
                "resources": value[0],
                "alignments": value[1]
            }
            segmentArrayList.append(segmentArrayelement)
        return segmentArrayList


    def metadataResources(self, m_list):
        value = {
            "languageCode": m_list[0],
            "name": m_list[1],
            "version": m_list[2]
        }
        return value


    def metadataArray(self, m_list):
        resources = {
            'r0': self.metadataResources(m_list[0]),
            'r1': self.metadataResources(m_list[1])
        }
        metadata = {
            "resources": resources,
            "modified": int(time.time())
        }
        return metadata

    def db_text_to_list(self, value):
        text_list = ['' for i in range(len(value))]
        for item in value:
            index = item[0]
            text_list[int(index) - 1] = item[1]
        return text_list

    def exportAlignments(self):

        # Create BCV LID Dict
        lid_dict = {}
        self.db.execute("SELECT ID, Book, Chapter, Verse FROM Bcv_LidMap WHERE Book = %s", (self.bc,))
        lid_rst = self.db.fetchall()
        for l,b,c,v in lid_rst:
            lid_dict[l] = str(b) + str(c).zfill(3) + str(v).zfill(3)

        bcv_dict = {v:k for k,v in lid_dict.items()}

        # Generate Range for the book selected
        low = bcv_dict[sorted(list(bcv_dict.keys()))[0]]
        high = low + 1000

        # Fetch Positional pair info from the Range
        self.db.execute("SELECT LidSrc, PositionSrc, WordSrc, PositionTrg, Strongs, Stage FROM \
        Hin_4_Grk_UGNT_Alignment WHERE LidSrc >= %s AND LidSrc < %s", (low, high))
        align_rst = self.db.fetchall()

        # Fetch Source word list from chopped Bible
        self.db.execute("SELECT LID, Position, Word FROM " + self.src_bible_words_table + \
        " WHERE LID >= %s AND LID < %s", (low, high))
        src_rst = self.db.fetchall()
        src_tup_dict = {}
        for item in src_rst:
            if item[0] in src_tup_dict:
                src_tup_dict[item[0]] = src_tup_dict[item[0]] + [(item[1], item[2])]
            else:
                src_tup_dict[item[0]] = [(item[1], item[2])]

        # Fetch Target word list from chopped Bible with LID as key
        self.db.execute("SELECT LID, Position, Strongs FROM " + self.trg_bible_words_table + \
        " WHERE LID >= %s AND LID < %s", (low, high))
        trg_rst = self.db.fetchall()
        trg_tup_dict = {}
        for item in trg_rst:
            if item[0] in trg_tup_dict:
                trg_tup_dict[item[0]] = trg_tup_dict[item[0]] + [(item[1], item[2])]
            else:
                trg_tup_dict[item[0]] = [(item[1], item[2])]

        # Create a dict with LID as key and joined bible words text as value for source and target
        src_text_dict = {}
        trg_text_dict = {}
        for key in src_tup_dict.keys():
            src_text_dict[key] = " ".join(self.db_text_to_list(src_tup_dict[key]))
        for key in trg_tup_dict.keys():
            trg_text_dict[key] = " ".join([str(x) for x in self.db_text_to_list(trg_tup_dict[key])])


        stage_dict = {}
        # Create positional pairs dict with LID as key
        positional_pairs = {}
        for item in align_rst:
            pos_pair = str(item[1]) + '-' + str(item[3])
            if item[0] in positional_pairs:
                positional_pairs[item[0]] = positional_pairs[item[0]]  + [pos_pair]
            else:
                positional_pairs[item[0]] = [pos_pair]
            stage_dict[item[0]] = item[5]

        # Fetch Target text
        self.db.execute("SELECT lid, verse FROM " + self.grk_table)
        grk_rst = self.db.fetchall()
        grk_dict = {}
        for g in grk_rst:
            grk_dict[g[0]] = g[1]

        # Fetch Source text
        self.db.execute("SELECT LID, Verse from " + self.src_text_table)
        rst_src_text = self.db.fetchall()
        src_text_dt = {}
        for tt in rst_src_text:
            src_text_dt[tt[0]] = tt[1]

        alignment_dict = {}

        for k in lid_dict.keys():
            align_list = []
            temp_dict = {}
            reverse_temp_dict = {}
            v = positional_pairs[k]
            for item in v:
                s, t = item.split('-')
                if s in temp_dict:
                    temp_dict[s] = temp_dict[s] + [t]
                else:
                    temp_dict[s] = [t]
            for r0, r1 in temp_dict.items():
                key = str(r0)
                value = ' '.join(str(x) for x in r1)
                if value in reverse_temp_dict:
                    reverse_temp_dict[value] = reverse_temp_dict[value] + ' ' + key
                else:
                    reverse_temp_dict[value] = key

            for ky, val in reverse_temp_dict.items():
                va1ue1 = []
                for i in ky.split(' '):
                    if i == '255':
                        pass
                    else:
                        va1ue1.append(int(i) - 1)
                value2 = []
                for j in val.split(' '):
                    if j == '255':
                        pass
                    else:
                        value2.append(int(j) - 1)
                align_list.append([value2, va1ue1])
                
            alignment_dict[k] = align_list

        j_list1 = [[self.src, 'UGNT', '0.1'], [self.trg, 'UGNT', '0.1']]

        j_list2 = []
        for item in sorted(alignment_dict.keys()):
            bcv = lid_dict[item]
            if item in grk_dict:
                src_text = grk_dict[item]
            else:
                src_text = src_text_dict[item]
            if src_text_dt[item].strip() != '':
                trg_text = src_text_dt[item]
            else:
                trg_text = trg_text_dict[item]
            alignments = alignment_dict[item]
            source_list = [0 for i in range(len(alignments))]

            if stage_dict[item] == 1:
                verified_list = [True for i in range(len(src_text_dict[item].split(" ")))]
            else:
                verified_list = [False for i in range(len(src_text_dict[item].split(" ")))]
            contextId = str(bcv)[-6:]
            contextId = self.book.upper() + contextId
            if self.usfmFlag:
                usfm_text = self.src_usfm_dict[int(bcv)]
                j_list2.append([[contextId, src_text, trg_text, usfm_text], [source_list, alignments, verified_list]])
            else:
                j_list2.append([[contextId, src_text, trg_text, []], [source_list, alignments, verified_list]])

        j_list = [j_list1] + [j_list2]

        metadata = self.metadataArray(j_list[0])
        segments = self.segmentArrayElements(j_list[1])

        json_text = json.dumps({
            "metadata": metadata,
            "conformsTo": "alignment-0.1",
            "segments": segments
            }, ensure_ascii=False)

        self.db.close()

        return json_text



