from PyQt5 import QtCore, QtGui, QtWidgets
from layout_filter_dialog import Ui_Dialog
import sqlite3
import pandas as pd
import numpy as np
import aux_functions as aux
import warnings
import pdb

class FilterDialog(QtWidgets.QDialog): #Ui_Dialog):

	# def __init__(self, dialog):
	def __init__(self, parent, init_filter_field, db_path):
		# Initializin the dialog and the layout
		super().__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)

		# Setting class level variables
		self.db_path = db_path
		self.parent = parent

		# Set combo box to initial field value
		self.ui.comboBox_Field.setCurrentText(init_filter_field)

		# Populate the list widet with the choices
		self.populateListValues(init_filter_field)

		# Connecting the ok/cancel buttons (so they do more than just close the window)
		self.ui.buttonBox.accepted.connect(self.acceptSelection)
		self.ui.buttonBox.rejected.connect(self.rejectSelection)

	def populateListValues(self, field_value):
		# This function populates all the values in the list view

		# Grabbing the project data from the DB
		conn = sqlite3.connect(self.db_path)
		curs = conn.cursor()
		if field_value == "Author":
			curs.execute("SELECT * FROM Authors")
			cols = [description[0] for description in curs.description]
			self.temp_df = pd.DataFrame(curs.fetchall(),columns=cols)
			self.temp_df['val'] = self.temp_df['last_name'] + ', ' + self.temp_df['first_name']
		elif field_value == "Journal":
			curs.execute("SELECT * FROM Documents")
			cols = [description[0] for description in curs.description]
			self.temp_df = pd.DataFrame(curs.fetchall(),columns=cols)
			self.temp_df['val'] = self.temp_df['journal']
		elif field_value == "Keyword":
			curs.execute("SELECT * FROM Documents")
			cols = [description[0] for description in curs.description]
			self.temp_df = pd.DataFrame(curs.fetchall(),columns=cols)
			self.temp_df['val'] = 'KEYWORDS'
		else:
			print(f"Filter field ({field_value}) was not recognized")
			return
		# self.temp_df.fillna("", inplace=True)
		conn.close()
		# pdb.set_trace()
		print(field_value)
		# Sorting and extracting values
		val_list = self.temp_df.sort_values('val')['val'].drop_duplicates()

		# Clearin list and adding new items
		self.ui.listWidget.clear()
		self.ui.listWidget.addItems(val_list)

		return

	def acceptSelection(self):
		self.parent.result = "Results was accepted."

	def rejectSelection(self):
		self.parent.result = "Canceled!! But why?"

	def saveAndClose(self):
		"""
			This function will save any of the information that has been entered
			into the dialog.
		"""
		# TODO: Implement comparing field data to the current values in DB

		# TODO: Implement saving any changed project data (and asking if okay)
		self.parent_window.close()
