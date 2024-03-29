import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtSql import QSqlTableModel, QSqlQueryModel, QSqlDatabase
from ProDa.layouts.layout_main import Ui_MainWindow
from ProDa.dialog_entry import EntryDialog
from ProDa.dialog_tree_select import TreeSelectDialog
from ProDa.myExtensions import QSqlTreeProxyModel
import sqlite3, os, time
from datetime import date, datetime, timedelta
import pandas as pd
import configparser
from util.my_widgets import QTextEditExt, MyDictionaryCompleter
import util.db_functions as db
import util.my_functions as mf
import ArDa.aux_functions as aux
import pdb, warnings
from profilehooks import profile


class ProDa(Ui_MainWindow):

	# Class variables
	h_scale = 40   #height of one row in the table

	def __init__(self, dialog):
		Ui_MainWindow.__init__(self)
		self.setupUi(dialog)
		self.parent = dialog

		# Load variables from the config file
		self.loadConfig()

		# Setting the default splitter weights (between docs and side panel)
		#self.splitter.setSizes([520, 80])

		# Initial project selection is all projects
		self.sel_proj_ids = []

		# Initialize and populate the document table
		self.initDiaryViewer()
		self.updateQueriesAndViews()

		# Connect the project selection button
		self.pushButton_ProjectSwitch.clicked.connect(self.openProjSelectDialog)

		# Connect the tool box buttons
		self.connectToolButtons()

		# Initialize the search box
		#self.initSearchBox()

		#self.parent.showMaximized()

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

		# Getting the field info
		self.field_df = aux.getDocumentDB(self.db_path, table_name='Fields')

	def currentQuery(self, which_table):
		''' Creates the SQL command that represents the current filter '''
		if which_table == 'diary':
			query = "SELECT * FROM Proj_Diary"
		elif which_table == "tasks":
			query = "SELECT * FROM Proj_Tasks"

		# TODO: Implement cascading (so all children projects are included)
		# Tacking on specific project selection
		if self.sel_proj_ids != []:
			str_ids = [str(proj_id) for proj_id in self.sel_proj_ids]
			query = query + " WHERE proj_id in (" + ", ".join(str_ids) + ")"

		return query

####end
##### Action/Response Functions ################################################
	def openEntryDialog(self, entry_mode, new_entry = False):
		''' This functions opens a dialog box for editing entry details
		 :param str entry_mode: should either be 'diary_mode' or 'task_mode'
		 :param bool new_entry: indicates whether this is a new entry
		'''
		print(f"A {entry_mode} entry dialog has been initiated.")
		# Check which entry is new or if should grab selection
		if new_entry:
			entry_id = None
		else:
			if (entry_mode == "diary_mode"):
				entry_id = self.tableView_Diary.selectionModel().selectedRows()[0].data()
			elif (entry_mode == "task_mode"):
				entry_id = self.treeView_Tasks.selectionModel().selectedRows()[0].data()

		self.e_diag = EntryDialog(self, self.db_path, entry_mode,
									entry_id=entry_id)
		if self.e_diag.exec_():
			print("Accepted")
			# Update the relevant query model
			if entry_mode == 'diary_mode':
				self.tqm_diary.setQuery(self.currentQuery('diary'))
			if entry_mode == 'task_mode':
				self.tqm_tasks.setQuery(self.currentQuery('tasks'))
		else:
			print("Entry/task dialog canceled")

	def openProjSelectDialog(self):
		"""
			This function opens the a selection dialog and populates it with items
		"""
		proj_df = db.getDocumentDB(self.db_path, table_name='Projects')
		# Convert column names to conform to tree selection dialog
		project_name_map = {'proj_id':'item_id',
							'parent_id':'parent_id',
							'proj_text':'item_text'}
		proj_df.rename(columns=project_name_map, inplace=True)
		# Instantiate the dialog
		self.ts_diag = TreeSelectDialog(self, proj_df, 'project',
												sel_ids=self.sel_proj_ids,
												all_option = True)
		self.ts_diag.setModal(True)

		# Open window and respond bsed on final selection
		if self.ts_diag.exec_(): 	# User selects okay
			print(f"Project(s) selected: {self.ts_diag.sel_ids}, {self.ts_diag.sel_texts}")
			self.sel_proj_ids = self.ts_diag.sel_ids
			self.updateQueriesAndViews()
		else:				# User selects cancel
			print("Project selection canceled.")

	def updateQueriesAndViews(self):
		''' Updates the queries and redraws the diary and task views '''
		# Updating the queries
		self.tqm_diary.setQuery(self.currentQuery('diary'))
		self.tqm_tasks.setQuery(self.currentQuery('tasks'))

		# Updating the project button
		if self.sel_proj_ids == []:
			button_text = "All Projects"
		else:
			# Extracting 'address' of each project
			df = db.getDocumentDB(self.db_path, "Projects")
			proj_texts = [mf.getAncestry(df, proj_id, 'proj_id', 'parent_id', 'proj_text')
									for proj_id in self.sel_proj_ids]
			# Converting each 'address part' to a single 'address' string
			if len(proj_texts) > 3:
				proj_texts = [text[-1] for text in proj_texts]
			else:
				proj_texts = ["/".join(text) for text in proj_texts]
			# Combining all address strings into a single string
			button_text = "; ".join(proj_texts)
		self.pushButton_ProjectSwitch.setText(button_text)

	# def SearchEngaged(self):
	# 	# This function is called when the search field is filled out
	#
	# 	# Getting search text and field to search on
	# 	search_text = self.lineEdit_Search.text()
	# 	search_col = self.comboBox_Search_Column.currentText()
	# 	print(f"Attempting search for '{search_text}' in columnn '{search_col}'.")
	# 	# search_col_index = (list(self.tm.arraydata.columns)).index(search_col)
	#
	# 	# Some edge cases
	# 	if search_text == "":
	# 		return
	#
	# 	# Defining string vs int fields (different searching)
	# 	# TODO: Tie these lists to their designation in the fields table
	# 	string_fields = ['Authors', 'Title', 'Journal']
	# 	int_fields = ['ID', 'Year']
	# 	date_fields = []
	#
	# 	# Case statement based on field types
	# 	if search_col == 'All Fields':
	# 		print("Still need to implement searching through all fields")
	# 		return
	# 	elif search_col in string_fields:
	# 		self.search_filter_ids = set(self.tm.arraydata[self.tm.arraydata[search_col].str.contains(search_text, regex=False, case=False, na=False)].ID)
	# 	elif search_col in int_fields:
	# 		try:
	# 			search_text = int(search_text)
	# 			self.search_filter_ids = set(self.tm.arraydata[self.tm.arraydata[search_col]==search_text].ID)
	# 		except ValueError:
	# 			print(f"Search value '{search_text}' is not castable to an int.")
	# 			return
	# 	else:
	# 		print(f"Do not recognize the type for searching on field: {search_col}")
	# 		return
	#
	# 	# Changing the filtered list in the proxy model
	# 	self.tm.beginResetModel()
	# 	self.all_filter_ids = self.proj_filter_ids & self.diag_filter_ids & \
	# 						self.custom_filter_ids & self.search_filter_ids
	# 	self.proxyModel.show_list = list(self.all_filter_ids)
	# 	self.tm.endResetModel()
	#
	# 	# Updating the current filter message
	# 	msg = f" search ('{search_text}' in {search_col});"
	# 	# Checking if there was an earlier filter in place
	# 	start = self.label_CurrentFilter.text().find(' search (')
	# 	if start != -1:
	# 		# Replacing old msg with the new
	# 		end = start + self.label_CurrentFilter.text()[start:].find(";") + 1
	# 		old_msg = self.label_CurrentFilter.text()[start:end]
	# 		new_msg = self.label_CurrentFilter.text().replace(old_msg, msg)
	# 		self.label_CurrentFilter.setText(new_msg)
	# 	else:
	# 		self.label_CurrentFilter.setText(self.label_CurrentFilter.text() + msg)
	# 	self.label_CurrentFilter.show()
	# 	self.pushButton_ClearFilter.show()

	# def openProjectDialog(self, new_project = False):
	# 	if new_project:
	# 		self.ui = ProjectDialog(self, None, self.db_path)
	# 	elif self.selected_proj_id != -1:
	# 		self.ui = ProjectDialog(self, self.selected_proj_id, self.db_path)
	# 	else:
	# 		warnings.warn("openProjectDialog() was called not on a new project and no project is selected.")
	# 		return
	#
	# 	self.ui.setModal(True)
	# 	# Checking for result from the dialog
	# 	if self.ui.exec_() and self.ui.saved_settings:
	# 		# Reloading the project comboboxes and tree (blocking signals momentarily)
	# 		self.comboBox_Filter_Project.blockSignals(True)
	# 		self.comboBox_Filter_Project.clear()
	# 		self.buildProjectComboBoxes(init_proj_id = self.selected_proj_id, connect_signals = False)
	# 		self.comboBox_Filter_Project.blockSignals(False)
	# 		self.initProjectViewModel(connect_context=False)

	# def openSettingsDialog(self):
	# 	self.s_diag = SettingsDialog(self, self.db_path)
	# 	if self.s_diag.exec_():
	# 		# If the custom filters were changed, reload the combobox
	# 		if self.s_diag.custom_filters_changed:
	# 			self.buildFilterComboBoxes()

####end
##### Auxiliary Functions #######################################################
	# def deleteProject(self, project_id, children_action = "reassign"):
	# 	"""
	# 		This method deletes a project (and its associations)
	# 		:param project_id: int indicating the ID of the project to delete
	# 		:param children_action: str indicating how to handle project children
	# 					"reassign": Assigns any childre to the parent of the deleted project
	# 					"delete": Delete children projects as well
	# 	"""
	# 	# Grabbing the project table
	# 	projs = aux.getDocumentDB(self.db_path, table_name = "Projects")
	# 	# Resetting the index so it matches the project id
	# 	projs.set_index('proj_id', drop=False, inplace=True)
	# 	# Extracting the parent of the current project
	# 	parent_id = projs.at[project_id, 'parent_id']
	#
	# 	# Extracting any children of this project
	# 	child_ids = list(projs[projs['parent_id']==project_id]['proj_id'])
	# 	# Iterate over the children and perform the appropriate action
	# 	for child_id in child_ids:
	# 		if children_action == "reassign":
	# 			print(f"Update child {child_id}")
	# 			cond_key = {'proj_id': child_id}
	# 			aux.updateDB(cond_key, 'parent_id', parent_id, self.db_path,
	# 							table_name = "Projects")
	# 		elif children_action == "delete":
	# 			print(f"Deleting child {child_id} (Still needs to be implemented).")
	# 		else:
	# 			warnings.warn(f"Unrecognized children action, {children_action}, "+\
	# 							"passed to deleteProject().")
	# 			return
	#
	# 	# Delete all associations with this project
	# 	cond_key = {'proj_id': project_id}
	# 	aux.deleteFromDB(cond_key, "Doc_Proj", self.db_path, force_commit=True)
	#
	# 	# Delete the project entry
	# 	aux.deleteFromDB(cond_key, "Projects", self.db_path, force_commit=True)
	#
	# 	# Reloading the project comboboxes and tree (blocking signals momentarily)
	# 	self.comboBox_Filter_Project.blockSignals(True)
	# 	self.comboBox_Filter_Project.clear()
	# 	self.buildProjectComboBoxes(connect_signals = False)
	# 	self.comboBox_Filter_Project.blockSignals(False)
	# 	self.initProjectViewModel(connect_context=False)

####end
##### Initialization Functions ##################################################
	def initDiaryViewer(self):
		# Initialize the various aspects of the table view that holds the documents

		# Open the SQL db and pass it to the table model
		db = QSqlDatabase.addDatabase("QSQLITE")
		db.setDatabaseName(self.db_path)
		if db.open():	print("DB connection made successfully.")
		else:			print("DB connection was unsuccessful.")

		# Connecting the diary entry data to the view
		self.tqm_diary = QSqlQueryModel()
		self.tqm_diary.setQuery(self.currentQuery('diary'))
		self.tableView_Diary.setModel(self.tqm_diary)
		# self.tableView_Diary.show()

		# Connecting the task data to the view
		self.tqm_tasks = QSqlQueryModel()
		self.tqm_tasks.setQuery(self.currentQuery('tasks'))
		# self.treeView_Tasks.setModel(self.tqm_tasks)
		self.tspm_tasks = QSqlTreeProxyModel(table_model=self.tqm_tasks)
		self.tspm_tasks.setSourceModel(self.tqm_tasks)
		self.treeView_Tasks.setModel(self.tspm_tasks)
		# self.treeView_Tasks.show()

		task_fields = self.field_df[self.field_df['table_name']=="Proj_Tasks"][['field', 'task_table_order', 'header_text']].copy()
		diary_fields = self.field_df[self.field_df['table_name']=="Proj_Diary"][['field', 'diary_table_order', 'header_text']].copy()


		# Ordering, hiding, renaming, and resizing the diary entry columns
		# TODO: get column ordering to work properly
		order_map = dict(zip(diary_fields.field, diary_fields.diary_table_order))
		name_map = dict(zip(diary_fields.field, diary_fields.header_text))
		for i in range(self.tqm_diary.columnCount()):
			header_text = self.tqm_diary.headerData(i, 1)
			self.tqm_diary.setHeaderData(i, 1, name_map[header_text])
			self.tableView_Diary.resizeColumnToContents(i)
			if order_map[header_text] != -1:
				header = self.tableView_Diary.horizontalHeader()
				# header.moveSection(i,order_map[header_text]-100)
			else: # Otherwise the column gets hidden
				self.tableView_Diary.setColumnHidden(i, True)
		self.tableView_Diary.resizeColumnsToContents()
		self.tableView_Diary.resizeRowsToContents()
		# Set last column to fill remainder of view (here last column will be the title)
		self.tableView_Diary.horizontalHeader().setStretchLastSection(True)

		# Ordering, hiding, renaming, and resizing the task columns
		# TODO: get column ordering to work properly
		order_map = dict(zip(task_fields.field, task_fields.task_table_order))
		name_map = dict(zip(task_fields.field, task_fields.header_text))
		for i in range(self.tqm_tasks.columnCount()):
			header_text = self.tqm_tasks.headerData(i, 1)
			self.tqm_tasks.setHeaderData(i, 1, name_map[header_text])
			self.treeView_Tasks.resizeColumnToContents(i)
			# print(f"{header_text}: {order_map[header_text]}")
			if order_map[header_text] == -1:
				self.treeView_Tasks.setColumnHidden(i, True)

		# listening for double clicks
		self.tableView_Diary.doubleClicked.connect(lambda :self.openEntryDialog('diary_mode'))
		self.treeView_Tasks.doubleClicked.connect(lambda :self.openEntryDialog('task_mode'))

	def connectToolButtons(self):
		# Connect all the tool buttons
		self.toolButton_AddDiaryEntry.clicked.connect(
					lambda: self.openEntryDialog('diary_mode', new_entry=True))
		self.toolButton_AddTask.clicked.connect(
					lambda: self.openEntryDialog('task_mode', new_entry=True))

	# 	# This in-between model will allow for sorting and easier filtering
	# 	self.proxyModel = mySortFilterProxy(table_model=self.tm) #QtCore.QSortFilterProxyModel() #self)
	# 	self.proxyModel.setSourceModel(self.tm)
	# 	self.tableView_Docs.setModel(self.proxyModel)
	# 	# # Turning off dynamic sorting (hoping this would speed up reset... but alas)
	# 	# self.proxyModel.setDynamicSortFilter(False)
	# 	# Setting the widths of the column (I think...)
	# 	self.tableView_Docs.verticalHeader().setDefaultSectionSize(self.h_scale)
	# 	# Makes whole row selected instead of single cells
	# 	self.tableView_Docs.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
	# 	# Make only single rows selectable
	# 	self.tableView_Docs.setSelectionMode(QtWidgets.QTableView.ContiguousSelection)
	# 	# Making the columns sortable
	# 	self.tableView_Docs.setSortingEnabled(True)
	# 	# Making column order draggable
	# 	self.tableView_Docs.horizontalHeader().setSectionsMovable(True)

	#
	# 	# Defining the context menu for document viewer
	# 	self.tableView_Docs.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
	# 	self.tableView_Docs.customContextMenuRequested.connect(self.openDocContextMenu)

	# def initSearchBox(self):
	# 	# This function initializes everything asociated with the search box
	#
	# 	# Initializing the filter id set
	# 	self.search_filter_ids = set(self.tm.arraydata.ID)
	#
	# 	# Also initializing the dialog id set (since nowhere else makes sense)
	# 	self.diag_filter_ids = set(self.tm.arraydata.ID)
	# 	self.all_filter_ids = set(self.tm.arraydata.ID)
	#
	# 	# Connecting search box to action
	# 	self.lineEdit_Search.returnPressed.connect(self.SearchEngaged)
	#
	# 	# Initially hiding the filter message
	# 	self.label_CurrentFilter.hide()
	# 	self.pushButton_ClearFilter.hide()
	# 	self.label_CurrentFilter.setText("Current subset:")
	#
	# 	# Connecting clear filter button
	# 	self.pushButton_ClearFilter.clicked.connect(self.resetAllFilters)
####end

if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()

	prog = ProDa(MainWindow)

	MainWindow.show()
	sys.exit(app.exec_())
