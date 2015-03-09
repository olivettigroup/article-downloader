#This script will sit in synthesis-database
from subprocess import call
from os import listdir
from models import Paper
 
pdf_list = []
pdf_dir = 'files/pdfs/'
xml_dir = 'files/xmls/'
tagged_xml_dir = 'files/tagged_xmls/'
tag_list = 'files/to-tag-list.txt'
 
for file in listdir(pdf_dir):
  pdf_list.append(file)
  
for pdf in pdf_list:
  #Run pstotext code
  call(['bin/pstotext ' +
    pdf_dir + pdf + ' > ' +
    xml_dir + pdf + '.xml'], shell=True)
    
#Create list file
with open(tag_list, 'wb') as f:
  for pdf in pdf_list:
    f.write(xml_dir + pdf + '.xml ' + '-> '
    +  tagged_xml_dir + 'tagged-' + pdf + '.xml')
    f.write('\n')
    
#Call metatagger crf
#TODO: test that this works... there will probably be an issue w/ relative file paths.
call(['cat', 'files/to-tag-list.txt', '|', 'bin/runcrf'], shell=True)
 
#Throw the files into Paper() objects and save them
#TODO: write this...