import sys
import nltk
import getopt
import os
import math
from nltk.stem.porter import PorterStemmer  
from nltk.tokenize import RegexpTokenizer
import xml.etree.ElementTree as ET
from nltk.corpus import stopwords
import string
import re


def index(directory_of_documents, dictionary_file, postings_file):
    
    # format {term: {docId: {'title':title_tf, 'desc': desc_tf}}} 
    inverted_index = {} 
    stop_words = stopwords.words('english')
    stemmer = PorterStemmer()
    tokenizer = RegexpTokenizer(r'\w+')
    dir_path = directory_of_documents
    files_list = os.listdir(dir_path)
    files_list.sort()

    for fn in files_list:
        f = open(os.path.join(dir_path, fn),'r')
        docId = fn[:-4]
        root = ET.parse(f).getroot()
        tags = root.getiterator('str')

        # read the relevant tags
        title_str = ''
        desc_str = ''

        for tag in tags:
            if tag.get('name') == 'Title':
                title_str = filter(lambda x: x in string.printable, tag.text.lower().strip())
            elif tag.get('name') == 'Abstract':
                desc_str = filter(lambda x: x in string.printable, tag.text.lower().strip())
        

        
        for word in tokenizer.tokenize(title_str):
            if word not in stop_words:
                term = str(stemmer.stem(word))
                if term in inverted_index:
                    if docId in inverted_index[term]:
                        inverted_index[term][docId]['title'] += 1
                    else:
                        inverted_index[term][docId] = {'title':1, 'desc':0}    
                else:    
                    inverted_index[term] = {docId: {'title': 1 ,'desc': 0}}

    
        for word in tokenizer.tokenize(desc_str):
            if word not in stop_words:
                term = str(stemmer.stem(word))

                if term in inverted_index:
                    if docId in inverted_index[term]:
                        inverted_index[term][docId]['desc'] += 1
                    else:
                        inverted_index[term][docId] = {'title': 0,'desc':1 }  
                else:    
                    inverted_index[term] = {docId: {'title': 0 ,'desc': 1}}
        

    
    dict_file = open(dictionary_file,'w')
    post_file = open(postings_file,'w')
    
    title_length_dict = {}
    desc_length_dict = {}
   
    lineNum = 1

    for term, posting in inverted_index.iteritems():
        post_str = ''
        for docId, inner_dict in posting.iteritems():
            tf = inner_dict.values()
            title_tf, desc_tf = tf[0], tf[1]
            if title_tf != 0:
                title_tf_wt = 1 + math.log(title_tf, 10)
                if docId in title_length_dict:
                    title_length_dict[docId] += title_tf_wt * title_tf_wt
                else:
                    title_length_dict[docId] = title_tf_wt * title_tf_wt
            
            if desc_tf != 0:    
                desc_tf_wt = 1 + math.log(desc_tf, 10)
                if docId in desc_length_dict:
                    desc_length_dict[docId] += desc_tf_wt * desc_tf_wt
                else:
                    desc_length_dict[docId] = desc_tf_wt * desc_tf_wt
            post_str += str(docId) + ' ' + str(title_tf) + ' ' + str(desc_tf) + ','
        post_file.write(post_str[:-1])
        post_file.write('\n')
        dict_file.write(term + ' ' + str(len(posting)) + ' ' + str(lineNum) + '\n')
        lineNum += 1
    dict_file.write('TOTAL_DOCS ' + str(len(files_list)) + ' ' + str(len(files_list)))
    
    dict_file.close()
    post_file.close()

    title_length_file = open('title_length.txt', 'w')
    for docId, wt in title_length_dict.iteritems():
        #calculate document vector length for normalisation
        title_length = math.sqrt(wt)
        #doc_length_file format: docId doc_length
        title_length_file.write(str(docId) + ' ' + str(title_length) + '\n')
    

    desc_length_file = open('desc_length.txt', 'w')
    for docId, wt in desc_length_dict.iteritems():
        #calculate document vector length for normalisation
        desc_length = math.sqrt(wt)
        #doc_length_file format: docId doc_length
        desc_length_file.write(str(docId) + ' ' + str(desc_length) + '\n')

    title_length_file.close()
    desc_length_file.close()

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p posting-file"

# main : get the input filenames and directory
directory_of_documents = dictionary_file = postings_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-i':
        directory_of_documents = a
    elif o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    else:
        assert False, "unhandled option"

if directory_of_documents == None or dictionary_file == None or postings_file == None:
    usage()
    sys.exit(2)


index(directory_of_documents, dictionary_file, postings_file)