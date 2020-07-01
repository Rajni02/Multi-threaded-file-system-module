'''
Program execution begins here
Contains a basic terminal based interface
'''
import os
import subprocess

if __name__ == "__main__":
    ui_exec_path = "python \"D:\\MTech CS\\sem2\\OS\\file_system_project\\venv\\vfs_user_interface.py\""
    os.system("start cmd.exe @cmd /k " + ui_exec_path)
