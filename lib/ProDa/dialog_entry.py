from PyQt5 import QtCore, QtGui, QtWidgets
from ProDa.layouts.layout_entry_dialog import Ui_Dialog
import pandas as pd
import numpy as np
from datetime import date
import ArDa.aux_functions as aux
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
				value_dict['date_completed'] = QtCore.QDateTime.currentDateTime()
		else:
			# Grab the info associated with that id
			pass

		# Then we set the values given in the dictionary
		self.ui.lineEdit_Title.setText(value_dict.get('title', ''))
		self.ui.lineEdit_ID.setText(str(value_dict.get('id', -1)))
		self.ui.dateEdit_Date.setDateTime(value_dict.get('date',
											QtCore.QDateTime.currentDateTime()))
		self.ui.pushButton_Project.setText(value_dict.get('project', 'WHICH PROJECT?'))
		self.ui.pushButton_Parent.setText(value_dict.get('project', 'WHICH PARENT?'))
		self.ui.dateEdit_Completed.setDateTime(value_dict.get('date_completed',
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
		print("Open up a tree selection dialog box")
		return

	def recordValues(self):
		# This function records (in the DB) all the setting values
		return

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
