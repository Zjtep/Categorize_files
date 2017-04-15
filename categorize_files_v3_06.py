'''
This batch script walks through a given root directory and finds all the older versions. 
Version files/folder are assume to be named '_v####', ex: 'renderpass/beauty_v001'.
You can specify the number of version to retain.

It performs lazy evaluation.  If the folder is a version folder, it will not visit the children content, since it's assume that entire folder will be removed anyway.
The exception is for the folder that are retained.  In which case it will visit the children directories.

ex:
\animal\dog_v001\beauty_render_v001
\animal\dog_v001\beauty_render_v002
\animal\dog_v002\beauty_render_v001
\animal\dog_v002\beauty_render_v002

In above case, where 1 version is specify to be retained, it will visit follow
\animal\dog_v001\
\animal\dog_v002\beauty_render_v001
\animal\dog_v002\beauty_render_v002

Children of dog_v001 is not visited because there is dog_v002.  It's assume dog_v001 will be removed entirely.
Children of dog_v002 are visited because dog_v002 is retained.


type:
python categorize_files_v3_06.py -r "your directory" -v some_int
eg:
python categorize_files_v3_06.py -r "C:\Users\j.zhu\Documents\Test Directory" -v 1
'''

import os
import re
import time
import urllib
#import win32com.client as com
import optparse
#from math import ceil

#searches for everything with _v followed by numbers 
VERSION_RG = re.compile('([\w_\s]+)_v([0-9]{1,10})')
WANT_SIZE = False
FULL_LIST=[]
KEEP_LIST=[]
REDUNDANT_LIST =[]

def create_file_struct( dirpath, full_name ):
    '''
    Given a path to either a file or folder, return a dictionary of meta data.
    @param dirpath: path to the file or folder 
    @param full_name: the name of the file or folder
    @return dictionary with meta data regarding the file/folder, size, date, header...etc.
             returns None if it doesn't if it's not a version
    '''
    match = VERSION_RG.search(full_name)
    
    if not match: # this is not a version file or folder
        return None
    
    header, version = match.groups()
    file_os = os.stat(os.path.join( dirpath, full_name))
    create_time = time.gmtime(file_os.st_ctime)
    create_time_hr = time.strftime("%m/%d/%Y %H:%M:%S", create_time)
    mod_time = time.gmtime(file_os.st_mtime)
    mod_time_hr = time.strftime("%m/%d/%Y %H:%M:%S", mod_time)
    dir_return = dirpath.replace("\\","/")
    
    '''
    Saves information
    parent directory of the file/directory
    header of the file/directory 
    version saves the version number of the file/directory
    full_name Full name of the file/directory 
    size: Size of file/directory
    create_time The time the file/directory was created
    mod_time The time the file/directory was modified
    '''
    
    if os.path.isdir(os.path.join(dirpath,full_name) ):
        return {'parent' : dir_return , 'header': header, 'version' : int(version), 'full_name' : full_name, 
                       'size': get_size(dirpath + '/'+ full_name), 
                       'create_time': str(create_time_hr),'mod_time': str(mod_time_hr)}   
    elif os.path.isfile(os.path.join(dirpath,full_name) ):
        GB=1024*1024*1024.0
        fsize = (os.stat(os.path.join(dirpath,full_name)).st_size)/GB
        return {'parent' : dir_return , 'header': header, 'version' : int(version), 'full_name' : full_name, 
                       'size': round(fsize,3), 
                       'create_time': str(create_time_hr),'mod_time': str(mod_time_hr)}      
    
def list_versioned_file_struct(root_path,want_listed_files,kept_version):
    '''
    Creating a list of file stucts from the root path, only if it matches the version pattern ie: blah_v0001
    @param root_path: path to start the search
    @param want_listed_files if the user wants to list files, passs in true
    @param kept_version Number of versions kept
    @return returns list of all redundant files in the root_path
    '''
    file_struct_list = []
    global KEEP_LIST
    global FULL_LIST
    global REDUNDANT_LIST
    
    
    for (dirpath, dirnames, filenames) in os.walk( root_path ):
        for_consider_remove_dir_list  = []
        for_consider_remove_file_list = []
 
        # iterate through folders and create/store the file structure        
        for dirs in dirnames:

            dir_struct =  create_file_struct( dirpath, dirs )
            
            # if file_struct is None, then it's not a versioned folder, hence skip to next one
            if dir_struct == None:
                continue
            FULL_LIST.append(dir_struct)
            dir_struct['is_file'] = False

            # if file_struct is returned, then it's a version, hence can skip it looking into it.
            for_consider_remove_dir_list.append(dir_struct)
            
        # group the file structs so that we can ignore looking into previous versions
        redundant_dir_list = find_redundant_version_dir  ( for_consider_remove_dir_list,kept_version )
        for dir_struct in for_consider_remove_dir_list:
            if dir_struct['full_name'] in redundant_dir_list:
                file_struct_list.append(dir_struct)   
#                REDUNDANT_LIST.append(dir_struct)      
       
        # remove the directory that are 'version', so no need to walk into it.
        for dirs in redundant_dir_list:
            dirnames.remove(dirs)
#            print 'no need to further examine dir', dirpath + '/' + dirs
       
        # iterate through files and create/store the file structure
        if want_listed_files:
            for files in filenames:
                file_struct =  create_file_struct( dirpath, files )            
                
                if file_struct!=None:
                    file_struct['is_file'] = True
                    for_consider_remove_file_list.append(file_struct)
            
            # group the file structs so that we can ignore looking into previous versions
            redundant_file_list = find_redundant_version_dir  ( for_consider_remove_file_list,kept_version )
            
            for file_struct in for_consider_remove_file_list:
                if file_struct['full_name'] in redundant_file_list:
                    file_struct_list.append(file_struct) 
#                    REDUNDANT_LIST.append(dir_struct) 
                else:
                    KEEP_LIST.append(file_struct)


    REDUNDANT_LIST = file_struct_list       
#    return REDUNDANT_LIST                
    return file_struct_list

def find_redundant_version_dir( dir_struct_list,kept_version ):
    '''
    Makes a dictionary of redundant files. 
    Sorts them by version number
    removes older versons
    group into dictionary, key: the dirpath and full_name, value:  
    @param dir_struct_list list of files/directories to look through
    @param kept_version Number of versions kept
    @return returns list of all redundant 
    '''

    group_dictionary = {}
    for dir_struct in dir_struct_list:
        header_key =  dir_struct['header']
         
        if not group_dictionary.has_key( header_key ):
            group_dictionary[ header_key ] = []
            
        group_dictionary[ header_key ].append( dir_struct )
            
    # sort the list of dir_struct for each header

    redundant_list = []
    for list_of_struct in group_dictionary.values() :
        list_of_struct.sort(lambda x,y: cmp( x['version'],  y['version'] ), reverse=True)
        for remove_item in list_of_struct[kept_version:]:
            redundant_list.append( remove_item['full_name'] )
    return redundant_list

def get_size(start_path):
    '''
    Searches http://stats01/cgi-bin/du.py?path=/mnt to get the file size
    If file size is unknown then the database hasn't updated yet
    @param start_path the starting directory
    @return returns the size of the directory
    '''
    if WANT_SIZE == True:
        url_path= 'http://stats01/cgi-bin/du.py?path=/mnt/fs01/' +start_path.replace(":","")
        c = urllib.urlopen(url_path).read()
        rg = re.compile('([\w_\s\.]+) GB,')
        match = rg.search(c)
        print 'Checked size of' ,url_path
    
        if match:
            t = match.groups()
           
            return ''.join(t) 
    return 0
    

def print_dictionary(dictionary):
    '''
    Prints the dictionary
    @param dictionary list of files/directories to print
    ''' 
    for x in dictionary:    
#        print 'header:  ' + x['header'], '   version: ' + str(x['version']), '  full name:   ' +x['full_name'],  '  parent: ' + x['parent'],  '  filesize: ' + str(x['size'])
        print 'parent:   '+ x['parent'] + '   full name:   '+x['full_name']

#         + 'mod time   ' + x['mod_time']

def sort_by_file_size(dictionary):
    '''
    Sorts files/directories by size. If the output is -1, that means that Andrew's database hasn't updated yet.
    @param dictionary list of files/directories to sort. 
    '''
    for x in dictionary:
        if x['size'] == 'Unknown' or x['size'] == None:
            x['size'] = manual_get_size(os.path.join(x['parent'],x['full_name']))
#            x['size']= -1
        else:
#        dictionary.sort(lambda x,y: cmp(x['size'], y['size'] ), reverse=True)
            dictionary.sort(lambda x,y: cmp( float(x['size']),  float(y['size'] )), reverse=True)
        

def manual_get_size(path):
    '''
    gets the file size by walking through the directory
    @param path the path of the directory
    @return size of directory in Gigabytes
    '''
    if WANT_SIZE == True:
        fso = com.Dispatch("Scripting.FileSystemObject")
        folder = fso.GetFolder(path)
        GB=1024*1024*1024.0
        return round(folder.Size/GB,3)
    return 0

def save_to_file(dictionary):   
    '''
    Save information to a text file to the working directory
    @param dictionary list of files/directories to save
    '''   
    f = open('Redundant files.txt','w')
    for x in dictionary:
        format_string = "{0:150} {1:30} {2:30}{3}".format(x['parent'], x['full_name'],str(x['size'])+ " GB",x['mod_time']+"\n")
        f.write(format_string)

def get_kept_list():

    global KEEP_LIST
    return KEEP_LIST

def get_full_list():
    global FULL_LIST
    return FULL_LIST
#    return list_versioned_file_struct(root_path,True,0)

def get_redundant_list():
    global REDUNDANT_LIST
    return REDUNDANT_LIST

if __name__ == '__main__':
    '''
    Takes user input for the directory.
    For the 'list_versioned_file_struct', if True: is passed in, the program will find files and directories. If False: the program will only find directories
    '''  
    parser = optparse.OptionParser()
    my_dictionary_list  =[]
    root_path= ""
    kept_version = 1
    
    parser.add_option("-r", "--rootpath",
                  action="store", type="string", dest="path")    
    parser.add_option("-v", "--keptversion",
                  action="store", type="string", dest="kept_version")     
    
    (options, args) = parser.parse_args()
    
#    (options, args) = parser.parse_args(['-r',r'Q:/studio/nut_job/prod/q160/s0180/lgt/render/render_passes/stereocameraleftshape/lana_shd_drp'])
    root_path = options.path
    if options.kept_version != None:
        kept_version = int(options.kept_version)
    if root_path != None:
        root_path = root_path.replace("\\","/")


#    my_dictionary_list = list_versioned_file_struct(root_path,True,kept_version)   
#    my_dictionary_list = get_full_list(root_path,True,kept_version)
#    sort_by_file_size(my_dictionary_list)

    my_dic = list_versioned_file_struct(root_path,True,kept_version)
    print'------EVERYTHING'
    print_dictionary(get_full_list() )
#    print get_full_list()
    print'------DELETE THESE'
    print_dictionary(get_redundant_list())
#    print get_redundant_list()
    print "-------------KEEP THeSE"
    print_dictionary(get_kept_list())
#    print get_kept_list()
    
#    raw_dictionary_list = list_versioned_file_struct("Q:/studio/nut_job/prod/q160/s0210",True)
#    raw_dictionary_list = list_versioned_file_struct(init_path,bool(raw_input))
#    raw_dictionary_list = list_versioned_file_struct("Q:/studio/nut_job/prod/q160/s0180/lgt/render/render_passes/stereocameraleftshape/lana_shd_drp",False)
#    raw_dictionary_list = list_versioned_file_struct("Q:/studio/nut_job/prod/q283/s0070/",True)
#    raw_dictionary_list = list_versioned_file_struct("Q:/studio/nut_job/prod/q283/s0050/flo/render/render_passes/stereocameraleftshape/leftcampass",False)
#    raw_dictionary_list = list_versioned_file_struct("Q:/studio/nut_job/prod/q160/s0380",False)
#    sort_by_file_size(raw_dictionary_list)
#    print_dictionary(raw_dictionary_list )
#    save_to_file(raw_dictionary_list)

