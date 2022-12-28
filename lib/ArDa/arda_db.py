# This define a class which allows for interacting with an ArDa database object

import pandas as pd
from os.path import exists, isfile, join
from os import makedirs, listdir
from datetime import date, datetime
import warnings, logging

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

    ## Status/Attribute Extraction Functions #######################
    ################################################################

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

    def get_doc_record(self, doc_id):
        raise NotImplementedError

    def get_next_id(self, id_type):
        raise NotImplementedError

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

    def get_projs_docs(self, proj_ids, cascade = False):
        """ This function returns a list of document ids that are in the 
            indicated project(s) (and of all children projects if cascade specified)
        """
        # Some initial checks/tweaks
        if not isinstance(proj_ids, list):
            proj_ids = [proj_ids]

        # Add any children projects if specified
        if cascade:
            all_proj_ids = []
            for proj_id in proj_ids:
                all_proj_ids = all_proj_ids + [proj_id] + self.get_proj_children(proj_id, include_x_children=99)
            proj_ids = list(set(all_proj_ids))

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
    
    def get_topo_list_proj_children(self, parent_proj_id, indent_txt = "", 
                    project_df = None, ignore_list = [], indent_level = 0):
        """
            Returns a topologically sorted lists of all descendant projects (both a list
            of project names and a corresponding list of project ids)

            :param parent_proj_id: (int) starting project ID (pass 0 for all projects)
            :param indent_text: (str) used for indentation of children if desired
            :param proj_df: (DataFrame) with all project information (will grab if not passed)
            :param ignore_list: any id's in this list will be ignored (along with their children)
            :param indent_level: (int) for tracking indent level, should call with 0
        """
        # Some initialization such as grabbing the project dataframe if not passed
        if project_df is None:
            project_df = self.get_table("Projects")
        proj_text_list, proj_id_list = [], []

        # Select only the children of the current parent
        children = project_df[project_df.parent_id==parent_proj_id]\
                            .sort_values('proj_text')
        # Add each child and any of their children (and their children...)
        for p in range(children.shape[0]):
            child_id = children.iloc[p]['proj_id']
            # Skip any children in the ignore list
            if child_id in ignore_list:
                continue
            # Adding the project text and id
            proj_text_list += [indent_txt*indent_level+children.iloc[p]['proj_text']]
            proj_id_list += [child_id]
            # Getting texts and ids for descendants
            child_text_list, child_id_list = self.get_topo_list_proj_children(child_id,
                            indent_txt, project_df = project_df,
                            ignore_list=ignore_list, indent_level=indent_level+1)
            # Adding them to our current lists
            proj_text_list += child_text_list
            proj_id_list += child_id_list
        return proj_text_list, proj_id_list

    ## Record Adding/Seleting/Editing Functions ####################
    ################################################################

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
            warnings.warn(f"Cannot add/rem doc {doc_id} to/from project {proj_id} because doc_id doesn't exist")
            return
        if proj_id not in all_proj_ids:
            warnings.warn(f"Cannot add/rem doc {doc_id} to/from project {proj_id} because proj_id doesn't exist")
            return

        # Perform the specified action
        if action == "add":
            self.add_table_record({'doc_id': doc_id, 'proj_id': proj_id}, "Doc_Proj")
        elif action == "remove":
            self.delete_table_record({'doc_id': doc_id, 'proj_id': proj_id}, "Doc_Proj")
        else:
            logging.debug(f"Cannot add/remove document because the action, {action}, was not recognized.")
            raise NotImplementedError

    ## Auxiliary Functions #########################################
    ################################################################

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

    def is_cite_key_unique(self, cite_key, include_doc_ids = None,
                            exclude_doc_ids = []):
        '''
            Checks if the passed citation key has already been used among comparison docs

            :param cite_key: (str) citation key being checked
            :param include_doc_ids: (list of int) doc_ids to check against. If None
                    then it checks against all doc_ids present in table
            :param exclude_doc_ids: (list of int) doc_ids to exclude from comparison
            Returns: True if it is unique and False if another doc uses it
        '''
        doc_df = self.get_table("Documents")
        if include_doc_ids is None:   # Look at all documents
            docs_to_compare = ~doc_df['doc_id'].isin(exclude_doc_ids)
        else:						  # Just look at docs specified in include_doc_ids
            include_doc_ids = list(set(include_doc_ids) - set(exclude_doc_ids))
            docs_to_compare = doc_df['doc_id'].isin(include_doc_ids)
        # Checking is passed key is found among those specified
        used_keys = doc_df[docs_to_compare]['citation_key'].unique().tolist()
        return (cite_key not in used_keys)

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

    def write_all_proj_bib_files(self, bib_folder, force_regen = False, cascade = False):
        """
            This function regenerates all the bib files associated with each
            project if there have been any changes to included bib records

            :param bib_folder: str path of where to save all bib files
            :param force_regen: boolean indicating whether to force the rewriting
                        (instead of checking whether anything has changed)
            :param cascade: boolean indicating if project document association
                should cascade (ie proj include all docs in itself AND descendant
                project documents)
        """
        logging.debug("--------------CHECKING/BUILDING BIB FILES-----------------")
        no_bib_files_built = True
        # Grabbing the current projects and document associations
        proj_df = self.get_table(table_name='Projects')
        proj_df.set_index('proj_id', inplace=True) # For easy indexing
        doc_proj_df = self.get_table(table_name='Doc_Proj')
        doc_df = self.get_table(table_name='Documents')

        # Iterate over each project
        for proj_id, proj_row in proj_df.iterrows():
            proj_name = proj_row['proj_text']
            # Grab all doc IDs associated with project(s)
            doc_ids = self.get_projs_docs(proj_id, cascade=cascade)

            if not force_regen: # If not being forced, we check last build times
                # Grab last build time and most recent modified time amongst bib entries
                last_build = proj_df.loc[proj_id]['bib_built']
                last_change = doc_df[doc_df['doc_id'].isin(doc_ids)]['modified_date'].max()
                # Skip the project if it has been built but last change was before last build
                if (len(doc_ids)==0) or ((last_build is not None) and (last_change < last_build)):
                    continue
                logging.debug(f"Changes found, rebuilding project '{proj_name}' (ID = {proj_id}).")
            # Generating filename
            file_path = bib_folder + "\\" + str(proj_id) + "-" + proj_name.replace(" ","") + ".bib"
            # Generating the associated bib file
            no_bib_files_built = False
            self.write_bib_file(doc_ids, file_path)
            # Generating additional bib files in the other project specific paths specified
            bib_paths = proj_row['bib_paths'].split(";")
            bib_paths = [bib.strip().replace("\\","/") for bib in bib_paths if bib!=""]
            for bib_path in bib_paths:
                self.write_bib_file(doc_ids, bib_path)
                
            # Updating the bib file build date and time
            dt_now = datetime.now().timestamp()*1e3
            self.update_record({'proj_id':proj_id}, 'bib_built', dt_now, table_name="Projects")
        
        # Checking if no bib files were built
        if no_bib_files_built: logging.debug("No changes since last build, so nothing new built.")
        logging.debug("------------------ Finished BIB FILES---------------------")