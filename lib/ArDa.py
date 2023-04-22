import sys
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
from ArDa.layouts.layout_main import Ui_MainWindow
import os, time
from shutil import copyfile
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import configparser
from ArDa.myExtensions import docTableModel, projTreeModel, mySortFilterProxy, docTableView
from util.my_widgets import QTextEditExt, MyDictionaryCompleter, QLabelElided
from ArDa.dialog_settings import SettingsDialog
from ArDa.dialog_project import ProjectDialog
from ArDa.dialog_filter import FilterDialog
from ArDa.dialog_compare import CompareDialog
from ArDa.dialog_doc_search import DocSearchDialog
import ArDa.aux_functions as aux
import ArDa.arda_init as arda_init
from ArDa.arda_db_sql import *
from ArDa.arda_db_obsid import *
from ArDa.arda_db_bib import *
import pdb, warnings
import bibtexparser
import logging
import traceback            # This for catching all errors for logging
from profilehooks import profile

class ArDa(Ui_MainWindow):

    # Class variables
    h_scale = 40   #height of one row in the table

    def __init__(self, dialog):
        Ui_MainWindow.__init__(self)
        self.setupUi(dialog)
        self.parent = dialog

        # Load variables from the config file
        self.loadConfig()

        # Setting the default splitter weights (between docs and side panel)
        self.splitter.setSizes([520, 80])

        # Initialize and populate the document table
        self.initDocumentViewer()

        # Build various combo boxes
        self.buildProjectComboBoxes()
        self.buildFilterComboBoxes()
        self.buildColumnComboBoxes()

        # Initialize the search box
        self.initSearchBox()

        # Initialize sidepanel buttons (ie connect them, set diabled, etc...)
        self.initSidePanelButtons()

        # Set other attributes of metadata fields
        self.initMetaDataFields()

        # Initialize the project viewer
        self.initProjectViewModel()

        # Initialize the column check boxes
        self.initColumnCheckboxes()

        # Connecting the menu actions to responses
        self.connectMenuActions()

        # Checking the watched folders
        if (self.config["General Properties"]["start_up_check_watched_folders"]=="True"):
            self.checkWatchedFolders()

        # Updating the backups
        self.updateBackups()

        self.parent.showMaximized()

##### Other? Functions ##############################################################
    def loadConfig(self):
        """
            This function reads the config file and sets various variables
            accordingly.
        """
        logging.debug('Reading config file')
        self.config = configparser.ConfigParser()
        self.config.read("user/config.ini")

        # Grabbing the variable values as specified in the config file
        self.db_path = self.config.get("Data Sources", "DB_path")  #"Data Sources" refers to the section
        logging.debug("DB Path: "+self.db_path)
        self.watch_path = self.config.get("Watch Paths", "path_001")
        self.last_check_watched = self.config.get("Other Variables", "last_check")
        self.all_bib_path = self.config.get("Bib", "all_bib_path")

        # Open the associated arda database
        self.adb = ArDa_DB_SQL()
        self.adb.open_db(self.db_path)

####end
##### Action/Response Functions ################################################
    def SearchEngaged(self):
        # This function is called when the search field is filled out

        # Getting search text and field to search on
        search_text = self.lineEdit_Search.text()
        search_col = self.comboBox_Search_Column.currentText()
        logging.debug(f"Attempting search for '{search_text}' in columnn '{search_col}'.")
        # search_col_index = (list(self.tm.arraydata.columns)).index(search_col)

        # Some edge cases
        if search_text == "":
            return

        # Defining string vs int fields (different searching)
        # TODO: Tie these lists to their designation in the fields table
        string_fields = ['Authors', 'Title', 'Journal']
        int_fields = ['ID', 'Year']
        date_fields = []

        # Case statement based on field types
        if search_col == 'All Fields':
            logging.debug("Still need to implement searching through all fields")
            return
        elif search_col in string_fields:
            self.search_filter_ids = set(self.tm.arraydata[self.tm.arraydata[search_col].str.contains(search_text, regex=False, case=False, na=False)].ID)
        elif search_col in int_fields:
            try:
                search_text = int(search_text)
                self.search_filter_ids = set(self.tm.arraydata[self.tm.arraydata[search_col]==search_text].ID)
            except ValueError:
                logging.debug(f"Search value '{search_text}' is not castable to an int.")
                return
        else:
            logging.debug(f"Do not recognize the type for searching on field: {search_col}")
            return

        # Changing the filtered list in the proxy model
        self.tm.beginResetModel()
        self.all_filter_ids = self.proj_filter_ids & self.diag_filter_ids & \
                            self.custom_filter_ids & self.search_filter_ids
        self.proxyModel.show_list = list(self.all_filter_ids)
        self.tm.endResetModel()

        # Updating the current filter message
        msg = f" search ('{search_text}' in {search_col});"
        # Checking if there was an earlier filter in place
        start = self.label_CurrentFilter.text().find(' search (')
        if start != -1:
            # Replacing old msg with the new
            end = start + self.label_CurrentFilter.text()[start:].find(";") + 1
            old_msg = self.label_CurrentFilter.text()[start:end]
            new_msg = self.label_CurrentFilter.text().replace(old_msg, msg)
            self.label_CurrentFilter.setText(new_msg)
        else:
            self.label_CurrentFilter.setText(self.label_CurrentFilter.text() + msg)
        self.label_CurrentFilter.show()
        self.pushButton_ClearFilter.show()

        # # The below code is for using the filter proxy's regex
        # # Setting the column to search on
        # self.proxyModel.setFilterKeyColumn(-1) #self.search_col)
        #
        # # Updating the set of ids? (maybe not needed)
        # # self.search_filter_ids = set(self.tm.arraydata.ID)
        #
        # # Setting the proxyModel search value
        # self.proxyModel.setFilterRegExp(str(self.lineEdit_Search.text()))

    def openDocContextMenu(self, position):
        # This function opens a custom context menu over document rows
        menu = QtWidgets.QMenu()
        # Submenu for opening the file
        docOpenWith = menu.addMenu("Open file with")
        docOpenDefault = QtWidgets.QAction("Default pdf reader")
        docOpenDrawboard = QtWidgets.QAction("Drawboard")
        docOpenDrawboard.setEnabled(False) # Disabled for now
        docOpenWith.addAction(docOpenDefault)
        docOpenWith.addAction(docOpenDrawboard)

        # Checks if multiple IDs are selected
        mult_txt = ""
        if len(self.selected_doc_ids) > 1:
            mult_txt = "all "

        # Gathers the read/unread status of each selected document
        sel_df = self.tm.arraydata[self.tm.arraydata.ID.isin(self.selected_doc_ids)]
        unread = (sel_df['Read'].isnull()) | (sel_df['Read'] == '')
        # Adds "read" option if any are unread
        if unread.any():
            docMarkReadToday = QtWidgets.QAction(f"Mark {mult_txt}read today")
            docMarkReadCustom = QtWidgets.QAction(f"Mark {mult_txt}read custom")
            menu.addAction(docMarkReadToday)
            menu.addAction(docMarkReadCustom)
            # Adds "unread" option if any are read
        if (~unread).any():
            docMarkUnread = QtWidgets.QAction(f"Mark {mult_txt}unread")
            menu.addAction(docMarkUnread)

        # Submenu for removing from a project
        docRemProj = menu.addMenu(f"Remove {mult_txt}from project")
        proj_dict = self.adb.get_docs_projs(self.selected_doc_ids, full_path=True)
        proj_id_list = list(proj_dict.keys())
        if len(proj_dict) > 0:
            docRemProj.setEnabled(True)
            docRemActions = [QtWidgets.QAction(value) for key, value in proj_dict.items()]
            for i in range(len(proj_dict)):
                docRemProj.addAction(docRemActions[i])
        else:
            docRemActions = []
            docRemProj.setEnabled(False)

        # Adding a merge option if 2 are selected
        if len(self.selected_doc_ids) == 2:
            docMergeTwo = QtWidgets.QAction("Compare/merge bib entries")
            menu.addAction(docMergeTwo)

        # Other Actions in main menu
        docActionDelete = QtWidgets.QAction(f"Delete {mult_txt}bib entry", None)
        menu.addAction(docActionDelete)
        # menu.addAction(docActionOpenWith)
        # menu.addMenu(docActionGroup)
        action = menu.exec_(self.tableView_Docs.mapToGlobal(position))

        # Responding to the action selected
        if action == docOpenDefault:
            self.openFileReader()
        elif action in docRemActions:
            act_ind = docRemActions.index(action)
            rem_proj_id = proj_id_list[act_ind]
            for sel_doc_id in self.selected_doc_ids:
                logging.debug(f'Removing doc ID = {sel_doc_id} from proj ID ' +\
                        f' = {rem_proj_id} ({proj_dict[rem_proj_id]})')
                self.adb.add_rem_doc_from_project(sel_doc_id, rem_proj_id, "remove")
            # Updating the document view if a proj is selected
            if self.comboBox_Filter_Project.currentIndex() != 0:
                self.projectFilterEngaged()
        elif (unread.any()) and (action == docMarkReadToday):
            td = date.today()
            today_int = td.year*10000 + td.month*100 + td.day
            # Iterating over all the selected document IDs
            for sel_doc_id in self.selected_doc_ids:
                # Updating the source database
                self.adb.update_record({'doc_id':sel_doc_id}, column_name="read_date",
                                new_value=today_int)
                # Updating the table model (and emitting a changed signal)
                self.updateDocViewCell(sel_doc_id, 'Read', today_int)
        elif (unread.any()) and (action == docMarkReadCustom):
            text_date, ok = QtWidgets.QInputDialog.getText(self.parent, 'Read Date Input',
                            'Enter the date this document was read (YYYYMMDD):')
            if ok: # If the user clicked okay
                try: # Check that input is valid
                    int_date = int(text_date)
                    # TODO: Need to check strcuture of input to make sure it is valid
                except ValueError:
                    logging.debug('Custom date input is not valid.')
                    return
                # Iterating over all the selected document IDs
                for sel_doc_id in self.selected_doc_ids:
                    # Updating the source database
                    self.adb.update_record({'doc_id':sel_doc_id}, column_name="read_date",
                                    new_value=int_date)
                    # Updating the table model (and emitting a changed signal)
                    self.updateDocViewCell(sel_doc_id, 'Read', int_date)
        elif ((~unread).any()) and (action == docMarkUnread):
            # Iterating over all the selected document IDs
            for sel_doc_id in self.selected_doc_ids:
                # Updating the source database
                self.adb.update_record({'doc_id':sel_doc_id}, column_name="read_date",
                                new_value="")
                # Updating the table model
                self.updateDocViewCell(sel_doc_id, 'Read', None)
        elif action == docActionDelete:
            if len(self.selected_doc_ids) > 5:
                # Issuing pop up if more than 5 documents are set to be deleted
                msg = f"You have selected {len(self.selected_doc_ids)} bib " +\
                        "entries to be deleted. Are you sure you want to continue?"
                msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,
                                        "Continue Deletion?", msg,
                                        QtWidgets.QMessageBox.Ok |
                                        QtWidgets.QMessageBox.Cancel)
                response = msg_diag.exec_()
                if response != QtWidgets.QMessageBox.Ok:		return

            # Iterating over all the selected document IDs
            doc_ids = self.selected_doc_ids.copy()
            for i in range(len(doc_ids)):
                sel_doc_id = doc_ids[i]
                # Delete record from the underlying bib DB
                self.adb.delete_doc_record(sel_doc_id)
                # Delete from the table model
                self.deleteBibFromTM(sel_doc_id)
                
            # Deselect any document
            self.tableView_Docs.selectionModel().clearSelection()
        elif (len(self.selected_doc_ids)==2) and (action == docMergeTwo):
            self.openCompareDialog(self.selected_doc_ids[0], self.selected_doc_ids[1],
                                        compare_mode="both old")
        else:
            logging.debug("Context menu exited without any selection made.")

        # Connecting the actions to response functions
        # self.docActionOpenWith.triggered.connect(self.openFileReader)

    def openPathContextMenu(self, position, path_index):
        # This function opens a custom context menu over the file path
        menu = QtWidgets.QMenu()
        # Adding actions to the context menu
        action_OpenFolder = QtWidgets.QAction("Open Containing Folder")
        action_OpenFolder.setEnabled(True)
        action_RemovePath = QtWidgets.QAction("Remove File Path")
        action_RemovePath.setEnabled(len(self.selected_doc_ids)==1)
        menu.addAction(action_OpenFolder)
        menu.addAction(action_RemovePath)
        # Open the menu and get the selection
        action = menu.exec_(self.meta_file_paths[path_index].mapToGlobal(position))

        # Gathering the filepath that was clicked
        file_path = self.meta_file_paths[path_index].text()
        file_path = file_path[file_path.find('///')+3:]
        file_path = file_path[:file_path.find("'>")]

        # Responding to the action selected
        if action == action_OpenFolder:
            file_path = file_path.replace("/", "\\")
            # folder_path = file_path[:file_path.rfind("\\")]
            os.system(f'explorer.exe /select,"{file_path}"')
        elif action == action_RemovePath:
            # Removing this path
            cond_key = {'doc_id':self.selected_doc_ids[0],
                        'full_path': file_path}
            self.adb.delete_table_record(cond_key, 'Doc_Paths')
            # Reload the meta data to reflect the change
            self.loadMetaData(self.selected_doc_ids)

    def openProjContextMenu(self, position):
        # This function opens a custom context menu over the file path
        menu = QtWidgets.QMenu()
        # Adding actions to the context menu
        action_ProjSettings = QtWidgets.QAction("Project Settings")
        action_AddProject = QtWidgets.QAction("Create Project")
        action_DeleteProject = QtWidgets.QAction("Delete Project")
        menu.addAction(action_ProjSettings)
        menu.addAction(action_AddProject)
        menu.addAction(action_DeleteProject)
        # Open the menu and get the selection
        action = menu.exec_(self.treeView_Projects.mapToGlobal(position))

        # Responding to the action selected
        if action == action_ProjSettings:
            self.openProjectDialog()
        elif action == action_AddProject:
            # Gathering the path to remove
            self.openProjectDialog(new_project = True)
        elif action == action_DeleteProject:
            # Getting The selected 	project ID
            sel_indices = self.treeView_Projects.selectionModel().selectedRows()
            self.selected_proj_id = sel_indices[0].internalPointer().uid
            # Grabbing documents in this project
            proj_docs = self.adb.get_projs_docs(self.selected_proj_id)
            if len(proj_docs) > 0:
                # Put up warning message that there are documents in this project
                msg = f"There are {len(proj_docs)} document(s) currently " +\
                        "associated with this project. These associations "+\
                        "will be deleted along with the project (the bib "+\
                        "entries will persist). Proceed with deletion?"
                msg_dele = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,
                                        "Delete Project", msg,
                                        QtWidgets.QMessageBox.Yes |
                                        QtWidgets.QMessageBox.No)
                # msg_diag.setInformativeText(f"Unselected fields: {', '.join(unsel_fields)}")
                result = msg_dele.exec_()
                if result != QtWidgets.QMessageBox.Yes:
                    return

            # Delete this project
            logging.debug(f"Delete project {self.selected_proj_id}:")
            self.adb.delete_project(self.selected_proj_id)

            # Reloading the project comboboxes and tree (blocking signals momentarily)
            self.comboBox_Filter_Project.blockSignals(True)
            self.comboBox_Filter_Project.clear()
            self.buildProjectComboBoxes(connect_signals = False)
            self.comboBox_Filter_Project.blockSignals(False)
            self.initProjectViewModel(connect_context=False)

    def addFilePath(self):
        # This function calls a file browser and adds the selected pdf file to
        #	the doc_paths of the selected row (aborts if multiple are selected)

        # Checks if none or multiple rows are selected and aborts
        if (self.selected_doc_ids == -1) or (len(self.selected_doc_ids)>1):
            warnings.warn("This should never be reachable (button should be disabled in under above conditions).")
            logging.debug("None or multiple rows are selected, cannot add a file path.")
            return

        # Setting the dialog start path (in case the proj path doesn't exist)
        diag_path_start = self.config['Data Sources']['def_pdfs_path']
        # Open a folder dialog to get a selected path
        new_file_path = QtWidgets.QFileDialog.getOpenFileName(self.parent,
                                                                'Open File',
                                                                diag_path_start)[0]

        # Check if a file was chosen (exit otherwise)
        if (new_file_path == None) or (new_file_path == ''):
            return

        # Inserting a new record with this path into doc_paths
        new_doc_path = {'doc_id': self.selected_doc_ids[0],
                        'full_path': new_file_path}
        self.adb.add_table_record(new_doc_path, "Doc_Paths")

        # Updating the meta fields to show the change
        self.loadMetaData([self.selected_doc_ids[0]])

    def addFromPDFFile(self):
        # This function calls a file browser and adds the selected pdf file
        
        # Open a folder dialog to get a selected path
        diag_path_start = self.config['Data Sources']['def_pdfs_path']
        new_file_path = QtWidgets.QFileDialog.getOpenFileName(self.parent,
                                                                'Open File',
                                                                diag_path_start)[0]
        # Check if a file was chosen
        if (new_file_path == None) or (new_file_path == ''):
            return

        # Extracting just the filename from the path
        new_filename = new_file_path[new_file_path.rfind("/")+1:]

        # Creating info for the bib entry and adding it
        new_bib_dict = {'Title': new_filename}
        new_bib_dict['full_path'] = new_file_path
        self.addBibEntry(new_bib_dict, supress_view_update = True)

    def addFromBibFile(self):
        # Opens a dialog to open a bib file and imports the bib entries
        # Setting the dialog start path (in case the proj path doesn't exist)
        diag_path_start = self.config['Data Sources']['def_pdfs_path']
        # Open a folder dialog to select a bib file
        bib_path = QtWidgets.QFileDialog.getOpenFileName(self.parent,
                                    'Open Bib File',
                                    diag_path_start,
                                    "Bib Files (*.bib)")[0]
        # Check if a file was chosen
        if (bib_path == None) or (bib_path == ''):
            return

        with open(bib_path, encoding='utf-8') as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file, )

        bib_entries = bib_database.entries_dict

        # Opening a dialog with a progress bar to track the import
        num_bibs = len(bib_entries)
        self.progress_dialog = QtWidgets.QProgressDialog("Starting import...",
                                                        "Cancel", 0, num_bibs)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setModal(True)
        self.progress_dialog.setWindowTitle("Importing Bib File")
        self.progress_dialog.setMinimumSize(500, 200)
        num_processed = 1
        self.progress_dialog.setValue(num_processed)

        # Initializing the repeat actions
        self.do_same = False
        self.do_action = None

        # Go over dict and import each entry
        for key, bib_entry in bib_entries.items():
            # Checking if the user canceled the operation
            if (self.progress_dialog.wasCanceled()):	break
            # Setting progress bar label (for user reference)
            self.progress_dialog.setLabelText(f"Now importing {bib_entry['ID']}"+\
                                            f" ({num_processed}/{num_bibs})")
            # Altering a few of the keys (before adding to DB)
            logging.debug(bib_entry)
            bib_entry['Citation Key'] = bib_entry.pop('ID')
            bib_entry['Type'] = bib_entry.pop('ENTRYTYPE')
            if 'file' in bib_entry:
                bib_entry['full_path'] = aux.pathCleaner(bib_entry.pop('file'))
            if 'link' in bib_entry: bib_entry['URL'] = bib_entry.pop('link')
            # if 'author' in bib_entry: bib_entry['author_lasts'] = bib_entry.pop('author')
            if 'arxivId' in bib_entry: bib_entry['arxiv_id'] = bib_entry.pop('arxivId')
            if 'arxivid' in bib_entry: bib_entry['arxiv_id'] = bib_entry.pop('arxivid')

            bib_entry = aux.convertBibEntryKeys(bib_entry, "header", self.field_df)
            # Adding the bib entry
            self.addBibEntry(bib_entry, supress_view_update = True,
                                        force_addition = False)
            # Updating the progress bar
            self.progress_dialog.setValue(num_processed)
            num_processed += 1

        # Resetting the repeat actions (so they aren't used inadvertently elsewhere)
        self.do_same = False
        self.do_action = None

        # Now we reset the view so that all these new entries are at the top
        # self.resetAllFilters()

    def openFileReader(self):
        # This function will open the selected file(s) in a pdf reader (acrobat for now)
        #  Note: If multiple rows are selected (or selected has multiple files)
        #		then only the first will be opened.

        # Checking if there is none or multiple selected
        if (self.selected_doc_ids == -1):
            logging.debug("No documents selected. Unable to open a file. Aborting for now.")
            return

        # Grabbing any paths associated with this document(s)
        doc_paths_df = self.adb.get_table("Doc_Paths")
        doc_paths = doc_paths_df[doc_paths_df['doc_id'].isin(self.selected_doc_ids)]['fullpath'].tolist()
        # Checking if there are paths found (and opening the first)
        if len(doc_paths) > 0:
            file_path = doc_paths[0].replace('&', '^&')
            logging.debug(f"Opening {file_path}")
            os.system("start "+file_path)
        else:
            logging.debug(f"No file paths found for doc_id: {self.selected_doc_ids[0]}")

    def openFilterDialog(self, filter_field):
        """
            This function opens the filter dialog and populates it with the
            relevant choices for the user.
            :param filter_field: string indicatin which type of filter to open,
                        eg "author", "journal", or "keyword"
        """
        self.ui = FilterDialog(self, filter_field, doc_id_subset = self.all_filter_ids)
        self.ui.setModal(True)

        # Open window and respond based on final selection
        if self.ui.exec_(): 	# User selects okay
            logging.debug(self.filter_field+": "+str(self.filter_choices))
            # Gathering IDs associated with the selected filter choice
            if self.filter_field == "Author":
                doc_auth_df = self.adb.get_table("Doc_Auth")
                rows_with_selected_authors = doc_auth_df['full_name'].isin(self.filter_choices)
                self.diag_filter_ids = doc_auth_df[rows_with_selected_authors]['doc_id'].tolist()
            elif self.filter_field == "Journal":
                doc_df = self.adb.get_table("Documents")
                rows_with_selected_journals = doc_df['journal'].isin(self.filter_choices)
                self.diag_filter_ids = doc_df[rows_with_selected_journals]['doc_id'].tolist()
            elif self.filter_field == "Keyword":
                doc_df = self.adb.get_table("Documents")
                # Check for each keyword
                doc_df['row_has_keyword'] = False
                for keyword in self.filter_choices:
                    doc_df['row_has_keyword'] = doc_df['row_has_keyword'] | doc_df['keyword'].str.contains(keyword)
                self.diag_filter_ids = doc_df[doc_df['row_has_keyword']]['doc_id'].tolist()
            else:
                warnings.warn(f"Filter field ({self.filter_field}) not recognized.")
                return
            # Changing to set (for aggregate filtering)
            self.diag_filter_ids = set(self.diag_filter_ids)
            
            # Changing the filtered list in the proxy model
            self.tm.beginResetModel()
            self.all_filter_ids = self.proj_filter_ids & self.diag_filter_ids & \
                                self.custom_filter_ids & self.search_filter_ids
            self.proxyModel.show_list = list(self.all_filter_ids)
            self.tm.endResetModel()

            # Updating the current filter message
            msg = f" filter ({str(self.filter_choices)} in {self.filter_field});"
            # Checking if there was an earlier filter in place
            start = self.label_CurrentFilter.text().find(' filter (')
            if start != -1:
                # Replacing old msg with the new
                end = start + self.label_CurrentFilter.text()[start:].find(";") + 1
                old_msg = self.label_CurrentFilter.text()[start:end]
                new_msg = self.label_CurrentFilter.text().replace(old_msg, msg)
                self.label_CurrentFilter.setText(new_msg)
            else:
                self.label_CurrentFilter.setText(self.label_CurrentFilter.text() + msg)
            self.label_CurrentFilter.show()
            self.pushButton_ClearFilter.show()
        else:				# User selects cancel
            logging.debug("Filter window canceled.")

    def openCompareDialog(self, doc_id_L, doc_id_R, compare_mode):
        """
            This function opens up a comparison dialog for the user to merge
            to documents together
            :param doc_id_L/doc_id_R: ints
            :param compare_mode: string which is either:
                    "both old": meaning both docs are old
                    "first new": meaning doc_id_L is a new entry
        """
        self.c_diag = CompareDialog(self, doc_id_L, doc_id_R)
        # Setting some specifics of this dialog depending on the mode
        self.c_diag.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Merge")
        if compare_mode == "both old":
            main_msg = "Choose which value to utilize for each of the fields" +\
                        " below. All fields that are not shown have the same"+\
                        " value across the two document."
        elif compare_mode == "first new":
            main_msg = "Compare the existing entry with the new entry and"+\
                        " choose values for each field. All fields not shown"+\
                        " have the same value."
            self.c_diag.ui.label_LeftTitle.setText("New Document")
            self.c_diag.ui.label_RightTitle.setText("Existing Document")
        else:
            warnings.warn(f"Compare mode ({compare_mode}) not recognized.")
            return

        self.c_diag.ui.plainTextEdit_Description.setPlainText(main_msg)

        # Open window and respond based on final selection
        if self.c_diag.exec(): 	# User selects okay
            logging.debug("User chose to merge.")
            logging.debug(f"Merged bib dict: {self.c_diag.merged_bib_dict}")
            logging.debug(f"Doc ID dict: {self.c_diag.doc_id_dict}")
            self.adb.merge_doc_records(doc_id_L, doc_id_R, self.c_diag.merged_bib_dict, self.c_diag.doc_id_dict)
            # Update the cells in the TM row and delete the other row in TM
            self.updateDocViewRow(self.c_diag.doc_id_dict['doc_id'])
            other_id = doc_id_L if (doc_id_R == self.c_diag.doc_id_dict['doc_id']) else doc_id_R
            self.deleteBibFromTM(other_id)
            return True
        else:
            logging.debug("User canceled.")
            return False

    def openDocSearchDialog(self):
        self.d_diag = DocSearchDialog(self)
        # TODO: Need to customize the buttons for crossref dialog (possibly using a mode parameter)

        if self.d_diag.exec_():
            logging.debug("Accepted")
            logging.debug(self.d_diag.bib_dict)
        else:
            logging.debug("Doc Search Canceled")

    def openProjectDialog(self, new_project = False):
        if new_project:
            self.ui = ProjectDialog(self, None, self.adb)
        elif self.selected_proj_id != -1:
            self.ui = ProjectDialog(self, self.selected_proj_id, self.adb)
        else:
            warnings.warn("openProjectDialog() was called not on a new project and no project is selected.")
            return

        self.ui.setModal(True)
        # Checking for result from the dialog
        if self.ui.exec_() and self.ui.saved_settings:
            # Reloading the project comboboxes and tree (blocking signals momentarily)
            self.comboBox_Filter_Project.blockSignals(True)
            self.comboBox_Filter_Project.clear()
            self.buildProjectComboBoxes(init_proj_id = self.selected_proj_id, connect_signals = False)
            self.comboBox_Filter_Project.blockSignals(False)
            self.initProjectViewModel(connect_context=False)

    def openProjectFolder(self):
        """ Opens the project folder (if specified) of the selected project """
        if self.selected_proj_id != -1:
            proj_path = self.adb.get_proj_folder_path(self.selected_proj_id)
            # Open the specified folder if there was a path found
            if proj_path is not None:
                os.startfile(proj_path)
        else:
            logging.debug(f"The openProjectFolder function was called despite no projects "+\
                        f"being selected: {self.selected_proj_id}")
        
    def openSettingsDialog(self):
        self.s_diag = SettingsDialog(self)
        if self.s_diag.exec_():
            # If the custom filters were changed then reload the combobox
            if self.s_diag.custom_filters_changed:
                self.buildFilterComboBoxes()
            # If the DB was changed then reload adb and app contents
            if self.s_diag.db_path_changed:
                msg = "The DB file has been changed, however ArDa must be " + \
                    "restarted in order far the new DB to be loaded. Please " + \
                    "close and reopen the application."
                msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information,
                                        "DB File Changed", msg,
                                        QtWidgets.QMessageBox.Ok)
                response = msg_diag.exec_()
                # self.adb.open_db(self.config.get("Data Sources", "DB_path"))
                # TODO: Restart app or reload all elements


    def projectFilterEngaged(self):
        # This function grabs the current selection in the project filter drop
        #	down menu and distills filters to those docs in the table view
        curr_choice = self.comboBox_Filter_Project.currentText().lstrip()
        if curr_choice == 'All projects':
            self.tm.beginResetModel()
            self.proj_filter_ids = set(self.tm.arraydata.ID)
            self.all_filter_ids = self.proj_filter_ids & self.diag_filter_ids & \
                                self.custom_filter_ids & self.search_filter_ids
            self.proxyModel.show_list = list(self.all_filter_ids)
            self.tm.endResetModel()
            # Clear any selection in the project tree view
            self.treeView_Projects.selectionModel().clearSelection()
            # Setting message for no projects filtered
            msg = ""
        else:
            # Get the project id associated with menu choice
            self.selected_proj_id = self.comboBox_Project_IDs[\
                                    self.comboBox_Filter_Project.currentIndex()]
            proj_ids = [self.selected_proj_id]
            # Grabbing the cascade setting
            cascade = (self.config["General Properties"]["project_selection_cascade"] == "True")
            # Selecting all doc IDs that are in this project (and children if cascading)
            self.proj_filter_ids = set(self.adb.get_projs_docs(proj_ids, cascade))

            # Changing the filtered list in the proxy model
            self.tm.beginResetModel()
            self.all_filter_ids = self.proj_filter_ids & self.diag_filter_ids & \
                                self.custom_filter_ids & self.search_filter_ids
            self.proxyModel.show_list = list(self.all_filter_ids)
            self.tm.endResetModel()

            # Updating the current filter message
            msg = f" project (ID = {str(self.selected_proj_id)});"
        # Checking if there was an earlier project filter in place
        start = self.label_CurrentFilter.text().find(' project (ID')
        if start != -1:
            # Replacing old msg with the new
            end = start + self.label_CurrentFilter.text()[start:].find(";") + 1
            old_msg = self.label_CurrentFilter.text()[start:end]
            new_msg = self.label_CurrentFilter.text().replace(old_msg, msg)
            self.label_CurrentFilter.setText(new_msg)
        else:
            self.label_CurrentFilter.setText(self.label_CurrentFilter.text() + msg)
        self.label_CurrentFilter.show()
        self.pushButton_ClearFilter.show()

        # Now we select the corresponding row in the project tree view
        # FIXME: Fix sync btw project combobox and project tree view (currently this selects only the cell not the row)
        # self.treeView_Projects.selectionModel().select(self.tree_nodes[curr_choice_id].index(), QtCore.QItemSelectionModel.Select)
        # TODO: Also need to deselect the currently selected row in the qtreeview (already handle clearin selection for "All Documents")
        # self.treeView_Projects.selectionModel().select(self.treeView_Projects.selectionModel().selectedRows()[0], QtCore.QItemSelectionModel.Toggle)

        # self.proxyModel.setFilterKeyColumn(self.search_col)

    def rowSelectChanged(self):
        # Undoing previous document selection
        self.selected_doc_ids = -1
        # Getting the current list of rows selected
        sel_rows = self.tableView_Docs.selectionModel().selectedRows()
        sel_row_indices = [i.row() for i in sorted(sel_rows)]
        # Extracting the IDs associated with these rows
        id_col_ind = self.tm.headerdata.tolist().index('ID')
        self.selected_doc_ids = [self.proxyModel.index(row_index,id_col_ind).data() for row_index in sel_row_indices]
        if len(sel_row_indices) == 0:  	# No rows are selected
            self.loadMetaData([])
            self.pushButton_AddFile.setEnabled(False)
        elif len(sel_row_indices) == 1: # One row is selected
            self.loadMetaData(self.selected_doc_ids)
            self.pushButton_AddFile.setEnabled(True)
        else:							# More than one row is selected
            self.loadMetaData(self.selected_doc_ids)
            self.pushButton_AddFile.setEnabled(False)

    def projSelectChanged(self):
        # Getting the current list of rows selected
        sel_indices = self.treeView_Projects.selectionModel().selectedRows()

        # Checking if no projects are selected
        if len(sel_indices) == 0:
            self.selected_proj_id = -1
            # Disabling the edit project button and open folder button
            self.pushButton_EditProject.setEnabled(False)
            self.pushButton_OpenProjectFolder.setEnabled(False)
            # Setting the project filter to all projects
            self.comboBox_Filter_Project.setCurrentIndex(0)

        else: # There is exactly one selected (multiple is not allowed)
            index = sel_indices[0]
            self.treeView_Projects.selectionModel()

            # Grabbing the text and id of the project that is selected
            # sel_proj_text = index.model().itemFromIndex(index).text()
            self.selected_proj_id = index.internalPointer().uid

            # Enabling the edit project button and open folder button
            self.pushButton_EditProject.setEnabled(True)
            self.pushButton_OpenProjectFolder.setEnabled(True)

            # Finding the corresponding proj id in combo box
            comboBox_index = self.comboBox_Project_IDs.index(self.selected_proj_id)
            self.comboBox_Filter_Project.setCurrentIndex(comboBox_index)

    def simpleMetaFieldChanged(self, field):
        """
            This function updates the DB info associated with the field passed.
            :param field: string with the field name (in bib file format)
        """
        # Check for rows associated with the field
        row_flag = (self.field_df['field']==field) & \
                        (self.field_df ['table_name']=="Documents")
        if ~row_flag.any(): # If no rows are found
            warnings.warn(f"Something went wrong and the field ({field}) could not be updated.")
            return

        # Gathering the widget associated with the passed field (and checking)
        row_ind = self.field_df[row_flag].index[0]
        field_widget = self.field_df.at[row_ind,'meta_widget']
        if field_widget is None:
            logging.debug(f"Edited field ({field}) does not have an associated widget. Cannot update.")
            return

        # Checking if multiple (or no) rows are selected
        if (self.selected_doc_ids == -1) or (len(self.selected_doc_ids)>1):
            logging.debug("Either no rows or multiple rows are selected. Edits have not been saved.")
            return

        # Extracting the new value from the widget (some field-specific commands)
        if field in ['title', 'abstract', 'author_lasts', 'keyword', 'note']:
            new_value = field_widget.toPlainText()
        elif field == 'doc_type':
            new_value = field_widget.currentText()
            if new_value == "undefined": new_value = ""
        elif field == "year":
            new_value = field_widget.text()
            if new_value != "":
                try: 
                    new_value = int(new_value)
                except ValueError:
                    msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Non-integer Year", 
                            f"The value of 'Year' must be an integer or empty. The value '{new_value}' is not permitted.",
                            QtWidgets.QMessageBox.Ok)          
                    response = msg_diag.exec_()
                    # Select the year text so it can be changed
                    self.lineEdit_Year.setFocus()
                    self.lineEdit_Year.selectAll()
                    return
        elif field == "citation_key":
            new_value = field_widget.text()
            key_is_unique = self.adb.is_cite_key_unique(new_value, exclude_doc_ids = [self.selected_doc_ids[0]])
            if (new_value != '') and (not key_is_unique):
                # Bring up warnings box that the citation key is alrady used
                # TODO: Get info associated with the bib entry that is using the key
                logging.debug(f"'{new_value}' is already being used as a citation key.")
                msg = f"This citation key, '{new_value}', is already "+\
                        "being used by another bibliographic entry: \n" +\
                        " < information of bib entry with that key (TBD) > "
                msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                        "Duplicate Citation Key", msg,
                                        QtWidgets.QMessageBox.Ok)
                response = msg_diag.exec_()
                # Select the citation key text so it can be changed
                self.lineEdit_Cite_Key.setFocus()
                self.lineEdit_Cite_Key.selectAll()
                return

        else:
            new_value = field_widget.text()

        # Trying to debug a common error
        try:
            sel_doc_id = self.selected_doc_ids[0]
        except:
            logging.debug("Error occurs here. Check some relevant variables:")
            logging.debug(f"selected_doc_ids: {self.selected_doc_ids}")
            logging.debug(f"field: {field}")
        sel_doc_id = self.selected_doc_ids[0]

        # Updating the source database (depends on whether authors or anything else)
        if field == "author_lasts":
            # Update authors in the underlying document DB
            self.adb.update_authors(sel_doc_id, new_value, as_editors=False)
            # Grab the updated doc record (to update the documents table model)
            doc_rec = self.adb.get_doc_record(sel_doc_id)
            self.updateDocViewCell(sel_doc_id, "Authors", doc_rec['author_lasts'])
        elif field == "editor":
            # Update authors in the underlying document DB
            self.adb.update_authors(sel_doc_id, new_value, as_editors=True)
            # Grab the updated doc record (to update the documents table model)
            doc_rec = self.adb.get_doc_record(sel_doc_id)
            self.updateDocViewCell(sel_doc_id, "Editors", doc_rec['editor'])
        else:	# updating the DB for all other field types
            self.adb.update_record({'doc_id':sel_doc_id}, column_name=field,
                            new_value=new_value)

            # Getting the column header associated with this field
            field_header = self.field_df.at[row_ind,'header_text']

            # Updating the table model (while converting field to header text)
            self.updateDocViewCell(sel_doc_id, field_header, new_value)
        
        # Updating the modified cell in the table
        dt_now = datetime.now().timestamp()*1e3
        self.updateDocViewCell(sel_doc_id, "Modified", dt_now)

        # Recompiling any relevant QCompleter objects
        if field == "journal":
            journals = sorted(self.tm.arraydata['Journal'].dropna().unique())
            self.completer_journal.setModel(QtCore.QStringListModel(journals))
        if field == "author_lasts":
            author_df = self.adb.get_table(table_name='Doc_Auth')
            authors = sorted(author_df['full_name'].dropna().unique())
            self.completer_authors.setModel(QtCore.QStringListModel(authors))

    def projectNoteChanged(self):
        """
            This function updates the DB info associated with the project note
        """
        # Checking if the widget is enabled
        if not self.textEditExt_ProjNote.isEnabled():
            warnings.warn("projectNoteChanged called when the widget is disabled.")
            return

        # Grab the selected project and selected document and note text
        curr_proj_id = self.comboBox_ProjNotes_IDs[self.comboBox_ProjNotes.currentIndex()]
        sel_doc_id = self.selected_doc_ids[0]
        row_dict = {'doc_id': sel_doc_id, 'proj_id': curr_proj_id}
        note_text = self.textEditExt_ProjNote.toPlainText()

        # If the note is empty remove it from the DB
        if note_text == '':
            self.adb.delete_table_record(row_dict, 'Proj_Notes')
            return

        # Grab the table of project notes
        proj_notes = self.adb.get_table('Proj_Notes')

        # Check if there is a note
        row_flag = (proj_notes.doc_id == sel_doc_id) & (proj_notes.proj_id == curr_proj_id)
        if row_flag.any():
            if len(proj_notes[row_flag].index) == 1:
                # Update the DB with the new note value
                self.adb.update_record(row_dict, 'proj_note', note_text,
                                    table_name = 'Proj_Notes')
            else:
                warnings.warn(f"Several notes found for the same doc id "+\
                            f"({sel_doc_id}) project ({curr_proj_id}) pair.")
                return
        else:
            # No project notes found so we insert the note
            note_data = {'doc_id': sel_doc_id, 'proj_id': curr_proj_id,
                        'proj_note': self.textEditExt_ProjNote.toPlainText()}
            self.adb.add_table_record(note_data, 'Proj_Notes')

    def write_all_proj_bib_files(self):
        """ Wrapper function for writing all project bib files """
        # Checking if project cascade is set to be on and passing to internal function
        cascade = (self.config["General Properties"]["project_selection_cascade"] == "True")
        self.adb.write_all_proj_bib_files(self.all_bib_path, cascade = cascade)

####end
##### Auxiliary Functions #######################################################
    def updateDocViewCell(self, doc_id, col_name, new_value):
        # Updating the table model (and emitting a changed signal)
        self.tm.arraydata.loc[self.tm.arraydata.ID==doc_id,
                                                    col_name] = new_value
        cell_row = self.tm.getRowOfDocID(doc_id)
        cell_col = list(self.tm.headerdata).index(col_name)
        cell_index = self.tm.index(cell_row, cell_col)
        self.tm.dataChanged.emit(cell_index, cell_index)
    
    def updateDocViewRow(self, doc_id):
        # Updates (from the DB) all the cells in the indicated row
        
        #Grab the documents info and convert keys to header text
        doc_dict = self.adb.get_doc_record(doc_id)
        doc_dict = self.adb.standardize_doc_dict_keys(doc_dict, "Documents", header_or_field="header")
        logging.debug(f"Doc_dict: {doc_dict}")
        columns = list(self.tm.headerdata)
        cell_row = self.tm.getRowOfDocID(doc_id)
        # Iterate over each column in table model and update the cell
        for cell_col in range(len(columns)):
            header_text = columns[cell_col]
            if header_text in doc_dict:
                self.tm.arraydata.loc[self.tm.arraydata.ID==doc_id,
                                                    header_text] = doc_dict[header_text]
                cell_index = self.tm.index(cell_row, cell_col)
                self.tm.dataChanged.emit(cell_index, cell_index)

    def addBibEntry(self, bib_dict = None, supress_view_update = False,
                    force_addition = True, select_new_row = True):
        """
            This function adds a new bib entry to the dataframe and table model

            :param bib_dict: dictionary of information included in this entry.
                Could include keys such as 'Title', 'ID', 'Authors',
                'file_path', ....
            :param suppress_view_update: boolean indicating whether to skip
                updating the table view (useful when multiple insertions )
            :param force_addition: boolean indicating whether to force the
                addition of this entry (without checking/prompting for duplicates)
        """
        # Setting some defaults (if no bib dict was passed)
        if bib_dict is None: bib_dict = dict()

        # Assign a new ID if none is passed
        if 'ID' not in bib_dict.keys():
            bib_dict['ID'] = self.adb.get_next_id("Documents")
        if list(bib_dict.keys()) == ['ID']:
            logging.debug(f"Adding an empty bib record with doc id {bib_dict['ID']}")
        else:
            logging.debug(f"Adding a new bib record with doc id {bib_dict['ID']} with the following info:\n{bib_dict}")

        # If it is not set to force the addition, check for duplicate entries
        if not force_addition:
            sim_ids = self.findDuplicates(bib_dict = {'Title':bib_dict.get('Title', 'New Title')})
            # If there are duplicates and repeat action was not selected
            if (len(sim_ids) > 0):
                # Check if the repeat action was previously selected
                if not self.do_same:
                    # TODO: Fully implement duplicate query when importing via bib file
                    # Issuing pop up if similar documents were found
                    msg = f"{len(sim_ids)} document(s) were found to be similar " +\
                            "to the document that is currently being added. " +\
                            "Would you like to add it anyway, skip it, or compare "+\
                            "with the first document in this list?"
                    msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,
                                            "Potential Duplicates", msg)#,
                                            # QtWidgets.QMessageBox.Ok |
                                            # QtWidgets.QMessageBox.Cancel)
                    # Defining custom buttons
                    self.buttonAdd = QtWidgets.QPushButton("Add")
                    self.buttonSkip = QtWidgets.QPushButton("Skip")
                    self.buttonComp = QtWidgets.QPushButton("Compare")
                    msg_diag.addButton(self.buttonAdd, QtWidgets.QMessageBox.AcceptRole)
                    msg_diag.addButton(self.buttonSkip, QtWidgets.QMessageBox.RejectRole)
                    msg_diag.addButton(self.buttonComp, QtWidgets.QMessageBox.HelpRole)
                    # Adding do same checkbox
                    checkboxDoSame = QtWidgets.QCheckBox("Do the same for remaining duplicates found.")
                    msg_diag.setCheckBox(checkboxDoSame)

                    response = msg_diag.exec_()
                    self.do_action = msg_diag.clickedButton()
                    self.do_same = checkboxDoSame.isChecked()

                # Handling the dialog responses (or repeating the last action)
                if self.do_action == self.buttonAdd:
                    logging.debug("Add anyway selected.")
                elif self.do_action == self.buttonSkip:
                    # Exit function without adding any entry
                    return
        
        # Add the bib entry into the main underlying documents table (this also handles authors)
        self.adb.add_table_record(bib_dict, "Documents")

        # Add in file paths (if any were passed)
        if 'full_path' in bib_dict:
            self.adb.add_table_record(bib_dict, "Doc_Paths")

        # Counting rows and columns to check insertion went correctly
        old_row_ct = self.tm.arraydata.shape[0]
        old_cols = set(self.tm.arraydata.columns)
        # Getting the info just inserted (and converting/filtering to header keys)
        tm_doc_dict = self.adb.standardize_doc_dict_keys(
                                self.adb.get_doc_record(bib_dict['ID']), 
                                "Documents", header_or_field="header")
        tm_doc_dict = {key:value for key, value in tm_doc_dict.items() if key in old_cols}
        # Adding the entry to the the class dataframe and the model data
        self.tm.beginInsertRows(QtCore.QModelIndex(),
                                self.tm.rowCount(self), self.tm.rowCount(self))
        self.tm.arraydata = self.tm.arraydata.append(tm_doc_dict, ignore_index=True)
        self.tm.endInsertRows()
        # Verifying insertion did nothing wierd (one more row and same columns)
        if (old_row_ct+1 != self.tm.arraydata.shape[0]) or (len(old_cols) != len(self.tm.arraydata.columns)):
            warn_msg = f"extra columns = {set(self.tm.arraydata.columns)-old_cols}"
            warn_msg = warn_msg + f", extra rows = {self.tm.arraydata.shape[0] - old_row_ct+1}."
            warnings.warn("Insertion did something funky, "+warn_msg)

        # Now comparing the entries (if there were duplicates and that was selected)
        if (not force_addition) and (len(sim_ids)>0) and (self.do_action == self.buttonComp):
            comp_id = sim_ids.pop()
            self.openCompareDialog(bib_dict['ID'], comp_id, compare_mode="first new")
            # TODO: Need to respond to choice in compare dialog

        if not supress_view_update:
            # Resetting all the filters to make sure new row is visible
            self.resetAllFilters()

        if select_new_row:
            # Selecting the row corresponding to this new entry (and focus on table)
            view_row = self.proxyModel.getRowFromDocID(bib_dict['ID'])
            self.tableView_Docs.selectRow(view_row)
            self.tableView_Docs.setFocus()

        return bib_dict['ID']

    def deleteBibFromTM(self, doc_id, update_table_model = True):
        """
            This method deletes the bib entry in the table model with the ID passed.
        """
        # Update the table model (if directed to)
        if update_table_model:
            tm_row_id = self.tm.getRowOfDocID(doc_id)
            tm_ind = self.tm.createIndex(tm_row_id, 0)
            # pdb.set_trace()
            # tm_ind = self.proxyModel.mapFromSource(tm_ind) # This will get the row in the proxy model (then change tm to proxyModel)
            self.tm.beginRemoveRows(tm_ind.parent(), tm_ind.row(), tm_ind.row())
            self.tm.arraydata.drop(tm_row_id, axis=0, inplace=True)
            self.tm.endRemoveRows()

    def resetAllFilters(self, sort_added = False):
        '''
            This function will reset all the filters so the view displays all docs

            :param sort_added: bool indicatin whether to sort on added column
        '''
        # Resetting the project combo box and project viewer
        self.comboBox_Filter_Project.blockSignals(True)
        self.comboBox_Filter_Project.setCurrentIndex(0)
        self.comboBox_Filter_Project.blockSignals(False)
        self.treeView_Projects.blockSignals(True)
        self.treeView_Projects.selectionModel().clearSelection()
        self.treeView_Projects.blockSignals(False)
        self.proj_filter_ids = set(self.tm.arraydata.ID)

        # Resetting the custom filter combo box
        self.comboBox_Filter.blockSignals(True)
        self.comboBox_Filter.setCurrentIndex(0)
        self.comboBox_Filter.blockSignals(True)
        self.custom_filter_ids = set(self.tm.arraydata.ID)

        # Resetting the search box
        self.lineEdit_Search.setText("")
        self.search_filter_ids = set(self.tm.arraydata.ID)

        # Resets the filter dialog (and all ids)
        self.diag_filter_ids = set(self.tm.arraydata.ID)
        self.all_filter_ids = set(self.tm.arraydata.ID)

        # Updating the proxy model to reflect showing everything
        # self.tm.beginResetModel()
        self.proxyModel.show_list = list(self.tm.arraydata.ID)
        # self.tm.endResetModel()
        self.proxyModel.invalidateFilter() # Alternative to beginResetModel/endResetModel (and seems faster)

        # Resets the sorting as well (by date added) !! VERY SLOW STEP !!
        if sort_added:
            self.proxyModel.sort(list(self.tm.headerdata).index("Added"),
                                                order = QtCore.Qt.DescendingOrder)

        # Hides the filter msg label and button as well
        self.label_CurrentFilter.hide()
        self.pushButton_ClearFilter.hide()
        self.label_CurrentFilter.setText("Current subset:")

    def loadMetaData(self, doc_ids):
        # This function will load the meta data for the passed id into the fields
        if not isinstance(doc_ids, list):
            warnings.warn("Load meta data called but passed a non list")
            return
        if len(doc_ids)==0: # Checking for deselection of all rows
            doc_row = self.tm.arraydata.iloc[0].copy()
            doc_row[:] = "" # Setting all labels to this
            # Setting blank author table
            doc_contrib = pd.DataFrame({'doc_id':[0], 'contribution':['Author'],
                                        'first_name':[''], 'last_name':['']})
        elif len(doc_ids)>1: # Checking if multiple IDs are selected
            logging.debug(f"Multiple selected IDs: {doc_ids}")
            doc_row = self.tm.arraydata.iloc[0].copy()
            doc_row[:] = "Multiple Selected" # Setting all labels to this
            # Setting blank author table
            doc_contrib = pd.DataFrame({'doc_id':[0], 'contribution':['Author'],
                                        'first_name':[''], 'last_name':['Multiple Selected']})
        else: # Otherwise we assume a single ID was passed in a list
            # Extract the info for the doc_id passed
            doc_row = self.tm.arraydata[self.tm.arraydata.ID == int(doc_ids[0])].iloc[0]
            # Converting any None of NaN values to empty strings
            doc_row[doc_row.isnull()] = ""

            # Gathering the contributors (if any) associated with this document
            doc_contrib = self.adb.get_table("Doc_Auth")
            doc_contrib = doc_contrib[doc_contrib.doc_id == doc_ids[0]]

        # Converting ints to strings
        # doc_ids = [str(doc_id) for doc_id in doc_ids] # Not sure why I every needed to convert to str
        # Special widgets (that require special attention)
        special_widgets = [self.comboBox_DocType, self.textEditExt_Authors,
                            self.lineEdit_Editors]

        # Iterate through meta widgets and load respective data fields
        for index, row in self.field_df.iterrows():
            field_widget = row['meta_widget']
            if (field_widget != None) and (field_widget not in special_widgets):
                # Getting the value of the field (from the table model data)
                field_value = doc_row[row['header_text']]
                # Specific adjustments for year (to remove the '.0')
                if (row['header_text'] == 'Year') and (len(doc_ids)==1):
                    if field_value != "":
                        # This removes the ".0" at end
                        field_value = str(int(field_value))
                # Setting the processed field value into the widet's text
                field_widget.setText(str(field_value))
                # Setting cursor to beginning (for lineEdit widgets)
                if type(field_widget) == QtWidgets.QLineEdit:
                    field_widget.setCursorPosition(0)
            elif (field_widget != None) and (field_widget == self.comboBox_DocType):
                # Getting the value of the field (from the table model data)
                field_value = doc_row[row['header_text']]
                if (isinstance(field_value, float)) and (np.isnan(field_value)):
                    field_value = 'undefined'
                if (field_value is None) or (field_value == ""):
                    field_value = 'undefined'
                self.comboBox_DocType.setCurrentText(field_value)
            elif (field_widget != None) and (field_widget == self.textEditExt_Authors):
                # Select only those who are authors
                flag = (doc_contrib.contribution == 'Author')
                # Creating list of author fullnames
                author_names = list(doc_contrib.loc[flag,'last_name'] + ', '+\
                                    doc_contrib.loc[flag,'first_name'])
                self.textEditExt_Authors.setText("\n".join(author_names))
            elif (field_widget != None) and (field_widget == self.lineEdit_Editors):
                # Select only those who are editors
                flag = (doc_contrib.contribution == 'Editor')
                # Creating list of editor fullnames
                editor_names = list(doc_contrib.loc[flag,'last_name'] + ', '+\
                                    doc_contrib.loc[flag,'first_name'])
                self.lineEdit_Editors.setText("; ".join(editor_names))

        # Adjusting heights to match text contained
        self.textEditExt_Title.setFixedHeight(int(self.textEditExt_Title.document().size().height())+5)
        self.textEditExt_Authors.setFixedHeight(int(self.textEditExt_Authors.document().size().height())+5)
        self.textEditExt_Keywords.setFixedHeight(int(self.textEditExt_Keywords.document().size().height())+5)

        # Gathering the paths (if any) associated with this document
        doc_paths = self.adb.get_table("Doc_Paths")
        doc_paths = doc_paths[doc_paths.doc_id.isin(doc_ids)]

        # Limiting to first 5 (since that's the most labels currently available)
        doc_paths = doc_paths.sort_values('doc_id')[0:5].copy()

        # First hiding all the labels
        for label in self.meta_file_paths:
            label.hide()

        # Now setting label text for any paths found
        full_paths = [x for x in list(doc_paths.full_path) if x != None]
        filenames = [path[path.rfind("/")+1:] for path in full_paths]
        file_path_links = []
        for i in range(len(full_paths)):
            label_text = f"<a href='file:///{full_paths[i]}'>"+filenames[i]+"</a>" #"<font color='blue'>"+paths[i]+"</font>"
            self.meta_file_paths[i].setText(label_text)
            self.meta_file_paths[i].setToolTip(full_paths[i])
            self.meta_file_paths[i].show()

        # Setting label for associated projects
        doc_proj = self.adb.get_table('Doc_Proj_Ext')
        proj_names = doc_proj[doc_proj['doc_id'].isin(doc_ids)]['proj_text'].tolist()
        proj_ids = doc_proj[doc_proj['doc_id'].isin(doc_ids)]['proj_id'].tolist()
        proj_names = [self.project_tree_model.projectPath(proj_id, ignore_x_parents = 1) for proj_id in proj_ids]
        self.lineEdit_Projects.setText(', '.join(proj_names))

        # Setting project specific note combobox
        self.comboBox_ProjNotes.setEnabled(len(proj_names)>0)
        self.textEditExt_ProjNote.setEnabled(len(proj_names)>0)
        self.comboBox_ProjNotes.blockSignals(True)
        self.comboBox_ProjNotes.clear()
        self.comboBox_ProjNotes.blockSignals(False)
        self.comboBox_ProjNotes_IDs = doc_proj[doc_proj['doc_id'].isin(doc_ids)]['proj_id'].tolist()
        proj_paths = [self.project_tree_model.projectPath(proj_id, ignore_x_parents = 1) for proj_id in self.comboBox_ProjNotes_IDs]
        self.comboBox_ProjNotes.addItems(proj_paths)

    def loadProjectNote(self):
        # This function loads the relevant project note (if there is one)

        # Only do this if the proj note is enabled and one row is selected
        do_this = self.textEditExt_ProjNote.isEnabled() and (self.selected_doc_ids != -1) \
                        and (len(self.selected_doc_ids) == 1)
        if do_this:
            # Grab the selected project and selected document
            curr_proj_id = self.comboBox_ProjNotes_IDs[self.comboBox_ProjNotes.currentIndex()]
            sel_doc_id = self.selected_doc_ids[0]
            # Grab the table of project notes
            proj_notes = self.adb.get_table('Proj_Notes')
            # Check if there is a note
            row_flag = (proj_notes.doc_id == sel_doc_id) & (proj_notes.proj_id == curr_proj_id)
            if row_flag.any():
                if len(proj_notes[row_flag].index) == 1:
                    # Setting the project note accordingly
                    ind = proj_notes[row_flag].index[0]
                    self.textEditExt_ProjNote.setText(proj_notes.at[ind,'proj_note'])
                else:
                    warnings.warn(f"Several notes found for the same doc id "+\
                                f"({sel_doc_id}) project ({curr_proj_id}) pair.")
                    return
            else:
                # No project notes found so a black is put in widget
                self.textEditExt_ProjNote.setText('')

    def findDuplicates(self, doc_id = None, compare_fields = None, bib_dict = None):
        """
            This function checks if any of the existing documents are similar
            to the bib information passed. Either 'doc_id' and 'compare_fields'
            must be passed or 'bib_dict' must be passed.

            :param doc_id: int with a doc id that is being compared
            :param compare_fields: list of strings containing the fields that
                should be compared (In header text format, ie Capitalized).
            :param bib_dict: dictionary whose keys are columns and values are those
                to check against.
        """
        sim_ids = set()
        # Checking if doc_id or bib_dict was passed
        if doc_id != None:
            if compare_fields == None:
                logging.debug("Must specify fields to compare along with document id.")

            # Extracting the row index for the passed doc_id
            row_ind = self.tm.arraydata[self.tm.arraydata['ID']==doc_id].index[0]
            # Checking if bib_dict was also erroneously passed
            if bib_dict != None:
                warnings.warn('Bibdict is being overwritten. Should not pass" +\
                                "all three arguments to findDuplicates.')
            # Creating dictionary of values of each field for given doc id
            bib_dict = {field: self.tm.arraydata.at[row_ind,field] for field \
                        in compare_fields if field in self.tm.arraydata.columns}
        elif bib_dict == None:
            warnings.warn('Insufficient arguments passed to findDuplicates.')
            return

        # Gather IDs that share values with any of the passed fields
        for field, field_val in bib_dict.items():
            # # Check if field is in the table (and skip if not)
            # if field not in self.tm.arraydata.columns:
            # 	warnings.warn(f"Field ({field}) is not found in the columns, "+\
            # 					"cannot find duplicates using it")
            # 	continue
            # # Get value of the field for the doc_id
            # field_val = self.tm.arraydata.at[row_ind,field]
            # Get doc_ids of those with same value
            new_ids = set(self.tm.arraydata[self.tm.arraydata[field]==field_val]['ID'])
            # Merge in the newly found IDs
            sim_ids = sim_ids | new_ids

        if doc_id is not None:
            # Removing the id that was passed (since it will definitely be in there)
            sim_ids = sim_ids - {doc_id}
            logging.debug(f"Primary: {doc_id}, Similar: {sim_ids}")
        return sim_ids

    def updateBackups(self):
        # This function updates backups as dictated by the current settings

        # Grabbing the backup settings
        backup_num = int(self.config["Backups"]["backups_number"])
        backup_freq = self.config["Backups"]["backups_frequency"]

        if backup_num == 0:
            return     # No backups

        # Setting time delta to compare (for testing whether to make a backup)
        time_thresh = {'On App Start': timedelta(days=0),
                        'Daily': timedelta(days=1),
                        'Weekly': timedelta(days=7),
                        'Monthly': timedelta(days=30)}
        if backup_freq not in time_thresh:
            warnings.warn(f"the back up frequency specified ({backup_freq}) "+\
            "is not reconized.")
            return

        # Extracting base filename and backups folder path
        db_path = self.adb.db_path
        base_filename = db_path[db_path.rfind("\\")+1:-7]
        backup_folder = self.config["Backups"]["backups_folder"]

        # Getting list of backup files (and creating directory if not found)
        try:
            backup_files = os.listdir(backup_folder)
        except FileNotFoundError:
            logging.debug("Creating directory for backup files.")
            os.mkdir(backup_folder)
            backup_files = os.listdir(backup_folder)

        # Subsetting to those files associated with the current DB (and are sqlite)
        backup_files = [filename for filename in backup_files if ('.sqlite' in filename)]
        backup_files = [filename for filename in backup_files if (base_filename in filename)]

        # Creating dataframe of current backup files (and their dates)
        backup_dates = [datetime.fromtimestamp(os.path.getmtime(backup_folder+"\\"+file)) for file in backup_files]
        backups = pd.DataFrame({'filename':backup_files, 'mtime':backup_dates})
        backups.sort_values('mtime', inplace=True)

        # Checking if there are any backups currently in existence
        if backups.shape[0] > 0:
            # Get date of most recent backup
            backup_last = backups.iloc[-1]['mtime'].to_pydatetime()
            # Checking if it is time for another backup
            time_since = datetime.now()-backup_last
            if  time_since < time_thresh[backup_freq]:
                return
            logging.debug(f"Last backup was {time_since.days} day(s) ago, making a new backup.")
        else:
            new_backup_filename = backup_folder+'\\'+base_filename+'_backup_01.sqlite'
            logging.debug(f"No backups found, making a new backup: "+new_backup_filename)
            copyfile(db_path, new_backup_filename)
            return

        # Deleting extra backups and renaming others
        for i in range(backups.shape[0]): #, -1, -1):
            backup_path = backup_folder+'\\'+backups.iloc[i]['filename']
            # Remove any backups beyond the number specified to carry
            if i <= (backups.shape[0]-backup_num):
                logging.debug(f"Removing extra backup: {backup_path}")
                os.remove(backup_path)
                continue
            else:	# If keeping then rename the backup (pushing it up the list)
                new_filename = base_filename+f'_backup_{str(backups.shape[0]-i+1).zfill(2)}.sqlite'
                # logging.debug(f"Renaming backup to: {new_filename}")
                os.rename(backup_path, backup_folder+'\\'+new_filename)

        # Saving the current backup
        copyfile(self.adb.db_path, backup_folder+'\\'+base_filename+'_backup_01.sqlite')

    def checkWatchedFolders(self):
        """
            This function will check the watch folders and return either False if
            there are no new files or true if there are new files. If there are new
            files then a class variable will be set that is a list of the new ids
        """
        # Grab the current list of watched folder paths
        watch_paths = [x[1] for x in self.config.items('Watch Paths')]
        files_found = pd.DataFrame()
        # For each path gather all files and extra information
        for path in watch_paths:
            filenames = os.listdir(path.replace("\\", "/"))
            num_files = len(filenames)
            # Getting the create time for each file
            ctimes = []
            mtimes = []
            fullpaths = []
            for file in filenames:
                file_path = (path+'\\'+file).replace("\\", "/")
                fullpaths += [file_path]
                ctimes += [date.fromtimestamp(os.path.getctime(file_path))]
                mtimes += [date.fromtimestamp(os.path.getmtime(file_path))]
                #logging.debug()
            temp_df = pd.DataFrame({'path': [path]*num_files,
                                    'filename': filenames,
                                    'full_path': fullpaths,
                                    'created': ctimes,
                                    'modified': mtimes})
            files_found = pd.concat([files_found, temp_df])
        files_found

        # Grabbing the current list of known file paths
        doc_paths = self.adb.get_table(table_name="Doc_Paths")

        # Checking which files are new
        files_found = files_found.merge(doc_paths, how = "left",
                                        on = "full_path", indicator=True)
        new_file_flag = files_found._merge == "left_only"
        num_new_files = sum(new_file_flag)
        print(f"Found {num_new_files} new files in watched folders:")
        for file_path in files_found[new_file_flag]['path'].unique():
            print(f"Folder: {file_path}")
            print(files_found[new_file_flag & (files_found['path']==file_path)].filename)

        # Updating the last check variable
        self.config['Other Variables']['last_check'] = str(date.today())

        # Writing another config file
        with open('user/config.ini', 'w') as configfile:
            self.config.write(configfile)

####end
##### Initialization Functions ##################################################
    def initProjectViewModel(self, connect_selection=True, connect_context=True):
        """
            Setting up the project viewer (tree view)
            :param reconnect: boolean indicating whether to connect signals
                (useful when this function is called again later to avoid reconnecting)
        """
        self.project_tree_model = projTreeModel(self.projects, self) # QtGui.QStandardItemModel() #
        # self.initProjectTreeView()
        self.treeView_Projects.setModel(self.project_tree_model)
        # self.populateTreeModel()
        self.treeView_Projects.setStyleSheet(open("lib/ArDa/mystylesheet.css").read())
        #self.treeView_Projects.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        # Enabling drops
        self.treeView_Projects.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)

        # Listening for changes in the projects that are selected
        # TODO: After view has been reimplmented, re-enable listening
        self.projSelectionModel = self.treeView_Projects.selectionModel()
        if connect_selection:
            # Connecting project selection
            self.projSelectionModel.selectionChanged.connect(self.projSelectChanged)
        if connect_context:
            # Defining the context menu for document viewer
            self.treeView_Projects.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.treeView_Projects.customContextMenuRequested.connect(self.openProjContextMenu)
        # TODO: Redraw the stylesheet images so the lines go through the arrows

        # Expanding any projects that were specified in expand_default in DB
        for index, row in self.projects.iterrows():
            if row['expand_default']==1:
                item_ind = self.project_tree_model.indexFromProjID(row.proj_id)
                self.treeView_Projects.expand(item_ind)

        # Resize the columns to fit the information populated
        for i in range(len(self.project_tree_model.rootItem.itemData)):
            self.treeView_Projects.resizeColumnToContents(i)

    def initDocumentViewer(self):
        # Initialize the various aspects of the table view that holds the documents

        # Getting document data and field info
        alldocs = self.adb.get_table("Documents", use_header_text=True)
        self.field_df = self.adb.get_table("Fields")
        doc_field_df = self.field_df[self.field_df['table_name']=="Documents"].copy()

        # Sorting data fields by what's specified (hidden columns go to end)
        doc_field_df.loc[doc_field_df.doc_table_order==-1,'doc_table_order'] = 1000
        default_col_order = doc_field_df.sort_values('doc_table_order')['header_text']
        alldocs = alldocs[default_col_order.tolist()].copy()
        # Sorting the actual data on the added date
        alldocs.sort_values('Added', ascending = False, inplace = True)

        # Putting documents in Table View
        header = alldocs.columns
        self.tm = docTableModel(alldocs, header, parent=self) #, self)

        # Creating the table view and adding to app
        self.tableView_Docs = docTableView(self.gridLayoutWidget) #QtWidgets.QTableView(self.gridLayoutWidget)
        self.tableView_Docs.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.gridLayout_2.addWidget(self.tableView_Docs, 4, 0, 1, 4)

        # This in-between model will allow for sorting and easier filtering
        self.proxyModel = mySortFilterProxy(table_model=self.tm) #QtCore.QSortFilterProxyModel() #self)
        self.proxyModel.setSourceModel(self.tm)
        self.tableView_Docs.setModel(self.proxyModel)
        # # Turning off dynamic sorting (hoping this would speed up reset... but alas)
        # self.proxyModel.setDynamicSortFilter(False)
        # Setting the widths of the column (I think...)
        self.tableView_Docs.verticalHeader().setDefaultSectionSize(self.h_scale)
        # Makes whole row selected instead of single cells
        self.tableView_Docs.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        # Make only single rows selectable
        self.tableView_Docs.setSelectionMode(QtWidgets.QTableView.ContiguousSelection)
        # Making the columns sortable
        self.tableView_Docs.setSortingEnabled(True)
        # Making column order draggable
        self.tableView_Docs.horizontalHeader().setSectionsMovable(True)

        # Resizing the columns to fit the information populated
        # TODO: Verify the default widths works, and remove this resizeColumnToContents (seems to be very time costly)
        # for i in range(len(self.tm.headerdata)):
        # 	self.tableView_Docs.resizeColumnToContents(i)

        # Getting the default field widths
        col_width_dict = dict(zip(doc_field_df.header_text, doc_field_df.col_width))
        data_header = list(self.tm.arraydata.columns)
        # Setting the default widths according to fields table
        for i in range(len(data_header)):
            col_text = data_header[i]
            self.tableView_Docs.setColumnWidth(i, int(col_width_dict[col_text]))

        # Setting initial doc id selection to nothing
        self.selected_doc_ids = -1

        # Setting the view so it supports dragging from
        self.tableView_Docs.setDragEnabled(True)

        # Listening for changes in the rows that are selected (to update meta)
        self.DocSelectionModel = self.tableView_Docs.selectionModel()
        self.DocSelectionModel.selectionChanged.connect(self.rowSelectChanged)

        # listening for double clicks (and making meta data the focus)
        self.tableView_Docs.doubleClicked.connect(lambda :self.tabSidePanel.setCurrentIndex(0))

        # Defining the context menu for document viewer
        self.tableView_Docs.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableView_Docs.customContextMenuRequested.connect(self.openDocContextMenu)

    def initColumnCheckboxes(self):
        # This function initializes all the column toggles
        self.colCheckBoxes = dict()
        self.funs = dict()
        # Extract the fields in the documents tables (and sort by name)
        doc_fields = self.field_df[self.field_df['table_name']=="Documents"].copy()
        doc_fields.sort_values('header_text', inplace=True)
        # Iterate over every field in this table
        for index, row in doc_fields.iterrows():
            # Getting the col index associated with this column
            col_ind = self.tm.arraydata.columns.tolist().index(row['header_text'])
            field = row['field']
            h_text = str(row['header_text'])
            # Create a checkbox for that field
            cboxwidg = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
            self.colCheckBoxes[field] = cboxwidg
            self.verticalLayout_6.addWidget(cboxwidg)
            cboxwidg.setText(h_text)
            # Turn the check box on or off (and set column visibility accordingly)
            if (not np.isnan(row['doc_table_order'])) and (row['doc_table_order'] != -1):
                cboxwidg.setChecked(True)
            else:
                self.tableView_Docs.setColumnHidden(col_ind, True)
            # Connect the check box to a listener to toggle column visibility
            temp_fun = (lambda *args, h_text=h_text: self.toggleColumnVisibility(h_text))
            self.colCheckBoxes[field].stateChanged.connect(temp_fun)

    def toggleColumnVisibility(self, header_text):
        # Find column index
        col_ind = self.tm.arraydata.columns.tolist().index(header_text)
        if self.tableView_Docs.isColumnHidden(col_ind):
            self.tableView_Docs.setColumnHidden(col_ind, False)
        else:
            self.tableView_Docs.setColumnHidden(col_ind, True)

    def initSidePanelButtons(self):
        # Set the edit project button to disabled initially
        self.pushButton_EditProject.setEnabled(False)

        # Connects the reponse to the various buttons in the side panel
        self.pushButton_EditProject.clicked.connect(self.openProjectDialog)
        self.pushButton_OpenProjectFolder.clicked.connect(self.openProjectFolder)
        self.pushButton_NewProject.clicked.connect(lambda : self.openProjectDialog(new_project=True))

    def initMetaDataFields(self):
        # Adding and formatting the title widget
        self.textEditExt_Title = QTextEditExt(self.tabSidePanelPage1_2, self,
                                    queriable=True, capitalize=True, meta_extract=True)
        self.textEditExt_Title.setPlaceholderText('Title')
        self.textEditExt_Title.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.textEditExt_Title.setMinimumHeight(200)
        self.textEditExt_Title.setAcceptDrops(False)
        self.textEditExt_Title.setAcceptRichText(False)
        self.verticalLayout_2.insertWidget(1, self.textEditExt_Title)
        font = QtGui.QFont("Arial", 12, 75, True)
        font.setBold(True)
        self.textEditExt_Title.setFont(font)
        self.parent.setTabOrder(self.comboBox_DocType ,self.textEditExt_Title)
        # Removing old placeholder widget
        self.textEdit_Title.hide()

        # Removing old placeholder widget (for authors)
        self.formLayout.removeWidget(self.textEdit_Authors)
        self.textEdit_Authors.deleteLater()
        self.textEdit_Authors = None
        # Adding and formatting the authors widget
        # self.textEditExt_Authors = QTextEditExt(self.scrollAreaWidgetContents_2,
        # 								self, queriable = True, capitalize = True,
        # 								enter_resize = True)
        self.textEditExt_Authors = QTextEditExt(self.scrollAreaWidgetContents_2,
                                                    self, queriable = True,
                                                    capitalize = True,
                                                    enter_resize=True)
        self.textEditExt_Authors.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.textEditExt_Authors.setAcceptDrops(False)
        self.textEditExt_Authors.setToolTip("Last, First (one author per line)")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.textEditExt_Authors)
        self.parent.setTabOrder(self.textEditExt_Title, self.textEditExt_Authors)
        self.parent.setTabOrder(self.textEditExt_Authors, self.lineEdit_Journal)

        # Adding and formatting the abstract widget
        self.textEditExt_Abstract = QTextEditExt(self.scrollAreaWidgetContents_2,
                                        self, queriable = True)
        self.textEditExt_Abstract.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.textEditExt_Abstract.setAcceptRichText(False)
        self.formLayout.setWidget(10, QtWidgets.QFormLayout.FieldRole, self.textEditExt_Abstract)
        self.parent.setTabOrder(self.lineEdit_Cite_Key, self.textEditExt_Abstract)
        self.textEditExt_Abstract.setMinimumHeight(200)

        # Adding and formatting the keywords widget
        self.textEditExt_Keywords = QTextEditExt(self.scrollAreaWidgetContents_2, self)
        self.textEditExt_Keywords.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.textEditExt_Keywords.setAcceptRichText(False)
        self.formLayout.setWidget(11, QtWidgets.QFormLayout.FieldRole, self.textEditExt_Keywords)
        self.parent.setTabOrder(self.textEditExt_Abstract, self.textEditExt_Keywords)
        self.parent.setTabOrder(self.textEditExt_Keywords, self.lineEdit_Projects)

        # Adding a QCompleter to the journals field
        journals = sorted(self.tm.arraydata['Journal'].dropna().unique())
        self.completer_journal = QtWidgets.QCompleter(journals)
        self.completer_journal.setFilterMode(QtCore.Qt.MatchContains)
        self.completer_journal.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.lineEdit_Journal.setCompleter(self.completer_journal)

        # Adding a (custom) QCompleter to the authors field
        author_df = self.adb.get_table("Doc_Auth")
        authors = sorted(author_df['full_name'].dropna().unique())
        self.completer_authors = MyDictionaryCompleter(myKeywords=authors)
        # self.completer_authors = QtWidgets.QCompleter(authors)
        self.completer_authors.setFilterMode(QtCore.Qt.MatchContains)
        self.completer_authors.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.textEditExt_Authors.setCompleter(self.completer_authors)

        # Adding and formatting the note and project note widgets
        self.textEditExt_Note = QTextEditExt(self.tab, self)
        self.verticalLayout_7.insertWidget(1, self.textEditExt_Note)
        self.textEditExt_ProjNote = QTextEditExt(self.tab, self)
        self.verticalLayout_7.addWidget(self.textEditExt_ProjNote)

        # Clearing and inserting the doc type items
        self.comboBox_DocType.clear()
        doc_types = list(self.tm.arraydata['Type'].dropna().unique())
        doc_types.sort(key=str.lower)
        doc_types.append('undefined')
        self.comboBox_DocType.addItems(doc_types)

        # Creating column which holds the actual meta field objects
        temp_widgets = []
        for widget_name in list(self.field_df.meta_widget_name):
            temp_widgets.append(getattr(self,widget_name,None))
        self.field_df['meta_widget'] = temp_widgets

        # Sets various attributes of the meta data fields (like hover responses)
        for widget in self.field_df.meta_widget: #fields:
            if widget is not None:
                widget.setStyleSheet(open("lib/ArDa/mystylesheet.css").read())
        # TODO: Fix hover for QTextEdits (not sure why it's not working)
        #self.textEdit_Title.setStyleSheet(open("lib/ArDa/mystylesheet.css").read())

        # Sizing them (for empty values)
        self.textEditExt_Title.setFixedHeight(int(self.textEditExt_Title.document().size().height())+12)
        self.textEditExt_Authors.setFixedHeight(int(self.textEditExt_Authors.document().size().height())+10)
        self.textEditExt_Keywords.setFixedHeight(int(self.textEditExt_Keywords.document().size().height())+10)

        # Connecting all the simple fields to their listening functions
        for index, row in self.field_df.iterrows():
            # Connecting all the simple fields
            if row['meta_widget_name'].startswith('lineEdit'):
                # Odd (but necesary) way to implement a lambda fun with a different variable each time
                f_key = row['field']
                row['meta_widget'].editingFinished.connect(lambda f_key=f_key: self.simpleMetaFieldChanged(f_key))
        # Connecting the slightly more complex fields
        self.textEditExt_Title.editingFinished.connect(lambda: self.simpleMetaFieldChanged('title'))
        self.textEditExt_Abstract.editingFinished.connect(lambda: self.simpleMetaFieldChanged('abstract'))
        self.textEditExt_Authors.editingFinished.connect(lambda: self.simpleMetaFieldChanged('author_lasts'))
        self.textEditExt_Keywords.editingFinished.connect(lambda: self.simpleMetaFieldChanged('keyword'))
        self.textEditExt_Note.editingFinished.connect(lambda: self.simpleMetaFieldChanged('note'))
        self.textEditExt_ProjNote.editingFinished.connect(self.projectNoteChanged)
        self.comboBox_DocType.currentIndexChanged.connect(lambda: self.simpleMetaFieldChanged('doc_type'))

        # Connecting the project note combo box
        self.comboBox_ProjNotes.currentIndexChanged.connect(self.loadProjectNote)

        # Initializing the file path labels (and hiding them all initially)
        self.meta_file_paths = [0, 1, 2, 3, 4]
        for i in range(5): #label in self.meta_file_paths:
            self.meta_file_paths[i] = QLabelElided(self.scrollAreaWidgetContents_2) #QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
            # TODO: Need to further fix the QLabelEllided so it displays hyperlinks
            self.meta_file_paths[i].hide()
            self.meta_file_paths[i].setOpenExternalLinks(True)
            self.meta_file_paths[i].setMinimumSize(200, 30)
            self.meta_file_paths[i].setStyleSheet('color: blue; text-decoration: underline')
            self.verticalLayout_MetaFiles.insertWidget(i, self.meta_file_paths[i])
            # Attaching the context menu
            self.meta_file_paths[i].setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.meta_file_paths[i].customContextMenuRequested.connect(lambda pos, i=i:self.openPathContextMenu(pos, i))

        # Connecting the add path button
        self.pushButton_AddFile.clicked.connect(self.addFilePath)

        # Correcting the strange color resulting from the sidepanel scroll area
        self.scrollAreaWidgetContents_2.setObjectName('sidePanel')
        self.scrollArea.setStyleSheet("QWidget#sidePanel{background-color:white;}")

    def connectMenuActions(self):
        # This function will attach all the menu choices to their relavant response
        self.action_Exit.triggered.connect(self.parent.close)
        self.actionCheck_for_New_Docs.triggered.connect(self.checkWatchedFolders)
        self.actionOpen_Selected_in_Acrobat.triggered.connect(self.openFileReader)
        self.actionPDF_File.triggered.connect(self.addFromPDFFile)
        self.actionBib_File.triggered.connect(self.addFromBibFile)
        self.action_New_Blank_Entry.triggered.connect(lambda: self.addBibEntry())
        self.actionFilter_by_Author.triggered.connect(lambda: self.openFilterDialog("Author"))
        self.actionFilter_by_Journal.triggered.connect(lambda: self.openFilterDialog("Journal"))
        self.actionFilter_by_Keyword.triggered.connect(lambda: self.openFilterDialog("Keyword"))
        self.actionBuild_Bib_Files.triggered.connect(self.write_all_proj_bib_files)
        self.action_Settings.triggered.connect(self.openSettingsDialog)
        self.actionSearch_Crossref.triggered.connect(self.openDocSearchDialog)

    def buildProjectComboBoxes(self, init_proj_id = None, connect_signals = True):
        # This function will initialize the project combo boxes with the projects
        #		found in the DB table "Projects"

        # Grab projects table and reset the index so it matches the project id
        self.projects = self.adb.get_table("Projects")
        self.projects.set_index('proj_id', drop=False, inplace=True)

        base_folders = self.projects[self.projects['parent_id']==0]\
                                                .sort_values(by=['proj_text'])

        # Setting the default selected proj (indicates all projects)
        self.selected_proj_id = -1

        # Adding the first and default "All Projects" selection
        self.comboBox_Project_Choices = ['All projects']
        # Starting list of project ids in same order as the combobox text
        self.comboBox_Project_IDs = [-1] # Reserved for all projects
        # Recursively adding the parent folders and child folders underneath
        proj_text_list, proj_id_list = self.adb.get_topo_list_proj_children(0, "  ")
        self.comboBox_Project_Choices += proj_text_list
        self.comboBox_Project_IDs += proj_id_list

        # Adding the list of projects to the combo box
        self.comboBox_Filter_Project.addItems(self.comboBox_Project_Choices)

        # Setting the current choice (if one was passed)
        if init_proj_id != None:
            combo_ind = self.comboBox_Project_IDs.index(init_proj_id)
            self.comboBox_Filter_Project.setCurrentIndex(combo_ind)

        # Connecting combo box to action
        if connect_signals:
            self.comboBox_Filter_Project.currentIndexChanged.connect(self.projectFilterEngaged)

        # Initializing the filter id set
        self.proj_filter_ids = set(self.tm.arraydata.ID)

    def buildFilterComboBoxes(self):
        # This function will initialize the filter combo box with the filters
        #		found in the DB table "Custom_Filters"

        # Grab the custom filters and sort by the filter ID
        filters = self.adb.get_table("Custom_Filters")
        filters.sort_values('filter_id', inplace=True)
        # Adding text to combo box (after clearing out items)
        self.comboBox_Filter.clear()
        self.comboBox_Filter.addItems(list(filters["filter_name"]))

        # Connecting combo box to action
        #self.comboBox_Filter_Project.currentIndexChanged.connect(self.FilterEngaged)
        #logging.debug(self.folders)

        # Initializing the filter id set
        self.custom_filter_ids = set(self.tm.arraydata.ID)

    def buildColumnComboBoxes(self):
        # This function will initialize the search field combo box
        self.comboBox_Search_Column.addItems(["All Fields"]+\
                                    list(self.tm.headerdata.sort_values()))
        # Connecting combo box to action
        self.comboBox_Search_Column.currentIndexChanged.connect(self.SearchEngaged)

    def initSearchBox(self):
        # This function initializes everything asociated with the search box

        # Initializing the filter id set
        self.search_filter_ids = set(self.tm.arraydata.ID)

        # Also initializing the dialog id set (since nowhere else makes sense)
        self.diag_filter_ids = set(self.tm.arraydata.ID)
        self.all_filter_ids = set(self.tm.arraydata.ID)

        # Connecting search box to action
        self.lineEdit_Search.returnPressed.connect(self.SearchEngaged)

        # Initially hiding the filter message
        self.label_CurrentFilter.hide()
        self.pushButton_ClearFilter.hide()
        self.label_CurrentFilter.setText("Current subset:")

        # Connecting clear filter button
        self.pushButton_ClearFilter.clicked.connect(self.resetAllFilters)

####end

def excepthook(exc_type, exc_value, exc_tb):
    # This function replaces the hook that sends exceptions to the stdout (set below in main)
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.exception(f'ArDa shutdown due to an error: \n {tb}')
    logging.debug('\n\n'+''.join(['#']*80)+'\n')
    sys.exit()
    # QtWidgets.QApplication.quit() # If I use this line, then it finishes the rest of the code after app.exec()
    # or QtWidgets.QApplication.exit(0)


def find_vcs_root(test, dirs=(".git",), default=None):
    # Takes a path and searches upward until it finds the vcs's root folder (eg. the root of a git repo)
    import os
    prev, test = None, os.path.abspath(test)
    while prev != test:
        if any(os.path.isdir(os.path.join(test, d)) for d in dirs):
            return test
        prev, test = test, os.path.abspath(os.path.join(test, os.pardir))
    return default

if __name__ == '__main__':
    # Moving to the root of git repo (if not there already)
    print(f"Current directory: {os.getcwd()}")
    git_root = find_vcs_root(os.getcwd())
    os.chdir(git_root)
    print(f"Moved to : {os.getcwd()}")
    
    # Checking if user directory exists (and initializing otherwise)
    if not os.path.exists('user'):
        print("User directory doesn't exist, initializing one...")
        arda_init.init_user()

    # Set up the logging file
    logging.basicConfig(filename='user/latest.log', level=logging.DEBUG,
                        format='%(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
                        # format='%(levelname)s  :%(message)s')

    # Replace the default exception hook function with my own to log exceptions
    sys.excepthook = excepthook
    
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    
    prog = ArDa(MainWindow)
    MainWindow.show()
    # sys.exit(app.exec_()) # Post said PyQt5 no longer needed the sys.exit() part

    app.exec_()
    logging.debug('ArDa shutdown successfully \n\n'+''.join(['#']*80)+'\n')