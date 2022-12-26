# This define a class which allows for interacting with an ArDa database object

import sqlite3
import pandas as pd
from os.path import exists, isfile, join
from os import makedirs, listdir
from datetime import date
import warnings, logging
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
                    logging.debug(f"Cannot add a document with id {doc_dict['doc_id']} because it already exists in db")
                    raise FileExistsError
            else:
                doc_dict["doc_id"] = self.get_next_id("Documents")

            # Adding some default values if nothing is found
            doc_dict['title'] = doc_dict.get("title", "New Title")
            # doc_dict['Authors'] = doc_dict.get("Authors", "Author Last, Author First")
            # doc_dict['doc_type'] = doc_dict.get("doc_type", "Article")
            # doc_dict['year'] = doc_dict.get("year", None)
            td = date.today()
            doc_dict['add_date'] = doc_dict.get('add_date', td.year*10000 + td.month*100 + td.day)
            
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
                    logging.debug(f"Cannot add a project with id {doc_dict['proj_id']} because it already exists in db")
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
            # Check that it includes all three necessary keys
            if ('doc_id' not in doc_dict) or ('proj_id' not in doc_dict) or ('proj_note' not in doc_dict):
                warnings.warn(f"Can't insert {doc_dict} into 'Doc_Paths' wihtout doc_id and full_path")
                return None
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

    def standardize_doc_dict_keys(self, doc_dict, table_name = "Documents", 
                header_or_field = "field"):
        """ This function standardizes the keys of the passed dictionary
        
            :param doc_dict: (dict) dictionary whose keys are to be standardized
            :param table_name: (str) indicates what kind of table should be referenced
            :param header_or_field: (str) indicates whether to make them header text 
                keys ("header") or field keys ("field")
        """
        # Get the fields table for creating appropriate keys
        field_df = pd.read_csv("lib//ArDa/Fields.csv")
        doc_fields = field_df[field_df.table_name==table_name]

        if header_or_field == "field":
            # First make all keys lowercase
            doc_dict = {key.lower():value for key, value in doc_dict.items()}

            # Create map between header names and field names (of the associated table)
            header_map = dict(zip(doc_fields.header_text.str.lower(), doc_fields.field))

            # Map all the keys using this dictionary
            doc_dict = {header_map.get(key, key):value for key, value in doc_dict.items()}

            # Check that the keys of the dictionary are all recognized
            recognizable_fields = set(header_map.keys()) | set(doc_fields.field) | {'author'}
            unrecognized_fields = set(doc_dict.keys()) - recognizable_fields
            recognized_fields = set(doc_dict.keys()) & recognizable_fields
        elif header_or_field == "header":
            # Create map between field names and header names (of the associated table)
            field_map = dict(zip(doc_fields.field, doc_fields.header_text))

            # Map all the keys using this dictionary
            doc_dict = {field_map.get(key, key):value for key, value in doc_dict.items()}

            # Check that the keys of the dictionary are all recognized
            recognizable_fields = set(field_map.keys()) | set(doc_fields.header_text)
            unrecognized_fields = set(doc_dict.keys()) - recognizable_fields
            recognized_fields = set(doc_dict.keys()) & recognizable_fields
        else:
            logging.debug(f"The standardization goal {header_or_field} was not recognized.")
            raise NotImplementedError

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
                logging.debug(f"Name format of '{auth_name}' is atypical, has no commas or more than one.")
                auth_entry['last_name'] = auth_name
                auth_entry['first_name'] = auth_name
            # Adding this entry to the list of authors
            auth_entries.append(auth_entry.copy())
        
        return auth_entries

    def get_projs_docs(self, proj_ids, cascade = False):
        """ This function returns a list of document ids that are in the 
            indicated project(s) (and of all children projects if cascade specified)
        """
        # Some initial checks/tweaks
        if not isinstance(proj_ids, list):
            proj_ids = [proj_ids]

        # Add any children projects if specified
        if cascade:
            for proj_id in proj_ids:
                proj_ids = proj_ids + self.get_proj_children(proj_id, include_x_children=99)

        # Return list of all documents associated with any of these projects
        all_docs = self.get_table("Doc_Proj")
        proj_docs = all_docs[all_docs.proj_id.isin(proj_ids)].doc_id.values.tolist()
        proj_docs = list(set(proj_docs))  # Removing duplicates
        return proj_docs

    def get_proj_children(self, proj_id, include_x_children = 1, proj_table = None):
        """ Returns the proj_ids of all children projects (and their childrens
            children etc) down to the level specified.

            :param proj_id: (int) identified the main project
            :param include_x_children: (int) >=0, indicates the generations to go down
                eg =1 means it will return list of children projects of proj_id. 
                eg =2 means it will return them as well as children of children, etc
            :param proj_table: (df) table containing project info, will be gatherered automatically
        """
        # Quick argument checks
        msg = "Argument include_x_children must be a non-negative integer"
        assert (isinstance(include_x_children, int) & include_x_children >=0), msg
        
        if proj_table is None:
            # Grab the table once and pass to future recursive calls
            proj_table = self.get_table("Projects")
        
        # Gather the ids of any proj who is a child of the indicated project
        proj_children = proj_table[proj_table.parent_id == proj_id].proj_id.values.tolist()

        # Stop recursion if this is the last set of children
        if include_x_children == 1:
            return proj_children
        # Otherwise recurse over every child
        all_children = proj_children
        for proj_child in proj_children:
            all_children = all_children + self.get_proj_children(proj_child, 
                                                include_x_children-1, proj_table)
        return all_children

    def get_doc_record(self, doc_id):
        raise NotImplementedError

    def get_next_id(self, id_type):
        raise NotImplementedError

    def write_bib_file(self, doc_ids, filename, fields_included = None):
        """
            This function writes a bib file using all the bib information of all
            the doc ids passed.

            :param doc_ids: list of ints indicating which doc IDs to include
            :param filename: string of the name of the file (including the path)
            :param fields_included: list of str indicating which fields to include
        """
        # Default fields to include
        if fields_included == None:
            fields_included = ['title', 'year', 'journal', 'pages', 'number',
                                'chapter', 'city', 'edition', 'institution',
                                'publisher', 'series', 'volume', 'editor', 'author',
                                'booktitle']

        # Grabbing relevant tables and setting index for ease
        author_db = self.get_table("Doc_Auth")
        doc_df = self.get_table("Documents")
        doc_df.set_index('doc_id', inplace=True)

        # Opening file writing stream
        f = open(filename, 'wb')

        for doc_id in doc_ids:
            # Gather the bib info associated with the doc ID (or skipping if not found)
            try:
                bib_info = doc_df.loc[doc_id].copy()
            except KeyError:
                logging.debug(f"WARNING: No bib record found for doc ID {doc_id}, skipping.")
                continue

            # Verify that the document type and key are present
            if ('doc_type' not in bib_info) | (bib_info['doc_type'] in [None, ""]):
                logging.debug(f"Document type not found in bib info for doc ID {doc_id}. Using 'article'.")
                bib_info['doc_type']="article"
            if ('citation_key' not in bib_info) | (bib_info['citation_key'] in [None, ""]):
                cite_key = f"doc_{str(doc_id).zfill(6)}"
                logging.debug(f"Citation key blank or not found for doc ID {doc_id}. Using {cite_key}.")
                bib_info['citation_key'] = cite_key

            # Print the header for the entry
            line = f"@{bib_info['doc_type']}{{{bib_info['citation_key']},\n"
            f.write(line.encode('utf8'))

            # Some field specific formatting
            if ("year" in bib_info):
                if bib_info['year'] is None:
                    bib_info['year'] = ""
                elif not isinstance(bib_info['year'], str):
                    bib_info['year'] = str(int(bib_info['year']))
            if ("author" in fields_included):
                auth_rows = author_db.contribution == "Author" # Ignoring editors
                author_list = author_db[auth_rows & (author_db.doc_id == doc_id)].full_name.to_list()
                bib_info['author'] = " and ".join(author_list)
            if (bib_info.get("editor", None) is not None):
                bib_info['editor'] = bib_info['editor'].replace(";", " and")

            # Iterate over all the fields and print any that are found
            for field in fields_included:
                if (field in bib_info) and (bib_info[field] != None) and (bib_info[field] != ""):
                    line = f'\t{field.ljust(12)} = {{{bib_info[field]}}},\n'
                    # TODO: Implement better way to handle special characters
                    line = line.replace("&", "\&")
                    f.write(line.encode('utf8'))

            f.write("}\n".encode('utf8'))
        f.close()
        logging.debug(f"Bibfile, {filename}, successfully written.")

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
        # Create a document and project notes table
        c.execute("CREATE TABLE 'Proj_Notes' ( `doc_id` INTEGER NOT NULL, `proj_id` INTEGER NOT NULL, `proj_note` TEXT NOT NULL )")
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

    def get_docs_projs(self, doc_ids, full_path = False, ignore_x_parents = 0):
        # This function returns a dictionary of all the projects that the currently
        #    selected document is in. Currently only those for the first ID (if multiple are selected)
        
        # Get all the project ids associated with the passed doc_ids
        projs = self.get_table("Doc_Proj")
        proj_ids = projs[projs.doc_id.isin(doc_ids)].proj_id.values.tolist()
        proj_ids = list(set(proj_ids))  # Removing duplicates

        # Get the full path names for each project
        if full_path:
            proj_ids = {proj_id:self.get_proj_full_path(proj_id, ignore_x_parents) for proj_id in proj_ids}

        return proj_ids

    def get_proj_full_path(self, proj_id, ignore_x_parents = 0, path_delim = "/"):
        """ This extracts the full path of the indicated project  and lops off
            the top x parents specified.
        """
        # Grab all the projects (and reset index for ease)
        all_projs = self.get_table("Projects")
        all_projs.set_index('proj_id', inplace=True)
        # Iterate up the tree until hitting the root
        curr_proj_id = proj_id
        curr_proj_id = proj_id
        full_path = [all_projs.loc[curr_proj_id].proj_text]
        while all_projs.loc[curr_proj_id].parent_id != 0:
            curr_proj_id = all_projs.loc[curr_proj_id].parent_id
            full_path.insert(0, all_projs.loc[curr_proj_id].proj_text)
            
        # Rolling back and removing the top number of parents specified
        if ignore_x_parents > 0:
            full_path = full_path[ignore_x_parents:]
        
        return path_delim.join(full_path)

    def add_table_record(self, doc_dict, table_name = "Documents"):
        # This function adds a new bib entry and assumes all keys in doc_dict 
        #   match a column in the DB exactly

        # First we do checks common to all class type (ie sql/obsidian/bib)
        doc_dict = super().add_table_record(doc_dict, table_name)
        if doc_dict is None: # ie the parent function found a problem
            return

        # Particular tweaks for "Documents" table insertion (before insertion)
        if table_name == "Documents":
            # Popping the author and editor fields (so they don't trigger unuser key warning)
            authors = doc_dict.pop("author", None)
            editors = doc_dict.pop("editor", None)

        # Inserting this row into the appropriate database
        unused_keys = aux.insertIntoDB(doc_dict, table_name, self.db_path)

        # Particular tweaks for "Documents" table insertion (after insertion)
        if table_name == "Documents":
            # Adding information associated with authors/editors
            self.update_authors(doc_dict['doc_id'], authors)
            if editors is not None:
                self.update_authors(doc_dict['doc_id'], editors, as_editors=True)

        # Notification of any unused keys
        if len(unused_keys) > 0:
            # logging.debug(f"Unused keys in bib entry (ID={bib_dict['ID']}) insertion: "+\
            #             f"{unused_keys}")
            logging.debug(f"Unused keys in bib entry (ID={doc_dict['doc_id']}) insertion: "+\
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
            aux.deleteFromDB({'doc_id': doc_id, 'proj_id': proj_id}, "Doc_Proj", self.db_path, True)
        else:
            logging.debug(f"Cannot add/remove document because the action, {action}, was not recognized.")
            raise NotImplementedError

    def delete_doc_record(self, doc_id):
        """ Removes the specified document record across all relevant tables """
        
        cond_key = {'doc_id':doc_id}
        aux.deleteFromDB(cond_key, 'Documents', self.db_path, force_commit=True)
        aux.deleteFromDB(cond_key, 'Doc_Paths', self.db_path, force_commit=True)
        aux.deleteFromDB(cond_key, 'Doc_Auth', self.db_path, force_commit=True)
        aux.deleteFromDB(cond_key, 'Doc_Proj', self.db_path, force_commit=True)

    def delete_project(self, project_id, children_action = "reassign"):
        """
            This method deletes a project (and its associations)
            :param project_id: int indicating the ID of the project to delete
            :param children_action: str indicating how to handle project children
                        "reassign": Assigns any childre to the parent of the deleted project
                        "delete": Delete children projects as well
        """
        # Grabbing the project table
        projs = self.get_table("Projects")
        # Resetting the index so it matches the project id
        projs.set_index('proj_id', drop=False, inplace=True)
        # Extracting the parent of the current project
        parent_id = projs.at[project_id, 'parent_id']

        # Extracting any children of this project
        child_ids = list(projs[projs['parent_id']==project_id]['proj_id'])
        # Iterate over the projects children and perform the appropriate action
        logging.debug(f"Updating child project(s) of project {project_id} ({children_action}):")
        for child_id in child_ids:
            if children_action == "reassign":
                logging.debug(f"Update project {child_id} from child of {project_id} to child of {parent_id}")
                cond_key = {'proj_id': child_id}
                self.update_record(cond_key, "parent_id", parent_id, table_name="Projects")
            elif children_action == "delete":
                logging.debug(f"Deleting project {child_id} (Still needs to be implemented).")
                raise NotImplementedError
            else:
                warnings.warn(f"Unrecognized children action, {children_action}, "+\
                                "passed to deleteProject().")
                return
        
        # Deal with the documents associated with this project
        logging.debug(f"Updating document(s) of project {project_id} ({children_action}):")
        if children_action == "reassign":
            # Iterate over all the associated documents and change their association to the parent
            proj_docs = self.get_projs_docs(project_id)
            logging.debug(f"Assigning docs {proj_docs} from project {project_id} to project {parent_id}")
            for doc_id in proj_docs:
                self.update_record({'proj_id': project_id, 'doc_id': doc_id}, "proj_id", 
                                    new_value=parent_id, table_name="Doc_Proj")
        elif children_action == "delete":
            # Delete all associations with this project
            logging.debug(f"Deleting all docs {proj_docs} associations with project {project_id}")
            aux.deleteFromDB({'proj_id': project_id}, "Doc_Proj", self.db_path, force_commit=True)

        # Delete the project entry
        aux.deleteFromDB({'proj_id': project_id}, "Projects", self.db_path, force_commit=True)

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
            aux.updateDB({'doc_id':doc_id}, column_name="author_lasts", new_value=last_names, 
                        db_path=self.db_path, table_name= "Documents")
        else:
            # Creating list of full names for editors
            full_names = "; ".join([auth['full_name'] for auth in auth_list])
            aux.updateDB({'doc_id':doc_id}, column_name="editor",
                            new_value=full_names, db_path=self.db_path)

    def merge_doc_records(self, doc_id_1, doc_id_2, value_dict, id_dict = None,
                        proj_union = True):
        """
            This function will merge two bib entries into a single one.

            :param doc_id_1: int
            :param doc_id_2: int
            :param value_dict: dictionary of field value pairs (holds info to be
                    put in the new bib entry that results)
            :param id_dict: dictionary of field doc_id pairs indicating which doc_id
                    the field should be grabbed from for the new bib entry
            :param proj_union: boolean indicating whether to assign new bib to all
                    projects that both docs were assigned (True) or just those for
                    the main doc (False)
        """
        # Establishing base doc_id (that for the mered entry) and other id
        bdoc_id = id_dict.get('doc_id', None)
        if (bdoc_id == None) or ((bdoc_id != doc_id_1) and (bdoc_id != doc_id_2)):
            warnings.warn("Main doc ID is either not defined or different from passed IDs.")
            return
        other_doc_id = (doc_id_2 if (doc_id_1 == bdoc_id) else doc_id_1)

        # Grabbing the fields in the Documents table
        doc_field_df = self.get_table("Fields")
        doc_field_df = doc_field_df[doc_field_df['table_name']=="Documents"]

        # Dealing with Documents table (iterate over it's fields)
        cond_key = {'doc_id':bdoc_id}
        skip_fields = ['doc_id']
        for index, row in doc_field_df.iterrows():
            field = row['field']
            if field in skip_fields:    continue
            # Update with value in value_dict if it is there
            if field in value_dict:
                aux.updateDB(cond_key, field, value_dict[field], self.db_path)
                # self.updateDocViewCell(bdoc_id, row['header_text'], value_dict[field])

        # Dealing with Authors (only need to if chose the other doc's authors)
        if ('author_lasts' in id_dict) and (id_dict['author_lasts'] != bdoc_id):
            # First we remove the old author information (associated with bdoc_id)
            aux.deleteFromDB({'doc_id':bdoc_id, 'contribution':"Author"}, 
                            "Doc_Auth", self.db_path, force_commit=True)
            # Then we copy the author info (from other_doc_id) over to the base doc id
            aux.updateDB({'doc_id': other_doc_id, 'contribution':"Author"}, 
                        'doc_id', bdoc_id, self.db_path, table_name='Doc_Auth')
        
        # Dealing with Editors (only need to if chose the other doc's editors)
        if ('editor' in id_dict) and (id_dict['editor'] != bdoc_id):
            # First we remove the old editor information (associated with bdoc_id)
            aux.deleteFromDB({'doc_id':bdoc_id, 'contribution':"Editor"}, 
                            "Doc_Auth", self.db_path, force_commit=True)
            # Then we copy the author info (from other_doc_id) over to the base doc id
            aux.updateDB({'doc_id': other_doc_id, 'contribution':"Editor"}, 
                        'doc_id', bdoc_id, self.db_path, table_name='Doc_Auth')

        # Dealing with Doc_Paths (only need to if chose the other doc's filepaths)
        if ('file_path' in id_dict) and (id_dict['file_path'] != bdoc_id):
            # First we remove the old file path information (associated with bdoc_id)
            aux.deleteFromDB(cond_key, "Doc_Paths", self.db_path, force_commit=True)
            # Then we copy the author info (from other_doc_id) over to the base doc id
            aux.updateDB({'doc_id': other_doc_id}, 'doc_id', bdoc_id, self.db_path, table_name='Doc_Paths')

        # Dealing with Doc_Proj (if membership union is specified)
        if proj_union:
            # Copy the project membership of the other document
            aux.updateDB({'doc_id': other_doc_id}, 'doc_id', bdoc_id, self.db_path, table_name='Doc_Proj')

        # Finally we delete any remnants of the old bib entry
        self.delete_doc_record(other_doc_id)

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
            logging.debug(f"Recieved more than one record for doc_id {doc_id}")
            logging.debug(doc_vals)
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
            logging.debug(f"Found {num_files} files in {db_path}.")
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
            logging.debug(f"Found {num_files} files in {db_path}.")
            if num_files > 0:
                raise FileExistsError
        else:
            makedirs(db_path)
        self.db_path = db_path

    def parse_bib_file(self, file_path):
        # Reads a bib file and returns a dictionary of the contents
        raise NotImplementedError