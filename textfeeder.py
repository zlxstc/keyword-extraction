#! /usr/bin/env python
#coding=utf-8
from rake import RakeKeywordExtractor
import nltk
import csv
from nltk.probability import *
from nltk.corpus import stopwords
from bs4 import BeautifulSoup, Tag

def postree(text):
    sentence_re = r'''(?x)      # set flag to allow verbose regexps
               ([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
             | \w+(-\w+)*            # words with optional internal hyphens
             | \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
             | \.\.\.                # ellipsis
             | [][.,;"'?():-_`]      # these are separate tokens
         '''
     
    toks = nltk.regexp_tokenize(text, sentence_re)
    postoks = nltk.tag.pos_tag(toks)    
    grammar = r"""
         NBAR:
             {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
             
         NP:
             {<NBAR>}
             {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
     """
    chunker = nltk.RegexpParser(grammar)
     
    tree = chunker.parse(postoks)
    return tree

    
 

def leaves(tree):
    """Finds NP (nounphrase) leaf nodes of a chunk tree."""
    for subtree in tree.subtrees(filter = lambda t: t.node=='NP'):
        yield subtree.leaves()
 
def normalise(word):
    """Normalises words to lowercase and stems and lemmatizes it."""
    word = word.lower()
    #word = stemmer.stem_word(word)
    stemmer = nltk.stem.porter.PorterStemmer()
    lemmatizer = nltk.WordNetLemmatizer()
    word = lemmatizer.lemmatize(word)
    return word
 
def acceptable_word(word):
    """Checks conditions for acceptable word: length, stopword."""
    from nltk.corpus import stopwords
    stopwords = stopwords.words('english')
    accepted = bool(2 <= len(word) <= 40
        and word.lower() not in stopwords)
    return accepted
 
 
def get_terms(tree):
    for leaf in leaves(tree):
        term = [ normalise(w) for w,t in leaf if acceptable_word(w) ]
        yield term

def freqwords(text): 
    """Get the frequent words for the given text"""   
    terms = get_terms(postree(text))
    words =[]
    for term in terms:
        for word in term:
            words.append(word)

    fdist = FreqDist()
    for word in words:
        fdist.inc(word.lower())
    return fdist.keys()

def keywords(text):
    tagtable = open('tagtable.csv','r')
    tags = []
    features = []     
    wordset = freqwords(text)
    for i in tagtable.readlines():
        tags.append(i.split(',')[0])

    rake = RakeKeywordExtractor()    
    rakelist = rake.test(text)
    for i in rakelist:        
        features.append(normalise(i[0]).replace(' ','-'))

    for keyword in wordset:
        for phrase in features:
            if(phrase.find(keyword)!=-1):
                features.append(keyword)
                break
            
    intersection = set(tags) & set(features)
#    print features
    return ' '.join(list(intersection))
def codeless(string):
    soup = BeautifulSoup(string)
    
    for tag in soup.find_all('code'):
        tag.replaceWith('')
    soup.html.unwrap()
    return str(soup)
if __name__ == '__main__':
    filename = 'test.csv'
    outputname = 'result.csv'
    f = csv.reader(open(filename,'r'))
    fout = open(outputname,'wb+')
    for line in f:
        if len(line)==0:
            continue
#        print line
        (id,title,body,tag)=line
        rawtext=title+codeless(body)
        predicted_tag = keywords(rawtext)
        tag_list = tag.split(' ')
        predicted_tag_list = predicted_tag.split(' ')
        intersection = set(tag_list) & set(predicted_tag_list)
        rate = float(len(intersection))/float(len(tag_list))
#        print tag
#        print keywords(rawtext)
        fout.write(tag + ',' + predicted_tag + ',' + str(rate) +'\n')