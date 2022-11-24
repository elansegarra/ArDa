# This define a class which allows for interacting with an ArDa database object

import sqlite3
import pandas as pd
from os.path import exists, isfile, join
from os import makedirs, listdir
from datetime import date
import ArDa.aux_functions as aux

class ArDa_DB:
    doc_vars = ['doc_id', 'title', 'year']
    proj_vars = ['proj_id', 'title', 'parent', 'children']

    def __init__(self):
        self.db = None

    def make_new_db(self, db_path):
        raise NotImplementedError

    def open_db(self, db_path):
        # Check if path is valid
        if (not exists(db_path)):
            raise FileNotFoundError
        self.db_path = db_path

    def add_doc_record(self, doc_dict):
        # Check if doc_id is included and grab new one if not
        if "doc_id" in doc_dict:
            # Check that the doc_id is not used by another record
            if (self.get_doc_record(doc_dict["doc_id"]) != None):
                print(f"Cannot add a document with id {doc_dict['doc_id']} because it already exists in db")
                raise FileExistsError
        else:
            doc_dict["doc_id"] = self.get_next_doc_id()

        # Check that the keys of the dictionary are all recognized
        # Putting in an added date if not found
        if 'Added' not in doc_dict:
            td = date.today()
            doc_dict['Added'] = td.year*10000 + td.month*100 + td.day

        # The rest of this function is implemented in the subclass

    def delete_doc_record(self, doc_id):
        raise NotImplementedError

    def update_doc_record(self, doc_dict):
        raise NotImplementedError

    def format_authors(self, authors):
        """
            This function formats the author text into a list of dicts of author details
            :param authors: string or list of strings of the authors
        """
        # Checking the var type of authors variable
        if isinstance(authors, str):
            if authors.find(" and ") != -1: # Checking if delimited by " and "s
                authors = authors.split(" and ")
            elif authors.find("\n") != -1:  # Checking if delimited by newlines
                authors = authors.split("\n")
            elif authors.find("; ") != -1:  # Checking if delimited by semicolons
                authors = authors.split("; ")
            else: 							# Treat as a single author
                authors = [authors]
        elif isinstance(authors, list):
            # If a list we assume each element is a separate author already
            authors = authors
        else:
            warnings.warn(f"Var type of author variable ({type(authors)}) is not recognized.")
            return

        # Creating base author/editor dictionary (which we add each name to)
        auth_entry = dict()
        # Creating a list of author entries (each a dict)
        auth_entries = []
        for auth_name in authors:
            if auth_name == "": continue
            # Trimming excess whitespace
            auth_name = auth_name.strip()
            auth_entry['full_name'] = auth_name
            # Checking for two part split separated by a comma
            if len(auth_name.split(", ")) == 2:
                auth_entry['last_name'] = auth_name.split(", ")[0]
                auth_entry['first_name'] = auth_name.split(", ")[1]
            else:
                # logging.debug(f"Name format of '{auth_name}' is atypical, has no commas or more than one.")
                print(f"Name format of '{auth_name}' is atypical, has no commas or more than one.")
                auth_entry['last_name'] = auth_name
                auth_entry['first_name'] = auth_name
            # Adding this entry to the list of authors
            auth_entries.append(auth_entry.copy())
        
        return auth_entries

    def get_doc_record(self, doc_id):
        raise NotImplementedError

    def get_next_doc_id(self):
        raise NotImplementedError

class ArDa_DB_SQL(ArDa_DB):
    def __init__(self):
        self.db_type = "sqllite"

    def make_new_db(self, db_path):
        # Check that path is valid and the file does not exist currently
        if (exists(db_path)):
            raise FileExistsError

        # Create the file and connect to it
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Create main document table
        c.execute("CREATE TABLE 'Documents' ( `doc_id` INTEGER NOT NULL, `favorite` TEXT, `read_date` INTEGER, "+
                    "`doc_type` TEXT, `abstract` TEXT, `add_date` INTEGER, `modified_date` INTEGER, `note` TEXT, "+
                    "`title` TEXT, `arxiv_id` TEXT, `chapter` TEXT, `citation_key` TEXT, `city` TEXT, `country` TEXT, "+
                    "`department` TEXT, `doi` TEXT, `edition` TEXT, `institution` TEXT, `isbn` TEXT, `issn` TEXT, "+
                    "`number` TEXT, `pages` TEXT, `pmid` TEXT, `journal` TEXT, `publisher` TEXT, `series` TEXT, "+
                    "`volume` TEXT, `year` INTEGER, `author_lasts` TEXT, `url` TEXT, `address` TEXT, `booktitle` TEXT, "+
                    "`crossref` TEXT, `month` TEXT, `organization` TEXT, `school` TEXT, `keyword` TEXT, `editor` TEXT, "+
                    "PRIMARY KEY(`doc_id`) )")
        # Create author table
        c.execute("CREATE TABLE 'Doc_Auth' ( `doc_id` INTEGER NOT NULL, `contribution` TEXT, `last_name` TEXT, "+
                    "`first_name` TEXT, `full_name` TEXT )")
        # Create document paths (ie to files) table
        c.execute("CREATE TABLE 'Doc_Paths' ( `doc_id` INTEGER, `full_path` TEXT )")
        # Create projects table
        c.execute("CREATE TABLE 'Projects' ( `proj_id` INTEGER NOT NULL, `proj_text` TEXT NOT NULL, `parent_id` INTEGER, "+
                    "`path` TEXT, `description` VARCHAR, `expand_default` INTEGER, `bib_built` INTEGER, "+
                    "`bib_path` TEXT, PRIMARY KEY(`proj_id`) )")
        # Create document project table
        c.execute("CREATE TABLE 'Doc_Proj' ( `doc_id` INTEGER NOT NULL, `proj_id` INTEGER NOT NULL)")
        
        conn.close()
        self.db_path = db_path

    def get_next_doc_id(self):
        # Returns the next available document id
        
        # Connect to the db and grab all document ids
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT doc_id FROM Documents")
        doc_ids = [a[0] for a in c.fetchall()]
        c.close()

        # Print the next available id (starting at 1)
        if len(doc_ids) == 0:
            return 1
        else:
            return max(doc_ids)+1

    def add_doc_record(self, doc_dict):
        # This function adds a new bib entry and assumes all keys in doc_dict 
        #   match a column in the DB exactly

        # First we do checks common to all class type (ie sql/obsidian/bib)
        super().add_doc_record(doc_dict)

        # Next we check to verify that there is not an entry at that doc_id already
        if self.get_doc_record(doc_dict["doc_id"]) is not None:
            print("Cannot add entry {doc_dict} because that doc_id is already there")
            raise FileExistsError

        unused_keys = aux.insertIntoDB(doc_dict, "Documents", self.db_path, debug_print=True)

    def get_doc_record(self, doc_id):
        # Connect to the db and grab the matching doc_id
        conn = sqlite3.connect(self.db_path)
        curs = conn.cursor()
        curs.execute(f"SELECT * FROM Documents WHERE doc_id = {doc_id}")
        doc_keys = [description[0] for description in curs.description]
        doc_vals = curs.fetchall()
        if len(doc_vals) == 0:
            return None
        elif len(doc_vals) == 1:
            doc_vals = doc_vals[0]
        else:
            print(f"Recieved more than one record for doc_id {doc_id}")
            print(doc_vals)
            raise NotImplementedError
        curs.close()

        # Assemble into a dictionary and drop None values
        doc_dict = dict(zip(doc_keys, doc_vals))
        doc_dict = {key:val for key, val in doc_dict.items() if val is not None}

        # Tack on other variables that are probably relevant (like authors)
        # TODO: gather author, project, and maybe path variables as well

        return doc_dict



class ArDa_DB_Obsid(ArDa_DB):
    def __init__(self):
        self.db_type = "obsidian"
        self.db_path = None

    def make_new_db(self, db_path):
        # Make the folder if it doesn't exist (and check if empty if it does exist)
        if exists(db_path):
            num_files = len([name for name in listdir(db_path) if isfile(join(db_path, name))])
            print(f"Found {num_files} files in {db_path}.")
            if num_files > 0:
                raise FileExistsError
        else:
            makedirs(db_path)
        self.db_path = db_path
    
    def parse_obsid_file(self, file_path):
        # Reads an obsidian file and returns a dictionary of the contents

        # Check if file exists (either as is or relative to db_path)
        if (self.db_path is not None) and (exists(self.db_path+"/"+file_path)):
            file_path = self.db_path+"/"+file_path
        elif (exists(file_path)):   pass
        else:                       raise FileNotFoundError

        # Read the file
        file_contents = {}
        with open(file_path) as f:
            lines = f.readlines()

        # Parse the yml
        assert lines[0].strip() == "---"
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                yml_line_end = i
                break
            line_vals = lines[i].split(":")
            file_contents[line_vals[0].strip()] = line_vals[1].strip()
            if len(line_vals) > 2:
                raise FormatError

        # Parse the rest of the file (break up by headings)
        h_num, h_title, h_body = 0, "No heading", ""
        print(yml_line_end)
        for i in range(yml_line_end+1, len(lines)):
            line = lines[i]
            if (len(line)>0) and (line[0] == "#"):
                file_contents["note_"+str(h_num)] = {"title": h_title, "body": h_body}
                h_num += 1
                h_title = line[1:]
                h_body = ""
            else:
                h_body += line
        # Storing last group 
        file_contents["note_"+str(h_num)] = {"title": h_title, "body": h_body}

        return file_contents




class ArDa_DB_Bib(ArDa_DB):
    def __init__(self):
        self.db_type = "bibtex"

    def make_new_db(self, db_path):
        # Make the folder if it doesn't exist (and check if empty if it does exist)
        if exists(db_path):
            num_files = len([name for name in listdir(db_path) if isfile(join(db_path, name))])
            print(f"Found {num_files} files in {db_path}.")
            if num_files > 0:
                raise FileExistsError
        else:
            makedirs(db_path)
        self.db_path = db_path

    def parse_bib_file(self, file_path):
        # Reads a bib file and returns a dictionary of the contents
        raise NotImplementedError