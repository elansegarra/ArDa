import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from layout_proj_dialog import Ui_Form
import sqlite3, os, datetime
import pandas as pd
import numpy as np
from datetime import date
import aux_functions as aux
import warnings
import pdb

class ProjectDialog(Ui_Form):
	def __init__(self, parent, proj_id, db_path):
		#super(ProjectDialog, self).__init__(parent)
		Ui_Form.__init__(self)
		self.setupUi(parent)
		self.parent_window = parent

		# Setting class level variables
		self.proj_id = proj_id
		self.db_path = db_path

		# Grabbing the project data from the DB
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Projects")
		self.projects = pd.DataFrame(curs.fetchall(),columns=[description[0] for description in curs.description])
		self.projects.fillna("", inplace=True)
		conn.close()
		# Resetting index for ease of navigation
		self.projects.set_index('proj_id', drop=False, inplace=True)

		# Connecting the buttons
		self.pushButton_SaveClose.clicked.connect(lambda: self.closeDialog(save_settings=True))
		self.pushButton_Close.clicked.connect(self.closeDialog)
		self.pushButton_ProjFolderPath.clicked.connect(self.setProjFolderPath)

		# Checking if new project (and leaving most values blank then)
		if self.proj_id is None:
			self.initParentComboBox()
			return

		# Setting various values of the project for ease
		self.parent_id = self.projects.at[self.proj_id, "parent_id"]
		self.proj_text = self.projects.at[self.proj_id, "proj_text"]
		self.proj_path = self.projects.at[self.proj_id, "path"].replace("\\", "/")
		self.proj_desc = self.projects.at[self.proj_id, "description"]
		self.last_build = self.projects.at[self.proj_id, "bib_built"]

		self.initParentComboBox()

		self.populateFields()

	def setProjFolderPath(self):
		# Setting the dialog start path (in case the proj path doesn't exist)
		if (self.proj_id != None) and (os.path.exists(self.proj_path)):
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

		# Setting value to default if this is a new project
		if self.proj_id is None:
			self.comboBox_ProjParent.setCurrentIndex(0)
			return

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
		if (self.last_build == '') or (self.last_build == None):
			dt_obj = ''
		else:
			dt_obj = datetime.datetime.fromtimestamp(self.last_build/1e3)
			dt_obj = dt_obj.strftime('%m/%d/%Y, %#I:%M %p')
		self.label_BibFileBuiltDate.setText(dt_obj)

	def closeDialog(self, save_settings = False):
		"""
			This function will save any of the information that has been entered
			into the dialog.
		"""
		if not save_settings:
			# Setting variable so that parent window knows settings were not changed
			self.saved_settings = False
			self.parent_window.close()
			return

		if self.lineEdit_ProjName.text() == '':
			# Put up message saying project name is missing
			msg = "Must enter a non-empty name for this project."
			msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
									"Necessary Fields Missing.", msg,
									QtWidgets.QMessageBox.Ok)
			msg_diag.exec_()
			return

		# Extracting the values found in the various widgets
		value_dict = {'proj_text': self.lineEdit_ProjName.text(),
					'parent_id':  self.comboBox_Parent_IDs[self.comboBox_ProjParent.currentIndex()],
					'path': self.lineEdit_ProjPath.text(),
					'description': self.textEdit_ProjDesc.toPlainText(),
					'expand_default': 0}

		# If this was a new project then pick an unused ID and insert a new record.
		if self.proj_id is None:
			self.proj_id = self.projects['proj_id'].max()+1
			proj_data = {'proj_id':self.proj_id,
							'proj_text': self.lineEdit_ProjName.text()}
			aux.insertIntoDB(proj_data, 'Projects', self.db_path)

		# Iterate over values and update the DB
		for col_name, col_value in value_dict.items():
			aux.updateDB({'proj_id': self.proj_id}, col_name, col_value,
							self.db_path, table_name = 'Projects')

		# Setting variable so that parent window knows settings were changed
		self.saved_settings = True
		self.parent_window.close()
