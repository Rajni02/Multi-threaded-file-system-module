'''
    Importing required modules
'''

class Index:
    # static variable
    index_block_offset = 299532     # stores offset of an index block

    '''
        Constuctor
    '''
    def __init__(self):
        self.data_pointers = [0 for x in range(1024)]

    '''
        This function fetched byte stream of index table
    '''
    def get_index_bytestream(self):


        byte_stream = bytearray()

        for x in self.data_pointers:
            byte_stream += x.to_bytes(2, byteorder='big')

        return byte_stream

