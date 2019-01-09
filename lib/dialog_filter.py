from PyQt5 import QtCore, QtGui, QtWidgets
from layout_filter_dialog import Ui_Dialog
import sqlite3
import pandas as pd
import warnings
import pdb

class FilterDialog(QtWidgets.QDialog):
	def __init__(self, parent, init_filter_field, db_path):
		# Initializing the dialog and the layout
		super().__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)

		# Setting class level variables
		self.db_path = db_path
		self.parent = parent

		# Set combo box to initial field value and connect to listener
		self.ui.comboBox_Field.setCurrentText(init_filter_field)
		self.ui.comboBox_Field.currentIndexChanged.connect(self.fieldChanged)

		# Populate the list widet with the choices
		self.populateListValues(init_filter_field)

		# Connecting the ok/cancel buttons (so they do more than just close the window)
		self.ui.buttonBox.accepted.connect(self.acceptSelection)
		self.ui.buttonBox.rejected.connect(self.rejectSelection)

	def fieldChanged(self):
		# This function repopulates the list values
		self.populateListValues(self.ui.comboBox_Field.currentText())

	def populateListValues(self, field_value):
		# This function populates all the values in the list view

		# Opening a connection to the DB
		conn = sqlite3.connect(self.db_path)
		curs = conn.cursor()
		# Grabbing the relevant data from the proper table
		if field_value == "Author":
			curs.execute("SELECT * FROM Doc_Auth")
			cols = [description[0] for description in curs.description]
			self.temp_df = pd.DataFrame(curs.fetchall(),columns=cols)
			self.temp_df['val'] = self.temp_df['full_name']
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
			# TODO: Implement keyword gathering for filtering dialog
		else:
			print(f"Filter field ({field_value}) was not recognized.")
			return
		conn.close()

		# Sorting, extracting, and deduplicating the values
		val_list = self.temp_df.sort_values('val')['val'].drop_duplicates()

		# Clearing list and adding new items
		self.ui.listWidget.clear()
		self.ui.listWidget.addItems(val_list)

	def acceptSelection(self):
		self.parent.filter_field = self.ui.comboBox_Field.currentText()
		self.parent.filter_choices = [str(x.text()) for x in \
									self.ui.listWidget.selectedItems()]

	def rejectSelection(self):
		return # Nothing else is done for the time being
