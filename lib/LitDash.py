import sys
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
from mainlayout import Ui_MainWindow
import sqlite3, os
import pandas as pd
import numpy as np
import configparser
from myExtensions import docTableModel, mySortFilterProxy
import pdb

class LitDash(Ui_MainWindow):

	# Class variables
	h_scale = 40   #height of one row in the table

	def __init__(self, dialog):
		Ui_MainWindow.__init__(self)
		self.setupUi(dialog)

		# Load variables from the config file
		self.loadConfig()

		# Load the main DB
		self.alldocs = self.getDocumentDB()
		self.currdocs = self.alldocs

		# Putting documents in Table View
		self.header = self.alldocs.columns
		self.tm = docTableModel(self.alldocs, self.header) #, self)

		# This in-between model will allow for sorting and easier filtering
		self.proxyModel = mySortFilterProxy(table_model=self.tm) #QtCore.QSortFilterProxyModel() #self)
		self.proxyModel.setSourceModel(self.tm)
		self.tableView_Docs.setModel(self.proxyModel)
		# Setting the widths of the column (I think...)
		self.tableView_Docs.verticalHeader().setDefaultSectionSize(self.h_scale)
		# Makes whole row selected instead of single cells
		self.tableView_Docs.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

		# Listening for changes in the rows that are selected (to update meta)
		self.DocSelectionModel = self.tableView_Docs.selectionModel()
		self.DocSelectionModel.selectionChanged.connect(self.rowSelectChanged)

		# Build various combo boxes
		self.buildProjectComboBoxes()
		self.buildFilterComboBoxes()
		self.buildColumnComboBoxes()

		# Setting up the project viewer (tree view)
		self.project_tree_model = QtGui.QStandardItemModel()
		self.initProjectTreeView()
		self.treeView_Projects.setModel(self.project_tree_model)
		self.populateTreeModel()
		self.treeView_Projects.setStyleSheet(open("mystylesheet.css").read())

		# Listening for changes in the projects that are selected
		self.projSelectionModel = self.treeView_Projects.selectionModel()
		self.projSelectionModel.selectionChanged.connect(self.projSelectChanged)

	def loadConfig(self):
		"""
			This function reads the config file and sets various variables
			accordingly.
		"""
		print('Reading config file')
		config = configparser.ConfigParser()
		config.read("../user/config.ini")

		# Grabbing the variable values as specified in the config file
		self.db_path = config.get("Data Sources", "DB_path")  #"Data Sources" refers to the section
		print("DB Path: "+self.db_path)

	def getDocumentDB(self):
		"""
			This function will load the database and perform any processing needed
		"""
		conn = sqlite3.connect(self.db_path)  #'MendCopy2.sqlite')
		c = conn.cursor()

		# Selects the first author from each document
		firstAuthors = "SELECT firstNames, min(lastName) as lastName, documentID FROM documentContributors "
		firstAuthors += "GROUP BY documentID ORDER BY documentID"
		# Selects all the documents and joins with first author
		command = "SELECT d.id, c.lastName, c.firstNames, d.title, d.year, d.read, d.added, d.modified, f.localUrl "
		command += "FROM documents AS d JOIN "
		command += "("+firstAuthors+")"
		command += "AS c ON d.ID=c.documentID "  #DocumentContributors AS c ON d.ID="
		command += "JOIN DocumentFiles AS df ON d.ID=df.documentId "
		command += "JOIN Files as f ON f.hash=df.hash"
		command += " WHERE d.deletionPending='false'"

		command = "SELECT doc_id, authors, title, journal, year, created_date FROM Documents"
		#print(command)
		c.execute(command)

		doc = c.fetchall()
		cols = ["ID", "Authors", "Title", "Journal", "Year", "CreateDate"]
		# cols = ['ID', 'LName', 'FName', 'Title', 'Year', 'MendRead', 'MendDateAdd', 'MendDateMod', 'Path']
		df = pd.DataFrame(doc, columns=cols)
		# df['MendDateAdd'] = pd.to_datetime(df['MendDateAdd'], unit='ms').dt.date
		# df['MendDateMod'] = pd.to_datetime(df['MendDateMod'], unit='ms').dt.date
		#
		# df['Author1'] = df['LName']+", "+df['FName']
		#
		# # Flagging all records of downloaded files
		# # TODO: Flag the files in appdata folder (since they will likely cause issues)
		#
		# # This will try to retrieve the file creation and modification dates usin the local url
		# # TODO Catch errors when the files are not found
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
		# #### Extracting Folders and Folder Assignments to Add to Doc List
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
		# # Merging Into Doc DataFrame
		# df2 = df2.merge(proj_names, how='left', on ='ID')
		# df2['Projects'].fillna(value = '', inplace=True)
		#
		# # Reordering columns (for how they will be displayed) and dropping a few unused ones (FName, LName, DocID)
		# df2 = df2[['ID', 'Author1', 'Author2', 'Year', 'Title', 'DateRead', 'DateCreated', 'DateModifiedF',
		# 			'Path', 'MendDateAdd', 'MendDateMod', 'MendRead', 'Projects']]

		conn.close()
		#elanConn.close()
		# return df2
		return df

#### Action/Response Functions #################################################

	def projectFilterEngaged(self):
		curr_choice = self.comboBox_Filter_Project.currentText().lstrip()
		if curr_choice == 'All projects':
			self.currdocs = self.alldocs
			self.tm.beginResetModel()
			self.proxyModel.show_list = list(self.currdocs.ID)
			self.tm.endResetModel()
		else:
			# Extract project ID for the selected project group
			conn = sqlite3.connect(self.db_path)
			curs = conn.cursor()
			curs.execute(f'SELECT proj_id FROM Projects WHERE proj_text == "{curr_choice}"')
			curr_choice_id = curs.fetchall()[0][0]
			# Selecting all doc IDs that are in this project
			curs.execute(f'SELECT doc_id FROM Doc_Proj WHERE proj_id == "{curr_choice_id}"')
			doc_id_list = [x[0] for x in curs.fetchall()]
			self.currdocs = self.alldocs[self.alldocs.ID.isin(doc_id_list)].copy()

			# Changing the filtered list in the proxy model
			self.tm.beginResetModel()
			self.proxyModel.show_list = doc_id_list
			self.tm.endResetModel()

			# self.lineEdit_SearchField.setText('')  # Setting the search field text to empty
			# self.search_col = 12
			# self.proxyModel.setFilterRegExp(curr_choice)
			conn.close()

		# self.proxyModel.setFilterKeyColumn(self.search_col)

	def rowSelectChanged(self):
		# Getting the current list of rows selected
		sel_rows = self.tableView_Docs.selectionModel().selectedRows()
		sel_row_indices = [i.row() for i in sorted(sel_rows)]
		if len(sel_row_indices) == 0:  	# No rows are selected
			return
		elif len(sel_row_indices) == 1: 	# Exactly one row is selected
			title = self.proxyModel.index(sel_row_indices[0],2).data()
			sel_doc_id = self.proxyModel.index(sel_row_indices[0],0).data()
			self.loadMetaData(sel_doc_id)
		else:						# More than one row is selected
			return

	def projSelectChanged(self):
		# Getting the current list of rows selected

		index = self.treeView_Projects.selectionModel().selectedRows()[0]
		#index = sel_rows[0]
		sel_proj_text = index.model().itemFromIndex(index).text()
		#pdb.set_trace()
		print(sel_proj_text)
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

#### Auxiliary Functions #######################################################
	def loadMetaData(self, doc_id):
		# This function will load the meta data for the passed id into the fields
		doc_row = self.alldocs[self.alldocs.ID == doc_id]
		multi_authors = (doc_row.iloc[0].Authors.find(";") != -1)
		if multi_authors: print("Multiple authors selected")
		self.textEdit_Title.setText(doc_row.iloc[0].Title)
		self.lineEdit_Authors.setText(doc_row.iloc[0].Authors)
		self.lineEdit_Journal.setText(doc_row.iloc[0].Journal)
		self.lineEdit_Year.setText(str(doc_row.iloc[0].Year))
		#self.lineEdit_Journal.setAlignment(QtCore.Qt.AlignLeft)
		line_edit_boxes = [self.lineEdit_Authors, self.lineEdit_Journal,
							self.lineEdit_Year]
		for line_edit in line_edit_boxes:
			line_edit.setCursorPosition(0)

#### Initialization Functions ##################################################
	def buildProjectComboBoxes(self):
		# This function will initialize the project combo boxes with the projects
		#		found in the DB table "Projects"
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Projects")
		self.projects = pd.DataFrame(curs.fetchall(),columns=['proj_id', 'proj_text',
														'parent_id', 'path', 'description'])
		# Reseting the index so it matche the project id
		self.projects.set_index('proj_id', drop=False, inplace=True)

		base_folders = self.projects[self.projects['parent_id']==0]\
												.sort_values(by=['proj_text'])

		# Adding the first and default "ALl Projects" selection
		self.comboBox_Project_Choices = ['All projects']
		# Recursively adding the parent folders and child folders underneath
		self.comboBox_Project_Choices += self.addChildrenOf(0, self.projects, "")

		# Adding the list of projects to the combo box
		self.comboBox_Filter_Project.addItems(self.comboBox_Project_Choices)

		# Connecting combo box to action
		self.comboBox_Filter_Project.currentIndexChanged.connect(self.projectFilterEngaged)
		#print(self.folders)
		conn.close()

	def buildFilterComboBoxes(self):
		# This function will initialize the filter combo box with the filters
		#		found in the DB table "Custom_Filters"
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Custom_Filters")
		filters = pd.DataFrame(curs.fetchall(),
							columns=['filter_id', 'filter_name','filter_code'])

		# Sorting by the filter ID
		filters.sort_values('filter_id', inplace=True)
		# Adding text to combo box
		self.comboBox_Filter.addItems(list(filters["filter_name"]))

		# Connecting combo box to action
		#self.comboBox_Filter_Project.currentIndexChanged.connect(self.FilterEngaged)
		#print(self.folders)

	def buildColumnComboBoxes(self):
		# This function will initialize the search column combo box with the
		#		columns in the document table
		self.comboBox_Search_Column.addItems(["All Fields"]+list(self.header.sort_values()))

		# Connecting combo box to action
		#self.comboBox_Filter_Project.currentIndexChanged.connect(self.FilterEngaged)
		#print(self.folders)

	def addChildrenOf(self, parent_proj_id, project_df, ind_txt):
		# Returns a list of all descendants of passed id (found recursively)
		child_list = []
		# Select only the children of the current parent
		children = project_df[project_df.parent_id==parent_proj_id]\
													.sort_values('proj_text')
		# Add each child and any of their children (and their children...)
		for p in range(children.shape[0]):
			child_id = children.iloc[p]['proj_id']
			child_list += [ind_txt+children.iloc[p]['proj_text']]
			child_list += self.addChildrenOf(child_id, project_df, ind_txt+"  ")
		return child_list

	def initProjectTreeView(self):
		# Defining dictionary of column indexes
		self.proj_col_dict = {"ID": 1, "Path": 2, "Description": 3}
		# Setting the header on the tree view
		self.project_tree_model = QtGui.QStandardItemModel(0, len(self.proj_col_dict.keys())+1)
		for col_name in self.proj_col_dict.keys():
			self.project_tree_model.setHeaderData(self.proj_col_dict[col_name],
													QtCore.Qt.Horizontal, col_name)

	def populateTreeModel(self):
		# This function will populate the tree model with the current projects

		# Make a dictinary of QStandardItems whose keys are the proj_ids
		self.tree_nodes = {x.proj_id: QtGui.QStandardItem(x.proj_text) \
											for index, x in self.projects.iterrows()}

		# Iterate over each and attach to their parent
		for node_id in self.tree_nodes:
			# Setting their ID into the object
			self.tree_nodes[node_id].setData(node_id)
			# Creating the row of data
			row_list = [self.tree_nodes[node_id],
						QtGui.QStandardItem(str(node_id)),
						QtGui.QStandardItem(self.projects.at[node_id, "path"]),
						QtGui.QStandardItem(self.projects.at[node_id, "description"])]
			# Get their parent's id
			parent_id = self.projects.at[node_id,'parent_id']
			if parent_id == 0:	# If they have no parent then append to root
				self.project_tree_model.invisibleRootItem().appendRow(row_list)
			else:				# Otherwise append to their parent
				self.tree_nodes[parent_id].appendRow(row_list)

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()

	prog = LitDash(MainWindow)

	MainWindow.show()
	sys.exit(app.exec_())
