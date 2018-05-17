from collections import Counter
import re
import glob
import os

books = {"1": "GEN", "2": "EXO", "3": "LEV", "4": "NUM", "5": "DEU", "6": "JOS", "7": "JDG", "8": "RUT", "9": "1SA", "10": "2SA", "11": "1KI", "12": "2KI", "13": "1CH", "14": "2CH", "15": "EZR", "16": "NEH", "17": "EST", "18": "JOB", "19": "PSA", "20": "PRO", "21": "ECC", "22": "SNG", "23": "ISA", "24": "JER", "25": "LAM", "26": "EZK", "27": "DAN", "28": "HOS", "29": "JOL", "30": "AMO", "31": "OBA", "32": "JON", "33": "MIC", "34": "NAM", "35": "HAB", "36": "ZEP", "37": "HAG", "38": "ZEC", "39": "MAL", "40": "MAT", "41": "MRK", "42": "LUK", "43": "JHN", "44": "ACT", "45": "ROM", "46": "1CO", "47": "2CO", "48": "GAL", "49": "EPH", "50": "PHP", "51": "COL", "52": "1TH", "53": "2TH", "54": "1TI", "55": "2TI", "56": "TIT", "57": "PHM", "58": "HEB", "59": "JAS", "60": "1PE", "61": "2PE", "62": "1JN", "63": "2JN", "64": "3JN", "65": "JUD", "66": "REV"}
books_inverse = {v:k for k,v in books.items()} 
stop_words =  ["के", "का", "की", "है", "यह", "हैं", "को", "इस", "कि", "जो", "ने", "हो", "था", "वाले", "बाद", "ये", "इसके", "थे", "होने", "वह", "वे", "होती", "थी", "हुई", "जा", "इसे", "जब", "होते", "कोई", "हुए", "व", "न", "अभी", "जैसे", "सभी", "तरह", "उस", "आदि", "कुल", "एस", "रहा", "रहे", "इसी", "रखें", "पे", "उसके"]
punctuations = '!"#$%&\\\'\(\)\*\+,\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।'
counter_list = []
greek_bible_text_dict = {}
counter_dict_sn = {}
greek_element_index = {}
greek_text_dict = {}
occ_dict = {}

def removeref(text):
    '''
    Cleans text by removing punctuations, numbers and special symbols
    '''
    fc = re.sub(r"[A-Z0-9]{3}\t\d+\t\d+\t ?", "", text)
    fc = re.sub(r'([!"#$%&\\\'\(\)\*\+,\.\/:;<=>\?\@\[\]^_`{|\}~\”\“\‘\’।0123456789cvpsSAQqCHPETIidmJNa])',"",fc)
    return fc


def ref_parser(text):
    '''
    Cleans the text by removing all cross references
    '''
    fc = re.sub(r'\((\W+)\)(.*)\((\W+)\)', r'opening_bracket\1closing_bracket\2opening_bracket\3closing_bracket', text)
    fc = re.sub(r'\((\W+)\)', r'opening_bracket\1closing_bracket', fc)
    fc = re.sub(r' \(.*\d+:\d+.*\)\n', '\n', fc)
    fc = re.sub('opening_bracket', '(', fc)
    fc = re.sub('closing_bracket', ')', fc)
    return fc


def hi_stem(word):
    '''
    Creates Stem words
    '''
    suffixes = {
    1: ["ो", "े", "ू", "ु", "ी", "ि", "ा"],
    2: ["कर", "ाओ", "िए", "ाई", "ाए", "ने", "नी", "ना", "ते", "ीं", "ती", "ता", "ाँ", "ां", "ों", "ें"],
    3: ["ाकर", "ाइए", "ाईं", "ाया", "ेगी", "ेगा", "ोगी", "ोगे", "ाने", "ाना", "ाते", "ाती", "ाता", "तीं", "ाओं", "ाएं", "ुओं", "ुएं", "ुआं"],
    4: ["ाएगी", "ाएगा", "ाओगी", "ाओगे", "एंगी", "ेंगी", "एंगे", "ेंगे", "ूंगी", "ूंगा", "ातीं", "नाओं", "नाएं", "ताओं", "ताएं", "ियाँ", "ियों", "ियां"],
    5: ["ाएंगी", "ाएंगे", "ाऊंगी", "ाऊंगा", "ाइयाँ", "ाइयों", "ाइयां"]
    }
    for L in 5, 4, 3, 2, 1:
        if len(word) > L + 1:
            for suf in suffixes[L]:
                if word.endswith(suf):
                    return word[:-L]
    return word


def digit_lenght_check(num):
    '''to convert all book, chapter and verse codes to 3 digit values
     to match the verse code from the "ProjectBiblicalTerms" file'''
    if len(num) == 1:
        return '00' + num
    else:
        return '0' + num

def generate_counters():
    counter_dict = {}
    counter_arr = Counter(counter_list)
    for k,v in counter_arr.items():
        if 'NULL' in k:
            continue
        word, sn = k.split('\t')
        if word in counter_dict:
            temp_dict = {}
            temp_dict = counter_dict[word]
            del counter_dict[word]
            if v in temp_dict:
                temp_dict[v] = temp_dict[v] + [sn]
            else:
                temp_dict[v] = [sn]
            counter_dict[word] = temp_dict
        else:
            counter_dict[word] = {v:[sn]}
        if sn in counter_dict_sn:
            temp_dict1 = {}
            temp_dict1 = counter_dict_sn[sn]
            del counter_dict_sn[sn]
            if v in temp_dict1:
                temp_dict1[v] = temp_dict1[v] + [word]
            else:
                temp_dict1[v] = [word]
            counter_dict_sn[sn] = temp_dict1
        else:
            counter_dict_sn[sn] = {v:[word]}
    return counter_dict

def occurance(stem_fc):
    f = open(os.getcwd() + '/externalfiles/temp.txt', 'r')
    fc = (f.read().strip()).split('\n')
    hindi_complete_dict = {}
    hindi_stem_dict = {}
    for line in stem_fc:
        line_split = line.split('\t')
        if line_split[3] == 'NULL':
            word = line_split[2]
        else:
            word = line_split[3]
        if line_split[0] in hindi_complete_dict:
            hindi_complete_dict[line_split[0]] = hindi_complete_dict[line_split[0]] + [word]
        else:
            hindi_complete_dict[line_split[0]] = [word]
        
        if word not in punctuations and word not in stop_words:
            word = hi_stem(word)
            if line_split[0] in hindi_stem_dict:
                hindi_stem_dict[line_split[0]] = hindi_stem_dict[line_split[0]] + [word]
            else:
                hindi_stem_dict[line_split[0]] = [word]
    for line in fc:
        vc, verse = line.split('\t')
        
        temp_occ_dict = {}
        temp_occ_list = []
        words = verse.split()
        for w in words:
            if w in stop_words:
                temp_occ_list.append(w)
            else:
                temp_occ_list.append(hi_stem(w))
        for wd in set(temp_occ_list):
            temp_occ_dict[wd] = temp_occ_list.count(wd)
        occ_dict[vc] = temp_occ_dict

    
def word_strong_vc_dict(textfile):
    '''
    Creates a dict with verse code(BCV) as key and another dict as value which contains
    the hindi word as key and a list of strong numbers as the value.
    '''
    pattern = re.compile(r'g\d+')
    vc_dict = {}
    i = 0
    for line in textfile:
        line_s = line.split('\t')
        vc = line_s[0]
        i += 1
        for l in line_s[1].split('> '):
            if l == '' or '<' not in l:
                continue
            word, sn = l.split(' <')
            if re.search(pattern, word):
                word, sn = sn, word
            if ' ' in word:
                word = word.split(' ')[1]
            if ' ' in sn:
                sn = sn.split(' ')[1]
            counter_list.append(word + '\t' + sn)
            if vc in vc_dict:
                temp = vc_dict[vc]
                if word in temp:
                    temp[word] = list(set(temp[word] + [sn]))
                else:
                    temp[word] = [sn]
                del vc_dict[vc]
                vc_dict[vc] = temp
            else:
                vc_dict[vc] = {word:[sn]}
    return vc_dict


def generate_greek_text(vc):
    pattern = re.compile(r'g\d+')
    pattern1 = re.compile('Sentence pair')
    giz_infile = open(os.getcwd() + '/externalfiles/combined_output.txt', 'r')
    giz_fc = (giz_infile.read().strip()).split('\n')
    greek_element_index_list = []
    greek_text_list = []
    for line in giz_fc:
        if re.search(pattern, line):
            greek_text_list.append(line)
    el_flag = False
    i = 0
    for line in giz_fc:
        if re.search(pattern1, line):
            el_flag = True
            continue
        if el_flag:
            line_split = line.split('})')
            line_split.pop(-1)
            temp_dict = {}
            for el in line_split:
                w, pos = el.split('({')
                w = w.strip()
                pos = [(','.join((pos.strip()).split(' ')),)]
                if w in temp_dict:
                    temp_dict[w] = temp_dict[w] + pos
                else:
                    temp_dict[w] = pos
            greek_element_index_list.append(temp_dict)
            el_flag = False
    for item in vc:
        greek_text_dict[item] = greek_text_list[i]
        greek_element_index[item] = greek_element_index_list[i]
        i += 1

def create_greek_lemma(content):
    main_list = []
    book_name = re.search(r'\\id ([1-9A-Z]{3})', content).group(1)
    for line in fc.split('\n'):
        i = 0
        if re.search(r'(\c )(\d+)', line):
            chapter_num = re.search(r'(\c )(\d+)', line).group(2)
        elif re.search(r'(\\v )(\d+)', line):
            verse_num = re.search(r'(\\v )(\d+)', line).group(2)
        elif re.search(r'(\\w )(.*)', line):
            verse = re.search(r'(\\w )(.*)', line).group(2)
            m = re.search(r'(.*)\|lemma="(.*)" strong="(.*)" x-morph="(.*)"(?:\sx.*)?\w*', verse)
            verse = re.sub(r'(\\w)(.*)', r'' + 'MAT\t' + str(chapter_num) + '\t' + str(verse_num) + '\t' + '\\2', line)
            verse_code = digit_lenght_check(books_inverse[book_name]) + digit_lenght_check(chapter_num) + digit_lenght_check(verse_num)
            x_content = m.group(1)
            lemma = m.group(2)
            strong = m.group(3).lower()
            morph = m.group(4).split('" ')[0]
            main_list.append([verse_code, str(i), x_content, lemma, strong, morph])
            i + 1
    return main_list

def generate_greek_lemma(contents):
    main_dict = {}
    for f in contents:
        fc = f[0]       #open(os.getcwd() + '/ugnt/' + filename, 'r').read().strip()
        book_name = re.search(r'\\id ([1-9A-Z]{3})', fc).group(1)
        for line in fc.split('\n'):
            if re.search(r'(\c )(\d+)', line):
                chapter_num = re.search(r'(\c )(\d+)', line).group(2)
            elif re.search(r'(\\v )(\d+)', line):
                verse_num = re.search(r'(\\v )(\d+)', line).group(2)
            elif re.search(r'(\\w )(.*)', line):
                verse = re.search(r'(\\w )(.*)', line).group(2)
                m = re.search(r'(.*)\|lemma="(.*)" strong="(.*)" x-morph="(.*)"(?:\sx.*)?\w*', verse)
                verse = re.sub(r'(\\w)(.*)', r'' + 'MAT\t' + str(chapter_num) + '\t' + str(verse_num) + '\t' + '\\2', line)
                verse_code = digit_lenght_check(books_inverse[book_name]) + digit_lenght_check(chapter_num) + digit_lenght_check(verse_num)
                x_content = m.group(1)
                lemma = m.group(2)
                strong = m.group(3).lower()
                morph = m.group(4).split('" ')[0]
                if verse_code in greek_bible_text_dict:
                    greek_bible_text_dict[verse_code] = greek_bible_text_dict[verse_code] + [x_content]
                else:
                    greek_bible_text_dict[verse_code] = [x_content]
                if verse_code in main_dict:
                    temp_dict = main_dict[verse_code]
                    if strong in temp_dict:
                        temp_strong_dict = temp_dict[strong]
                        similar_check = False
                        for k,v in temp_strong_dict.items():
                            if v['lemma'] == lemma and v['morph'] == morph and v['x_content'] == x_content:
                                similar_check = True
                                break
                        if similar_check == False:
                            count = len(temp_strong_dict)
                            temp_strong_dict[count + 1] = {'lemma':lemma, 'morph':morph, 'x_content':x_content}
                            del temp_dict[strong]
                            temp_dict[strong] = temp_strong_dict
                            del main_dict[verse_code]
                            main_dict[verse_code] = temp_dict
                    else:
                        temp_dict[strong] = {1:{'lemma':lemma, 'morph':morph, 'x_content':x_content}}
                        del main_dict[verse_code]
                        main_dict[verse_code] = temp_dict
                else:
                    main_dict[verse_code] = {strong:{1:{'lemma':lemma, 'morph':morph, 'x_content':x_content}}}
    return main_dict


def create_positional_pairs(stemtext, hindi_vc_dict, strong_vc_dict, counter_dict, main_dict):
    main_text_list = []
    positional_pairs_list = []
    strongs_pattern = re.compile(r'g\d+')
    current_vc = None
    for line in stemtext:
        items = line.split('\t')
        # greek_text_dict --> vc -> key , strong number verse text -> value
        if items[0] in greek_text_dict:
            full_greek_verse_list = greek_text_dict[items[0]].split(' ')
        if items[0] not in hindi_vc_dict:
            positional_pairs_list.append('\t'.join(items[0:2]))
            continue
        # Check if any greek/strongs is left out. Also re - initialize dicts used in the program
        if items[0] != current_vc:
            # Checks if it's the first iteration or not
            if current_vc != None:
                # main dict has the lemma, strong and x_content
                temp_lem_dict = main_dict[current_vc]
                all_greek = greek_text_dict[current_vc].split(' ')
                remain = set(all_greek) - set(current_strongs_list)
                line_no = int(items[0]) - 1
                temp_sn_list = []
                for sn in remain:
                    grk_temp_list = greek_text_dict[current_vc].split(' ')
                    if sn not in temp_sn_list:
                        position = grk_temp_list.index(sn) + 1
                        temp_sn_list.append(sn)
                    else:
                        sn_count = grk_temp_list.count(sn)
                        temp_list_count = temp_sn_list.count(sn)
                        for i in range(temp_list_count):
                            grk_temp_list.remove(sn)
                        position = grk_temp_list.index(sn) + temp_list_count + 1
                        temp_sn_list.append(sn)
                    if sn in temp_lem_dict:
                        mor_lem_dict = temp_lem_dict[sn]
                        mor_lem_dict = mor_lem_dict[1]
                        x_occ = mor_lem_dict['x_content']
                        lem = mor_lem_dict['lemma']
                        morp = mor_lem_dict['morph']
                        length = greek_bible_text_dict[current_vc].count(x_occ)            
                        positional_pairs_list.append(current_vc + '\t' + '-' + '\t' + '-' + '\t' + str(position) + '\t' + sn + '\t' + x_occ + '\t' + '-')
                    else:
                        positional_pairs_list.append(current_vc + '\t' + '-' + '\t' + '-' + '\t' + str(position) + '\t' + sn + '\t' + x_occ + '\t' + '-')
            current_strongs_list = []
            hindi_dt = hindi_vc_dict[items[0]]
            strong_dt = strong_vc_dict[items[0]]
            occurance_dict = {}
            occurance_main_dict = occ_dict[items[0]]
            punct_count = 0
        current_vc = items[0]
        if items[3] in occurance_dict:
            occurance_dict[items[3]] = occurance_dict[items[3]] + 1
        else:
            occurance_dict[items[3]] = 1
        if items[3] == 'NULL' or items[3] in punctuations:
            positional_pairs_list.append('\t'.join(items[0:3]) + '\t-' * 4)
        else:
            confidence_dict = {}
            if items[3] in hindi_dt and items[3] in strong_dt:
                for item in hindi_dt[items[3]]:
                    if item not in full_greek_verse_list:
                        continue
                    if item in strong_dt[items[3]]:
                        confidence_dict[item] = 2
                    else:
                        confidence_dict[item] = 1
                additional_sn = set(strong_dt[items[3]]) - set(hindi_dt[items[3]])
                comb_check = []
                comb_sn = []
                for it in additional_sn:
                    if it not in full_greek_verse_list:
                        continue
                    for k,v in hindi_dt.items():
                        if k == 'NULL' and it in v:
                            comb_check.append(it)
                        else:
                            continue
                for s in comb_check:
                    confidence_dict[s] = 1
            elif items[3] in strong_dt and items[3] not in hindi_dt:
#                 if items[4] in strong_dt:
                for item in strong_dt[items[3]]:
                    if item not in full_greek_verse_list:
                        continue
                    if 'NULL' in hindi_dt.items():
                        if item in hindi_dt['NULL']:
                            confidence_dict[item] = 1
            else:
                # counter dict = {hindi_word: {no_of_occurence:[list of strongs number]}}
                if items[3] in counter_dict:
                    no_sn = counter_dict[items[3]]
                    max_val = max(no_sn.keys())
                    for s in no_sn[max_val]:
                        if s != 'NULL' and s in full_greek_verse_list:
                            confidence_dict[s] = 5
                else:
                    print(items[3])
            sn_list = []
            conf_list = []
            for k,v in confidence_dict.items():
                sn_list.append(k)
                conf_list.append(str(v))
            temp_lemma_dict = main_dict[items[0]]
            x_content_list = []
            morph_list = []
            lemma_list = []
            greek_lenght = []
            temp_sn_list1 = []
            pos_list = []
            position = ''
            for num in sn_list:
                if re.search(strongs_pattern, num):
                    current_strongs_list.append(num)
                    grk_temp_list1 = greek_text_dict[items[0]].split(' ')
                    m_count_sn = grk_temp_list1.count(num)
                    # Check previous strong to acertain greek position
                    if num not in temp_sn_list1:
                        position = str(grk_temp_list1.index(num) + 1)
                        pos_list.append(position)
                        temp_sn_list1.append(num)
                    else:
                        sn_count = grk_temp_list1.count(num)
                        temp_list_count = temp_sn_list1.count(num)
                        for i in range(temp_list_count):
                            grk_temp_list1.remove(num)
                        position = str(grk_temp_list1.index(num) + temp_list_count + 1)
                        pos_list.append(position)
                        temp_sn_list1.append(num)

                if num == 'NULL':
                    x_content_list.append('NULL')
                    morph_list.append('NULL')
                    lemma_list.append('NULL')
                elif num not in temp_lemma_dict:
                    x_content_list.append('NULL')
                    morph_list.append('NULL')
                    lemma_list.append('NULL')
                else:
                    morph_lemma_dict = temp_lemma_dict[num]
                    morph_lemma_dict = morph_lemma_dict[1]
                    x_content_list.append(morph_lemma_dict['x_content'])
                    morph_list.append(morph_lemma_dict['morph'])
                    lemma_list.append(morph_lemma_dict['lemma'])

            for grk in x_content_list:
                length = greek_bible_text_dict[items[0]].count(grk)
                greek_lenght.append(str(length))
            positional_pairs_list.append('\t'.join(items[0:3]) + '\t' + ','.join(pos_list) + '\t' + ','.join(sn_list) +  '\t' + ','.join(x_content_list) + '\t' + ','.join(conf_list))
    return '\n'.join(positional_pairs_list)

def aligned_texts(main_dict):
    hindi_itl = (open(os.getcwd() + '/externalfiles/hindi_interlinear.txt', 'r').read().strip()).split('\n')
    strong_itl = (open(os.getcwd() + '/externalfiles/strong_interlinear.txt', 'r').read().strip()).split('\n')
    hindi_vc_text = (open(os.getcwd() + '/externalfiles/vc_hindi_text.txt', 'r').read().strip()).split('\n')
    stem_text = (open(os.getcwd() + '/externalfiles/stemmed_vc_text.txt', 'r').read().strip()).split('\n')
    hindi_itl_vc = [hindi_vc_text[i].split('\t')[0] + '\t' + hindi_itl[i]  for i in range(len(hindi_vc_text))]
    print('First')
    verse_code_list = [item.split('\t')[0] for item in hindi_itl_vc]
    strong_itl_vc = [hindi_vc_text[i].split('\t')[0] + '\t' + strong_itl[i]  for i in range(len(hindi_vc_text))]
    generate_greek_text(verse_code_list)
    print('Second')
    occurance(stem_text)
    generate_counters()
    hindi_vc_dict = word_strong_vc_dict(hindi_itl_vc)
    strong_vc_dict = word_strong_vc_dict(strong_itl_vc)
    # greek_strongs_vc = (open('greek_strongs_text.txt', 'r').read().strip().split('\n'))
    counter_dict = generate_counters()
    print('Also here')
    json_file = create_positional_pairs(stem_text, hindi_vc_dict, strong_vc_dict, counter_dict, main_dict)
    tofile = open('posi.output.txt', 'w')
    tofile.write(json_file)
    tofile.close()