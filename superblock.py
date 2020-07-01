'''
Importing important modules
'''
import datetime
from pathlib import Path
import os


from inode import *
from index import *


class Superblock :

    #__defining data members of class, static variables, shared by all

    drive_filename = "virtual_drive.csfs"   # contains name of the file in which filesystem is stored

    file_sys_type = "CS"    # to check if filesystem is of proper format
    superblock_size = 512   # size of superblock data, hardcoded 512 as standard
    total_used_blocks = 1   # count of actually used block, 0th data block is reserved
    bytes_per_block = 4096  # no of bytes per block
    total_blocks = 16384    # no of all(free+used) block
    total_inodes_used = 0   # no of consumed inodes
    bytes_per_inode = 256   # no of bytes consumed per inode
    total_inodes = 1024     # no of total inodes (free+consumed)
    total_used_index = 0    # no of index tables in use
    total_index = 512       # no of total index tables available
    last_mount_time = []    # contains last time the filesystem was mounted
    last_modified_time = [] # contains last time the filesystem was modified
    no_of_users = 1         # contains total active users (root/admin is always active)
    max_no_of_users = 8     # count of maximum users allowed
    username_list = []      # list of usernames[max 16 char long] ("admin" is permanant username for root/admin)
    passwd_list = []        # list of passwords[max 16 char long] ("admin" is temparary password for all)

    extra_space = 220       # extra space kept for future development


    #data elements for data block list segment
    data_block_size = 32772     # stores total size of the data block
    block_list_size = 16384     # contains size of total block list
    block_list_head = 1         # pointer of free data-block list head,initially points to 1 (not 0 as,
    # zero indicates absense of data block pointer in inode "data block pointer" list
    block_list = []             # contains array representation of singly linked data block list


    #data elements for inode list segment
    ilist_block_size = 2052     # stores total size of inode list block
    inode_list_size = 1024      # contains total length of inode free list
    inode_list_head = 0         # pointer of free inode list head,initially points to 0
    inode_list = []             # contains array representation of list

    inode_block_size = 262144   # Total size of inode blocks (1024*256) = 262144

    #data elements for index table list
    idxList_block_size = 2052   # size of total index table list block
    index_list_size = 512       # contains total length of index table list
    index_list_head = 0         # pointer of free index list head,initially points to 0
    index_list = []             # contains array representation of singly linked index table list


    active_inode_dict = {}      # contains Dictionary of active inode objects, key of each object is its inode number


    #__Defining dentry elements on file system, built when drive in mounted

    # contains childrens present within a directory, key = directory inode number
    # value = tuple of (child inode list,child filename list) for every active inode

    child_dict = {x : ([], []) for x in range(1024)}



    # members to keep track of current directory
    cur_working_dir = '/'        # contains sequence of directory strings of current path
    cur_working_dir_num = 0     # contains inode of the current directory,initially set to root

    # current user name and index, default is (admin, 0)
    cur_uname = 'Guest'
    cur_uidx = -1

    #__Defining member functions of the class

    '''
    This function will be called when filesystem is being created for very first time
    '''
    def vfs_create_init(self):

        #setting mount and access time
        time_now = datetime.datetime.now()
        self.last_mount_time = [time_now.year % 2000,time_now.month,time_now.day,time_now.hour,time_now.minute,time_now.second]
        self.last_modified_time = [time_now.year % 2000,time_now.month,time_now.day,time_now.hour,time_now.minute, time_now.second]

        '''
        setting users on system, first is default admin user with username "admin" which cannot be deleted
        rest of the user names are "0" as default -> indicating missing user/user not created
        default password for admin : "admin", rest of the users - 0
        '''
        self.username_list = ["admin", "0", "0", "0", "0", "0", "0", "0"]
        self.passwd_list = ["admin", "0", "0", "0", "0", "0", "0", "0"]

        '''
        Initializing the block list (array representation of singly linked list)
        '''
        self.block_list = [x for x in range(1, self.block_list_size)]
        self.block_list.append(self.block_list_size)

        '''
        Initializing the free inode list
        '''
        self.inode_list = [x for x in range(1, self.inode_list_size)]
        self.inode_list.append(self.inode_list_size)

        '''
        Initializing the free index table list
        '''
        self.index_list = [x for x in range(1, self.index_list_size)]
        self.index_list.append(self.index_list_size)


    def create_empty_vfs(self):
        try:
            drivefile = Path(os.getcwd() + "\\" + self.drive_filename)
            size = 69505548

            #initialising to defaults
            self.vfs_create_init()

            #check if file exists, else create it
            if drivefile.is_file():
                self.write_sblock_to_file()
                self.write_dblist_to_file()
                self.write_ilist_to_file()
                self.write_iblock_to_file()
                self.write_idxList_to_file()
                self.write_idxBlock_to_file()
                print("Existing drive overwritten !")
            else:
                fp = open(self.drive_filename, 'wb')
                #fp.seek(size-1)
                #fp.write(b'\x00')
                fp.close()
                self.write_sblock_to_file()
                self.write_dblist_to_file()
                self.write_ilist_to_file()
                self.write_iblock_to_file()
                self.write_idxList_to_file()
                self.write_idxBlock_to_file()

                print("Drive created !")

            # creating root directory and write it to drive file
            self.create_root_dir()
            self.active_inode_dict[0].write_inode_to_file()

            # writing changes back to directory
            self.write_sblock_to_file()
            self.write_ilist_to_file()
            return 0
        except Exception:
            return -1




    '''
    ###############################################
        WRITE SECTION :
            contains write to file functions
    ###############################################
    '''

    #__this fuunction dumps superblock components to file
    def write_sblock_to_file(self):
        #__bytes for last mount time and last modified time
        # creating bytestream, this will store all the bytes of superblock that are to be written on file
        byte_stream = bytearray()

        # appendting bytes of file system type
        ch_code = [ord(x) for x in self.file_sys_type]
        for x in ch_code:
            byte_stream.append(x)

        # bytes of superblock size
        byte_stream += self.superblock_size.to_bytes(2, byteorder='big')
        byte_stream += self.total_used_blocks.to_bytes(2, byteorder='big')

        # bytes of total bytes per block
        byte_stream += (self.bytes_per_block.to_bytes(2, byteorder='big'))

        # bytes of total comsumed blocks
        byte_stream += (self.total_blocks.to_bytes(2, byteorder='big'))

        # bytes of total inodes and rest of the single valued print
        byte_stream += (self.total_inodes_used.to_bytes(2, byteorder='big'))
        byte_stream += (self.bytes_per_inode.to_bytes(2, byteorder='big'))
        byte_stream += (self.total_inodes.to_bytes(2, byteorder='big'))
        byte_stream += (self.total_used_index.to_bytes(2, byteorder='big'))
        byte_stream += (self.total_index.to_bytes(2, byteorder='big'))

        # bytes for time stamps
        for x in self.last_mount_time:
            byte_stream += x.to_bytes(1, byteorder='big')

        for x in self.last_modified_time:
            byte_stream += x.to_bytes(1, byteorder='big')

        byte_stream += (self.no_of_users.to_bytes(2, byteorder='big'))
        byte_stream += (self.max_no_of_users.to_bytes(2, byteorder='big'))

        # bytes for usernames
        for names in self.username_list:
            names = names.rjust(16)
            ch_code = [ord(x) for x in names]
            for x in ch_code:
                byte_stream.append(x)

        # bytes for password
        for pwd in self.passwd_list:
            pwd = pwd.rjust(16)
            ch_code = [ord(x) for x in pwd]
            for x in ch_code:
                byte_stream.append(x)


        # bytes for extra space
        for x in range(220):
            byte_stream.append(0)


        # writing superblock to file
        with open(self.drive_filename, "rb+") as fp:
            fp.seek(0)
            fp.write(byte_stream)




    '''
        This function writes Data block list to drive
    '''
    def write_dblist_to_file(self):

        byte_stream = bytearray()

        # bytes of block list size
        byte_stream += self.block_list_size.to_bytes(2, byteorder='big')

        # bytes of head of free block list
        byte_stream += self.block_list_head.to_bytes(2, byteorder='big')

        # bytes for entire byte free list
        for x in self.block_list:
            byte_stream += x.to_bytes(2, byteorder='big')

        # writing byte stream of data block to file
        with open(self.drive_filename, 'rb+') as fp:
            fp.seek(self.superblock_size)
            fp.write(byte_stream)

        #print(byte_stream, len(byte_stream))


    '''
        This function writes inode list block to drive
    '''
    def write_ilist_to_file(self):

        byte_stream = bytearray()

        # bytes for size of entire inode list
        byte_stream += self.inode_list_size.to_bytes(2, byteorder='big')

        # bytes for head of the free inode list
        byte_stream += self.inode_list_head.to_bytes(2, byteorder='big')

        # bytes for entire inode list
        for x in self.inode_list:
            byte_stream += x.to_bytes(2, byteorder='big')

        # writing byte stream to file
        with open(self.drive_filename, 'rb+') as fp:
            fp.seek(self.superblock_size+self.data_block_size)
            fp.write(byte_stream)



    '''
        This function writes entire inode block to drive
    '''
    def write_iblock_to_file(self):

        byte_stream = bytearray()

        # collecting bytes streams for individual inode
        for i in range(1024):
            node = Inode(i)
            byte_stream += node.get_inode_bytestream()

        # writing data to file
        with open(self.drive_filename, 'rb+') as fp:
            fp.seek(self.superblock_size+self.data_block_size+self.ilist_block_size)
            fp.write(byte_stream)
        #print(len(byte_stream))



    '''
        This function writes index list block to drive
    '''
    def write_idxList_to_file(self):

        byte_stream = bytearray()

        # bytes for index list size
        byte_stream += self.index_list_size.to_bytes(2, byteorder='big')

        # bytes for head of the index list
        byte_stream += self.index_list_head.to_bytes(2, byteorder='big')

        # bytes for entire lndex list
        for x in self.index_list:
            byte_stream += x.to_bytes(4, byteorder='big')

        with open(self.drive_filename, 'rb+') as fp:
            fp.seek(self.superblock_size+self.data_block_size+self.ilist_block_size+self.inode_block_size)
            fp.write(byte_stream)



    '''
        This function writes entire index block to file
    '''
    def write_idxBlock_to_file(self):

        byte_stream = bytearray()

        #collecting byte streams for every index table
        for i in range(512):
            table = Index()
            byte_stream += table.get_index_bytestream()

        with open(self.drive_filename, 'rb+') as fp:
            fp.seek(self.superblock_size+self.data_block_size+self.ilist_block_size+self.inode_block_size+self.idxList_block_size)
            fp.write(byte_stream)




    '''
    #########################################################
        READ FUNCTION SECTION :
            contains read from file functions
    #########################################################
    '''

    '''
        Function to load vfs to file 
    '''
    def read_vfs(self):

        try:
            # reading superblock from file
            self.read_sblock_from_file()

            # reading data block list from file
            self.read_dblist_from_file()

            # reading inode list from file
            self.read_iList_from_file()

            # read index list from file
            self.read_idxList_from_file()

            # fetching all active inodes
            self.build_act_inode_dict()

            # bulding dentry dictionary
            self.build_dentry_obj()


            # assign "root" as current working directory
            self.cur_working_dir = '/'
            self.cur_working_dir_num = 0
            return 1
        except :
            return -1



    def read_iList_from_file(self):

        byte_stream = bytearray()

        try:
            with open(self.drive_filename, 'rb') as fp:
                fp.seek(self.superblock_size+self.data_block_size)
                byte_stream = bytearray(fp.read(self.ilist_block_size))
        except IOError:
            print('Error in reading Inode List Block')

        # processing byte stream
        offset = 0
        self.inode_list_size = int.from_bytes(byte_stream[offset:offset+2], byteorder='big', signed=False)
        offset += 2
        self.inode_list_head = int.from_bytes(byte_stream[offset:offset+2], byteorder='big', signed=False)
        offset += 2

        # setting inode list empty
        self.inode_list = []
        for i in range(0, self.inode_list_size):
            self.inode_list.append(int.from_bytes(byte_stream[offset:offset+2], byteorder='big', signed=False))
            offset += 2



    def read_sblock_from_file(self):
        byte_stream = bytearray()  # bytearray(b'') = output

        try:
            with open(self.drive_filename, 'rb') as fp:  # for opening binary files
                byte_stream = bytearray(
                    fp.read(self.superblock_size))  # store evth in file in the binary format in byte_stream
        except IOError:
            print('Error in reading Superblock')

        #print(byte_stream)
        # processing byte stream
        offset = 0
        # appending characters of file system type
        ch_list = []
        for i in range(2):
            ch_list.append(int.from_bytes(byte_stream[offset + i:offset + i + 1], byteorder='big', signed=False))
            # converting byte to integer (ascii value)

        self.file_sys_type = "".join([chr(c) for c in ch_list])  # chr gives the character value  x= [67, 83]
        # chr gives the character value  x= [67, 83]

        # calculating superblock size
        offset += 2
        self.superblock_size = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)
        offset += 2
        self.total_used_blocks = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        # value of total bytes per block
        offset += 2
        self.bytes_per_block = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        # calculating total consumed blocks
        offset += 2
        self.total_blocks = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        # values of total inodes and rest of the single valued print
        offset += 2
        self.total_inodes_used = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.bytes_per_inode = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.total_inodes = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.total_used_index = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.total_index = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        # retrieving time stamps : mount time
        offset += 2

        for i in range(0, 6):
            self.last_mount_time.append(
                int.from_bytes(byte_stream[offset:offset + 1], byteorder='big', signed=False))
            offset += 1

        # retrieving time stamps : modified time
        for i in range(0, 6):
            self.last_modified_time.append(
                int.from_bytes(byte_stream[offset:offset + 1], byteorder='big', signed=False))
            offset += 1

        self.no_of_users = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.max_no_of_users = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.username_list = []
        for user in range(0, self.max_no_of_users):
            user_name = []
            for x in range(0, 16):
                user_name.append(int.from_bytes(byte_stream[offset:offset + 1], byteorder='big', signed=False))
                offset += 1
            self.username_list.append(("".join([chr(c) for c in user_name])).strip())

        #print(self.username_list)
        self.passwd_list = []
        for user in range(0, self.max_no_of_users):
            password = []
            for x in range(0, 16):
                password.append(int.from_bytes(byte_stream[offset:offset + 1], byteorder='big', signed=False))
                offset += 1
            self.passwd_list.append(("".join([chr(c) for c in password])).strip())
        #print(self.passwd_list)

        #print(self.file_sys_type, self.superblock_size, self.total_used_blocks, self.last_mount_time,
        #      self.last_modified_time, self.max_no_of_users, self.username_list, self.passwd_list)


    '''
       This function writes Data block list from file to the data block
    '''
    def read_dblist_from_file(self):

        byte_stream = bytearray()

        try:
            with open(self.drive_filename, 'rb') as fp:  # for opening binary files
                fp.seek(self.superblock_size)  # reach till the datablock list
                byte_stream = bytearray(
                    fp.read(self.data_block_size))  # store evth in file in the binary format in byte_stream
        except IOError:
            print('Error in reading data Block list')

        #print(byte_stream)

        # processing byte stream
        offset = 0
        self.block_list_size = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        self.block_list_head = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        offset += 2
        # bytes for entire byte free list

        for x in range(0, self.total_blocks):
            self.block_list.append(int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False))
            offset += 2

            # print(byte_stream, len(byte_stream))


    '''
        This function writes index list block to drive
    '''
    def read_idxList_from_file(self):

        byte_stream = bytearray()

        try:
            with open(self.drive_filename, 'rb') as fp:  # for opening binary files
                fp.seek(
                    self.superblock_size + self.data_block_size + self.ilist_block_size + self.inode_block_size)  # reach till the datablock list
                byte_stream = bytearray(
                    fp.read(self.idxList_block_size))  # store evth in file in the binary format in byte_stream
        except IOError:
            print('Error in reading index list')

        #print(byte_stream)

        # value of index list size
        offset = 0
        self.index_list_size = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        # value of head of the index list
        offset += 2
        self.index_list_head = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)

        # bytes for entire lndex list
        for x in range(0, self.total_index):
            self.index_list.append(int.from_bytes(byte_stream[offset:offset + 4], byteorder='big', signed=False))
            offset += 4



    '''
    #######################################################
        INTERNAL FILE SYSTEM FUNCTIONs
    #######################################################
    '''

    '''
        Function to fetch free inode number:
            it checks if any free inode number exists, if yes then fetches that inode number
    '''
    def fetch_inode(self):

        if self.total_inodes_used < self.total_inodes :
            inode_num = self.inode_list_head
            self.inode_list_head = self.inode_list[self.inode_list_head]
            self.inode_list[inode_num] = inode_num

            self.active_inode_dict[inode_num] = Inode(inode_num)

            # fetching inode object data from file
            # self.active_inode_dict[inode_num].read_inode_from_file()

            # incrementing count in superblock
            self.total_inodes_used += 1

            return inode_num
            #print(self.active_inode_dict.keys(), "\n")
            #print(self.inode_list, "\n")
            #print(self.inode_list_head)
        else:
            print("Max file limit exceeded !")
            return -1


    '''
        Function to free inode :
            this function accepts inode number and releases the inode object associated with it
    '''
    def release_inode(self, inode_num):
        if inode_num in self.active_inode_dict.keys():
            self.inode_list[inode_num] = self.inode_list_head
            self.inode_list_head = inode_num
            self.active_inode_dict.pop(inode_num, None)

            #print(self.active_inode_dict.keys(), "\n")
            #print(self.inode_list, "\n")
            #print(self.inode_list_head)

        else:
            print("Inode not in use !")


    '''
        Function to create the root directory, called only when new file system is being created
    '''
    def create_root_dir(self):
        if self.fetch_inode() > -1:
            self.active_inode_dict[0].set_root()
        else:
            return -1



    '''
        Function to build active inode list 
    '''
    def build_act_inode_dict(self):
        # fetching all occupied inodes
        active_inode_num = [x for x in range(self.inode_list_size) if self.inode_list[x] == x]

        # add root to active inode dict and children dictionary
        for num in active_inode_num:
            self.active_inode_dict[num] = Inode(num)
            self.active_inode_dict[num].read_inode_from_file()


    '''
        Function to build dentry objects
    '''
    def build_dentry_obj(self):
        active_inode_num = list(self.active_inode_dict.keys())

        # removing root as it wont be child of any other inode
        active_inode_num.remove(0)
        for num in active_inode_num:
            self.child_dict[self.active_inode_dict[num].parent_inode][0].append(num)
            self.child_dict[self.active_inode_dict[num].parent_inode][1].append(self.active_inode_dict[num].filename)



    '''
        Function to add inode to dentry object : child_dict
    '''
    def add_inode_to_dentry(self, inode_number):

        self.child_dict[self.active_inode_dict[inode_number].parent_inode][0].append(inode_number)
        self.child_dict[self.active_inode_dict[inode_number].parent_inode][1].append(self.active_inode_dict[inode_number].filename)



    '''
        Function to pop dentry object
    '''
    def remove_inode_from_dentry(self, inode_number):
        idx = self.child_dict[self.active_inode_dict[inode_number].parent_inode][0].index(inode_number)
        self.child_dict[self.active_inode_dict[inode_number].parent_inode][0].pop(idx)
        self.child_dict[self.active_inode_dict[inode_number].parent_inode][1].pop(idx)



    '''
        Function to get filenamses present in current directory
    '''
    def get_cwd_filenames(self):
        filenames = []
        cwd_inodes = self.child_dict[self.cur_working_dir_num][0]
        cwd_filenames = self.child_dict[self.cur_working_dir_num][1]

        for i in range(len(cwd_inodes)):
            if self.active_inode_dict[cwd_inodes[i]].file_type == 1:
                filenames.append(cwd_filenames[i])
        return filenames



    '''
        Function to get dictionaries under cwd
    '''
    def get_cwd_directories(self):
        directories = []
        cwd_inodes = self.child_dict[self.cur_working_dir_num][0]
        cwd_filenames = self.child_dict[self.cur_working_dir_num][1]

        for i in range(len(cwd_inodes)):
            if self.active_inode_dict[cwd_inodes[i]].file_type == 0:
                directories.append(cwd_filenames[i])
        return directories


    '''
        Function to get inode number of current working directory
    '''
    def get_cwd_child_inodes(self):

        return self.child_dict[self.cur_working_dir_num][0]


    '''
        Function to fetch inode number based on filename
    '''
    def get_file_inode_number(self, filename):
        cwd_filenames = self.child_dict[self.cur_working_dir_num][1]

        if filename in cwd_filenames:
            idx = cwd_filenames.index(filename)
            return self.child_dict[self.cur_working_dir_num][0][idx]
        else:
            return -1



    '''
        Function to validate absolute path of file
        Returns inode of last directory if path is valid, -1 otherwise
    '''
    def validate_abs_path(self, path_mod):
        # cleaning up path_mod list
        path_mod = path_mod.strip()

        # checking if path contains any spaces
        if ' ' in path_mod:
            return -1

        # checking if abs path is root
        if path_mod == '/':
            return 0

        # splitting string based on '/'
        path_mod = path_mod.split('/')

        if path_mod[0] == '':
            path_mod.pop(0)
        if path_mod[-1] == '':
            path_mod.pop(-1)
        if '' in path_mod or len(path_mod) == 0:
            return -1

        last_dir_inode = 0
        while len(path_mod) != 0:
            try:
                idx = self.child_dict[last_dir_inode][1].index(path_mod[0])
                last_dir_inode = self.child_dict[last_dir_inode][0][idx]
                path_mod.pop(0)
            except ValueError:
                return -1

        return last_dir_inode


    '''
        Function to validate relative path of file
        Returns inode of last directory if path is valid, -1 otherwise
    '''
    def validate_rel_path(self, path_mod):
        # cleaning up leading and trailing spaces in path_mod
        path_mod = path_mod.strip()

        # checking if path contains any spaces
        if ' ' in path_mod:
            return -1

        # checking if abs path is root
        if path_mod == '/':
            return 0

        # splitting string based on '/'
        path_mod = path_mod.split('/')

        # cleaning up path mod list
        if path_mod[0] == '':
            path_mod.pop(0)
        if path_mod[-1] == '':
            path_mod.pop(-1)
        if '' in path_mod or len(path_mod) == 0:
            return -1

        last_dir_inode = self.cur_working_dir_num
        while len(path_mod) != 0:
            try:
                idx = self.child_dict[last_dir_inode][1].index(path_mod[0])
                last_dir_inode = self.child_dict[last_dir_inode][0][idx]
                path_mod.pop(0)
            except ValueError:
                return -1

        return last_dir_inode



    '''
        Function to set current working directory number and path
    '''
    def set_cwd(self, inode_num):
        self.cur_working_dir_num = inode_num

        cwd_path = []

        while inode_num != 0:
            cwd_path.insert(0, self.active_inode_dict[inode_num].filename)
            inode_num = self.active_inode_dict[inode_num].parent_inode

        self.cur_working_dir = '/' + '/'.join(cwd_path)

    '''
        Function to get current working directory path
    '''
    def get_cwd(self):
        return self.cur_working_dir

    '''
    ####################################################################
        OPERATIONS related to DATA BLOCKS and DATA BLOCK LIST
    ####################################################################
    '''

    '''
        Function to fetch 'n' free datablocks out of data block list
    '''
    def fetch_data_blocks(self, n):
        data_blocks = []
        if self.total_used_blocks + n < self.total_blocks:
            self.total_used_blocks += n

            # capturing free data blocks from data block list
            while n > 0:
                data_blocks.append(self.block_list_head)
                self.block_list_head = self.block_list[self.block_list_head]
                n -= 1
        else:
            print("No free data blocks available !")

        return data_blocks


    '''
        Function to release requested data_blocks[]
    '''
    def release_data_blocks(self, inode_num):
        data_blocks = self.active_inode_dict[inode_num].direct_block_pointers
        data_blocks = [x for x in data_blocks if x != 0]
        self.active_inode_dict[inode_num].blocks_allocated = 0
        self.active_inode_dict[inode_num].direct_block_pointers = [0 for x in range(16)]

        while len(data_blocks) != 0:
            tmp_block = data_blocks.pop(0)
            self.block_list[tmp_block] = self.block_list_head
            self.block_list_head = tmp_block


    '''
    ####################################################
    FUNCTIONS related to user
    ####################################################
    '''

    '''
        Function to return index of the 
    '''
    def get_user_idx(self, user):
        return self.username_list.index(user)

    '''
        Function to get current username
    '''
    def get_cur_username(self):
        return self.cur_uname

    '''
        Function to get current user index
    '''
    def get_cur_useridx(self):
        return self.cur_uidx

    '''
        Function to set current user
    '''
    def set_cur_user(self, username):
        if username in self.username_list:
            self.cur_uname = username
            self.cur_uidx = self.username_list.index(username)


    '''
        Function to verify new user
    '''
    def check_usr_validity(self, username, password):
        if username in self.username_list and username != '0':
            idx = self.username_list.index(username)
            if password == self.passwd_list[idx]:
                return True
            else:
                print('abc')
                return False
        else:
            return False


    '''
        Function to add new user
    '''
    def add_user(self, username, password):
        try:
            if self.cur_uidx == 0:

                if username != '0' and len(username) > 0 and len(password) > 0 and len(username) < 17 and \
                        len(password) < 17 and username not in self.username_list:
                    if '0' in self.username_list:
                        idx = self.username_list.index('0')
                        self.username_list[idx] = username
                        self.passwd_list[idx] = password

                        # writing changes to file
                        self.write_sblock_to_file()
                        return 0
                    else:
                        print('Max user limit exhausted')
                        return -1
                else:
                    print('Invalid username/password')
                    return -2
            else:
                print('only \'admin\' can add new user')
                return -3
        except Exception as e:
            return -4



    '''
        Function to delete existing user
    '''
    def del_user(self, user_list):
        try:
            if self.cur_uidx == 0:
                for username in user_list:
                    if username in self.username_list and username != 'admin':
                        idx = self.username_list.index(username)
                        self.username_list[idx] = '0'
                        self.passwd_list[idx] = '0'

                        # write changes to file
                        self.write_sblock_to_file()
                        return 0
                    else:
                        print('invalid user.')
                        return -1
            else:
                print('only \'admin\' can delete the user.')
                return -2
        except Exception as e:
            return -3


    '''
        Function to fetch user list
    '''
    def get_user_list(self):
        return self.username_list
















