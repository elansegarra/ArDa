from PyQt5 import QtGui
import sqlite3
import pandas as pd
import pdb, warnings
import functools, time, datetime

# This file houses auxiliary functions used by the main class

# Decorator function to time specific parts of the app
def timer(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()    # 1
        value = func(*args, **kwargs)
        end_time = time.perf_counter()      # 2
        run_time = end_time - start_time    # 3
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs")
        return value
    return wrapper_timer

def addChildrenOf(parent_proj_id, project_df, ind_txt, proj_id_list, ignore_list = []):
    """
        Returns a list of all descendants of passed id (found recursively)

        :param ignore_list: any id's in this list will be ignored (along with their children)
    """
    child_list = []

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
        child_list += [ind_txt+children.iloc[p]['proj_text']]
        proj_id_list += [children.iloc[p]['proj_id']]
        # Getting texts and ids for descendants
        new_child_list, new_proj_id = addChildrenOf(child_id,
                                                    project_df,
                                                    ind_txt+"  ",
                                                    [],
                                                    ignore_list=ignore_list)
        # Adding them to our current lists
        child_list += new_child_list
        proj_id_list += new_proj_id
    return child_list, proj_id_list

def setTreeLevels(df, id_col, parent_col, parent_id, curr_level=1):
    """
        This function takes in a data frame and adds a column that contains
        the tree level of every node represented in the dataframe. When
        the df is sorted on this column, nodes can be added in row order without
        worry that a node's parent hasn't been added yet.

        :param df: dataframe that contains columns for id_col and parent_col
        :param parent_id: id of the node to start in (typically the root)
        :param curr_level: the current level being assigned (recursively)
    """

    # Validating each row is a unique node
    if len(df[id_col].unique()) != df.shape[0]:
        print('Non unique ids found. Aborting.')
        return

    # Checking if tree level column is there (and creating it if not)
    if 'tree_level' not in df:
        df['tree_level'] = -1

    # Flagging the current set of parents
    child_flags = (df[parent_col]==parent_id)

    # Checking this is the first time these parents have been visited
    # TODO: Check parent hasn't been visited already
    if (df[child_flags]['tree_level']!=-1).any():
        print('Cycle found in tree structure. Aborting.')
        return

    # Setting the level for the current set of parents
    df.loc[child_flags,'tree_level'] = curr_level

    # Iteratin over all the children
    for child_id in list(df[child_flags][id_col]):
        setTreeLevels(df, id_col, parent_col, child_id, curr_level+1)


def getAuthorLastNames(full_names):
    """
        This function takes a list of full names (or single string) and extracts
        the last names of the authors.

        :param fullnames: Either a list with the form
                    ["lastname, firstname", "lastname2, firstname2", ...]
                    Or a string with the form
                    "lastname, firstname; lastname2, firstname2; ..."

        :return: a list if sent a list and a string if sent a string.
    """
    if type(full_names) == list:
        full_names_list = full_names
    elif type(full_names) == str:
        full_names_list = full_names.split(";")
    else:
        print(f"Unrecognized type ({type(full_names)}) sent to this function."+\
               "Returning the argument.")
        return full_names

    result_list = [x[:x.find(",")].strip() for x in full_names_list]

    if type(full_names) == list:
        return result_list
    elif type(full_names) == str:
        return "; ".join(result_list)
    return result

def autoResizeTextWidget(my_widget, resize_height=True, height_padding=0, resize_width=False, width_padding=0):
    """
        This function will take the passed widget and resize the height and width
        to fit the text within.
        :param my_widget: Widget to be resized (must have a text attribute)
        """
    # text = my_widget.toPlainText()
    # font = my_widget.document().defaultFont()    # or another font if you change it
    # fontMetrics = QtGui.QFontMetrics(font)      # a QFontMetrics based on our font
    # textSize = fontMetrics.size(0, text)
    #
    # textWidth = textSize.width() + 30       # constant may need to be tweaked
    # textHeight = textSize.height() + 30     # constant may need to be tweaked
    #
    # my_widget.setMinimumSize(textWidth, textHeight)  # good if you want to insert this into a layout
    # my_widget.resize(textWidth, textHeight)
    textWidth = my_widget.document().size().width()
    textHeight = my_widget.document().size().height()
    print(f"Resizing to W:{textWidth} and H:{textHeight}")
    #my_widget.resize(textWidth, textHeight)
    #my_widget.setFixedWidth(textWidth + 30)
    my_widget.setFixedHeight(textHeight + 10)
    textWidth = my_widget.document().size().width()
    textHeight = my_widget.document().size().height()
    print(f"After resizing W:{textWidth} and H:{textHeight}")
    #my_widget.updateGeometry()

def getDocumentDB(db_path, table_name='Documents'):
    """
        This function will load the database and perform any processing needed
    """
    # TODO: Alter this function so that it returns a specifically specified table
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()

    # Checking that a valid table name has been sent
    if table_name not in ['Documents', 'Fields', 'Projects', 'Doc_Auth',
                            'Doc_Proj', 'Doc_Paths', 'Settings', 'Doc_Proj_Ext']:
        warnings.warn(f"Table name ({table_name}) not recognized.")
        return pd.DataFrame()

    # Simple extraction for a few tables
    if table_name in ['Fields', 'Projects', 'Doc_Proj', 'Settings']:
        c.execute(f'SELECT * FROM {table_name}')
        temp_df = pd.DataFrame(c.fetchall(), columns=[description[0] for description in c.description])
        conn.close()
        return temp_df

    # Special extraction for extended doc project
    if table_name == 'Doc_Proj_Ext':
        c.execute("SELECT * FROM Doc_Proj as dp Join Projects as p on dp.proj_id = p.proj_id")
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
    # pdb.set_trace()
    df = pd.DataFrame(c.fetchall(),
                        columns=[field_to_header[field] for field in cols])

    # Converting the Author list to just the last names
    # df["AuthorsLast"] = df.Authors.apply(getAuthorLastNames)


    # df['MendDateAdd'] = pd.to_datetime(df['MendDateAdd'], unit='ms').dt.date
    # df['MendDateMod'] = pd.to_datetime(df['MendDateMod'], unit='ms').dt.date
    #
    # url_to_path = lambda x:urllib.request.unquote(urllib.request.unquote(x[8:]))
    # df['Path'] = df['Path'].apply(url_to_path)
    # df['DateCreated'] = df['Path'].apply(lambda x: date.fromtimestamp(os.path.getctime(x)) if os.path.exists(x) else self.null_date)
    # df['DateModifiedF'] = df['Path'].apply(lambda x: date.fromtimestamp(os.path.getmtime(x)) if os.path.exists(x) else self.null_date)
    #
    # # Add in a column that gives the date the file was read (taken from the local DB)
    # #df['DateRead'] = null_date #date.today()  #None
    # elanConn = sqlite3.connect(self.aux_db_path) #"ElanDB.sqlite")
    # elanC = elanConn.cursor()
    # elanC.execute("SELECT Doc_ID, DateRead FROM ArticlesRead")
    # elanDB = pd.DataFrame(elanC.fetchall(), columns=['Doc_ID', 'DateRead'])
    #
    # # Left merging in any documents in my DB marked as read
    # df2 = pd.merge(df, elanDB, how='left', left_on='ID', right_on='Doc_ID')
    # df2['DateRead'].fillna(value = self.null_date_int, inplace=True)
    # df2['DateRead']= df2['DateRead'].apply(lambda x: date(int(str(x)[0:4]), int(str(x)[4:6]), int(str(x)[6:8])))
    #
    # # read = (df['DateCreated'] != df['DateModifiedF']) & (df['DateModifiedF'] < date.today() - timedelta(days=90))
    # # df.ix[read, 'DateRead'] = df['DateModifiedF']
    #
    # df2['Author2'] = ''  # Place holder for later addition of a second author
    #
    # $#### Extracting Folders and Folder Assignments to Add to Doc List
    # c.execute("SELECT id , name, parentId FROM Folders")
    # self.folders = pd.DataFrame(c.fetchall(), columns=['Folder_ID', 'Name', 'Parent_ID'])
    #
    # c.execute("SELECT documentID, folderId FROM DocumentFoldersBase") # WHERE status= 'ObjectUnchanged'")
    # self.doc_folders = pd.DataFrame(c.fetchall(), columns = ['ID', 'Folder_ID'])
    # self.doc_folders = self.doc_folders.merge(self.folders, how = 'left', on = 'Folder_ID')
    # #print(self.doc_folders)
    #
    # # Adding labels for the parent folders (TODO?)
    #
    # # Concatenating all the Projects for each file
    # proj_names = self.doc_folders.groupby('ID')['Name'].apply(lambda x: ', '.join(x)).to_frame('Projects').reset_index()
    #
    # # Reordering columns (for how they will be displayed) and dropping a few unused ones (FName, LName, DocID)
    # df2 = df2[['ID', 'Author1', 'Author2', 'Year', 'Title', 'DateRead', 'DateCreated', 'DateModifiedF',
    # 			'Path', 'MendDateAdd', 'MendDateMod', 'MendRead', 'Projects']]

    conn.close()
    #elanConn.close()
    # return df2
    return df

def getNextDocID(db_path, debug_print=False):
    # Returns the next unused document ID
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT doc_id FROM Documents")
    doc_ids_1 = [x[0] for x in c.fetchall()]
    doc_1_max = max(doc_ids_1)
    c.execute("SELECT doc_id FROM Doc_Paths")
    doc_ids_2 = [x[0] for x in c.fetchall()]
    doc_2_max = max(doc_ids_2)
    c.execute("SELECT doc_id FROM Doc_Proj")
    doc_ids_3 = [x[0] for x in c.fetchall()]
    doc_3_max = max(doc_ids_3)
    c.execute("SELECT doc_id FROM Doc_Auth")
    doc_ids_4 = [x[0] for x in c.fetchall()]
    doc_4_max = max(doc_ids_4)

    if debug_print:
        print(f"Highest IDs in Documents ({doc_1_max}), Doc_paths ({doc_2_max})," +\
                f" Doc_Proj ({doc_3_max}), Doc_Auth ({max(doc_ids_4)})")

    conn.close()

    return max(doc_ids_1 + doc_ids_2 + doc_ids_3 + doc_ids_4) + 1

def pathCleaner(path_str):
    """
        This function takes a string representing a path and cleans it and
        standardizes it.

        :param path_str: string with the original path
    """
    # Removing certain substrings
    substrings_to_remove = ["$\\backslash$", ":pdf"]
    for substring in substrings_to_remove:
            path_str = path_str.replace(substring, "")
    # Other idiosyncracies to correct
    if path_str[0] == ":":
        path_str = path_str[1:]

    return path_str

def convertBibEntryKeys(bib_dict_raw, key_format, field_df, debug_print = False):
    """
        This function converts the keys in a bib entry dict to conform
        with the desired format (bib files or table header)
        :param bib_dict: dictionary of fields and values
        :param key_format: str indicating which format should be used:
            'bib' = bib file format (and DB field column names)
            'header' = header names in the table view dataframe
        :param field_df: dataframe containing all the various possible keys
    """
    # Copying the row data so we don't change the source
    bib_dict = bib_dict_raw.copy()

    # Creating a dictionary for key mapping depending on the format desired
    if key_format == "bib":
        all_fields = field_df['field']
        key_chg_dict = dict(zip(field_df['header_text'], field_df['field']))
    elif key_format == "header":
        all_fields = field_df['header_text']
        key_chg_dict = dict(zip(field_df['field'], field_df['header_text']))
    else:
        print(f"Key format, {key_format}, not recognized. No keys changed.")
        return bib_dict

    # Converting any keys according to the dictionary created. (ignoring null values)
    for old_key, new_key in key_chg_dict.items():
        if (old_key in [None, '']) or (new_key in [None, '']):
            continue
        if old_key in bib_dict:
            bib_dict[new_key] = bib_dict.pop(old_key)

    # Finding any keys that will not be used
    unused_keys = set(bib_dict.keys()) - set(all_fields)
    if (debug_print) and (len(unused_keys) > 0):
        print(f"Some keys were unrecognized: {unused_keys}.")

    return bib_dict

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
    # Checking that a valid table name has been sent
    if table_name not in ['Documents', 'Projects', 'Settings', 'Fields', 'Doc_Proj', 'Doc_Paths', "Doc_Auth"]:
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
    except sqlite3.OperationalError:
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
        row_dict = convertBibEntryKeys(row_dict, 'bib', field_df)

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
    if curs.rowcount != 1:
        if debug_print:
            print(f"{curs.rowcount} rows were affected in the most recent sql call.")
        if force_commit:
            ans = "y"
        else:
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
