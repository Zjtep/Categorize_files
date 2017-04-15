'''
This batch script will publish a sequence of external scenes, fix scene characters. etc.   
path will be changed from non existing paths to toonbox paths
eg 
Y:/JOBS/1370ff_nut_job//assets/characters/versions/tnj_c0010a_jimmy_rig_animRig_v047.mb 
will change to
T:/publish/nut_job/rig/assets/chr/tnj_c0010a_jimmy/animRig/tnj_c0010a_jimmy_rig_animRig_v047.mb 
'''

import os, re, time, sys, traceback
from tactic.tactic_asset_db import conn
import optparse
import shutil
cmds = None

REF_CONTENT_BUFFER = 1000000  # the amount of the maya file to read to do the file replacement

def make_new_path(ref_file_path):
    '''
    @param ref_file_path given the reference node file path, 
    @return the tactic path    
    
    ex: given Y:/some/external/company/directory/tnj_p001ta_nutstcutoutsign_rig_animRig_v009.mb
        return T:/publish/nut_job/rig/assets/prp/tnj_p001ta_nutstcutoutsign/animRig/tnj_p001ta_nutstcutoutsign_rig_animRig_v009.mb  
    '''

    match = re.search('([\w]{3}_[a-z|0-9]{5,9})[\w]*_v([0-9]{3})', ref_file_path)        
    
    if not match:
        LOG ("Warning: can not determine production information from reference node %s..." % ref_file_path)
        return None   
             
    asset_code, version = match.groups()
    
    if 'animRig' in ref_file_path:
        ss = conn().get_snapshot_by_context_version(asset_code,  'rig/animRig', version,include_path = True)
    elif 'roughass' in ref_file_path:
        ss = conn().get_snapshot_by_context_version(asset_code, 'roughass/rig', version, include_path=True)
        
    if not ss:
        LOG ("Warning: can not find published anim rig %s %s %s" % (asset_code,  'rig/animRig', version) )
        return None
         
    ss = conn().get_snapshot(ss['code'])
   
    if not ss.has_key('__paths__') or len(ss['__paths__'])==0:
        LOG ("Warning: can not determine path for tactic anim rig publish from %s" % ss)
        return None
    
    tactic_path = ss['__paths__'][0]
    LOG ( "Found replacement path \n%s, now replace for  \n%s..." % (tactic_path,ref_file_path) ,True)
    
    return tactic_path

    
    
def list_reference_node(scene_path):
    '''
    @param scene_path given path to maya scene, 
    @return the list of tuples, where each tuple is (reference node, reference path)  
    '''
    # new file
    LOG("Opening file %s ..." % scene_path)
    
    content = open(scene_path).read(REF_CONTENT_BUFFER) # read a megabyte of characters
    
    return re.findall('"([\w_]*)" "([\w_\/\:]*.mb)";', content)

def update_scene_to_internal_path(scene_path, output_path):
    '''
    @param scene_path Given scene_path, replace all the external paths to internal publish paths ans save to output_path
    @param output_path 
    '''
    # query for all the reference node from the scene path
    ref_info_list = list_reference_node(scene_path)
    
    # create a map between original and new paths
    path_map = {}
    bad_path = [] # source path where the corresponding tactic path can not be found. 
    
    for ref_name, ref_path in ref_info_list:
        
        tactic_path = make_new_path(ref_path)
        if tactic_path:
            path_map[ref_path] = tactic_path
        else:
            bad_path.append(ref_path)
        
    # read a chunk of the header, then replace all the source path with tactic paths 
    old_file = open(scene_path).read(REF_CONTENT_BUFFER)
    for source_path in path_map.keys():        
        tactic_path = path_map[source_path]
        
#        print "replace %s with %s..." % (source_path, tactic_path )
        
        old_file = old_file.replace( source_path, tactic_path )
    
    # read the non reference content
    source_file = open(scene_path)
    source_file.seek(REF_CONTENT_BUFFER)  # skip to content not yet read
    the_rest_of_file = source_file.read()
        
    # write to the output file the result.
    output = open( output_path, 'w')
    
    output.write( old_file)    
    output.write( the_rest_of_file )
    output.close()
    
    LOG ( "Process complete, writing to %s..." % output_path)
    if len(bad_path):
        LOG ( "There are %s problematic paths. The following paths were skipped: \n%s" % (len(bad_path), '\n'.join(bad_path) ) )


def list_all_scence_from_root(root_path):
    '''
    @param root_path given the root path, walk and collect all the scenes that has shot information, and hence can be imported to production.
    @return a hash where key is the shot name, and the value is a list of files
    
    ex: given ..\some\path\
        return 
        { 'tnj_q100_s1000':[ '..\some\path\tnj_q100_s1000_flo_v002.ma', ]
          'tnj_q100_s1000':[...] etc
        }
    '''

    publish_dic = {}
    
    rg = re.compile('([\w]{3}_q[0-9]{0,5}_s[0-9]{0,5})')
    
    for (dirpath, dirnames, filenames) in os.walk(root_path):
        dirpath = dirpath.replace('\\', '/')

        for x in filenames:
            if '.ma' in x:    
                match = rg.search(x)
                if match: 
                    split_filename=match.group()     
                    publish_dic[split_filename]= dirpath +'/'+x 

                    print 'File name',x
                    print 'READ HERE',publish_dic
    return publish_dic
    


def LOG(msg, header=False):
    
    if header: print '#' * 50 
    print '\n >', time.ctime(), ':', msg
    if header: print '#' * 50 
    
    print '\n'
    
if __name__ == '__main__':    
    '''
    Takes user input for scene paths and the output paths
    example 
    python C:\Users\j.zhu\Documents\workspace\feature_pipeline2\g2\tt_g2\python\tools\batch\sequence_scene_importer.py -r "C:\Users\j.zhu\Documents\fixing maya tesg"
    python sequence_scene_importer.py -r "C:\Users\j.zhu\Documents\scene_path" -s "C:\Users\j.zhu\Documents\out_path"
    '''  

    parser = optparse.OptionParser()

    parser.add_option("-r", "--root_path",
                  action="store", type="string", dest="path",
                  help="The root directory from which to query for broken characters in maya")   
    
    parser.add_option("-s", "--new_path",
                  action="store", type="string", dest="new_path",
                  help="The directory of the newly saved maya files")   
    
    (options, args) = parser.parse_args()
    
    if options.path != None:
        root_path = options.path.replace("\\","/")
    else:
        parser.print_help()
        sys.exit(0)

    if options.new_path != None:
        new_root_path = options.new_path.replace("\\","/")
    else:
        parser.print_help()
        sys.exit(0)
#    root_path = r'C:\Users\j.zhu\Documents\fixing maya test'

    

    all_process_scenes = list_all_scence_from_root(root_path)
    
    for shot_code in all_process_scenes.keys():
        head,tail = os.path.split(all_process_scenes[shot_code])
        print "processing shot %s" % shot_code
       
#        output_path =new_root_path+shot_code+"_processed.ma"
#        print os.path.join(new_root_path,shot_code)
        output_path = os.path.join(new_root_path,shot_code)+"_processed.ma"
        shutil.copyfile(all_process_scenes[shot_code], output_path)
        update_scene_to_internal_path(all_process_scenes[shot_code], output_path)

        print "saved at",new_root_path


    