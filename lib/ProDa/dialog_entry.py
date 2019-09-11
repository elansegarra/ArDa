from PyQt5 import QtCore, QtGui, QtWidgets
from ProDa.layouts.layout_entry_dialog import Ui_Dialog
from ProDa.dialog_tree_select import TreeSelectDialog
import pandas as pd
import numpy as np
from datetime import date
import ArDa.aux_functions as aux
import util.db_functions as db
import util.my_functions as mf
import warnings, pdb

class EntryDialog(QtWidgets.QDialog):

	def __init__(self, parent, db_path, entry_mode, entry_id = None,
					values_dict = None):
		# Initializing the dialog and the layout
		super().__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)
		self.parent_window = parent
		self.entry_mode = entry_mode
		self.db_path = db_path
		self.entry_id = entry_id

		# Defining the visible/invisible widgets
		self.DIARY_WIDGETS = []
		self.TASK_WIDGETS = [
			self.ui.label_Parent, self.ui.pushButton_Parent,
			self.ui.label_Completed, self.ui.checkBox_Completed,
			self.ui.dateEdit_Completed
		]
		self.ALWAYS_HIDDEN_WIDGETS = [self.ui.label_ID, self.ui.lineEdit_ID]

		self.initializeDialogMode()

		# Grabbing the settings and field data from the DB
		self.field_df = aux.getDocumentDB(self.db_path, table_name='Fields')

		# Populating all the settings values
		self.populateValues()

		# Setting up the button actions
		self.assignButtonActions()

	def initializeDialogMode(self):
		''' Shows and hides fields that are relevant or irrelevant '''

		if self.entry_mode == "diary_mode":
			visible_widgets = self.DIARY_WIDGETS
			hidden_widgets = self.TASK_WIDGETS + self.ALWAYS_HIDDEN_WIDGETS
			self.ui.label_Date.setText("Date")
			self.setWindowTitle("Edit Entry")
		elif self.entry_mode == "task_mode":
			visible_widgets = self.TASK_WIDGETS
			hidden_widgets =  self.DIARY_WIDGETS + self.ALWAYS_HIDDEN_WIDGETS
			self.ui.label_Date.setText("Due Date")
			self.setWindowTitle("Edit Task")
		else:
			print(f"Entry mode, {entry_mode}, was not recognized.")
			self.reject()

		# Iterate though and hide/unhide the listed widgets
		for widget in visible_widgets:
			widget.setVisible(True)
		for widget in hidden_widgets:
			widget.setVisible(False)

	def populateValues(self):
		# First we gather the values into a dictionary
		value_dict = dict()
		if self.entry_id is None:
			# Grab the next available entry id
			value_dict['id'] = 948
			# Initialize an empty value dictionary
			value_dict['date'] = QtCore.QDateTime.currentDateTime()
			if self.entry_mode == "diary_mode":
				value_dict['title'] = "New Entry"
			elif self.entry_mode == "task_mode":
				value_dict['title'] = "New Task"
				value_dict['comp_date'] = QtCore.QDateTime.currentDateTime()
		else:
			# Grab the info associated with that id
			table_name = "Proj_Diary" if (self.entry_mode == "diary_mode") else "Proj_Tasks"
			id_col = "entry_id" if (self.entry_mode == "diary_mode") else "task_id"
			value_dict = db.getRowRecord(self.db_path, table_name, id_col, self.entry_id)
			# Change the keys for some variables
			if self.entry_mode == "diary_mode":
				value_dict['id'] = value_dict['entry_id']
				value_dict['date'] = value_dict['entry_date']
			elif self.entry_mode == "task_mode":
				value_dict['id'] = value_dict['task_id']
				value_dict['date'] = value_dict['due_date']
				self.parent_id = value_dict['parent_id']
				if self.parent_id != 0:
					parent_dict = db.getRowRecord(self.db_path, table_name, id_col, self.parent_id)
					value_dict['parent'] = parent_dict['title']
			df = db.getDocumentDB(self.db_path, "Projects")
			self.proj_id = value_dict['proj_id']
			proj_address = mf.getAncestry(df, self.proj_id, 'proj_id', 'parent_id', 'proj_text')
			value_dict['project'] = "/".join(proj_address)

		# Converting dates from string to QDateTime
		for key in ['date', 'comp_date']:
			if key in value_dict:
				value_dict[key] = QtCore.QDateTime.fromString(value_dict[key])

		# Then we set the values given in the dictionary
		self.ui.lineEdit_Title.setText(value_dict.get('title', ''))
		self.ui.lineEdit_ID.setText(str(value_dict.get('id', -1)))
		self.ui.dateEdit_Date.setDateTime(value_dict.get('date',
											QtCore.QDateTime.currentDateTime()))
		self.ui.pushButton_Project.setText(value_dict.get('project', 'WHICH PROJECT?'))
		self.ui.pushButton_Parent.setText(value_dict.get('parent', 'None'))
		self.ui.dateEdit_Completed.setDateTime(value_dict.get('comp_date',
											QtCore.QDateTime.currentDateTime()))
		self.ui.plainTextEdit_Description.document().setPlainText(value_dict.get(
											'description', ''))

	def assignButtonActions(self):
		# Assign reponses to the various buttons in the settings dialog
		self.ui.pushButton_Project.clicked.connect(lambda : self.openTreeDialog('project'))
		self.ui.pushButton_Parent.clicked.connect(lambda : self.openTreeDialog('task'))
		self.ui.pushButton_Save.clicked.connect(self.closeDialog)
		self.ui.pushButton_Cancel.clicked.connect(lambda: self.closeDialog(no_save=True))

	def openTreeDialog(self, proj_or_task):
		""" Opens up project or parent task selection dialog """
		if proj_or_task == "project":
			proj_df = db.getDocumentDB(self.db_path, table_name='Projects')
			# Convert column names to conform to tree selection dialog
			project_name_map = {'proj_id':'item_id',
								'parent_id':'parent_id',
								'proj_text':'item_text'}
			proj_df.rename(columns=project_name_map, inplace=True)
			# Instantiate the dialog
			self.ts_diag = TreeSelectDialog(self, proj_df, 'project',
												sel_ids=[self.proj_id],
												single_selection = True)
			self.ts_diag.setModal(True)
		elif proj_or_task == "task":
			# Grabbing tasks associated with the current project
			task_df = db.getDocumentDB(self.db_path, table_name='Proj_Tasks')
			task_df = task_df[task_df['proj_id']==self.proj_id]
			# Convert column names to conform to tree selection dialog
			project_name_map = {'task_id':'item_id',
								'parent_id':'parent_id',
								'title':'item_text'}
			task_df.rename(columns=project_name_map, inplace=True)
			task_df['expand_default'] = 1 # Expand all tasks
			# TODO: Should remove all tasks that are subtasks of the current task
			# Instantiate the dialog
			self.ts_diag = TreeSelectDialog(self, task_df, 'task',
												sel_ids=[self.parent_id],
												single_selection = True,
												none_option = True)
			self.ts_diag.setModal(True)

		# Open window and respond based on final selection
		diag_result_accept = self.ts_diag.exec_()
		if diag_result_accept and (proj_or_task == "project"): 	# User selects okay
			print(f"Project(s) selected: {self.ts_diag.sel_ids}, {self.ts_diag.sel_texts}")
			# Verify that something besides 'All Projects' was selected
			if (self.ts_diag.sel_ids != []) and (self.ts_diag.sel_ids[0] != -1):
				self.proj_id = self.ts_diag.sel_ids[0]
				df = db.getDocumentDB(self.db_path, "Projects")
				proj_address = mf.getAncestry(df, self.proj_id, 'proj_id', 'parent_id', 'proj_text')
				self.ui.pushButton_Project.setText("/".join(proj_address))
		elif diag_result_accept and (proj_or_task == "task"):
			print(f"Parent task selected: {self.ts_diag.sel_ids}, {self.ts_diag.sel_texts}")
			# Grabbing the selected parent task id and it's associated title
			self.parent_id = self.ts_diag.sel_ids[0]
			if self.parent_id == 0:
				self.ui.pushButton_Parent.setText("None")
			else:
				parent_dict = db.getRowRecord(self.db_path, "Proj_Tasks",
												"task_id", self.parent_id)
				self.ui.pushButton_Parent.setText(parent_dict['title'])
		else:				# User selects cancel
			print("Project selection canceled.")

	def recordValues(self):
		# This function records (in the DB) all the setting values
		# First we grab values from all the widget elements (depending on the mode)
		value_dict = dict()
		if self.entry_mode == "diary_mode":
			value_dict['entry_id'] = self.entry_id
			value_dict['entry_date'] = self.ui.dateEdit_Date.dateTime().toString()
		else:
			value_dict['task_id'] = self.entry_id
			value_dict['due_date'] = self.ui.dateEdit_Date.dateTime().toString()
			value_dict['parent_id'] = self.parent_id
			value_dict['comp_date'] = self.ui.dateEdit_Completed.dateTime().toString()
			value_dict['comp_level'] = 100 if self.ui.checkBox_Completed.isChecked() else 0
		value_dict['title'] = self.ui.lineEdit_Title.text()
		value_dict['proj_id'] = self.proj_id  # self.ui.pushButton_Project.text()
		value_dict['description'] = self.ui.plainTextEdit_Description.toPlainText()
		value_dict['tags'] = self.extractTags(value_dict['title'] + ' ' + value_dict['description'])

		value_dict['title'] = self.ui.lineEdit_Title.text()

		# TODO: Convert project and parent text into their IDs
		value_dict['proj_id'] = int(value_dict['proj_id'])
		# value_dict['parent_id'] = int(value_dict['parent_id'])
		print(value_dict)

		# Update the database (first delete and then insert)
		if self.entry_mode == 'diary_mode':
			del_cond = {'entry_id': value_dict['entry_id']}
			table_name = 'Proj_Diary'
		else:
			del_cond = {'task_id': value_dict['task_id']}
			table_name = 'Proj_Tasks'
		db.deleteFromDB(del_cond, table_name, self.db_path, debug_print=True,
															force_commit=True)
		db.insertIntoDB(value_dict, table_name, self.db_path, debug_print=True)

	def extractTags(self, text):
		''' Extracts tags (word after #) and returns semi-colon separated string '''
		tag_list = [word for word in text.split() if word.startswith('#')]
		return ';'.join(tag_list)

	def closeDialog(self, no_save = False):
		"""
			This function will save any of the information that has been entered
			into the dialog.
		"""
		if no_save:
			self.reject()
		else:
			self.recordValues()
			self.accept()
