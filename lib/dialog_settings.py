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



	def initParentComboBox(self):
		# This fills in the choices for the parent drop down menu
		base_folders = self.projects[self.projects['parent_id']==0]\
												.sort_values(by=['proj_text'])

		# Adding the first and default "ALl Projects" selection
		self.comboBox_Parent_Choices = ['< None >']
		# Starting list of project ids in same order as the combobox text
		self.comboBox_Parent_IDs = [0] # For those projects without a parent
		# Recursively adding the parent folders and child folders underneath
		child_list, proj_id_list = aux.addChildrenOf(0, self.projects, "", [],
													ignore_list=[self.proj_id])
		self.comboBox_Parent_Choices += child_list
		self.comboBox_Parent_IDs += proj_id_list

		# Adding the list of projects to the combo box
		self.comboBox_ProjParent.addItems(self.comboBox_Parent_Choices)

		# Getting current parent and setting value in combo box
		if self.parent_id not in self.comboBox_Parent_IDs:
			warnings.warn("Parent ID not found in the list during generation of parent combobox.")
		else:
			init_choice = self.comboBox_Parent_IDs.index(self.parent_id)
			self.comboBox_ProjParent.setCurrentIndex(init_choice)

		# Connecting combo box to action
		#self.comboBox_ProjParent.currentIndexChanged.connect(self.projectFilterEngaged)

	def populateFields(self):
		# This function initializes all the fields in the dialog

		# Setting values in main fields
		self.lineEdit_ProjName.setText(self.proj_text)
		self.textEdit_ProjDesc.setText(self.proj_desc)
		self.lineEdit_ProjPath.setText(self.proj_path)

		# Converting and setting last build date
		dt_obj = datetime.datetime.fromtimestamp(self.last_build/1e3)
		dt_obj = dt_obj.strftime('%m/%d/%Y, %#I:%M %p')
		self.label_BibFileBuiltDate.setText(dt_obj)

	def saveAndClose(self):
		"""
			This function will save any of the information that has been entered
			into the dialog.
		"""
		# TODO: Implement comparing field data to the current values in DB

		# TODO: Implement saving any changed project data (and asking if okay)
		self.parent_window.close()
