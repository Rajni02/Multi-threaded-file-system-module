'''
Importing important modules
'''
import datetime

class Inode:

    # Static variable, shared by all instances of class
    inode_block_offset = 35336              # starting position of inode block
    data_block_offset = 1348108             # starting position of data block
    inode_size = 256                        # stores inode size in bytes
    drive_filename = "virtual_drive.csfs"   # file name of virtual drive

    mon_map = {1:'Jan', 2:'Feb', 3:'Mar',
               4:'Apr', 5:'May', 6:'Jun',
               7:'Jul', 8:'Aug', 9:'Sep',
               10:'Oct', 11:'Nov', 12:'Dec'}

    '''
        Class constructor
    '''
    def __init__(self, inode_num):
        # __defining data members
        self.read_mode = 0b00000001                             # Only root has access to read (0th bit is set)
        self.write_mode = 0b00000001                            # Only root has access to write (0th bit is set)
        self.edit_flag = 0b00000000                             # Indicates which user has checked out a particular file, initailly set to 0
        self.inode_number = inode_num                           # represents INODE NUMBER of file, incremented sequentially
        self.parent_inode = 0                                   # root is default parent
        self.file_type = 0                                      # initially file type is directory (0), can be set to normal file (1)
        self.size_in_bytes = 0                                  # stores file size in bytes, intially zero
        self.file_creation_time = []                            # stores when file was created
        self.last_access_time = []                              # stores timestamp when file was last accessed, initially
        self.last_modify_time = []                              # stores when file was last modified
        self.blocks_allocated = 0                               # stores number of blocks allocated
        self.direct_block_pointers = []                         # stores direct pointers of file blocks, total 16, each of size 4 bytes
        self.indirect_block_pointers = []                       # stores indirect pointers of file blocks, total 16, each of size 4 bytes
        self.filename = ""                                      # stores name of the file, max 64 characters
        self.extra_space = 90                                   # extra space of 90 bytes, reserved for future
        self.inode_create_init()


    '''
        This function handles some initial assignments when
        inodes are created for first time
    '''
    def inode_create_init(self):

        # assigning dummy timestamps
        self.file_creation_time = [0 for x in range(6)]
        self.last_access_time = [0 for x in range(6)]
        self.last_modify_time = [0 for x in range(6)]

        # assigning direct and indirect block pointers
        self.direct_block_pointers = [0 for x in range(16)]
        self.indirect_block_pointers = [0 for x in range(16)]


    '''
        This function fetches bytestream of a particular inode object
    '''
    def get_inode_bytestream(self):

        byte_stream = bytearray()

        # bytes for private data members of object Inode
        byte_stream += self.read_mode.to_bytes(1, byteorder='big')
        byte_stream += self.write_mode.to_bytes(1, byteorder='big')
        byte_stream += self.edit_flag.to_bytes(1, byteorder='big')
        byte_stream += self.inode_number.to_bytes(4, byteorder='big')
        byte_stream += self.parent_inode.to_bytes(4, byteorder='big')
        byte_stream += self.file_type.to_bytes(1, byteorder='big')
        byte_stream += self.size_in_bytes.to_bytes(4, byteorder='big')

        # bytes for file related timestamps
        for x in self.file_creation_time:
            byte_stream += x.to_bytes(1, byteorder='big')

        for x in self.last_access_time:
            byte_stream += x.to_bytes(1, byteorder='big')

        for x in self.last_modify_time:
            byte_stream += x.to_bytes(1, byteorder='big')

        byte_stream += self.blocks_allocated.to_bytes(4, byteorder='big')

        # bytes for direct and indirect block pointers
        for x in self.direct_block_pointers:
            byte_stream += x.to_bytes(2, byteorder='big')

        for x in self.indirect_block_pointers:
            byte_stream += x.to_bytes(2, byteorder='big')

        fname = self.filename.rjust(64 , '\0')
        ch_code = [ord(x) for x in fname]
        for x in ch_code:
            byte_stream.append(x)

        # bytes for extra space
        byte_stream += bytearray(90)

        return byte_stream


    '''
    ###########################################################
        INODE WRITE SECTION
    ###########################################################
    '''


    '''
        Function to write inode data to drive file
    '''
    def write_inode_to_file(self):

        # creating byte stream
        byte_stream = self.get_inode_bytestream()

        try:
            with open(self.drive_filename, 'rb+') as fp:
                fp.seek(self.inode_block_offset+self.inode_number*self.inode_size)
                fp.write(byte_stream)
        except IOError:
            print("Error writing file to drive !")


    def write_stream_to_blocks(self, byte_stream):
        n = self.blocks_allocated
        offset = 0

        try:
            with open(self.drive_filename, 'rb+') as fp:
                # writing first n-1 blocks
                for i in range(n-1):
                    fp.seek(self.data_block_offset+self.direct_block_pointers[i]*4096)
                    fp.write(byte_stream[offset:offset+4096])
                    offset += 4096

                # writing last block
                fp.seek(self.data_block_offset+self.direct_block_pointers[n-1]*4096)
                fp.write(byte_stream[offset:self.size_in_bytes])
        except IOError:
            print('Error in writing data blocks !')
            return







    '''
    ###########################################################
        INODE READ SECTION
    ###########################################################
    '''
    def read_inode_from_file(self):

        # byte stream of entire inode
        byte_stream = bytearray()

        try:
            with open(self.drive_filename, 'rb') as fp:
                fp.seek(self.inode_block_offset+self.inode_number*self.inode_size)
                byte_stream = bytearray(fp.read(self.inode_size))
        except IOError:
            print("Error in reading Inode data !")

        # processing byte_stream
        offset = 0
        self.read_mode = int.from_bytes(byte_stream[offset:offset+1], byteorder='big', signed=False)
        offset += 1
        self.write_mode = int.from_bytes(byte_stream[offset:offset+1], byteorder='big', signed=False)
        offset += 1
        self.edit_flag = int.from_bytes(byte_stream[offset:offset+1], byteorder='big', signed=False)
        offset += 1
        self.inode_number = int.from_bytes(byte_stream[offset:offset+4], byteorder='big', signed=False)
        offset += 4
        self.parent_inode = int.from_bytes(byte_stream[offset:offset+4], byteorder='big', signed=False)
        offset += 4
        self.file_type = int.from_bytes(byte_stream[offset:offset+1], byteorder='big', signed=False)
        offset += 1
        self.size_in_bytes = int.from_bytes(byte_stream[offset:offset+4], byteorder='big', signed=False)
        offset += 4

        # reading timestamps
        for i in range(6):
            self.file_creation_time[i] = int.from_bytes(byte_stream[offset:offset+1], byteorder='big', signed=False)
            offset += 1

        for i in range(6):
            self.last_access_time[i] = int.from_bytes(byte_stream[offset:offset + 1], byteorder='big', signed=False)
            offset += 1

        for i in range(6):
            self.last_modify_time[i] = int.from_bytes(byte_stream[offset:offset + 1], byteorder='big', signed=False)
            offset += 1

        self.blocks_allocated = int.from_bytes(byte_stream[offset:offset+4], byteorder='big', signed=False)
        offset += 4

        # reading direct and indirect block pointers
        for i in range(16):
            self.direct_block_pointers[i] = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)
            offset += 2

        for i in range(16):
            self.indirect_block_pointers[i] = int.from_bytes(byte_stream[offset:offset + 2], byteorder='big', signed=False)
            offset += 2

        # reading filename
        self.filename = byte_stream[offset:offset+64].decode('utf-8')
        self.filename = self.filename.strip('\0')




    '''
        Function to read data blocks allocated to the inode
    '''
    def read_data_blocks(self):

        # check if inode is a dictionary
        if self.file_type == 0:
            print(self.filename + ' is a dictionary !')
            return bytearray()
        if self.blocks_allocated == 0:
            return bytearray()

        n = self.blocks_allocated
        byte_stream = bytearray()

        # reading first n-1 blocks
        with open(self.drive_filename, 'rb') as fp:
            for i in range(n-1):
                fp.seek(self.data_block_offset+self.direct_block_pointers[i]*4096)
                byte_stream += fp.read(4096)
            fp.seek(self.data_block_offset+self.direct_block_pointers[n-1]*4096)
            byte_stream += fp.read(self.size_in_bytes - (n-1)*4096)

        return byte_stream


    '''
    ################################################
        INTERNAL INODE MODIFICATION SECTION
    ################################################
    '''

    def set_root(self):

        time_now = datetime.datetime.now()
        self.file_creation_time = [time_now.year % 2000, time_now.month, time_now.day, time_now.hour, time_now.minute, time_now.second]
        self.last_modify_time = [time_now.year % 2000, time_now.month, time_now.day, time_now.hour, time_now.minute,time_now.second]
        self.last_access_time = [time_now.year % 2000, time_now.month, time_now.day, time_now.hour, time_now.minute,time_now.second]


    def set_last_access_time(self):
        time_now = datetime.datetime.now()
        self.last_access_time = [time_now.year % 2000, time_now.month, time_now.day, time_now.hour, time_now.minute,time_now.second]

    def set_file_creation_time(self):
        time_now = datetime.datetime.now()
        self.file_creation_time = [time_now.year % 2000, time_now.month, time_now.day, time_now.hour, time_now.minute,time_now.second]

    def set_last_modify_time(self):
        time_now = datetime.datetime.now()
        self.last_modify_time = [time_now.year % 2000, time_now.month, time_now.day, time_now.hour, time_now.minute, time_now.second]


    '''
        Function to set user permission for every user index
        user admin has default index '0'
    '''
    def set_read_perm(self, usr_idx_list):
        for idx in usr_idx_list:
            self.read_mode = self.read_mode | (1 << idx)

    '''
        Function to set user permission for every user index
        user admin has default index '0'
    '''
    def set_write_perm(self, usr_idx_list):
        for idx in usr_idx_list:
            self.write_mode = self.write_mode | (1 << idx)

    '''
        Function to reset the read permission except admin
    '''
    def reset_read_perm(self, usr_idx_list):
        for idx in usr_idx_list:
            self.read_mode = self.read_mode & ((0 << idx) + 1)

    '''
        Function to reset the write permission except admin
    '''
    def reset_write_perm(self, usr_idx_list):
        for idx in usr_idx_list:
            self.write_mode = self.write_mode & ((0 << idx) + 1)




    '''
    #############################################
        FUNCTIONS to fetch inode data
    #############################################
    '''

    '''
        Function to get file type
    '''
    def get_file_type(self):
        return self.file_type

    '''
        Function to get file read permission
    '''
    def get_file_permissions(self, usr_idx):
        return int(self.read_mode & (1 << usr_idx)), int(self.write_mode & (1 << usr_idx))

    '''
        Function to get the file size
    '''
    def get_file_size(self):
        return self.size_in_bytes


    '''
        Functions to fetch last modified date
    '''
    def get_last_modify_date(self):
        return '{0:2d} '.format(self.last_modify_time[2]) + self.mon_map[self.last_modify_time[1]] + \
               ' {0:2d}  {1:02d}:{2:02d}'.format(self.last_modify_time[0], self.last_modify_time[3],
                                              self.last_modify_time[4])


    '''
        Functions to fetch filename of inodes
    '''
    def get_filename(self):
        return self.filename


    '''
        Function to fetch read permission based on given user index
        returns TRUE if user has permission, FALSE otherwise
    '''
    def get_read_perm(self, usr_idx):
        if (self.read_mode & (1 << usr_idx)) > 0:
            return True
        else:
            return False


    '''
        Function to fetch read permission based on given user index
        returns TRUE if user has permission, FALSE otherwise
    '''
    def get_write_perm(self, usr_idx):
        if (self.write_mode & (1 << usr_idx)) > 0:
            return True
        else:
            return False
