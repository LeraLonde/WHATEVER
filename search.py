import nltk
import sys
import getopt
import math
import linecache
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer
import xml.etree.ElementTree as ET
import string


stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

# read dictionary file into dictionary stored in memory, return dictionary and total number of documents
def read_dict(dictionary_file):
    dictionary = {}
    for line in dictionary_file:
        # format: term doc_freq lineNum
        content = line.split()
        
        dictionary[content[0]] = {
            'doc_freq': int(content[1]),
            'line': int(content[2])
        }
    return dictionary

# read document length file into doc_len_dict, for document length normalisation
def read_doc_length(doc_length_file):
    doc_len_dict = {}
    for line in doc_length_file:
        docId, doc_len = line.split()
        doc_len_dict[docId] = float(doc_len)
    return doc_len_dict

# get posting list of a given term from postings file
def get_posting(term_dictionary, postings_file):
  
    line_number = term_dictionary['line']
    posting_str = linecache.getline(postings_file,line_number)
    posting_list = posting_str.strip().split(',')

    return posting_list


# main method
def search(dictionary_file,postings_file,input_file,output_file):
    dictionary_file = file(dictionary_file)
    #postings_file = file(postings_file)
    input_file = file(input_file)
    output_file = file(output_file, 'w')
    title_length_file = file('title_length.txt')
    desc_length_file = file('desc_length.txt')

    # keep the dictionary in memory, total_doc_freq keeps track of total number of documents
    dictionary = read_dict(dictionary_file)
    total_document = dictionary['TOTAL_DOCS']['doc_freq']
    # read document length
    title_length_dict = read_doc_length(title_length_file)
    desc_length_dict = read_doc_length(desc_length_file)
    
    root = ET.parse(input_file).getroot()
    tags = root.getiterator()

    # read the relevant tags
    title_string = ''
    desc_string = ''
    for tag in tags:
        if tag.tag == 'title' :
            # filter non-ascii characters
            title_string = filter(lambda x: x in string.printable, tag.text.lower().strip())
        elif tag.tag == 'description':
            desc_string = filter(lambda x: x in string.printable, tag.text.lower().strip().replace('relevant documents will describe', ''))
    
    title_list = tokenizer.tokenize(title_string)
    desc_list = tokenizer.tokenize(desc_string)
    title_list = map(stemmer.stem, title_list)
    desc_list = map(stemmer.stem, desc_list)

    title_set = set(title_list)
    desc_set = set(desc_list)
    title_score = {}
    desc_score = {}
    title_vector = []
    desc_vector = []

    for term in title_set:
        if term in dictionary:
            df = dictionary[term]['doc_freq']
            idf = math.log(total_document/df, 10)

            tf_raw = title_list.count(term)
            tf_wt = 1 + math.log(tf_raw, 10)
            title_weight = idf * tf_wt

            title_vector.append(title_weight)
            posting = get_posting(dictionary[term], postings_file)

            for p in posting:
                
                p_list= p.split()
                docId, title_tf = p_list[0], float(p_list[1])
                if title_tf != 0:
                    title_tf_wt = 1 + math.log(title_tf, 10)
                    if docId in title_score:
                        title_score[docId] += title_weight * title_tf_wt
                    else:
                        title_score[docId] = title_weight * title_tf_wt

    for term in desc_set:
        if term in dictionary:
            df = dictionary[term]['doc_freq']
            idf = math.log(total_document/df, 10)

            tf_raw = desc_list.count(term)
            tf_wt = 1 + math.log(tf_raw, 10)
            desc_weight = idf * tf_wt

            desc_vector.append(desc_weight)
            posting = get_posting(dictionary[term], postings_file)

            for p in posting:
                p_list= p.split()
                docId, desc_tf = p_list[0], float(p_list[2])
                if desc_tf != 0:
                    desc_tf_wt = 1 + math.log(desc_tf, 10)
                    if docId in desc_score:
                        desc_score[docId] += desc_weight * desc_tf_wt
                    else:
                        desc_score[docId] = desc_weight * desc_tf_wt
    
    sum_title_wt = 0
    for wt in title_vector:
        sum_title_wt += wt * wt
    title_vector_length = math.sqrt(sum_title_wt)

    sum_desc_wt = 0
    for wt in desc_vector:
        sum_desc_wt += wt * wt
    desc_vector_length = math.sqrt(sum_desc_wt)

    for docId, score in title_score.iteritems():
            title_length = title_length_dict[docId]
            title_score[docId] = score / title_vector_length / title_length

    for docId, score in desc_score.iteritems():
            desc_length = desc_length_dict[docId]
            desc_score[docId] = score / desc_vector_length / desc_length

    #print title_score
    #print desc_score
    combined_score = {}
    for docId, score in title_score.iteritems():
        if docId not in combined_score:
            combined_score[docId] = 0.8*score
        else:
            combined_score[docId] += 0.8*score
    
    for docId, score in desc_score.iteritems():
        if docId not in combined_score:
            combined_score[docId] = 0.2*score
        else:
            combined_score[docId] += 0.2*score
    print combined_score

    result = ''
    for key, value in sorted(combined_score.items(), key=lambda x: (-1*x[1], x[0])):           
        if value > 0.1:
            result += str(key) + ' '
                     
    output_file.write(result.strip(' ')) 


    dictionary_file.close()
    
    input_file.close()
    output_file.close()
    title_length_file.close()
    desc_length_file.close()

def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

dictionary_file = postings_file = input_file = output_file = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        input_file = a
    elif o == '-o':
    	output_file = a 
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or input_file == None or output_file == None:
    usage()
    sys.exit(2)


search(dictionary_file,postings_file,input_file,output_file)
