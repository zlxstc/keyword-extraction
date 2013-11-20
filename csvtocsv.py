#! /usr/bin/env python
#coding=utf-8
import csv
f=csv.reader(open('test/output_1.csv','r'))
fout=csv.writer(open('test/output_1_.csv','wb'))

for line in f:
    if len(line)>0:
        list=[]
        for word in line:
            word=word.strip('\n')
            word =word.replace('\n\n','')
            word=word.replace('\n','')
            word.replace('\n','')
            list.append(word)
        fout.writerow(list)