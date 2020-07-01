"""
Contains the functions associated with user interface
Has separate parser to understand user input
"""



'''
    Importing necessary modules
'''
from superblock import *
from vfs_core_interface import *
from pathlib import Path
import traceback
import getpass

'''
    A "command parse tree" utilised by command_parser() to make
'''

cmd_parse_tree = {
    "create" : {"vfs" : 1},
    "mount" : 2,
    "touch" : {"#": 3},
    "ls"    : {"$": 4, "-l" : 14},
    "rm"    : {"#" : 5, "-r" : {"#" : 8}, '*' : 16},
    "mkdir" : {"#" : 6},
    "cd"    : {"$": 15, '#' : 7},
    "put"   : {'#' : 9},
    "get"   : {'#' : 10},
    "mv"    : {'#' : {'#' : 11}},
    "cp"    : {'#' : {'#' : 12}},
    "exit" : 13,
    "ll"    : {"$" : 14},
    'cat'   : {'#': 17},
    'adduser'   : 18,
    'deluser'   : {'#'  : 19},
    'chmod'   : 20,
    'ulist'     : 21,
    'pwd'     : 22,
}

cur_user_name = 'admin'
cur_user_idx = 0

'''
    A global set of invalid characters in filenames
'''
invalid_chars_file = set(' \\/,*\'#[]')
invalid_chars_dir = set(' \\,*\'#[]')


drive_filename = 'virtual_drive.csfs'


'''
    Function to check if command is in proper format,  returns a positive integer associated with command if
    parsing is successfull, -1 otherwise
'''
def command_parser(command, trace):
    if len(command) == 0:
        if type(trace) == int:
            return trace
        else:
            return -1
    else:
        if type(trace) is dict and command[0] in trace.keys():
            trace = trace[command[0]]
            command.pop(0)
            return command_parser(command, trace)
        else:
            return -1



'''
    Function to pre-process the command (assuming path doesnt have any spaces and '#' at all)
    This function detects the path and replaces it with some constant string '#'
'''
def cammand_preprocessor(command):
    if command[0] == 'touch' or command[0] == 'mkdir':
        if len(command) != 2:
            return -1
        else:
            command[1] = '#'
            return command
    for i in range(len(command)):
        if '\\' in command[i]:
            command[i] = '#'

    return command


'''
    Function to validate directory path 
'''
def path_validator(path):

    #when path is directory
    if path == '' or path[-1] != '/':
        return -1
    else:
        # checking for absolute path
        if path[0] == '/':
            return validate_abs_path_core(path)
        else:
            return validate_rel_path_core(path)



'''
    Function to validate filename (not directory name)
    returns filename if valid, returns '' otherwise
'''
def filename_validator(fname):
    fname_split = fname.split('/')
    for x in fname_split:
        if any((c in invalid_chars_file) for c in x):
            return ''

    return fname



'''
    Function to validate directory name,
    :return directory path/name if valid, returns '' otherwise
'''
def dirname_validator(fname):
    fname_split = fname.split('/')
    for x in fname_split:
        if any((c in invalid_chars_dir) for c in fname_split):
            return ''

    return fname



'''
    Function to print file list
'''
def print_ls(filename_list):
    for x in filename_list:
        print(x)


'''
    Function to print the ll function output
'''
def print_ll(ll_out):
    if len(ll_out) > 0:
        filenm_len = str(2+max([len(ll_out[a0][-1]) for a0 in range(len(ll_out))]))
        size_len = str(max([len(ll_out[a0][1]) for a0 in range(len(ll_out))]))
        blk_sp = ' '*2
        print('total  {0}'.format(len(ll_out)))
        for row in ll_out:
            print(row[0] + blk_sp + ('{0:' + size_len + 's}').format(row[1]) + blk_sp +
                  row[2] + blk_sp + ('{0:' + filenm_len + 's}').format(row[3]))
    else:
        print('total  0')


'''
    Function to print cat output
'''
def print_cat(cat_out):
    try:
        for data in cat_out:
            print(data.decode('utf-8'))
    except Exception as e:
        return


'''
    Function to print user list
'''
def print_ulist(ulist):
    print('{0:20s}'.format('USERNAME') + 'USER_ID\n')

    for idx, name in enumerate(ulist):
        if name == '0':
            print('{0:20s}'.format('-') + str(idx))
        else:
            print('{0:20s}'.format(name) + str(idx))



'''
    This function breaks user command into pieces and strips any extra spaces
    and passes list of command pieces to command_parser() to analyse it
'''
def command_interpreter(command):
    #splitting command into its subparts, removing spaces
    command = command.split()
    command = [x.strip() for x in command]

    # temparary path
    filename = ''
    if len(command) == 0:
        return 0, ''

    if command[0] == 'touch':
        if len(command) > 1:
            filename = []
            for fname in command[1:]:
                filename.append(filename_validator(fname))
            command[1] = '#'
            command = command[0:2]
        else:
            return -1, ''
    elif command[0] == 'mkdir':
        if len(command) > 1:
            filename = []
            for fname in command[1:]:
                filename.append(dirname_validator(fname))
            command[1] = '#'
            command = command[0:2]
        else:
            return -1, ''
    elif command[0] == 'rm':
        if len(command) == 2:
            filename = filename_validator(command[1])
            command[1] = '#'
        elif len(command) == 3 and command[1] == '-r':
            filename = filename_validator(command[2])
            command[2] = '#'
        else:
            return -1, ''
    elif command[0] == 'cd':
        if len(command) == 1:
            command.append('$')
        elif len(command) == 2:
            filename = dirname_validator(command[1])
            command[1] = '#'
        else:
            return -1, ''
    elif command[0] == 'put':
        command_mod = []
        if len(command) >= 2:
            command_mod.append(command[0])
            command.pop(0)
            command_mod.append(' '.join(command))
            if Path(command_mod[1]).exists():
                filename = command_mod[1]
                command_mod[1] = '#'
                command = command_mod
            else:
                return -1, ''
        else:
            return -1, ''
    elif command[0] == 'get':
        if len(command) == 2:
            filename = dirname_validator(command[1])
            command[1] = '#'
        else:
            return -1, ''
    elif command[0] == 'mv':
        if len(command) == 3:
            filename = [dirname_validator(command[1])]
            command[1] = '#'
            filename.append(dirname_validator(command[2]))
            command[2] = '#'
        else:
            return -1, ''
    elif command[0] == 'cp':
        if len(command) == 3:
            filename = [dirname_validator(command[1])]
            command[1] = '#'
            filename.append(dirname_validator(command[2]))
            command[2] = '#'
        else:
            return -1, ''
    elif command[0] == 'ls':
        if len(command) == 1:
            command.append('$')
    elif command[0] == 'll':
        if len(command) == 1:
            command.append('$')
    elif command[0] == 'cat':
        if len(command) > 1:
            filename = command[1:]
            command[1] = '#'
            command = command[0:2]
        else:
            return -1, ''
    elif command[0] == 'deluser':
        if len(command) > 1:
            filename = command[1:]
            command[1] = '#'
            command = command[0:2]
    elif command[0] == 'chmod':
        if len(command) != 4:
            print('chmod needs 3 operands')
            return -1, ''
        else:
            filename = command[1:]
            command = command[0:1]


    return command_parser(command, cmd_parse_tree), filename



'''
    This function mimics user command promt and accepts user input 
    user input is then passed to interpreter to check if command is valid or not
'''
def user_terminal():

    try:
        # temporary declarations to check functionality ! TO BE REPLACED
        command = ''
        user = get_cur_user()


        #terminate user interface when command is empty
        while command != "exit":

            command = input('\n'+user+'@Virtual_file_system:'+get_cwd()+"$ ")
            status, filename = command_interpreter(command)

            if status == 1:
                create_vfs()
                mounted = 0
            elif status == 2:
                mounted = mount_vfs()
            elif status == 3:
                if len(filename) == 0:
                    print('missing filenames after \'touch\' command')
                else:
                    touch_cmd(list(filename))
            elif status == 4:
                filename_list = ls_cmd()
                print_ls(filename_list)
            elif status == 5:
                if len(filename) == 0:
                    print('Invalid path/filename !')
                else:
                    rm_cmd(filename)
            elif status == 6:
                if len(filename) == 0:
                    print('Invalid path/directory name !')
                else:
                    mkdir_cmd(list(filename))
            elif status == 7:
                if len(filename) == 0:
                    print('Invalid path/Directory name !')
                else:
                    cd_cmd(filename)
            elif status == 8:
                if len(filename) == 0:
                    print('Invalid path !')
                else:
                    rm_r_cmd(filename)
            elif status == 9:
                if len(filename) == 0:
                    print('Invalid path !')
                else:
                    put_cmd(filename)
            elif status == 10:
                if len(filename) == 0:
                    print('Invalid path !')
                else:
                    get_cmd(filename)
            elif status == 11:
                if len(filename) == 2:
                    mv_cmd(filename[0], filename[1])
                else:
                    print('Invalid command !')
            elif status == 12:
                if len(filename) == 2:
                    cp_cmd(filename[0], filename[1])
                else:
                    print('Invalid command !')
            elif status == 13:
                exit_cmd()
            elif status == 14:
                ll_out = ll_cmd()
                print_ll(ll_out)
            elif status == 15:
                cd_cmd('$')
            elif status == 17:
                cat_out = cat_cmd(list(filename))
                print_cat(cat_out)
            elif status == 18:
                print('Enter new user credentials - ')
                uname, passwd = get_usr_cred()
                adduser_cmd(uname, passwd)
            elif status == 19:
                deluser_cmd(filename)
            elif status == 20:
                chmod_cmd(filename[0], filename[1], filename[2])
            elif status == 21:
                ulist = ulist_cmd()
                print_ulist(ulist)
            elif status == 22:
                print(get_cwd())
            elif status == -1:
                print('Invalid command !')
    except Exception as e:
        print(traceback.format_exc())
        print('Fatal error occured !')
        user_terminal()
        return



'''
    Function to accept user credentials
'''
def get_usr_cred():
    print('Username : ', end='')
    username = input()
    passwd = getpass.getpass('Password : ')

    return username, passwd


'''
    Function to create drive
'''
def vfs_interface_init():
    if Path(drive_filename).is_file():
        mounted = 0
    else:
        mounted = -1

    while mounted != 2:
        if mounted == -1:
            print('File system not created !')
            print('* Use \"create vfs\" to create the file system')
            print('* Use \"mount\" command to load file system')
        elif mounted == 0:
            print('File system not mounted !')
            print('* Use \"mount\" command to load file system')
        elif mounted == 1:
            print('\nPlease login in order to continue...')
            mounted = user_login()

        if mounted < 1:
            cmd = input('>')
            if cmd == 'create vfs':
                status = create_vfs()
                if status == 0:
                    mounted = 0
            elif cmd == 'mount':
                if mounted != -1:
                    mounted = mount_vfs()




def user_login():
    logged = 0
    while logged == 0:
        uname, passwd = get_usr_cred()
        if check_usr_validity(uname, passwd):
            logged = 2
            set_cur_usr(uname)
        else:
            print('\nInvalid username/password. Please try again.')

    return logged


if __name__ == "__main__":
    #calling terminal
    init_filesystem()
    vfs_interface_init()
    user_terminal()