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

		# Grabbing the project data from the DB
		self.s_df = aux.getDocumentDB(self.db_path, table_name='Settings')
		pdb.set_trace()
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

	def setProjFolderPath(self):
		# Setting the dialog start path (in case the proj path doesn't exist)
		if os.path.exists(self.proj_path):
			dialog_path = self.proj_path
		else:
			dialog_path = "C:/Users/Phoenix/Documents/Research"
		# Open a folder dialog to get a selected path
		self.new_path = QtWidgets.QFileDialog.getExistingDirectory(
													self.parent_window,
													'Open File',
													dialog_path)
		# Updating the project path field
		self.lineEdit_ProjPath.setText(self.new_path)

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
