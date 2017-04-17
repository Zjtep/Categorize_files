import urllib2
# import urllib
import StringIO
import re


def make_dictionary():
    
    url ='http://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_name'
    file_dictionary = []
    
    response = urllib2.urlopen(url)
    html = response.read()
    pattern =re.compile(' <span class="plainlinks"><a href="/wiki/(.*?)</span>')
    
    s = StringIO.StringIO(html)
    # print s
    # for line in s:
    #     f = re.findall(pattern,str(line))
    # #     file_dictionary.append(f)
    #     print f
    
    paragraph = re.findall(pattern,str(html))
    
    
    # for (poke_name,poke_url) in paragraph:
    
    for item in paragraph:
    #     poke_name = re.findall(r'[A-Z](.*?)_',item)    
        poke_name = re.findall(r'[A-Z]\w+\_',item)
        poke_url = re.findall(r'src="(.*?)"',item)
#         print poke_name
#         print poke_url
    
        file_struct={'Name': poke_name,'Url':poke_url}
        file_dictionary.append(file_struct)
    
    return file_dictionary

# print(html)
# print(paragraph)




def print_dictionary(dictionary):

    print '[%s]' % ', '.join(map(str, dictionary))
        
        
if __name__ == '__main__':
    file_dictionary=[]
    
    file_dictionary=make_dictionary()
    print_dictionary(file_dictionary)

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    