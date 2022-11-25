# This define a class which allows for interacting with an ArDa database object

import sqlite3
import pandas as pd
from os.path import exists, isfile, join
from os import makedirs, listdir
from datetime import date
import warnings
try: 
    import ArDa.aux_functions as aux
except ModuleNotFoundError:
    import lib.ArDa.aux_functions as aux

class ArDa_DB:

    def __init__(self):
        self.db = None

    def make_new_db(self, db_path):
        raise NotImplementedError

    def open_db(self, db_path):
        # Check if path is valid
        if (not exists(db_path)):
            raise FileNotFoundError
        self.db_path = db_path

    def add_table_record(self, doc_dict, table_name = "Documents"):
        """ This function adds the the record information passed into 
            one of the tables of the DB 

            :param doc_dict: A dictionary whose keys are the fields of the table
                    and whose values are the values to be added
            :param table_name: string with the table to update
        """
        # First we check that this is a table we can insert records into
        if table_name not in ['Documents', 'Projects', 'Doc_Proj', 'Doc_Paths', 
                                'Proj_Notes', 'Custom_Filters']:
            warnings.warn(f"Table name ({table_name}) not recognized.")
            return None

        # Then we standardize the document dictionary keys
        doc_dict = self.standardize_doc_dict_keys(doc_dict, table_name)

        if table_name == 'Documents':
            # Check if doc_id is included and grab new one if not
            if "doc_id" in doc_dict:
                # Check that the doc_id is not used by another record
                if (self.get_doc_record(doc_dict["doc_id"]) != None):
                    print(f"Cannot add a document with id {doc_dict['doc_id']} because it already exists in db")
                    raise FileExistsError
            else:
                doc_dict["doc_id"] = self.get_next_id("Documents")

            # Putting in an added date if not found
            if 'add_date' not in doc_dict:
                td = date.today()
                doc_dict['add_date'] = td.year*10000 + td.month*100 + td.day

            # Altering keyword delimiters if need be
            if "keyword" in doc_dict:
                if (doc_dict['keyword'].find(";")==-1) and (doc_dict['keyword'].find(",")!=-1):
                    doc_dict['keyword'] = doc_dict['keyword'].replace(",", ";")
        elif table_name == 'Projects':
            # Check if proj_id is included and grab new one if not
            if "proj_id" in doc_dict:
                # Check that the doc_id is not used by another record
                projs = self.get_table("Projects")
                used_proj_ids = projs.proj_id.values.tolist()
                if (doc_dict["proj_id"] in used_proj_ids):
                    print(f"Cannot add a project with id {doc_dict['proj_id']} because it already exists in db")
                    raise FileExistsError
            else:
                doc_dict["proj_id"] = self.get_next_id("Projects")
        elif table_name == 'Doc_Proj':
             # Check that it includes the only two necessary keys
            if ('doc_id' not in doc_dict) or ('proj_id' not in doc_dict):
                warnings.warn(f"Can't insert {doc_dict} into 'Doc_Proj' wihtout doc_id and proj_id")
                return None
        elif table_name == 'Doc_Paths':
            # Check that it includes the only two necessary keys
            if ('doc_id' not in doc_dict) or ('full_path' not in doc_dict):
                warnings.warn(f"Can't insert {doc_dict} into 'Doc_Paths' wihtout doc_id and full_path")
                return None
        elif table_name == 'Proj_Notes':
            raise NotImplementedError
        elif table_name == 'Custom_Filters':
            raise NotImplementedError

        # The rest of this function is implemented in the subclass
        return doc_dict

    def delete_doc_record(self, doc_id):
        raise NotImplementedError

    def update_record(self, doc_dict):
        raise NotImplementedError
    
    def get_table(self, table_name='Documents'):
        """ Extracts and returns the specified table """
        # Checking that a valid table name has been sent
        if table_name not in ['Documents', 'Fields', 'Projects', 'Doc_Auth', 'Doc_Proj_Ext',
                                'Doc_Proj', 'Doc_Paths', 'Proj_Notes', 'Custom_Filters']:
            warnings.warn(f"Table name ({table_name}) not recognized.")
            return pd.DataFrame()
        # Verify that a db is loaded
        if self.db_path is None:
            warnings.warn(f"Cannot grab the {table_name} table because no db is loaded.")
        
        # The rest of this function is implemented in the subclass

    def standardize_doc_dict_keys(self, doc_dict, table_name = "Documents"):
        """ This function standardizes the keys of the dictionary containing document info """

        # First make all keys lowercase
        doc_dict = {key.lower():value for key, value in doc_dict.items()}

        # Create map between header names and field names (of the associated table)
        field_df = pd.read_csv("lib//ArDa/Fields.csv")
        doc_fields = field_df[field_df.table_name==table_name]
        header_map = dict(zip(doc_fields.header_text.str.lower(), doc_fields.field))

        # Map all the keys using this dictionary
        doc_dict = {header_map.get(key, key):value for key, value in doc_dict.items()}

        # Check that the keys of the dictionary are all recognized
        recognizable_fields = set(header_map.keys()) | set(doc_fields.field) | {'author'}
        unrecognized_fields = set(doc_dict.keys()) - recognizable_fields
        recognized_fields = set(doc_dict.keys()) & recognizable_fields

        # Quick warning about unrecognized fields
        if len(unrecognized_fields) > 0:
            warnings.warn(f"When standardizing these fields were not recognized: {unrecognized_fields}")

        return doc_dict

    def format_authors(self, authors):
        """
            This function formats the author text into a list of dicts of author details
            :param authors: string or list of strings of the authors
        """
        # Return an empty list if None is passed
        if authors is None: return []

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

    def get_next_id(self, id_type):
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

    def open_db(self, db_path):
        return super().open_db(db_path)

    def get_next_id(self, table_type):
        # Returns the next available id from either the Documents or Projects tables
        
        # Connect to the db and grab all document/project ids
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if table_type == "Documents":
            c.execute("SELECT doc_id FROM Documents")
        elif table_type == "Projects":
            c.execute("SELECT proj_id FROM Projects")
        else:
            raise NotImplementedError
        ids_found = [a[0] for a in c.fetchall()]
        c.close()

        # Print the next available id (starting at 1)
        if len(ids_found) == 0:
            return 1
        else:
            return max(ids_found)+1

    def get_table(self, table_name='Documents', use_header_text = False):
        """ Extracts and returns the specified table """
        # Run parent class function which checks the inputs
        super().get_table(table_name)

        # Connect to the underlying sql db
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Simple extraction for a few tables
        if table_name in ['Fields', 'Projects', 'Doc_Proj', 'Doc_Auth', 'Documents',
                            'Proj_Notes', 'Custom_Filters', 'Doc_Paths']:
            c.execute(f'SELECT * FROM {table_name}')
            temp_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
        # Special extraction for extended doc project
        elif table_name == 'Doc_Proj_Ext':
            c.execute("SELECT p.*, dp.doc_id FROM Doc_Proj as dp Join Projects as p on dp.proj_id = p.proj_id")
            temp_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
        else:
            # Should not be possible to reach here (the parent function should have screened this out)
            raise NotImplementedError

        # Reordering the cols in the documents table (if that is one asked for)
        if table_name == "Documents":
            front_cols = ['doc_id', 'doc_type', 'title', 'year', 'journal']
            temp_df = temp_df[front_cols + [col for col in temp_df.columns if col not in front_cols]]

        # Checking if using header text for column labels
        if use_header_text:
            # Grab the fields associated with this table
            c.execute(f'SELECT * FROM Fields WHERE table_name = "{table_name}"')
            field_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
            field_to_header = dict(zip(field_df.field, field_df.header_text))
            field_to_header = {key:value for key, value in field_to_header.items() if value is not None}
            # Map the columns to their hearder version (if found)
            temp_df.columns = [field_to_header.get(field, field) for field in temp_df.columns]

        conn.close()
        return temp_df

    def add_table_record(self, doc_dict, table_name = "Documents"):
        # This function adds a new bib entry and assumes all keys in doc_dict 
        #   match a column in the DB exactly

        # First we do checks common to all class type (ie sql/obsidian/bib)
        doc_dict = super().add_table_record(doc_dict, table_name)
        if doc_dict is None: # ie the parent function found a problem
            return

        # Particular tweaks for "Documents" table insertion
        if table_name == "Documents":
            # Popping the author and editor fields (so they don't trigger unuser key warning)
            authors = doc_dict.pop("author", None)
            editors = doc_dict.pop("editor", None)

            # Adding information associated with authors/editors
            self.update_authors(doc_dict['doc_id'], authors)
            if editors is not None:
                self.update_authors(doc_dict['doc_id'], editors, as_editors=True)

        # Inserting this row into the appropriate database
        unused_keys = aux.insertIntoDB(doc_dict, table_name, self.db_path)

        # Notification of any unused keys
        if len(unused_keys) > 0:
            # logging.debug(f"Unused keys in bib entry (ID={bib_dict['ID']}) insertion: "+\
            #             f"{unused_keys}")
            print(f"Unused keys in bib entry (ID={doc_dict['doc_id']}) insertion: "+\
                        f"{unused_keys}")

    def update_record(self, cond_dict, column_name, new_value, table_name = "Documents",
                            debug_print = False):
        """
            This function updates a single cell in a specified table

            :param cond_dict: A dictionary whose keys are the fields of the table
                    and whose values are values to condition on. Eg if passed
                    {'doc_id':4, 'proj_id':2}, then all rows with doc_id==4 and proj_id==2
                    will be updated in the DB.
                    In total this will execute:
                    UPDATE table_name SET column_name = new_value WHERE cond_dict
            :param column_name: string indicating the column to update
            :param new_value: the value to be updated with
            :param table_name: string with the table to update
        """
        aux.updateDB(cond_dict, column_name, new_value, db_path=self.db_path, 
                        table_name=table_name, debug_print=debug_print)
        
    def add_rem_doc_from_project(self, doc_id, proj_id, action):
        """ Add or remove a document from a specified group
        
            :param doc_id: int indicating which document this is about
            :param proj_id: int indicating which project this is in reference to
            :param action" str either "add" or "remove" indicating the action to perform
        """
        # Check that the doc_id and proj_id refer to actual objects
        all_doc_ids = self.get_table("Documents")['doc_id'].values.tolist()
        all_proj_ids = self.get_table("Projects")['proj_id'].values.tolist()
        if doc_id not in all_doc_ids:
            warnings.warn(f"Cannot add doc {doc_id} to project {proj_id} because doc_id doesn't exist")
            return
        if proj_id not in all_proj_ids:
            warnings.warn(f"Cannot add doc {doc_id} to project {proj_id} because proj_id doesn't exist")
            return

        # Perform the specified action
        if action == "add":
            self.add_table_record({'doc_id': doc_id, 'proj_id': proj_id}, "Doc_Proj")
        elif action == "remove":
            aux.deleteFromDB({'doc_id': doc_id, 'proj_id': proj_id}, "Doc_Proj", self.db_path)
        else:
            print(f"Cannot add/remove document because the action, {action}, was not recognized.")
            raise NotImplementedError


    def update_authors(self, doc_id, authors, as_editors=False):
        """
            This function updates the authors associated with the passed doc ID
            :param doc_id: int indicating which document to change
            :param authors: string or list of strings of the authors.
            :param as_editors: boolean indicating whether these are editors (true)
                    or authors (false)
        """
        # Formatting the authors variables into a list of dict of author details
        auth_list = super().format_authors(authors)

        # Adding in other variables based off the other passed information
        for auth in auth_list:
            auth['doc_id'] = doc_id
            auth['contribution'] = "Editor" if as_editors else "Author"

        # First we delete all the authors (or editors) currently associated with this doc
        del_cond_key = {'doc_id':doc_id, 'contribution':"Editor" if as_editors else "Author"}
        aux.deleteFromDB(del_cond_key, 'Doc_Auth', self.db_path, force_commit=True)
        # Then add the authors back to the author table (assuming nonempty)
        if len(auth_list) > 0:
            aux.insertIntoDB(auth_list, 'Doc_Auth', self.db_path)

        # Updating the Documents table
        if not as_editors:
            # Creating list of last names for authors
            last_names = ", ".join([auth['last_name'] for auth in auth_list])
            aux.updateDB({'doc_id':doc_id}, column_name="author_lasts",
                            new_value=last_names, db_path=self.db_path)
        else:
            # Creating list of full names for editors
            full_names = "; ".join([auth['full_name'] for auth in auth_list])
            aux.updateDB({'doc_id':doc_id}, column_name="editor",
                            new_value=full_names, db_path=self.db_path)

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
    
    def open_db(self, db_path):
        # First execute all commands common across db types
        super().open_db(db_path)

        # Now we read and load the doc info from the obsidian files

    
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
                raise NotImplementedError

        # Parse the rest of the file (break up by headings)
        h_num, h_title, h_body = 0, "No heading", ""
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