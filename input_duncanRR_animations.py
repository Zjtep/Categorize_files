'''
To run this program 
python filepath -s "PATH OF FILE" -d "YOUR DEPARTMENT"  -c "YOUR COMMENTS" -t/-f
eg:
python input_duncanRR_animations.py -s "\\toonboxent\Studio\shows\nut_job\Manage\Redrover\received_from\2013.04.02" -d anm -c "comment testing two" -t
'''
import review_tool   
from review_tool.lib import frame_submit_api as fsa
fsapi = fsa.FrameSubmitApi()
import os
import re
import optparse


VERSION_RG_1 = re.compile('_sq([0-9]{1,10})_sh([0-9]{1,10})')
VERSION_RG_2 = re.compile('_q([0-9]{1,10})_s([0-9]{1,10})')

'''
Creates a struct with all the files information only if it has a sequence number and a shot number
@param dirpath: path of file
@param dept: The department the shot goes into
@param comment: The comment to display
'''
def create_file_struct( dirpath, full_name,dept,comment):
    match = VERSION_RG_1.search(full_name)
    match2 = VERSION_RG_2.search(full_name)
    
    if match: 

        seq_num,shot_num = match.groups()
        return {'parent' : dirpath , 'full_name' : full_name,  'seq_num' : seq_num, 'shot_num' : shot_num, 'dept' : dept,'comment' :comment}   
    elif match2:
        
        seq_num,shot_num = match2.groups()
        return {'parent' : dirpath , 'full_name' : full_name,  'seq_num' : seq_num, 'shot_num' : shot_num, 'dept' : dept, 'comment' :comment}           
    else:
        return None

'''
Finds all files that are .mov and makes a list of file_structs
@param root_path: Path of the top directory
@param dept: The department the shot goes into
@param comment: The comment to display
'''    
def find_files(root_path,dept,comment):

    publish_list = []
    for (dirpath, dirnames, filenames) in os.walk(root_path):

        for x in filenames:
            if '.mov' in x:         
                file_struct = create_file_struct(dirpath,x,dept,comment)
                if file_struct == None:
                    continue
                publish_list.append(file_struct)
    return publish_list 

'''
Submits files to Review tool
@param publish_list: List of file information to be published
'''  
def publish_files(publish_list):

    for item in publish_list:
        publish_file_name = 'tnj_q' + item['seq_num'] + '_s' + item['shot_num']
        full_path= os.path.join( item['parent'], item['full_name'])

        print full_path
        fsapi.submit_movie(full_path, 'tnj_q999_s0010', item['dept'],item['comment'])
#        fsapi.submit_movie(full_path, publish_file_name, item['dept'],item['comment'])
        '''
        #this is the line that actually publishes onto the main reviewtool. 
        fsapi.submit_movie(full_path, publish_file_name, item['dept'],item['comment'])
        '''

'''
Submits files from an user inputted path to the review tool
-s is for the root_path
-d is for the department
-c is for comments
-t for publishing all the files
-f for just testing
''' 
if __name__ == '__main__':

    parser = optparse.OptionParser()
    publish_list = []
#    root_path = r'\\toonboxent\Studio\shows\nut_job\Manage\Redrover\received_from\2013.05.29 - duncan'
    parser.add_option("-s", "--source",
                  action="store", type="string", dest="path")

    parser.add_option("-d", "--dept",
                  action="store", type="string", dest="dept")

    parser.add_option("-c", "--comment",
                  action="store", type="string", dest="comment")

    parser.add_option("-t",
                  action="store_true", dest="test")
    
    parser.add_option("-f",
                  action="store_false", dest="test")
    (options, args) = parser.parse_args()
#    (options, args) = parser.parse_args(['-f',r'\\toonboxent\Studio\shows\nut_job\Manage\Redrover\received_from\2013.03.22\q357 Detail Ani'])

    root_path =options.path 
    dept = options.dept
    comment = options.comment
    run_full = options.test
#    root_path = r'\\toonboxent\Studio\shows\nut_job\Manage\Redrover\received_from\2013.02.08\q150_blocking'
#    print root_path,dept
    
    if run_full == True:  
        if root_path != "":
            root_path = root_path.replace("\\","/")

            publish_list = find_files(root_path,dept,comment)
            publish_files(publish_list)
    elif run_full==False:
        publish_list = find_files(root_path,dept,comment)

    x = 0
    for item in publish_list:
        x +=1
        print x, item
