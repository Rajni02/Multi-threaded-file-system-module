
'''
Importing supporting class files and packages
'''

from superblock import *
from inode import *
from pathlib import Path

import os
import math
import ntpath



'''
    A global variable 'filesystem' is defined to represent the entire drive 
'''
file_system = None
invalid_chars_file = set(' \\/,*\'#[]')
invalid_chars_dir = set(' \\,*\'#[]')


'''
    Function to create a global Superblock object to represent a file
'''
def init_filesystem():
    global file_system
    file_system = Superblock()


'''
    Function to create new virtual file system
'''
def create_vfs():
    global file_system
    return file_system.create_empty_vfs()


'''
    function to mount existing filesystem, identify root
'''
def mount_vfs():

    # declaring file_system aas global variable
    global file_system
    #file_system = Superblock()
    return file_system.read_vfs()




'''
    Function to get current working directory
'''
def get_cwd():
    global file_system
    if file_system == 0:
        return '...'
    else:
        return file_system.cur_working_dir


'''
    Function to implement touch command
'''
def touch_cmd(fname_list):
    global file_system

    # fetch current working dir and current user
    cur_uidx = file_system.cur_uidx
    cur_wdno = file_system.cur_working_dir_num


    for filename in fname_list:
        # check if length of filename is <= 64
        if len(filename) > 64:
            print('filename can have max 64 characters !')
            return
        # check if length of filename is zero
        if len(filename) == 0:
            print('filename cannot contain *, \',\\,/,[,]')
            return
        # check if filename contains invalid characters
        if any((c in invalid_chars_file) for c in filename):
            print('filename contains invalid characters !')
            return

    # Check if user has access to edit current working dir
    if not file_system.active_inode_dict[cur_wdno].get_write_perm(cur_uidx):
        print('current user do not have write permission to current directory')
        return

    # check if file exists in curernt directory
    cwd_files = file_system.get_cwd_directories() + file_system.get_cwd_filenames()

    for filename in fname_list:
        if filename not in cwd_files:
            # fetching inode
            inode_num = file_system.fetch_inode()

            # modifying filename, filetype, rw permission
            file_system.active_inode_dict[inode_num].filename = filename
            file_system.active_inode_dict[inode_num].file_type = 1
            file_system.active_inode_dict[inode_num].parent_inode = file_system.cur_working_dir_num
            file_system.active_inode_dict[inode_num].set_read_perm([cur_uidx])
            file_system.active_inode_dict[inode_num].set_write_perm([cur_uidx])


            # adding inode to dentry objects
            file_system.add_inode_to_dentry(inode_num)

            # setting file creation and modify time
            file_system.active_inode_dict[inode_num].set_file_creation_time()
            file_system.active_inode_dict[inode_num].set_last_modify_time()

            # setting file read and write permission
            file_system.active_inode_dict[inode_num].set_read_perm(list([file_system.cur_uidx, 0]))
            file_system.active_inode_dict[inode_num].set_write_perm(list([file_system.cur_uidx, 0]))

        else:
            idx = file_system.child_dict[file_system.cur_working_dir_num][1].index(filename)
            inode_num = file_system.child_dict[file_system.cur_working_dir_num][0][idx]

        # modifying access time
        file_system.active_inode_dict[inode_num].set_last_modify_time()

        # writing inode to file
        file_system.write_ilist_to_file()
        file_system.active_inode_dict[inode_num].write_inode_to_file()



'''
    Function to implement ls command
'''
def ls_cmd():
    global file_system

    # to fetch list of all files and directories in "current working directory"
    return ['['+f+']' for f in file_system.get_cwd_directories()] + file_system.get_cwd_filenames()



'''
    Function to implement rm command
'''
def rm_cmd(filename):
    global file_system
    cur_usr_idx = file_system.cur_uidx

    # validating filename/path
    inode_num = -1
    if len(filename) == 0:
        print('Invalid path.')
        return
    if filename[0] == '/':
        inode_num = file_system.validate_abs_path(filename)
    else:
        inode_num = file_system.validate_rel_path(filename)

    if inode_num > 0 :

        if file_system.active_inode_dict[inode_num].file_type == 0 and len(file_system.child_dict[inode_num][0]) != 0 :
            print('\"'+filename+'\"'+' is not an empty directory !')
            print('use \"rm -r\" instead')
            return

        # releasing dentry objects
        file_system.remove_inode_from_dentry(inode_num)

        # releasing data blocks associated with inode
        file_system.release_data_blocks(inode_num)

        # relesing inode number
        file_system.release_inode(inode_num)

        # writing changed inode list to file
        file_system.write_ilist_to_file()
    else:
        print('File doesn\'t exists !')



'''
    Function to implement rm -r command
'''
def rm_r_cmd(dirpath):
    global file_system
    cur_usr_idx = file_system.cur_uidx

    # validating filename/path
    inode_num = -1
    if len(dirpath) == 0:
        print('Invalid path.')
        return
    if dirpath[0] == '/':
        inode_num = file_system.validate_abs_path(dirpath)
    else:
        inode_num = file_system.validate_rel_path(dirpath)

    inode_Q = []
    if inode_num > 0:
        inode_Q.append([inode_num])

        # fetching every inode within given directory tree
        while len(inode_Q[-1]) != 0:
            tmp_inode_q, q = list(inode_Q[-1]), []
            while len(tmp_inode_q) != 0:
                tmp_i = tmp_inode_q.pop(0)
                if not file_system.active_inode_dict[tmp_i].get_write_perm(cur_usr_idx):
                    print('current user do not have write permission for all files in directory tree')
                    return
                q = q + file_system.child_dict[tmp_i][0]
            inode_Q.append(q)

        inode_Q.pop()
        # converting lists of list into a single list
        inode_Q = [x for y in inode_Q for x in y]

        while len(inode_Q) != 0 :
            tmp_inode = inode_Q.pop(0)

            # releasing dentry objects
            file_system.remove_inode_from_dentry(tmp_inode)

            # releasing data blocks occupied by inode
            file_system.release_data_blocks(tmp_inode)

            # relesing inode number
            file_system.release_inode(tmp_inode)

        # writing changed inode list,data block list to file
        file_system.write_ilist_to_file()
        file_system.write_dblist_to_file()

    else:
        print('Invalid file/directory path !')





'''
    Intermediate function to call validate_abs_path() function
'''
def validate_abs_path_core(path):
    global file_system
    return file_system.validate_abs_path(path)



'''
    Intermediate function to call validate_rel_path() function
'''
def validate_rel_path_core(path):
    global file_system
    return file_system.validate_rel_path(path)



'''
    Function to implement 'mkdir' command
'''
def mkdir_cmd(dname_list):
    global file_system
    # fetch current working dir and current user
    cur_uidx = file_system.cur_uidx
    cur_wdno = file_system.cur_working_dir_num

    for dirname in dname_list:
        # check if length of filename <= 64
        if len(dirname) > 64 :
            print('Directory name can contain at most 64 characters !')
            return

        # check if any directory name is invalid
        if len(dirname) == 0:
            print('filename cannot contain *, \',\\,/,[,]')
            return

    # Check if user has access to edit current working dir
    if not file_system.active_inode_dict[cur_wdno].get_write_perm(cur_uidx):
        print('current user do not have write permission to current directory.')
        return


    # check if directory name exists in curernt directory
    cwd_files = file_system.get_cwd_filenames()
    cwd_dir = file_system.get_cwd_directories()

    for dirname in dname_list:
        if dirname not in cwd_files and dirname not in cwd_dir:
            # fetching inode
            inode_num = file_system.fetch_inode()

            # modifying filename, filetype, parent of directory, rw permission
            file_system.active_inode_dict[inode_num].filename = dirname
            file_system.active_inode_dict[inode_num].file_type = 0
            file_system.active_inode_dict[inode_num].parent_inode = file_system.cur_working_dir_num
            file_system.active_inode_dict[inode_num].set_read_perm([cur_uidx])
            file_system.active_inode_dict[inode_num].set_write_perm([cur_uidx])

            # adding inode to dentry objects
            file_system.add_inode_to_dentry(inode_num)

            # modifying access time, file creation time and modify time
            file_system.active_inode_dict[inode_num].set_last_access_time()
            file_system.active_inode_dict[inode_num].set_file_creation_time()
            file_system.active_inode_dict[inode_num].set_last_modify_time()

            # writing inode list and new inode to file
            file_system.write_ilist_to_file()
            file_system.active_inode_dict[inode_num].write_inode_to_file()


        else:
            print('\n Directory \'{0}\' already exists!'.format(dirname))


'''
    Function to implement cd command
'''
def cd_cmd(path):
    global file_system
    cur_usr_idx = file_system.cur_uidx
    inode_num = -1

    # implementing return cd
    if len(path) == 0:
        print('Invalid path.')
        return
    if path == '..':
        inode_num = file_system.active_inode_dict[file_system.cur_working_dir_num].parent_inode
        file_system.set_cwd(inode_num)
        return
    if path == '$' or path == '.':
        file_system.set_cwd(0)
        return
    if path[0] == '/':
        inode_num = file_system.validate_abs_path(path)
    else:
        inode_num = file_system.validate_rel_path(path)

    if inode_num == -1:
        print('Path invalid !')
        return
    elif file_system.active_inode_dict[inode_num].file_type == 0:
        if file_system.active_inode_dict[inode_num].get_read_perm(cur_usr_idx):
            file_system.set_cwd(inode_num)
        else:
            print('current user do not have read permission for this directory')
            return
    else:
        print('Path must be a directory !')
        return


'''
    Function to perform write operations before exiting
'''
def exit_cmd():
    global file_system

    # dumping superblock, data list and inode list metadata to file
    #file_system.write_sblock_to_file()
    #file_system.write_dblist_to_file()
    #file_system.write_ilist_to_file()

    # writing active inodes to file
    #for inode_num in file_system.active_inode_dict:
    #    file_system.active_inode_dict[inode_num].write_inode_to_file()


'''
    Function to implement "put" command:
        "put <filepath1>" command receives an external file from filepath1 and puts it into 
        current working directory of virtual file system
'''
def put_cmd(ext_path):
    global file_system
    cur_usr_idx = file_system.cur_uidx

    if os.path.isfile(ext_path):
        file_size = os.path.getsize(ext_path)

        # getting file name
        filename = ntpath.basename(ext_path)

        # check length of filename
        if len(filename) > 64:
            print('Filename has more than 64 characters !')
            return

        # check validity of filename
        invalid_chars_file = set(' \\/,*\'#')

        fname_split = filename.split('/')
        for x in fname_split:
            if any((c in invalid_chars_file) for c in x):
                print('Filename contains invalid characters !')
                print('Rename the file, and try again')
                return



        # check if file size is less than 64KB
        if file_size < 65536:
            # read file into a byte stream
            byte_stream = bytearray()
            try:
                with open(ext_path, 'rb') as fp:
                    fp.seek(0)
                    byte_stream = bytearray(fp.read(file_size))
            except IOError:
                print('Error in reading file !')
                return


            # check if file exists in current working directory and if user has permission to edit directory
            cwd_no = file_system.cur_working_dir_num
            if not file_system.active_inode_dict[cwd_no].get_write_perm(cur_usr_idx):
                print('current user do not have permission to edit this directory.')
                return

            inode_num = file_system.get_file_inode_number(filename)

            if inode_num > 0:
                # releasing preoccupied blocks by existing inode
                file_system.release_data_blocks(inode_num)
                file_system.active_inode_dict[inode_num].blocks_allocated = 0

                if file_size > 0:
                    # allocating new blocks if file_size > 0
                    data_blocks = file_system.fetch_data_blocks(math.ceil(file_size / 4096))
                    if len(data_blocks) == 0:
                        print('Error in fetching free data blocks !')
                        return
                else:
                    # using touch if file size == 0
                    return touch_cmd(filename)

            else:

                if file_size > 0:
                    # allocating new blocks if file_size > 0
                    data_blocks = file_system.fetch_data_blocks(math.ceil(file_size / 4096))
                    if len(data_blocks) == 0:
                        print('Error in fetching free data blocks !')
                        return
                else:
                    # using touch if file size == 0
                    return touch_cmd(filename)

                # fetching free inode from file
                inode_num = file_system.fetch_inode()

            # setting inode parameters appropriately
            file_system.active_inode_dict[inode_num].filename = filename
            file_system.active_inode_dict[inode_num].file_type = 1
            file_system.active_inode_dict[inode_num].parent_inode = file_system.cur_working_dir_num
            file_system.active_inode_dict[inode_num].size_in_bytes = file_size
            file_system.active_inode_dict[inode_num].blocks_allocated = len(data_blocks)
            file_system.active_inode_dict[inode_num].set_last_access_time()
            file_system.active_inode_dict[inode_num].set_last_modify_time()
            file_system.active_inode_dict[inode_num].set_file_creation_time()
            file_system.active_inode_dict[inode_num].set_write_perm([cur_usr_idx])
            file_system.active_inode_dict[inode_num].set_read_perm([cur_usr_idx])


            # assigning direct data block pointers to inode
            file_system.active_inode_dict[inode_num].direct_block_pointers = [0 for x in range(16)]
            for i in range(len(data_blocks)):
                file_system.active_inode_dict[inode_num].direct_block_pointers[i] = data_blocks[i]

            # writing file to data blocks
            file_system.active_inode_dict[inode_num].write_stream_to_blocks(byte_stream)

            # add inode to dentry
            file_system.add_inode_to_dentry(inode_num)

            # write data block list, inode list & new inode to file
            file_system.write_ilist_to_file()
            file_system.write_dblist_to_file()
            file_system.active_inode_dict[inode_num].write_inode_to_file()


        else:
            print('File larger than 64KB , put operation aborted !')
            return
    else:
        print('File doesn\'t exists !')
        return


'''
    Function to implement 'get' command:
        get <filename> - extracts the 'file' provided in <filename> to current working directory of external OS
'''
def get_cmd(path):
    global file_system
    cur_usr_idx = file_system.cur_uidx

    inode_num = -1
    if len(path) == 0:
        print('Invalid path.')
        return
    if path[0] == '/':
        inode_num = file_system.validate_abs_path(path)
    else:
        inode_num = file_system.validate_rel_path(path)

    if inode_num > 0:

        # check permissions
        if not file_system.active_inode_dict[inode_num].get_write_perm(cur_usr_idx) or not file_system.active_inode_dict[inode_num].get_read_perm(cur_usr_idx):
            print('user must have both read and write permission to check out the file.')
            return

        if file_system.active_inode_dict[inode_num].file_type == 0:
            print('directory cannot be checked out.')
            return

        byte_stream = file_system.active_inode_dict[inode_num].read_data_blocks()
        filename = file_system.active_inode_dict[inode_num].filename

        if Path(filename).exists():
            print('File already exists at path - '+ str(Path.cwd()))
            return
        else:
            try:
                with open(filename, 'wb') as fp:
                    fp.seek(0)
                    fp.write(byte_stream)
            except IOError:
                print('Error in file creation !')
                return

    else:
        print('Invalid filename/path !')
        return


'''
    Function to implement 'mv' command 
'''
def mv_cmd(source_path, dest_path):

    global file_system
    cur_usr_idx = file_system.cur_uidx

    # fetching inode numbers of source and destination paths
    source_inode, dest_inode = -1, -1


    if len(source_path) == 0:
        print('Invalid path.')
        return
    if source_path[0] == '/':
        source_inode = file_system.validate_abs_path(source_path)
    else:
        source_inode = file_system.validate_rel_path(source_path)


    if len(dest_path) == 0:
        print('Invalid path.')
        return
    if dest_path[0] == '/':
        dest_inode = file_system.validate_abs_path(dest_path)
    else:
        dest_inode = file_system.validate_rel_path(dest_path)

    # checking validity of source and destination
    if source_inode == -1 :
        print('Invalid source path !')
        return


    if dest_inode == -1 :

        # checking for write permission
        if not file_system.active_inode_dict[source_inode].get_write_perm(cur_usr_idx):
            print('current user do not have write permissions for file provided')
            return

        # extract name out of destination path
        dest_name = [s for s in dest_path.split('/') if s != []]
        if len(dest_path) == 0:
            print('Destination path is empty !')
        else:
            # renaming the source file
            all_cwd_files = file_system.get_cwd_directories() + file_system.get_cwd_filenames()
            if dest_name[-1] not in all_cwd_files:
                file_system.active_inode_dict[source_inode].filename = dest_name[-1]
                parent = file_system.active_inode_dict[source_inode].parent_inode
                idx = file_system.child_dict[parent][0].index(source_inode)
                file_system.child_dict[parent][1][idx] = dest_name[-1]
                file_system.active_inode_dict[source_inode].write_inode_to_file()
                return
            else:
                print('Filename already exists !')
                return


    if file_system.active_inode_dict[source_inode].file_type == 0 and file_system.active_inode_dict[dest_inode].file_type == 1:
        print('Source cannot be directory if destination is a file !')
        return

    # when destination is directory
    if file_system.active_inode_dict[dest_inode].file_type == 0:
        if not file_system.active_inode_dict[dest_inode].get_write_perm(cur_usr_idx):
            print('current user do not have permission to write in destination')
            return

        filename = file_system.active_inode_dict[source_inode].filename
        if filename in file_system.child_dict[dest_inode][1]:
            print('Source filename already exists at destination !')
            return
        else:
            # removing old entry from child list of 'source parent'
            src_parent = file_system.active_inode_dict[source_inode].parent_inode
            idx = file_system.child_dict[src_parent][0].index(source_inode)
            file_system.child_dict[src_parent][0].pop(idx)
            file_system.child_dict[src_parent][1].pop(idx)

            # making new entry at child list of destination
            file_system.active_inode_dict[source_inode].parent_inode = dest_inode
            file_system.child_dict[dest_inode][0].append(source_inode)
            file_system.child_dict[dest_inode][1].append(filename)
            
            file_system.active_inode_dict[source_inode].write_inode_to_file()

    # when both source and destination are files, its a rename operation
    if file_system.active_inode_dict[dest_inode].file_type == 1 :
        print('Filename already exists')
        return


'''
    Function to copy a file into directory (currently source must be a file)
'''
def cp_cmd(source_path, dest_path):
    global file_system
    cur_usr_idx = file_system.cur_uidx

    # validating source and destination paths
    source_inode, dest_inode = -1, -1
    if len(source_path) == 0:
        print('Invalid path.')
        return
    if source_path[0] == '/':
        source_inode = file_system.validate_abs_path(source_path)
    else:
        source_inode = file_system.validate_rel_path(source_path)

    if len(dest_path) == 0:
        print('Invalid path.')
        return
    if dest_path[0] == '/':
        dest_inode = file_system.validate_abs_path(dest_path)
    else:
        dest_inode = file_system.validate_rel_path(dest_path)

    # checking validity of source and destination path
    if source_inode == -1:
        print('Invalid source path !')
        return
    if file_system.active_inode_dict[source_inode].file_type == 0:
        print('Directory copy feature is not yet provided. Please use it to copy files only !')
        return
    if dest_inode == -1:
        print('Invalid destination path !')
        return
    if file_system.active_inode_dict[dest_inode].file_type == 1:
        print('Copy cant be made on existing file !')
        return

    # check if file with same name already exists at destination
    if file_system.active_inode_dict[source_inode].filename in file_system.child_dict[dest_inode][1]:
        print('File with same name exists at destination !')
        return

    # checking for write permission
    if not file_system.active_inode_dict[dest_inode].get_write_perm(cur_usr_idx):
        print('current user do not have permission to write at destination !')
        return

    # creating new inode
    cp_inode = file_system.fetch_inode()

    if cp_inode > 0:
        # copying basic parameters of an inode
        file_system.active_inode_dict[cp_inode].read_mode = file_system.active_inode_dict[source_inode].read_mode
        file_system.active_inode_dict[cp_inode].write_mode = file_system.active_inode_dict[source_inode].write_mode
        file_system.active_inode_dict[cp_inode].edit_flag = file_system.active_inode_dict[source_inode].edit_flag
        file_system.active_inode_dict[cp_inode].file_type = file_system.active_inode_dict[source_inode].file_type
        file_system.active_inode_dict[cp_inode].size_in_bytes = file_system.active_inode_dict[source_inode].size_in_bytes
        file_system.active_inode_dict[cp_inode].blocks_allocated = file_system.active_inode_dict[source_inode].blocks_allocated
        file_system.active_inode_dict[cp_inode].filename = file_system.active_inode_dict[source_inode].filename

        file_system.active_inode_dict[cp_inode].parent_inode = dest_inode

        # adding dentry to filesystem
        file_system.add_inode_to_dentry(cp_inode)


        # fetching blocks if file size is non zero
        if file_system.active_inode_dict[source_inode].blocks_allocated > 0:
            data_blocks = file_system.fetch_data_blocks(file_system.active_inode_dict[source_inode].blocks_allocated)
            if len(data_blocks) == 0:
                print('Error in fetching free data blocks !')
                return

            # Assigning data blocks to copied file
            file_system.active_inode_dict[cp_inode].direct_block_pointers = [0 for x in range(16)]
            for i in range(len(data_blocks)):
                file_system.active_inode_dict[cp_inode].direct_block_pointers[i] = data_blocks[i]

            # Copying the original file data to copied file
            byte_stream = file_system.active_inode_dict[source_inode].read_data_blocks()
            file_system.active_inode_dict[cp_inode].write_stream_to_blocks(byte_stream)

    # Write inode to drive file
    file_system.active_inode_dict[cp_inode].write_inode_to_file()

    return



'''
    Function to print detailed file list, should provide output resembling to command 'll' or 'ls -l'
'''

def ll_cmd():
    global file_system
    inode_ls = file_system.get_cwd_child_inodes()
    user_idx = file_system.cur_uidx
    ll_out = []
    for a0 in range(len(inode_ls)):
        dper = ['-', '-', '-']        # directory/file indicator and permissions
        files_contained = 1 # denotes the no of files directories within
        file_size = 0       # denotes filesize
        date = '-------'    # denotes date of the file
        filename = ''       # denotes name of the file

        filename = file_system.active_inode_dict[inode_ls[a0]].get_filename()


        perm = file_system.active_inode_dict[inode_ls[a0]].get_file_permissions(user_idx)
        if perm[0] >= 1:
            dper[1] = 'r'
        if perm[1] >= 1:
            dper[2] = 'w'

        file_size = file_system.active_inode_dict[inode_ls[a0]].get_file_size()
        date = file_system.active_inode_dict[inode_ls[a0]].get_last_modify_date()

        if file_system.active_inode_dict[inode_ls[a0]].file_type == 0:
            dper[0] = 'd'
            filename = '[' + filename + ']'
            ll_out.insert(0, [''.join(dper), str(file_size), date, filename])
        else:
            ll_out.append([''.join(dper), str(file_size), date, filename])

    return ll_out


'''
    Function to implement simple 'cat' command that accepts multiple filenames as
    arguments and prints it on standard output device
'''
def cat_cmd(file_list):
    global file_system
    cat_out = []

    # fetch current working dir and current user
    cur_uidx = file_system.cur_uidx
    cur_wdno = file_system.cur_working_dir_num

    # validating every file in the list
    file_inode_list = []
    if len(file_list) == 0:
        print('missing file input for \'cat\' command')
        return cat_out

    for file in file_list:
        if len(file) > 0:
            tmp_inode = -1
            if file[0] == '/':
                tmp_inode = file_system.validate_abs_path(file)
            else:
                tmp_inode = file_system.validate_rel_path(file)

            if tmp_inode == -1:
                print('file does not exists')
                return cat_out

            # checking read permission
            if not file_system.active_inode_dict[tmp_inode].get_read_perm(cur_uidx):
                print('current user do not have read permission for \'{0}\''.format(file))
                return cat_out

            # checking if file is not directory
            if file_system.active_inode_dict[tmp_inode].get_file_type() == 0:
                print('\'{0}\' is a directory, not a file')
                return cat_out

            file_inode_list.append(tmp_inode)
        else:
            print('enter a valid filename')
            return cat_out


    # fetching data from file
    for inode in file_inode_list:
        cat_out.append(file_system.active_inode_dict[inode].read_data_blocks())

    return cat_out


'''
    Function to implement 'chmod' 
'''
def chmod_cmd(perm, path, uidx=''):
    global file_system
    cur_uidx = file_system.cur_uidx

    uidx = uidx.strip().split()
    for a0 in range(len(uidx)):
        if uidx[a0].isdigit():
            uidx[a0] = int(uidx[a0])
            if uidx[a0] > 7 or uidx[a0] < 0:
                print('Invalid userid.')
                return
        else:
            print('Invalid userid.')
            return

    # validating filename/path
    inode_num = -1
    if len(path) == 0:
        print('Invalid path.')
        return
    if path[0] == '/':
        inode_num = file_system.validate_abs_path(path)
    else:
        inode_num = file_system.validate_rel_path(path)

    if inode_num < 0 :
        print('Invalid path.')
        return
    if not file_system.active_inode_dict[inode_num].get_write_perm(cur_uidx):
        print('current user do not have permission to modify selected file.')
        return

    if perm == '00':
        file_system.active_inode_dict[inode_num].reset_read_perm(uidx)
        file_system.active_inode_dict[inode_num].reset_write_perm(uidx)
    elif perm == '10':
        file_system.active_inode_dict[inode_num].reset_write_perm(uidx)
        file_system.active_inode_dict[inode_num].set_read_perm(uidx)
    elif perm == '11':
        file_system.active_inode_dict[inode_num].set_read_perm(uidx)
        file_system.active_inode_dict[inode_num].set_write_perm(uidx)
    else:
        print('invalid permission assignment.')
        return

    # writing changes to file
    file_system.active_inode_dict[inode_num].write_inode_to_file()
    return


'''
    Function to implement pwd command
'''
def pwd_cmd():
    global file_system
    return file_system.get_cwd()

'''
    Function to implement edit command
'''
def edit_cmd(data_stream, path, edit_opt):
    global file_system
    cur_uidx = file_system.cur_uidx

    # validating filename/path
    inode_num = -1
    if len(path) == 0:
        print('Invalid path.')
        return
    if path[0] == '/':
        inode_num = file_system.validate_abs_path(path)
    else:
        inode_num = file_system.validate_rel_path(path)

    if inode_num < 0:
        print('Invalid path.')
        return
    if not file_system.active_inode_dict[inode_num].get_write_perm(cur_uidx):
        print('current user do not have permission to modify selected file.')
        return






'''
    Function to implement 'ulist' (userlist) command
'''
def ulist_cmd():
    global file_system
    return file_system.get_user_list()

'''
    Function to implement 'adduser' command
'''
def adduser_cmd(username, password):
    global file_system
    return file_system.add_user(username, password)

'''
    Function to implement 'deluser' command
'''
def deluser_cmd(user_list):
    global file_system
    return file_system.del_user(user_list)



'''
    Function to set current file system user
'''
def set_cur_usr(username):
    global file_system
    file_system.set_cur_user(username)


'''
    Function to check user validity
'''
def check_usr_validity(uname, passwd):
    global file_system
    return file_system.check_usr_validity(uname, passwd)


'''
    Function to get current user
'''
def get_cur_user():
    global file_system
    return file_system.get_cur_username()



