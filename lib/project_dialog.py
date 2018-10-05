import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from layout_proj_dialog import Ui_Form
import sqlite3, os
import pandas as pd
import numpy as np
from datetime import date
import aux_functions as aux
import warnings

class ProjectDialog(Ui_Form):

	#def __init__(self, dialog):
	def __init__(self, parent, proj_id, db_path):
		#super(ProjectDialog, self).__init__(parent)
		Ui_Form.__init__(self)
		self.setupUi(parent)

		# Setting class level variables
		self.proj_id = proj_id
		self.db_path = db_path

		# Grabbing the project data from the DB
		conn = sqlite3.connect(self.db_path) #"ElanDB.sqlite")
		curs = conn.cursor()
		curs.execute("SELECT * FROM Projects")
		self.projects = pd.DataFrame(curs.fetchall(),columns=['proj_id', 'proj_text',
														'parent_id', 'path', 'description'])
		conn.close()
		# Resetting index for ease of navigation
		self.projects.set_index('proj_id', drop=False, inplace=True)

		# Setting the id of the parent project and the the project text
		self.parent_id = self.projects.at[self.proj_id, "parent_id"]
		self.proj_text = self.projects.at[self.proj_id, "proj_text"]

		self.initParentComboBox()

		self.populateFields()

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

		# Removing the given project from these lists (it cannot be it's own parent)
		# temp_list = [x.strip() for x in self.comboBox_Parent_Choices]
		# this_proj_choice_index = temp_list.index(self.proj_text)
		# del self.comboBox_Parent_Choices[this_proj_choice_index]
		# del self.comboBox_Parent_IDs[this_proj_choice_index]
		# TODO: Fix removal of parent (still leans on the same project text)
		# TODO: Need to remove all children of this project as well

		# Adding the list of projects to the combo box
		self.comboBox_ProjParent.addItems(self.comboBox_Parent_Choices)

		# Getting current parent and setting value in combo box
		if self.parent_id not in self.comboBox_Parent_IDs:
			warnings.warn("Parent ID not found in the list")
		else:
			init_choice = self.comboBox_Parent_IDs.index(self.parent_id)
			self.comboBox_ProjParent.setCurrentIndex(init_choice)

		# Connecting combo box to action
		#self.comboBox_ProjParent.currentIndexChanged.connect(self.projectFilterEngaged)

	def populateFields(self):
		# This function initializes all the fields in the dialog

		# Setting values in main fields
		self.lineEdit_ProjName.setText(self.projects.at[self.proj_id, "proj_text"])
		self.textEdit_ProjDesc.setText(self.projects.at[self.proj_id, "description"])
		self.pushButton_ProjFolderPath.setText(self.projects.at[self.proj_id, "path"])
