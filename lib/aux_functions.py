from PyQt5 import QtGui
import sqlite3
import pandas as pd
import pdb

# This file houses auxiliary functions used by the main class
def addChildrenOf(parent_proj_id, project_df, ind_txt, proj_id_list,
                    ignore_list = []):
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

def getDocumentDB(db_path):
    """
        This function will load the database and perform any processing needed
    """
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()

    command = "SELECT doc_id, authors, title, journal, year, add_date FROM Documents"
    #print(command)
    c.execute(command)

    doc = c.fetchall()
    cols = ["ID", "Authors", "Title", "Journal", "Year", "DateAdded"]
    # cols = ['ID', 'LName', 'FName', 'Title', 'Year', 'MendRead', 'MendDateAdd', 'MendDateMod', 'Path']
    df = pd.DataFrame(doc, columns=cols)

    # Converting the Author list to just the last names
    df["AuthorsLast"] = df.Authors.apply(getAuthorLastNames)
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

def updateDB(doc_id, column_name, new_value, db_path):
    # Updates the database for the given document ID in the given column with the
    #	passed value.
    print(f"Updating doc_id={doc_id}, column={column_name}, value={new_value}")
    # Opening connection and executing command
    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()
    command = f'UPDATE Documents SET {column_name} = "{new_value}" ' +\
                f'WHERE doc_id == {doc_id}'
    # print(command)
    c.execute(command)
    # Saving changes
    conn.commit()
    result = c.fetchall()
    # Parse the result to test whether it was a success or not
    print("Result:"+str(result))
    # FIXME: Update the table model to reflect the changes just sent to DB
    conn.close()

def insertIntoDB(row_dict, table_name, db_path):
    """
        Inserts a single record into the specified table

        :param row_dict: A dictionary whose keys are the fields of the table
                and whose values are the values to be put in the table.
        :param table_name: The name of which table these should be put in
    """
    # First we define a map from the dict keys to the db field names
    if table_name == "Documents":
        key_map = {'ID': 'doc_id', 'Title':'title', 'Journal':'journal',
                    'Authors':'authors', 'Year':'year',
                    'DateAdded':'add_date'}
        # TODO: Implement difference between string/int/date fields
        string_fields = ['title', 'journal', 'authors']
        date_fields = ['add_date']
    else:
        print(f"Key map for table={table_name} is not yet implemented.")
        return

    # Now we convert the dictionary keys (and values to strings)
    row_dict = {key_map[name]: str(val)  for name, val in row_dict.items()}
    # Adding apostrophes for the string values
    row_dict = {name: ("'"+val+"'" if name in string_fields else val)\
                                        for name, val in row_dict.items()}

    conn = sqlite3.connect(db_path)  #'MendCopy2.sqlite')
    c = conn.cursor()
    command = f"INSERT INTO {table_name} ("
    command += ", ".join(row_dict.keys())
    command += ") VALUES ("
    command += ", ".join(row_dict.values())
    command += ")"
    # command = f'UPDATE Documents SET {column_name} = "{new_value}" ' +\
    # 			f'WHERE doc_id == {doc_id}'
    # print(command)
    print(command)
    # pdb.set_trace()
    c.execute(command)

    try:
        # Saving changes
        conn.commit()
    except sqlite3.OperationalError:
        print("Unable to save the DB changes (DB may be open elsewhere)")
    result = c.fetchall()
    # Parse the result to test whether it was a success or not
    print("Result:"+str(result))
    # FIXME: Update the table model to reflect the changes just sent to DB
    conn.close()
