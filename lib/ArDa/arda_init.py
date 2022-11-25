# This files contains functions that initialize various parts of the app
import os, sqlite3
import configparser
from datetime import date
import ArDa.arda_db as adb
import pandas as pd

def init_user():
    # This initializes the user directory and creates a basic config 
    #   file as well as a starting DB file

    # Create a user directory and others necessary for initialization
    os.mkdir('user')
    os.mkdir('user\\bib_files')
    os.mkdir('user\\backups')
    root_path = str(os.getcwd())

    # Create a default config file
    config_file = configparser.ConfigParser()
    config_file["General Properties"]={
            "start_up_check_watched_folders": "False",
            "project_selection_cascade": "True",
            "file_found_action" : "Do Nothing"
            }
    config_file["Data Sources"]={
            "db_path": root_path+"\\user\\user_db.sqlite"
            }
    config_file["Watch Paths"]={
            "path_001": root_path+"\\user"
            }
    config_file["Bib"]={
            "all_bib_path": root_path+"\\user\\bib_files",
            "bib_gen_frequency": "On App Start" 
            }
    config_file["Backups"]={
            "backups_folder": root_path+"\\user\\backups",
            "backups_number": 10,
            "backups_frequency": "Daily"
    }
    config_file["Design Defaults"]={}
    config_file["Other Variables"]={
            "last_check": str(date.today())
            }
    # Save the config file
    with open("user/config.ini","w") as file_object:
        config_file.write(file_object)

    # Create a new blank sql db
    blank_db = adb.ArDa_DB_SQL()
    db_path = root_path+'\\user\\user_db.sqlite'
    print(f"Creating new empty sql lite db at: {db_path}")
    blank_db.make_new_db(db_path)

    # Opening connection to new DB to add app specific tables
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Creating the custom filters table and filling it with defaults
    c.execute("CREATE TABLE 'Custom_Filters' ( 'filter_id' INTEGER, 'filter_name' TEXT, 'filter_code' TEXT,"+
                "PRIMARY KEY (filter_id))")
    c.execute("INSERT INTO Custom_Filters VALUES "+
            "(0, 'All Documents', ''), (1,'Currently Reading', 'who who'), "+
            "(2, 'Unread Documents', 'read == false'), (3,'Read Documents', 'read == true')")
    conn.commit()

    # Create fields table and populate it with the fields.csv file data (essentially default values)
    c.execute("CREATE TABLE 'Fields' ( `table_name` TEXT, `field` TEXT, `diary_table_order` INTEGER, "+
                "`task_table_order` INTEGER, `header_text` TEXT, `var_type` TEXT, `meta_widget_name` TEXT, "+
                "`col_width` INTEGER, `include_bib_field` INTEGER, `doc_table_order` INTEGER, "+
                "`meta_article_order` INTEGER, `meta_book_order` INTEGER )")
    field_df = pd.read_csv(str(os.getcwd())+'\\lib\\ArDa\\Fields.csv')
    field_df.fillna({'meta_widget_name':"", }, inplace=True)
    field_data = list(field_df.itertuples(index=False, name=None))
    insert_stmt = "INSERT INTO Fields VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"
    c.executemany(insert_stmt, field_data)
    conn.commit()
    conn.close()

    # Add a few documents to start the DB off with something in it
    blank_db.add_table_record({'doc_type': 'article',
            'title':"A Difficulty in the Concept of Social Welfare",
            'author':"Arrow, Kenneth J.", 'journal':"Journal of Political Economy",
            'volume':58, 'number':4, 'pages':"328--346",
            'year':1950, 'doi':"https://doi.org/10.1086/256963"})
    blank_db.add_table_record({'doc_type': 'book',
            'title':"Probabilistic Reasoning in Intelligent Systems: Networks of Plausible Inference",
            'author':"Pearl, Judea", 'publisher':"Morgan Kaufmann Publishers Inc.",
            'address':"San Francisco, CA, USA", 'year':1988})
    blank_db.add_table_record({'doc_type': 'article',
            'title':"Sample Selection Bias as a Specification Error",
            'author':"Heckman, James J.", 'journal':"Econometrica",
            'volume':47, 'number':1, 'pages':"153--161",
            'year':1979, 'doi':"http://dx.doi.org/10.2307/1912352"})
    blank_db.add_table_record({'doc_type': 'article',
            'title':"The State of Applied Econometrics - Causality and Policy Evaluation",
            'author':"Athey, Susan; Imbens, Guido W.", 'journal':"Journal of Economic Perspectives",
            'volume':31, 'number':2, 'pages':"3--32",
            'year':2017, 'doi':"https://doi.org/10.1257/jep.31.2.3"})
    # Add a few projects/groups to illustrate behavior
    blank_db.add_table_record({'proj_id':1,'proj_text': "Sample Group 1", 'parent_id':0, 'expand_default':1,
                "description": "This is one project or group"}, "Projects")
    blank_db.add_table_record({'proj_id':2,'proj_text': "Sample Subgroup", 'parent_id':1,
                "description": "This is another project or group under group 1"}, "Projects")
    blank_db.add_table_record({'proj_id':3,'proj_text': "Sample Group 3", 'parent_id':0,
                "description": "This is yet another group, go wild."}, "Projects")
    # Add some of the docs to these projects
