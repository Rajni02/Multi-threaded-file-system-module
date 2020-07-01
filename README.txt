Implemented a fixed size multi-threaded file system from very scratch level, which is supported by a few basic operations like touch, mkdir, cp, mv, rm etc.


---------------------------------------
1.1     FILE SYSTEM Constrains :
---------------------------------------
- This file system uses 64MB data on disc for its implementation. TO see the more detailed description of FILE System
  please take a look at 'CS_VirtualFileSystem.xlsx'
- All valid paths (relative and absolute, including filenames) are WITHOUT BLANK SPACES and special characters such as
  '\', '/', '#', '*', ']', '[', single quote and double quotes
- So far, the default user is always 'admin', and has access to edit everything except 'root' directory
- commands implemented : create, mount, touch, ls, rm, mkdir, cd, "put" and "get" (special commands), mv, cp, exit
  for more decription of syntax see the section below

--use command "python3.6 vfs_user_interface.py" to launch user interface to operate on file system




--------------------------------------------------------
1.2     USER INTERFACE COMMAND DISCRIPTION and SYNTAX
--------------------------------------------------------

1.2.1   create command ->

    Syntax : create vfs
    Description : Creates new file-system/drive (as described in 'CS_VirtualFileSystem.xlsx') stored in file named
                  'virtual_drive.csfs' (this is where entire drive is stored), with admin as default user and root as
                  default directory. If drive already exists, then its formatted.




1.2.2   mount command ->
    Syntax : mount
    Description : Mounts the existing drive into memory, gives error if the drive is missing. Mounting of drive is
                  necessary in order to operate over file system.




1.2.3   touch command ->
    Syntax : touch <filename1> <filename2> ...
    Description : creates an empty file with valid filename(cannot be a relative or absolute path) provided, in current
                  working directory




1.2.4   ls command ->
    Syntax : ls [-l]
    Description : prints list of files and directories present in current working directory
    example :
        $ ls
        [dir1]
        [dir2]
        file1
        file2

        All directory names are displayed as '[<dirname>]' and regular files are displayed as it is
		
		"ls -l" generates detailed file list




1.2.5   rm command ->
    Syntax : rm [-r] <filename/dirname>
    Description : rm <filename> removes a file from file-system
                  rm -r <dirname> removes a directory recursively



1.2.6   mkdir command ->
    Syntax : mkdir <dirname1> <dirname2>
    Description : creates a new directory within current working directory with name specified in <dirname_list> (cannot be
                    abs or relative path, must be just a filename)



1.2.7   cd command ->
    Syntax : cd [<path>, ..]
    Description : changes current working directory to the path specified (relative or absolute). One can use '..' as
                  path to go to parent directory
                  eg. :/Documents/Dir1 $ cd ..
                      :/Documents $



1.2.8   put command ->
    Syntax : put <external_file_path>
    Description : Checks if external_file provided in path exists, if it does, and has size <= 64KB, then creates the
                  copy of that file within current woring directory of drive.
                  eg. let "text1.txt" be a 10KB file residing at location - /Documents/text1.txt
                  then
                  :/dir1 $ put /Documents/text1.txt
                  :/dir1 $ ls
                  text1.txt

                  :/dir1 $




1.2.9   get command ->
    Syntax : get <internal_file_path>
    Description : Checks if the internal file path exists, if true then, writes that file to "external current working
                  directory"
                  eg. Assume the program is being executed from external path - /Downloads/programs/ (so this will be our
                  external cwd), and at internal file-system, we have,

                  :/dir1 $ ls
                  file_1.txt
                  file_2.bin

                  :/dir1 $ get file_1.txt

                  Last command will create file with name "file_1.txt" on location - /Downloads/programs/



1.2.10  move command ->
    Syntax : mv <source_path> <destination_path>
    Description : moves file/directory from source to detination (both paths can be absolute or relative)
                  if destination path is absent, then this works as rename operation


1.2.11  copy command ->
    Syntax : cp <source_path> <destination_path>
    Description : copies a source file (cannot be directory) to destination path (must be directory path, absolute or
                  relative)


1.2.12  exit command ->
    Syntax : exit
    Description : Unmounts the file system, and exits the user interface

	
1.2.13 ll command ->
	Syntax : ll
	Description : Displays detailed list of directories and files in current working directory. For each file/directory, 
					list shows permissions of current user, size of file in bytes(only for files), last modified date, and filename
	

1.2.14 cat command ->
	Syntax : cat <filename>
	Description : Displays content of file provided as argument. 
					eg. consider a file named 'f1' contains "data1 and data2" inside it.
					$ ls
					f1
					
					$ cat f1
					data1 and data2
					

1.2.15 'adduser' command (only available to admin) ->
	Syntax : adduser
	Description : Allows admin to add other users in filesystem (at most 7); username and password can be at most 16 characters long
					eg.
					$ adduser
					Enter user credentials :
					username : user1
					password : xxxx
					
				Next time, 'user1' can use proper credentials to log onto file-system

1.2.16 'deluser' command (only available to admin) ->
	Syntax : deluser
	Description : Allows admin to add other users in filesystem (at most 7)
					eg. 
					$ deluser user1 user2
					
				This deletes user1 and user2 from file-system.

				

