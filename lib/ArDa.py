import sys
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
from layout_main import Ui_MainWindow
import sqlite3, os
import pandas as pd
import numpy as np
from datetime import date
import configparser
from myExtensions import docTableModel, projTreeModel, mySortFilterProxy
from project_dialog import ProjectDialog
import aux_functions as aux
import pdb, warnings

class ArDa(Ui_MainWindow):

	# Class variables
	h_scale = 40   #height of one row in the table

	def __init__(self, dialog):
		Ui_MainWindow.__init__(self)
		self.setupUi(dialog)
		self.parent = dialog

		# Load variables from the config file
		self.loadConfig()

		# Initialize and populate the document table
		self.initDocumentViewer()

		# Build various combo boxes
		self.buildProjectComboBoxes()
		self.buildFilterComboBoxes()
		self.buildColumnComboBoxes()

		# Initialize the saerch box
		self.initSearchBox()

		# Initialize sidepanel buttons (ie connect them, set diabled, etc...)
		self.initSidePanelButtons()

		# Set other attributes of metadata fields
		self.setMetaDataFieldAttributes()

		# TODO: Put all of this into a buildProjectTreeView function
		# Setting up the project viewer (tree view)
		self.project_tree_model = projTreeModel(self.projects, self.db_path) # QtGui.QStandardItemModel() #
		# self.initProjectTreeView()
		self.treeView_Projects.setModel(self.project_tree_model)
		# self.populateTreeModel()
		self.treeView_Projects.setStyleSheet(open("mystylesheet.css").read())
		#self.treeView_Projects.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
		# Now it resizes the columns to fit the information populated
		for i in range(len(self.project_tree_model.rootItem.itemData)):
			self.treeView_Projects.resizeColumnToContents(i)
		# Enabling drops
		self.treeView_Projects.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)

		# Listening for changes in the projects that are selected
		# TODO: After view has been reimplmented, re-enable listening
		self.projSelectionModel = self.treeView_Projects.selectionModel()
		self.projSelectionModel.selectionChanged.connect(self.projSelectChanged)
		# TODO: Redraw the stylesheet images so the lines go through the arrows


		# Connecting the menu actions to responses
		self.connectMenuActions()

		# Checking the watched folders
		if (self.config["General Properties"]["start_up_check_watched_folders"]=="True"):
			self.checkWatchedFolders()

##### Other? Functions ##############################################################
	def loadConfig(self):
		"""
			This function reads the config file and sets various variables
			accordingly.
		"""
		print('Reading config file')
		self.config = configparser.ConfigParser()
		self.config.read("../user/config.ini")

		# Grabbing the variable values as specified in the config file
		self.db_path = self.config.get("Data Sources", "DB_path")  #"Data Sources" refers to the section
		print("DB Path: "+self.db_path)
		self.watch_path = self.config.get("Watch Paths", "path_001")
		self.last_check_watched = self.config.get("Other Variables", "last_check")

####end
##### Action/Response Functions ################################################
	def addEmptyBibEntry(self):
		# This function will add a new (empty) bib entry into the table and DB
		# new_doc_id = aux.getNextDocID(self.db_path)
		# print(new_doc_id)
		bib_dict = dict()
		self.addNewBibEntry(bib_dict)

	def addFilePath(self):
		# This function calls a file browser and adds the selected pdf file to the doc_paths

		# Setting the dialog start path (in case the proj path doesn't exist)
		dialog_path = "C:/Users/Phoenix/Documents/Literature"
		# TODO: Move this default start path to a config variable
		# Open a folder dialog to get a selected path
		new_file_path = QtWidgets.QFileDialog.getOpenFileName(self.parent,
																'Open File',
																dialog_path)[0]

		# Inserting a new record with this path into doc_paths
		new_doc_path = {'doc_id': self.selected_doc_id,
						'full_path': new_file_path}
		aux.insertIntoDB(new_doc_path, 'Doc_Paths', self.db_path)

		# Updating the meta fields to show the change
		self.loadMetaData(self.selected_doc_id)

	def addFromPDFFile(self):
		# This function calls a file browser and adds the selected pdf file
		# Setting the dialog start path (in case the proj path doesn't exist)
		dialog_path = "C:/Users/Phoenix/Documents/Literature"
		# TODO: Move this default start path to a config variable
		# Open a folder dialog to get a selected path
		new_file_path = QtWidgets.QFileDialog.getOpenFileName(
													self.parent,
													'Open File',
													dialog_path)[0]

		# Extracting just the filename from the path
		new_filename = new_file_path[new_file_path.rfind("/")+1:]

		# Updating the project path field
		print(new_file_path)
		# After file path field exists update it here


		new_bib_dict = {'Title': new_filename}
		new_bib_dict['full_path'] = new_file_path
		self.addNewBibEntry(new_bib_dict)
		# TODO: Add a new bib entry with this file path

		# Defining dictionary for doc_paths

	def openFileReader(self):
		# This function will open the selected file(s) in a pdf reader (acrobat for now)
		# Checking if there is one document selected
		if self.selected_doc_id != -1:
			# Grabbing any paths associated with this document
			conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
			curs = conn.cursor()
			curs.execute(f"SELECT * FROM Doc_Paths WHERE doc_id = {self.selected_doc_id}")
			doc_paths = pd.DataFrame(curs.fetchall(),columns=['doc_id', 'fullpath'])
			conn.close()
			# Checking if there are paths found
			if doc_paths.shape[0] > 0:
				file_path = doc_paths.at[0,"fullpath"]
				print(f"Opening {file_path}")
				os.system("start "+file_path)
			else:
				print(f"No file paths found for doc_id: {self.selected_doc_id}")
		else:
			print("Either no documents or multiple documents are selected. Need to implement this.")

	def openProjectDialog(self):
		self.window = QtWidgets.QWidget()
		self.ui = ProjectDialog(self.window, self.selected_proj_id, self.db_path)
		#self.ui.setupUi()
		self.window.show()

	def projectFilterEngaged(self):
		# This function grabs the current selection in the project filter drop
		#	down menu and distills filters to those docs in the table view
		curr_choice = self.comboBox_Filter_Project.currentText().lstrip()
		if curr_choice == 'All projects':
			self.tm.beginResetModel()
			self.proj_filter_ids = set(self.tm.arraydata.ID)
			self.all_filter_ids = self.proj_filter_ids & \
								self.custom_filter_ids & self.search_filter_ids
			self.proxyModel.show_list = list(self.all_filter_ids)
			self.tm.endResetModel()
			# Clear any selection in the project tree view
			self.treeView_Projects.selectionModel().clearSelection()
		else:
			# Get the project id associated with menu choice
			self.selected_proj_id = self.comboBox_Project_IDs[\
									self.comboBox_Filter_Project.currentIndex()]
			# Selecting all doc IDs that are in this project
			conn = sqlite3.connect(self.db_path)
			curs = conn.cursor()
			curs.execute(f'SELECT doc_id FROM Doc_Proj WHERE proj_id == "{self.selected_proj_id}"')
			self.proj_filter_ids = set([x[0] for x in curs.fetchall()])
			conn.close()

			# Changing the filtered list in the proxy model
			self.tm.beginResetModel()
			self.all_filter_ids = self.proj_filter_ids & \
								self.custom_filter_ids & self.search_filter_ids
			self.proxyModel.show_list = list(self.all_filter_ids)
			self.tm.endResetModel()

		# Now we select the corresponding row in the project tree view
		# FIXME: Fix sync btw project combobox and project tree view (currently this selects only the cell not the row)
		# self.treeView_Projects.selectionModel().select(self.tree_nodes[curr_choice_id].index(), QtCore.QItemSelectionModel.Select)
		# TODO: Also need to deselect the currently selected row in the qtreeview (already handle clearin selection for "All Documents")
		# self.treeView_Projects.selectionModel().select(self.treeView_Projects.selectionModel().selectedRows()[0], QtCore.QItemSelectionModel.Toggle)

		# self.proxyModel.setFilterKeyColumn(self.search_col)

	def rowSelectChanged(self):
		# Undoing previous document selection
		self.selected_doc_id = -1
		# Getting the current list of rows selected
		sel_rows = self.tableView_Docs.selectionModel().selectedRows()
		sel_row_indices = [i.row() for i in sorted(sel_rows)]
		if len(sel_row_indices) == 0:  	# No rows are selected
			return
		elif len(sel_row_indices) == 1: 	# Exactly one row is selected
			title = self.proxyModel.index(sel_row_indices[0],2).data()
			self.selected_doc_id = self.proxyModel.index(sel_row_indices[0],0).data()
			self.loadMetaData(self.selected_doc_id)
		else:						# More than one row is selected
			print("Need to implement something in this scenario.")
			# TODO: Implement response when multiple rows are selected
			return

	def projSelectChanged(self):
		# Getting the current list of rows selected
		sel_indices = self.treeView_Projects.selectionModel().selectedRows()

		# Checking if no projects are selected
		if len(sel_indices) == 0:
			self.selected_proj_id = -1
			# Disabling the edit project button
			self.pushButton_EditProject.setEnabled(False)
			# Setting the project filter to all projects
			self.comboBox_Filter_Project.setCurrentIndex(0)

		else: # There is exactly one selected (multiple is not allowed)
			index = sel_indices[0]
			self.treeView_Projects.selectionModel()

			# Grabbing the text and id of the project that is selected
			# sel_proj_text = index.model().itemFromIndex(index).text()
			self.selected_proj_id = index.internalPointer().uid

			# Enabling the edit project button
			self.pushButton_EditProject.setEnabled(True)

			# Finding the corresponding proj id in combo box
			comboBox_index = self.comboBox_Project_IDs.index(self.selected_proj_id)
			self.comboBox_Filter_Project.setCurrentIndex(comboBox_index)

			# TODO: Need to select the proj_id (to allow for multi project to have same text, eg two parojects that each have "Theory" subprojects)
			#pdb.set_trace()

			# if len(sel_row_indices) == 0:  	# No rows are selected
			# 	return
			# elif len(sel_row_indices) == 1: 	# Exactly one row is selected
			# 	title = self.proxyModel.index(sel_row_indices[0],2).data()
			# 	sel_doc_id = self.proxyModel.index(sel_row_indices[0],0).data()
			# 	self.loadMetaData(sel_doc_id)
			# else:						# More than one row is selected
			# 	return

	def journalChanged(self):
		# This function updates the journal when the user enters a change to it
		if (self.selected_doc_id != -1):
			print(self.tm.arraydata[self.tm.arraydata.ID == self.selected_doc_id ].Title)
			new_journal = self.lineEdit_Journal.text()
			print(new_journal)
			# Updating the source database
			aux.updateDB(doc_id=self.selected_doc_id, column_name="journal",
							new_value=new_journal, db_path=self.db_path)

			# Updating the table model (and emitting a changed signal)
			self.tm.arraydata.loc[self.tm.arraydata.ID==self.selected_doc_id,
														'Journal'] = new_journal
			cell_row = self.tm.getRowOfDocID(self.selected_doc_id)
			cell_col = list(self.tm.headerdata).index("Journal")
			cell_index = self.tm.index(cell_row, cell_col)
			self.tm.dataChanged.emit(cell_index, cell_index)
		else:
			print("Either no rows or multiple rows are selected. Edits have not been saved.")
####end
##### Auxiliary Functions #######################################################
	def addNewBibEntry(self, bib_dict):
		"""
			This function adds a new bib entry to the dataframe and table model

			:param bib_dict: dictionary of information included in this entry.
				Could include keys such as 'title', 'ID', 'authors',
				'file_path', ....
		"""
		# Assign a new ID if none is passed
		if 'ID' not in bib_dict.keys():
			bib_dict['ID'] = aux.getNextDocID(self.db_path)

		# Verify this doc ID is new and unique
		if bib_dict['ID'] in self.tm.arraydata.ID:
			warnings.warn(f"Document ID = {bib_dict['ID']} is already " + \
							"being used. Double check what called this.")
			return False

		# Assigning any values that are not found in the dictionary
		bib_dict['Title'] = bib_dict.get("Title", "New Title")
		bib_dict['Authors'] = bib_dict.get("Authors", "Author Names")
		bib_dict['Journal'] = bib_dict.get("Journal", "")
		bib_dict['Year'] = bib_dict.get("Year", -1)
		td = date.today()
		bib_dict['DateAdded'] = td.year*10000 + td.month*100 + td.day

		# Adding the entry to the the class dataframe and the model data
		doc_fields = ['ID','Title','Authors','Journal','Year','DateAdded','AuthorsLast']
		doc_dict = {key:value for key, value in bib_dict.items() if key in doc_fields}
		self.tm.beginInsertRows(QtCore.QModelIndex(),
								self.tm.rowCount(self), self.tm.rowCount(self))
		self.tm.arraydata = self.tm.arraydata.append(doc_dict, ignore_index=True)
		self.tm.endInsertRows()

		# Inserting this row into the document database
		aux.insertIntoDB(bib_dict, "Documents", self.db_path)

		# Inserting a new record into the doc_paths database
		aux.insertIntoDB(bib_dict, 'Doc_Paths', self.db_path)

		# Resetting all the filters to make sure new row is visible
		self.resetAllFilters()

		# Selecting the row corresponding to this new entry
		view_row = self.proxyModel.getRowFromDocID(bib_dict['ID'])
		self.tableView_Docs.selectRow(view_row)

		# Reloading metadata (since it may happen to select same row as before, especially after consecutive adds)
		self.loadMetaData(bib_dict['ID'])

		# TODO: Reset the filters to be sure document is diplayed

	def resetAllFilters(self):
		# This function will reset all the filters so the view displays all docs

		# Resetting the project combo box and project viewer
		self.comboBox_Filter_Project.setCurrentIndex(0)
		self.treeView_Projects.selectionModel().clearSelection()
		self.proj_filter_ids = set(self.tm.arraydata.ID)

		# Resetting the custom filter combo box
		self.comboBox_Filter.setCurrentIndex(0)
		self.custom_filter_ids = set(self.tm.arraydata.ID)

		# Resetting the search box
		self.lineEdit_Search.setText("")
		self.search_filter_ids = set(self.tm.arraydata.ID)
		# Updating the proxy model to reflect showing everything
		self.tm.beginResetModel()
		self.proxyModel.show_list = list(self.tm.arraydata.ID)
		self.tm.endResetModel()

		# Resets the sorting as well (by date added)
		self.proxyModel.sort(list(self.tm.headerdata).index("DateAdded"),
								order = QtCore.Qt.DescendingOrder)

	def loadMetaData(self, doc_id):
		# This function will load the meta data for the passed id into the fields
		doc_row = self.tm.arraydata[self.tm.arraydata.ID == doc_id]
		multi_authors = (doc_row.iloc[0].Authors.find(";") != -1)
		if multi_authors: print("Multiple authors selected")
		self.textEdit_Title.setText(doc_row.iloc[0].Title)
		# Adjusting height to match title text
		self.textEdit_Title.setFixedHeight(self.textEdit_Title.document().size().height()+10)
		#aux.autoResizeTextWidget(self.textEdit_Title)
		authors_split = doc_row.iloc[0].Authors.replace("; ","\n")
		self.textEdit_Authors.setText(authors_split)
		# Adjusting height to match number of authors (in text)
		self.textEdit_Authors.setFixedHeight(self.textEdit_Authors.document().size().height()+10)
		#aux.autoResizeTextWidget(self.textEdit_Authors)
		self.lineEdit_Journal.setText(doc_row.iloc[0].Journal)
		self.lineEdit_Year.setText(str(doc_row.iloc[0].Year))
		#self.lineEdit_Journal.setAlignment(QtCore.Qt.AlignLeft)
		line_edit_boxes = [self.lineEdit_Journal, self.lineEdit_Year]
		for line_edit in line_edit_boxes:
			line_edit.setCursorPosition(0)

		# Gathering the paths (if any) associated with this document
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute(f"SELECT * FROM Doc_Paths WHERE doc_id = {self.selected_doc_id}")
		doc_paths = pd.DataFrame(curs.fetchall(),columns=['doc_id', 'fullpath'])
		conn.close()

		# First hiding all the labels
		for label in self.meta_file_paths:
			label.hide()

		# Now setting label text for any paths found
		fullpaths = [x for x in list(doc_paths.fullpath) if x != None]
		filenames = [path[path.rfind("/")+1:] for path in fullpaths]
		file_path_links = []
		for i in range(len(fullpaths)):
			label_text = f"<a href='file:///{fullpaths[i]}'>"+filenames[i]+"</a>" #"<font color='blue'>"+paths[i]+"</font>"
			self.meta_file_paths[i].setText(label_text)
			self.meta_file_paths[i].show()

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
		        #print()
		    temp_df = pd.DataFrame({'path': [path]*num_files,
		                            'filename': filenames,
		                            'fullpath': fullpaths,
		                            'created': ctimes,
		                            'modified': mtimes})
		    files_found = pd.concat([files_found, temp_df])
		files_found

		# Grabbing the current list of known file paths
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Doc_Paths")
		doc_paths = pd.DataFrame(curs.fetchall(),columns=['doc_id', 'fullpath'])
		conn.close()

		# Checking which files are new
		files_found = files_found.merge(doc_paths, how = "left",
										on = "fullpath", indicator=True)
		new_file_flag = files_found._merge == "left_only"
		num_new_files = sum(new_file_flag)
		print(f"Found {num_new_files} new files in watched folders:")
		print(files_found[new_file_flag].filename)

		# Updating the last check variable
		self.config['Other Variables']['last_check'] = str(date.today())

		# Writing another config file
		with open('../user/config.ini', 'w') as configfile:
			self.config.write(configfile)
####end
##### Initialization Functions ##################################################
	def initDocumentViewer(self):
		# Initialize the various aspects of the table view that holds the documents

		# Load the main DB
		alldocs = aux.getDocumentDB(self.db_path)

		# Putting documents in Table View
		header = alldocs.columns
		self.tm = docTableModel(alldocs, header) #, self)

		# This in-between model will allow for sorting and easier filtering
		self.proxyModel = mySortFilterProxy(table_model=self.tm) #QtCore.QSortFilterProxyModel() #self)
		self.proxyModel.setSourceModel(self.tm)
		self.tableView_Docs.setModel(self.proxyModel)
		# Setting the widths of the column (I think...)
		self.tableView_Docs.verticalHeader().setDefaultSectionSize(self.h_scale)
		# Makes whole row selected instead of single cells
		self.tableView_Docs.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
		# Make only single rows selectable
		self.tableView_Docs.setSelectionMode(QtWidgets.QTableView.ContiguousSelection)
		# Making the columns sortable (and setting initial sorting on DateAdded)
		self.tableView_Docs.setSortingEnabled(True)
		self.proxyModel.sort(list(self.tm.headerdata).index("DateAdded"),
								order = QtCore.Qt.DescendingOrder)

		# Resizing the columns to fit the information populated
		for i in range(len(self.tm.headerdata)):
			self.tableView_Docs.resizeColumnToContents(i)

		# Resizing according to the default widths
		self.tableView_Docs.setColumnWidth(1, 250)
		self.tableView_Docs.setColumnWidth(2, 400)
		self.tableView_Docs.setColumnWidth(3, 250)
		# TODO: Gather default widths from new fields DB table

		# Setting initial doc id selection to nothing
		self.selected_doc_id = -1

		# Setting the view so it supports dragging from
		self.tableView_Docs.setDragEnabled(True)

		# Listening for changes in the rows that are selected (to update meta)
		self.DocSelectionModel = self.tableView_Docs.selectionModel()
		self.DocSelectionModel.selectionChanged.connect(self.rowSelectChanged)

	def initSidePanelButtons(self):
		# Set the edit project button to disabled initially
		self.pushButton_EditProject.setEnabled(False)

		# Connects the reponse to the various buttons in the side panel
		self.pushButton_EditProject.clicked.connect(self.openProjectDialog)

	def setMetaDataFieldAttributes(self):
		# Sets various attributes of the meta data fields (like hover responses)
		fields = [self.textEdit_Title, self.textEdit_Authors, self.lineEdit_Journal,
					self.lineEdit_Year, self.lineEdit_Issue]
		for widget in fields:
			widget.setStyleSheet(open("mystylesheet.css").read())
		# TODO: Fix hover for QTextEdits (not sure why it's not working)
		#self.textEdit_Title.setStyleSheet(open("mystylesheet.css").read())

		# Sizing them (for empty values)
		self.textEdit_Title.setFixedHeight(self.textEdit_Title.document().size().height()+10)
		self.textEdit_Authors.setFixedHeight(self.textEdit_Authors.document().size().height()+10)

		# Connecting fields to listening functions
		self.lineEdit_Journal.editingFinished.connect(self.journalChanged)

		# Initializing the file path labels (and hiding them all initially)
		self.meta_file_paths = [self.label_meta_path_1, self.label_meta_path_2,
								self.label_meta_path_3, self.label_meta_path_4,
								self.label_meta_path_5]
		for label in self.meta_file_paths:
			label.hide()
			label.setOpenExternalLinks(True)

		# Connecting the add path button
		self.pushButton_AddFile.clicked.connect(self.addFilePath)

	def connectMenuActions(self):
		# This function will attach all the menu choices to their relavant response
		self.action_Exit.triggered.connect(self.parent.close)
		self.actionCheck_for_New_Docs.triggered.connect(self.checkWatchedFolders)
		self.actionOpen_Selected_in_Acrobat.triggered.connect(self.openFileReader)
		self.actionPDF_File.triggered.connect(self.addFromPDFFile)
		self.action_New_Blank_Entry.triggered.connect(self.addEmptyBibEntry)

	def buildProjectComboBoxes(self):
		# This function will initialize the project combo boxes with the projects
		#		found in the DB table "Projects"
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Projects")
		self.projects = pd.DataFrame(curs.fetchall(),columns=['proj_id', 'proj_text',
														'parent_id', 'path', 'description'])
		conn.close()
		# Reseting the index so it matche the project id
		self.projects.set_index('proj_id', drop=False, inplace=True)

		base_folders = self.projects[self.projects['parent_id']==0]\
												.sort_values(by=['proj_text'])

		# Adding the first and default "ALl Projects" selection
		self.comboBox_Project_Choices = ['All projects']
		# Starting list of project ids in same order as the combobox text
		self.comboBox_Project_IDs = [-1] # Reserved for all projects
		# Recursively adding the parent folders and child folders underneath
		child_list, proj_id_list = aux.addChildrenOf(0, self.projects, "", [])
		self.comboBox_Project_Choices += child_list
		self.comboBox_Project_IDs += proj_id_list

		# Adding the list of projects to the combo box
		self.comboBox_Filter_Project.addItems(self.comboBox_Project_Choices)

		# Connecting combo box to action
		#self.comboBox_Filter_Project.currentIndexChanged.connect(self.projectFilterEngaged)
		self.comboBox_Filter_Project.currentIndexChanged.connect(self.projectFilterEngaged)
		#print(self.folders)

		# Initializing the filter id set
		self.proj_filter_ids = set(self.tm.arraydata.ID)

	def buildFilterComboBoxes(self):
		# This function will initialize the filter combo box with the filters
		#		found in the DB table "Custom_Filters"
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Custom_Filters")
		filters = pd.DataFrame(curs.fetchall(),
							columns=['filter_id', 'filter_name','filter_code'])
		conn.close()
		# Sorting by the filter ID
		filters.sort_values('filter_id', inplace=True)
		# Adding text to combo box
		self.comboBox_Filter.addItems(list(filters["filter_name"]))

		# Connecting combo box to action
		#self.comboBox_Filter_Project.currentIndexChanged.connect(self.FilterEngaged)
		#print(self.folders)

		# Initializing the filter id set
		self.custom_filter_ids = set(self.tm.arraydata.ID)

	def buildColumnComboBoxes(self):
		# This function will initialize the search column combo box with the
		#		columns in the document table
		self.comboBox_Search_Column.addItems(["All Fields"]+\
									list(self.tm.headerdata.sort_values()))

		# Connecting combo box to action
		#self.comboBox_Filter_Project.currentIndexChanged.connect(self.FilterEngaged)
		#print(self.folders)

	def initSearchBox(self):
		# This function initializes everythin asociated with the search box

		# Initializing the filter id set
		self.search_filter_ids = set(self.tm.arraydata.ID)

		# Connecting search box to action
		#self.lineEdit_Search.??.connect(self.searchChanged)

	# This function is also obsolete
	# def initProjectTreeView(self):
	# 	# Defining dictionary of column indexes
	# 	self.proj_col_dict = {"Project": 0, "ID": 1, "Path": 2, "Description": 3}
	# 	# Setting the header on the tree view
	# 	# self.project_tree_model = QtGui.QStandardItemModel(0, len(self.proj_col_dict.keys()))
	# 	for col_name in self.proj_col_dict.keys():
	# 		self.project_tree_model.setHeaderData(self.proj_col_dict[col_name],
	# 												QtCore.Qt.Horizontal, col_name)
	#
	# 	# Enabling the treeview to accept drops (for categorizing articles)
	# 	# TODO: Initialize the acceptance of dropped articles in the project view
	# 	self.treeView_Projects.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
	# 	# self.treeView_Projects.setAcceptDrops(True) # Another way to enable dropping (though seems too low level)

	# The below function is obsolete (all this is done in the model instantiation)
	# def populateTreeModel(self):
	# 	# This function will populate the tree model with the current projects
	#
	# 	# Make a dictinary of QStandardItems whose keys are the proj_ids
	# 	self.tree_nodes = {x.proj_id: QtGui.QStandardItem(x.proj_text) \
	# 										for index, x in self.projects.iterrows()}
	#
	# 	# Iterate over each and attach to their parent
	# 	for node_id in self.tree_nodes:
	# 		# Setting their ID into the object
	# 		self.tree_nodes[node_id].setData(node_id)
	# 		# Creating the row of data
	# 		row_list = [self.tree_nodes[node_id],
	# 					QtGui.QStandardItem(str(node_id)),
	# 					QtGui.QStandardItem(self.projects.at[node_id, "path"]),
	# 					QtGui.QStandardItem(self.projects.at[node_id, "description"])]
	# 		# Get their parent's id
	# 		parent_id = self.projects.at[node_id,'parent_id']
	# 		if parent_id == 0:	# If they have no parent then append to root
	# 			self.project_tree_model.invisibleRootItem().appendRow(row_list)
	# 		else:				# Otherwise append to their parent
	# 			self.tree_nodes[parent_id].appendRow(row_list)

####end

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()

	prog = ArDa(MainWindow)

	MainWindow.show()
	sys.exit(app.exec_())