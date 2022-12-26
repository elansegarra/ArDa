from ArDa.arda_db import *
import sqlite3, logging, warnings
import pandas as pd
from os.path import exists

try: 
    import ArDa.aux_functions as aux
except ModuleNotFoundError:
    import lib.ArDa.aux_functions as aux


class ArDa_DB_SQL(ArDa_DB):
    """
        This is a subclass of ArDa_DB which implements a back-end
        of ArDa where all data is stored in a single sqlite DB.    
    """

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

    ## Status/Attribute Extraction Functions #######################
    ################################################################

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

    ## Record Adding/Seleting/Editing Functions ####################
    ################################################################

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

    def delete_table_record(self, cond_key, table_name):
        """ Removes the record(s) specified by cond_key from the specified table """
        aux.deleteFromDB(cond_key, table_name, self.db_path, force_commit=True)

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

    ## Auxiliary Functions #########################################
    ################################################################

