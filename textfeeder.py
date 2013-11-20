#! /usr/bin/env python
#coding=utf-8
from rake import RakeKeywordExtractor
import nltk
import csv
from nltk.probability import *
from nltk.corpus import stopwords
from bs4 import BeautifulSoup, Tag
from mrjob.job import *
from mrjob.runner import MRJobRunner
import time

class tag_generator(MRJob):
    def postree(self,text):
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

        
     

    def leaves(self,tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter = lambda t: t.node=='NP'):
            yield subtree.leaves()
     
    def normalise(self,word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        word = word.lower()
        #word = stemmer.stem_word(word)
        stemmer = nltk.stem.porter.PorterStemmer()
        lemmatizer = nltk.WordNetLemmatizer()
        word = lemmatizer.lemmatize(word)
        return word
     
    def acceptable_word(self,word):
        """Checks conditions for acceptable word: length, stopword."""
        from nltk.corpus import stopwords
        stopwords = stopwords.words('english')
        accepted = bool(2 <= len(word) <= 40
            and word.lower() not in stopwords)
        return accepted
     
     
    def get_terms(self,tree):
        for leaf in self.leaves(tree):
            term = [ self.normalise(w) for w,t in leaf if self.acceptable_word(w) ]
            yield term

    def freqwords(self,text): 
        """Get the frequent words for the given text"""   
        terms = self.get_terms(self.postree(text))
        words =[]
        for term in terms:
            for word in term:
                words.append(word)

        fdist = FreqDist()
        for word in words:
            fdist.inc(word.lower())
        return fdist.keys()

    def keywords(self,text,tag_table):
        tagtable = open(tag_table,'r')
        tags = []
        features = []     
        wordset = self.freqwords(text)
        for i in tagtable.readlines():
            tags.append(i.split(',')[0])

        rake = RakeKeywordExtractor()    
        rakelist = rake.test(text)
        for i in rakelist:        
            features.append(self.normalise(i[0]).replace(' ','-'))

        for keyword in wordset:
            for phrase in features:
                if phrase.find(keyword)!= -1 :
                    features.append(keyword)
                    break
                
        intersection = set(tags) & set(features)
    #    print features
        return ' '.join(list(intersection))

    def mapper(self, _, filename): 
        tag_table = "s3:/elasticbeanstalk-us-east-1-756771937249/tagtable.csv"
        if len(filename)!=0:
#            print line
            id=filename.split(',')[0]
            title=filename.split(',')[1]
            body=filename.split(',')[2:-2]
            body= str(body)
            tag=filename.split(',')[-1]
            rawtext=title+self.codeless(body)
            predicted_tag = self.keywords(rawtext,tag_table)
            tag_list = tag.split(' ')
            predicted_tag_list = predicted_tag.split(' ')
            intersection = set(tag_list) & set(predicted_tag_list)
            rate = float(len(intersection))/float(len(tag_list))
            yield id,predicted_tag
#            fout.write(tag + ',' + predicted_tag + ',' + str(rate) +'\n')
#    def reducer(self, key, values):
#        yield key, values   
    def codeless(self,string):
        soup = BeautifulSoup(string)
        
        for tag in soup.find_all('code'):
            tag.replaceWith('')
        soup.html.unwrap()
        return str(soup)
    
    
if __name__ == '__main__':
    start = time.clock()
    mytag_generator = tag_generator()
    mytag_generator.run()
    elapsed = (time.clock() - start)
    print elapsed
#    print mytag_generator.parse_out_line(line)
#    with mytag_generator.make_runner() as runner1:
#        runner1.run()
#        for line in runner1.stream_output():
#            key, value = mr_job.parse_output_line(line)
#            print key # do something with the parsed output
        
#    key, value = tag_generator.parse_output_line(line)
    
#    filename = 'test.csv'
#            outputname = 'result.csv'
#            tag_table = 'tagtable.csv'
#            f = csv.reader(open(filename,'r'))
#            fout = open(outputname,'wb+')
#            for line in f:
    