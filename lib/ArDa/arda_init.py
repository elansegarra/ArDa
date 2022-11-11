# This files contains functions that initialize various parts of the app
import os
import configparser
from datetime import date

def init_user():
    # This initializes the user directory and creates a basic config 
    #   file as well as a starting DB file

    # Create a user directory and others necessary for initialization
    os.mkdir('user')
    os.mkdir('user\\bib_files')
    root_path = str(os.getcwd())

    # Create a default config file
    config_file = configparser.ConfigParser()
    config_file["General Properties"]={
            "start_up_check_watched_folders": "False",
            "project_selection_cascade": "True"
            }
    config_file["Data Sources"]={
            "db_path": root_path+"\\user\\arda_db.sqlite"
            }
    config_file["Watch Paths"]={
            "path_001": root_path+"\\user"
            }
    config_file["Bib Paths"]={
            "all_bib": root_path+"\\user\\bib_files"
            }
    config_file["Design Defaults"]={}
    config_file["Other Variables"]={
            "last_check": str(date.today())
            }
    # Save the config file
    with open("user/config.ini","w") as file_object:
        config_file.write(file_object)

    quit()