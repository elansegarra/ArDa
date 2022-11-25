''' Various functions for interacting with a database object '''

import sqlite3
import pandas as pd
import warnings

def getDocumentDB(db_path, table_name='Documents'):
    """
        This function will grab a table and return it as a dataframe

        :param str db_path: path to the SQLite file
        :param str table_name: name of the table in the db to be extracted
    """
    # TODO: Alter this function so that it returns a specifically specified table
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()

    # Checking that a valid table name has been sent
    if table_name not in ['Documents', 'Fields', 'Projects', 'Doc_Auth',
                            'Doc_Proj', 'Doc_Paths', 'Doc_Proj_Ext',
                            'Proj_Tasks', 'Proj_Diary',
                            'Proj_Notes', 'Custom_Filters']:
        warnings.warn(f"Table name ({table_name}) not recognized.")
        return pd.DataFrame()

    # Simple extraction for a few tables
    if table_name in ['Fields', 'Projects', 'Doc_Proj', 'Doc_Auth',
                        'Proj_Notes', 'Custom_Filters', 'Doc_Paths',
                        'Proj_Tasks', 'Proj_Diary']:
        c.execute(f'SELECT * FROM {table_name}')
        temp_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
        conn.close()
        return temp_df

    # Special extraction for extended doc project
    if table_name == 'Doc_Proj_Ext':
        c.execute("SELECT p.*, dp.doc_id FROM Doc_Proj as dp Join Projects as p on dp.proj_id = p.proj_id")
        temp_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
        conn.close()
        return temp_df

    c.execute(f'SELECT * FROM Fields WHERE table_name = "{table_name}"')
    field_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
    field_to_header = dict(zip(field_df.field, field_df.header_text))

    # Determining which columns to include (for now just using the indicator in the fields table)
    field_df.sort_values('doc_table_order', inplace=True)
    included_cols = [row['field'] for index, row in field_df.iterrows() if row['table_name']=='Documents'] #if row['init_visible']]
    included_cols = ", ".join(included_cols)

    #command = "SELECT doc_id, author_lasts, title, publication, year, add_date, pages FROM Documents" # limit 100"
    command = "SELECT "+included_cols+" FROM Documents"
    c.execute(command)

    cols = [description[0] for description in c.description]
    df = pd.DataFrame(c.fetchall(),
                        columns=[field_to_header[field] for field in cols])

    conn.close()
    return df

def updateDB(cond_dict, column_name, new_value, db_path, table_name = "Documents",
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
        :param db_path: string path to the DB file
        :param table_name: string with the table to update
    """
    # print(f"Updating {column_name}:{new_value}")
    # Checking that a valid table name has been sent
    if table_name not in ['Documents', 'Projects', 'Fields', 'Doc_Proj', 
                                'Doc_Paths', "Doc_Auth", 'Proj_Notes']:
        warnings.warn(f"Table name ({table_name}) not recognized (or not yet implemented).")
        return pd.DataFrame()
    # If it is a string we clean it and add quotes
    if isinstance(new_value, str):
        new_value = new_value.replace('"','')
        new_value = new_value.replace("'","")
        new_value = '"'+new_value+'"'
    elif isinstance(new_value, bool): # Replace booleans with their strings
        new_value = ("True" if new_value else "False")
        new_value = '"'+new_value+'"'
    # Opening connection and executing command
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    command = f'UPDATE {table_name} SET {column_name} = {new_value} ' +\
                f'WHERE '
    conditions = [key+"='"+value+"'" if isinstance(value,str) else key+"="+str(value)
                    for key, value in cond_dict.items()]
    command += " AND ".join(conditions)
    if debug_print:
        print(command)
    try:
        c.execute(command)
        result = c.fetchall()
    except sqlite3.Error:
        print(f"There was a sql error with the following: {command}")
        # Saving changes
        conn.close()
        return

    # Parse the result to test whether it was a success or not
    if debug_print:
        print("Result:"+str(result))

    # Also updating the modified date (if in the documents table)
    if table_name == "Documents":
        dt_obj = datetime.datetime.now().timestamp()*1e3
        command = f'UPDATE Documents SET modified_date = "{dt_obj}" ' +\
                    f'WHERE doc_id == {cond_dict["doc_id"]}'
        c.execute(command)

    # Saving changes
    conn.commit()
    conn.close()

def insertIntoDB(data_in, table_name, db_path, debug_print = False):
    """
        Inserts a single record into the specified table and returns unused keys

        :param data_in: A dictionary whose keys are the fields of the table
                and whose values are the values to be put in the table.
                May also be a list of dictionaries to be iterated over.
        :param table_name: The name of which table these should be put in
    """
    # Checking that a valid table name has been sent
    if table_name not in ['Documents', 'Projects', 'Fields', 'Doc_Proj', 
                            'Doc_Paths', "Doc_Auth", 'Proj_Notes',
                            'Proj_Diary', 'Proj_Tasks']:
        warnings.warn(f"Table name ({table_name}) not recognized (or not yet implemented).")
        return

    # Checking the variable type to act accordingly (dict or list)
    if isinstance(data_in, dict):
        data_in = [data_in]
    elif not isinstance(data_in, list):
        warnings.warn(f"Do not recognize the variable type of row_raw_dict. "+\
                        "Should be a dictionary or list of dictionaries")
        return

    # Initializing the unused keys
    unused_keys = set()

    # Extracting info about the fields of the DB we're inserting into
    field_df = getDocumentDB(db_path, table_name='Fields')
    field_df = field_df[field_df.table_name==table_name].copy()

    # Getting list of fields by their var type
    string_fields = list(field_df[(field_df.var_type=="string")]['field'])
    int_fields = list(field_df[(field_df.var_type=="int")]['field'])
    boolean_fields = list(field_df[(field_df.var_type=="boolean")]['field'])

    # Connecting to the database
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()

    # Getting the table cols
    c.execute(f"SELECT * FROM {table_name} LIMIT 5")
    col_names = [description[0] for description in c.description]

    # Iterating over every dictionary in the list
    for row_dict_raw in data_in:
        # Check that item is a dictionary (skip if not)
        if not isinstance(row_dict_raw, dict):
            print("Element is not a dictionary, can't insert into DB.")
            continue
        # Copying the row data so we don't change the source
        row_dict = row_dict_raw.copy()
        # Convert keys to match those in the DB (same as bib fields)
        # TODO: This need to be implemented outside of this function to keep this function generic
        # row_dict = convertBibEntryKeys(row_dict, 'bib', field_df)

        # Canceling operation if no path to insert
        if (table_name == "Doc_Paths") and ('full_path' not in row_dict):
            return set(row_dict.keys())

        # Converting all values to strings
        row_dict = {key: str(val) for key, val in row_dict.items()}
        # Adding apostrophes for the string values (and escape chars)
        row_dict = {key: ("'"+val.replace("'", "''")+"'" if key in string_fields else val)\
                                            for key, val in row_dict.items()}


        # Filtering the keys to just those in table columns (and getting unused)
        unused_keys = unused_keys | (set(row_dict.keys()) - set(col_names))
        row_dict = {key: val for key, val in row_dict.items() if key in col_names}

        # Forming insertion command and executing it
        command = f"INSERT INTO {table_name} ("
        command += ", ".join(row_dict.keys())
        command += ") VALUES ("
        command += ", ".join(row_dict.values())
        command += ")"
        if debug_print:
            print(command)
        c.execute(command)

    # Saving changes
    try:
        conn.commit()
    except sqlite3.OperationalError:
        print("Unable to save the DB changes (DB may be open elsewhere)")
        conn.close()
        return
    result = c.fetchall()
    conn.close()

    # Returning any keys that were not used in the insertion
    return unused_keys

def deleteFromDB(cond_dict, table_name, db_path, force_commit=False, debug_print=False):
    """
        Deletes records from the specified DB according to the conditions passed

        :param cond_dict: A dictionary whose keys are the fields of the table
                and whose values are values to condition on. Eg if passed
                {'doc_id':4, 'proj_id':2}, then all rows with doc_id==4 and proj_id==2
                will be deleted from the DB.
        :param table_name: The name of which table these should be put in
        :param db_path: str path of the DB to open
        :param force_commit: boolean indicating whether to ask to continue
                if more or less than 1 row is affected by the DB change
    """
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    curs = conn.cursor()
    command = f"DELETE FROM {table_name} WHERE "
    conditions = [key+"='"+value+"'" if isinstance(value,str) else key+"="+str(value)
                    for key, value in cond_dict.items()]
    command += " AND ".join(conditions)
    if debug_print:
        print(command)
    curs.execute(command)

    if force_commit or (curs.rowcount == 0):
        ans = "y"
    else:
        print(command)
        print(f"{curs.rowcount} rows were affected in the most recent sql call.")
        # TODO: This now seems to enter a never ending print loop with the new version of PyQt5
        ans = input("Continue (y/n)? ")

    if (ans != "y") & (ans != "yes"):
        print("Aborting deletions made to the DB.")
        conn.close()
        return

    try:
        # Saving changes
        conn.commit()
    except sqlite3.OperationalError:
        print("Unable to save the DB changes (DB may be open elsewhere)")
        conn.close()
        return
    result = curs.fetchall()
    conn.close()

def getRowRecord(db_path, table_name, id_col, id_value, as_dict = True):
    ''' Returns a dictionary of the data in the row queried '''
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()

    c.execute(f'SELECT * FROM {table_name} WHERE {id_col} = "{id_value}"')
    row_data = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
    conn.close()

    if as_dict:
        row_data = row_data.to_dict('records')[0]

    return row_data

def getNextID(db_path, id_var, debug_print=False):
    ''' Returns the next unused ID for a given id variable
        :param str id_var: either 'doc_id', 'proj_id', 'entry_id' or 'task_id'
    '''
    # Defining which tables to search through for IDs
    if id_var == 'entry_id':
        dbs = ['Proj_Diary']
    elif id_var == 'task_id':
        dbs = ['Proj_Tasks']
    elif id_var == 'proj_id':
        dbs = ['Projects', 'Doc_Proj', 'Proj_Diary', 'Proj_Tasks', 'Proj_Notes']
    elif id_var == 'doc_id':
        dbs = ['Documents', 'Doc_Paths', 'Doc_Proj', 'Doc_Auth', 'Proj_Notes']
    else:
        print(f"ID variable {id_var} is not recognized.")
        return None

    doc_id_maxes = []
    # Grab the highest id within each table (and then across tables)
    for table_name in dbs:
        df = getDocumentDB(db_path, table_name)
        doc_id_maxes.append(df[id_var].max())
    next_id = max(doc_id_maxes) + 1

    if debug_print:
        print(f"Highest {id_var} in {dbs} are {doc_id_maxes}, so next is {next_id}.")

    return next_id
