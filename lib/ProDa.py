import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from ProDa.layouts.layout_main import Ui_MainWindow
import sqlite3, os, time
from datetime import date, datetime, timedelta
import configparser
from util.my_widgets import QTextEditExt, MyDictionaryCompleter
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
		#self.loadConfig()

		# Setting the default splitter weights (between docs and side panel)
		#self.splitter.setSizes([520, 80])

		# Initialize and populate the document table
		#self.initDocumentViewer()

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

####end
##### Action/Response Functions ################################################
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
	# def initDocumentViewer(self):
	# 	# Initialize the various aspects of the table view that holds the documents
	#
	# 	# Getting document data and field info
	# 	alldocs = aux.getDocumentDB(self.db_path)
	# 	self.field_df = aux.getDocumentDB(self.db_path, table_name='Fields')
	# 	doc_field_df = self.field_df[self.field_df['table_name']=="Documents"].copy()
	#
	# 	# Sorting data fields by what's specified (hidden columns go to end)
	# 	doc_field_df.loc[doc_field_df.doc_table_order==-1,'doc_table_order'] = 1000
	# 	default_col_order = doc_field_df.sort_values('doc_table_order')['header_text']
	# 	alldocs = alldocs[default_col_order.tolist()].copy()
	# 	# Sorting the actual data on the added date
	# 	alldocs.sort_values('Added', ascending = False, inplace = True)
	#
	# 	# Putting documents in Table View
	# 	header = alldocs.columns
	# 	self.tm = docTableModel(alldocs, header, parent=self) #, self)
	#
	# 	# Creating the table view and adding to app
	# 	self.tableView_Docs = docTableView(self.gridLayoutWidget) #QtWidgets.QTableView(self.gridLayoutWidget)
	# 	self.tableView_Docs.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
	# 	self.gridLayout_2.addWidget(self.tableView_Docs, 4, 0, 1, 4)
	#
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
	# 	# Getting the default field widths
	# 	col_width_dict = dict(zip(doc_field_df.header_text, doc_field_df.col_width))
	# 	data_header = list(self.tm.arraydata.columns)
	# 	# Setting the default widths according to fields table
	# 	for i in range(len(data_header)):
	# 		col_text = data_header[i]
	# 		self.tableView_Docs.setColumnWidth(i, col_width_dict[col_text])
	#
	# 	# Setting initial doc id selection to nothing
	# 	self.selected_doc_ids = -1
	#
	# 	# Setting the view so it supports dragging from
	# 	self.tableView_Docs.setDragEnabled(True)
	#
	# 	# Listening for changes in the rows that are selected (to update meta)
	# 	self.DocSelectionModel = self.tableView_Docs.selectionModel()
	# 	self.DocSelectionModel.selectionChanged.connect(self.rowSelectChanged)
	#
	# 	# listening for double clicks (and making meta data the focus)
	# 	self.tableView_Docs.doubleClicked.connect(lambda :self.tabSidePanel.setCurrentIndex(0))
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
