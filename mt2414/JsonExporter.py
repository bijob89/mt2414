import time
import json

class JsonExporter:

    def __init__(self, db, src, trg, tablename):
        self.db = db.cursor()
        self.src = src
        self.trg = trg
        self.tablename = tablename #self.src + '_' + self.trg + '_' + 'alignment'
        self.src_table = 'lid_strong_text'
        self.trg_table = 'lid_' + self.trg + '_text'

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
        value = {
            "text": r_list[1],
            "tokens": r_list[1].split(' '),
            "metadata": metadata
        }
        return value


    def segmentResourceArray(self, r_list):
        '''Resource Array for a verse'''
        # print(r_list)
        resources = {
            "r0": self.segmentResourceValue([r_list[0], r_list[1]]),
            "r1": self.segmentResourceValue([r_list[0], r_list[2]])
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
        # print(len(s_list))
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


    def exportAlignments(self):

        lid_dict = {}
        self.db.execute("SELECT bcv, lid FROM bcv_lid_map")
        lid_rst = self.db.fetchall()
        for item in lid_rst:
            lid_dict[item[1]] = item[0]

        src_text_dict = {}
        self.db.execute("SELECT lid, verse FROM " + self.src_table)
        src_rst = self.db.fetchall()
        for item in src_rst:
            src_text_dict[item[0]] = item[1]

        trg_text_dict = {}
        self.db.execute("SELECT lid, verse FROM " + self.trg_table)
        trg_rst = self.db.fetchall()
        for item in trg_rst:
            trg_text_dict[item[0]] = item[1]

        self.db.execute("SELECT lid, source_wordID, target_wordID FROM " + self.tablename)
        ppr_rst = self.db.fetchall()
        ppr_dict = {}
        for items in ppr_rst:
            if items[0] in ppr_dict:
                ppr_dict[items[0]] = ppr_dict[items[0]] + [items[1].split('_')[1] \
                + '-' + items[2].split('_')[1]]
            else:
                ppr_dict[items[0]] = [items[1].split('_')[1] + '-' + items[2].split('_')[1]]

        alignment_dict = {}
        for k,v in ppr_dict.items():
            align_list = []
            temp_dict = {}
            reverse_temp_dict = {}
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
                va1ue1 = [int(i) for i in ky.split(' ')]
                value2 = [int(j) for j in val.split(' ')]
                align_list.append([value2, va1ue1])
            
            alignment_dict[k] = align_list

        j_list1 = [[self.src, 'UGNT', '0.1'], [self.trg, 'UGNT', '0.1']]

        j_list2 = []
        for item in sorted(alignment_dict.keys()):
            bcv = lid_dict[item]
            src_text = src_text_dict[item]
            trg_text = trg_text_dict[item]
            alignments = alignment_dict[item]
            source_list = [0 for i in range(len(alignments))]
            verified_list = [False for i in range(len(alignments))]
            j_list2.append([[bcv, src_text, trg_text], [source_list, alignments, verified_list]])

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



