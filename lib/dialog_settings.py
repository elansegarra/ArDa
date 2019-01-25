import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from layout_settings_dialog import Ui_Form
import sqlite3, os, datetime
import pandas as pd
import numpy as np
from datetime import date
import aux_functions as aux
import warnings
import pdb

class SettingsDialog(Ui_Form):
	def __init__(self, parent, db_path):
		#super(ProjectDialog, self).__init__(parent)
		Ui_Form.__init__(self)
		self.setupUi(parent)
		self.parent_window = parent

		# Setting class level variables
		self.db_path = db_path

		# Grabbing the settings and field data from the DB
		self.s_df = aux.getDocumentDB(self.db_path, table_name='Settings')
		self.field_df = aux.getDocumentDB(self.db_path, table_name='Fields')

		# Transforming the dataframe into a dictionary
		self.settings_dict = {k: g["var_value"].tolist() for k, g in self.s_df.groupby('var_name')}

		# Populating all the settings values
		self.populateSettingValues()

		# Setting up the button actions
		self.assignButtonActions()

		# Populate the Bib field checkboxes
		self.populateBibFields()

		# Populate the doc table column
		self.populateDocColumns()
		# conn = sqlite3.connect(self.db_path)
		# curs = conn.cursor()
		# curs.execute("SELECT * FROM Projects")
		# self.projects = pd.DataFrame(curs.fetchall(),columns=[description[0] for description in curs.description])
		# self.projects.fillna("", inplace=True)
		# conn.close()
		# # Resetting index for ease of navigation
		# self.projects.set_index('proj_id', drop=False, inplace=True)

		# Setting various values of the project for ease
		# self.parent_id = self.projects.at[self.proj_id, "parent_id"]
		# self.proj_text = self.projects.at[self.proj_id, "proj_text"]
		# self.proj_path = self.projects.at[self.proj_id, "path"].replace("\\", "/")
		# self.proj_desc = self.projects.at[self.proj_id, "description"]
		# self.last_build = self.projects.at[self.proj_id, "bib_built"]

		# self.initParentComboBox()

		# self.populateFields()

		# Connecting the buttons
		# self.pushButton_SaveClose.clicked.connect(self.parent_window.close)
		# self.pushButton_Close.clicked.connect(self.parent_window.close)
		# self.pushButton_ProjFolderPath.clicked.connect(self.setProjFolderPath)

	def populateSettingValues(self):
		# Setting the current DB path
		self.lineEdit_DBPath.setText(self.db_path)
		# Adding in the current watched folders
		for folder_path in self.settings_dict['watch_path']:
			self.listWidget_WatchedFolders.addItem(folder_path)
		# Loading other watched folder settings
		temp = (self.settings_dict['check_watched_on_startup'][0] == "True")
		self.checkBox_CheckWatchStartup.setChecked(temp)
		self.comboBox_FileFoundAction.setCurrentText(self.settings_dict['file_found_action'][0])

		# Loading backup parameters
		self.spinBox_BackupsNumber.setValue(int(self.settings_dict['backups_number'][0]))
		self.comboBox_BackupsFreq.setCurrentText(self.settings_dict['backups_frequency'][0])

		# Loading project settings
		temp = (self.settings_dict['project_cascade'][0] == "True")
		self.checkBox_Cascade.setChecked(temp)

		# Loading bib file settings
		self.lineEdit_BibPath.setText(self.settings_dict['main_bib_path'][0])
		self.comboBox_BibGenFreq.setCurrentText(self.settings_dict['bib_gen_frequency'][0])

	def assignButtonActions(self):
		# Assign reponses to the various buttons in the settings dialog
		self.pushButton_AddWatchFolder.clicked.connect(self.addWatchPath)
		self.pushButton_RemoveWatchFolder.clicked.connect(self.removeWatchPath)
		self.pushButton_SaveClose.clicked.connect(self.closeDialog)
		self.pushButton_Close.clicked.connect(lambda: self.closeDialog(no_save=True))

		# Assign action to watch path selection (enableing the remove button)
		self.listWidget_WatchedFolders.itemSelectionChanged.connect(self.watchPathSelChanged)

	def addWatchPath(self):
		# Open a file dialog and pick a folder
		dialog_path = self.db_path
		watch_folder = QtWidgets.QFileDialog.getExistingDirectory(self.parent_window,
																'Pick Watch Folder',
																dialog_path)
		# Add the watch path if a folder was selected
		if watch_folder != '':
			self.listWidget_WatchedFolders.addItem(watch_folder)

	def removeWatchPath(self):
		# Checks the selected watch path and removes it from the list widget
		sel_row = self.listWidget_WatchedFolders.currentRow()
		# Remove the selected folder (if there's one selected)
		if sel_row != -1:
			self.listWidget_WatchedFolders.takeItem(sel_row)
		# Check the number of items
		if self.listWidget_WatchedFolders.count() == 0:
			self.pushButton_RemoveWatchFolder.setEnabled(False)

	def watchPathSelChanged(self):
		# Extract the selected watch paths
		sel_row = self.listWidget_WatchedFolders.currentRow()
		# Enable/disable remove folder button accordingly
		if sel_row != -1:
			self.pushButton_RemoveWatchFolder.setEnabled(True)
		else:
			self.pushButton_RemoveWatchFolder.setEnabled(False)

	def updateLocalSettingsDict(self):
		# Erasing the old dictionary
		self.settings_dict = dict()
		# This function updates self.settings_dict
		self.settings_dict['check_watched_on_startup'] = self.checkBox_CheckWatchStartup.isChecked()
		self.settings_dict['project_cascade'] = self.checkBox_Cascade.isChecked()
		self.settings_dict['main_bib_path'] = self.lineEdit_BibPath.text()
		self.settings_dict['file_found_action'] = self.comboBox_FileFoundAction.currentText()
		self.settings_dict['backups_number'] = self.spinBox_BackupsNumber.value()
		self.settings_dict['backups_frequency'] = self.comboBox_BackupsFreq.currentText()
		self.settings_dict['bib_gen_frequency'] = self.comboBox_BibGenFreq.currentText()

		# Extracting all the watched folders
		self.settings_dict['watch_path'] = []
		for i in range(self.listWidget_WatchedFolders.count()):
			self.settings_dict['watch_path'].append(self.listWidget_WatchedFolders.item(i).text())

	def populateDocColumns(self):
		# This function fills in the doc table columns in the list widgets

		temp_df = self.field_df[self.field_df['table_name']=='Documents'].copy()
		temp_df.sort_values(['doc_table_order', 'field'], inplace=True)

		# Iterate over the fields in the document table
		for index, row in temp_df.iterrows():
			# Skipping null rows
			if np.isnan(row['doc_table_order']):
				continue
			# Check if hidden
			if row['doc_table_order'] == -1:
				self.listWidget_HiddenCols.addItem(row['field'])
			else:
				self.listWidget_VisibleCols.addItem(row['field'])

	def populateBibFields(self):
		# This function adds checkboxes for the bib fields (and sets them accordingly)

		temp_df = self.field_df[self.field_df['table_name']=='Documents'].copy()
		temp_df.sort_values('field', inplace=True)
		# Creating dictionary to hold the checkbox widgets
		self.bib_checkboxes = dict()
		# Specifying some parameters for displaying checkboxes
		num_cols = 6		# Number of columns
		vert_order = True	# Indicates vertical ordering (True)
		num_fields = sum(~temp_df['include_bib_field'].isnull())
		num_rows = (num_fields // num_cols) + 1
		curr_index = 0

		# Iterate over the fields
		for index, row in temp_df.iterrows():
			if np.isnan(row['include_bib_field']):
				# print(row['field'])
				continue
			else:
				# Create a checkbox object for this field
				self.bib_checkboxes[row['field']] = QtWidgets.QCheckBox(self.groupBox_2)
				self.bib_checkboxes[row['field']].setText(row['field'])
				# Setting the row and col to insert this checkbox into
				row_ind = (curr_index % num_rows if vert_order else curr_index // num_cols)
				col_ind = (curr_index // num_rows if vert_order else curr_index % num_cols)
				self.gridLayout_3.addWidget(self.bib_checkboxes[row['field']],
												row_ind, col_ind, 1, 1)
				# Set to checked if indicated to be
				if row['include_bib_field'] == 1:
					self.bib_checkboxes[row['field']].setChecked(True)
				# Incrementing position index
				curr_index+= 1


	def recordSettingsValues(self):
		# This function records (in the DB) all the setting values

		# First we update the local dictionary
		self.updateLocalSettingsDict()

		# Next we iterate through the dictionary and update each entry
		for var_name, var_value in self.settings_dict.items():
			# Add several rows if value is a list
			if isinstance(var_value, list):
				# First we delete all of these entries
				aux.deleteFromDB({'var_name':'watch_path'}, "Settings",
									self.db_path, force_commit=True)
				# Then we add the values back in
				# pdb.set_trace()
				# Inserting rows for each element
				val_list = [{'var_name':'watch_path', 'var_value': var_item} for var_item in var_value]
				aux.insertIntoDB(val_list, "Settings", self.db_path)
			else: # Otherwise update the single element
				cond_dict = {'var_name':var_name}
				aux.updateDB(cond_dict, 'var_value', var_value, self.db_path,
														table_name = "Settings")

		# This iterates through bib field defaults and updates DB with checkbox state
		for field, checkbox in self.bib_checkboxes.items():
			val = (1 if checkbox.isChecked() else 0)
			cond_dict = {'table_name':'Documents', 'field':field}
			aux.updateDB(cond_dict, 'include_bib_field', val, self.db_path,
							table_name='Fields')

		# This iterates through elements of column lists (hidden and visible)
		for i in range(self.listWidget_HiddenCols.count()):
			field = self.listWidget_HiddenCols.item(i).text()
			cond_dict = {'table_name':'Documents', 'field':field}
			aux.updateDB(cond_dict, 'doc_table_order', -1, self.db_path,
							table_name = "Fields")
		for i in range(self.listWidget_VisibleCols.count()):
			field = self.listWidget_VisibleCols.item(i).text()
			cond_dict = {'table_name':'Documents', 'field':field}
			aux.updateDB(cond_dict, 'doc_table_order', i, self.db_path,
							table_name = "Fields")

	def closeDialog(self, no_save = False):
		"""
			This function will save any of the information that has been entered
			into the dialog.
		"""
		if no_save:
			self.parent_window.close()
		else:
			self.recordSettingsValues()
			self.parent_window.close()
