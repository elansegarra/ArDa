from PyQt5 import QtCore, QtGui, QtWidgets
from layout_compare_dialog import Ui_Dialog
import sqlite3
import pandas as pd
import warnings
import pdb

class CompareDialog(QtWidgets.QDialog):
	def __init__(self, parent, doc_id_1, doc_id_2, db_path):
		# Initializing the dialog and the layout
		super().__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)

		# Setting class level variables
		self.parent_window = parent
		self.db_path = db_path

		# Grabbing the project data from the DB
		conn = sqlite3.connect(self.db_path)
		curs = conn.cursor()
		curs.execute(f"SELECT * FROM Documents WHERE doc_id in "+\
							f"({doc_id_1}, {doc_id_2})")
		self.doc_df = pd.DataFrame(curs.fetchall(),columns=[description[0] for description in curs.description])
		self.doc_df.fillna("", inplace=True)
		conn.close()

		# Check that two docs were found
		if self.doc_df.shape[0] != 2:
			print(f"Fewer than 2 bib entries found for IDs {doc_id_1} and "+\
					f"{doc_id_2}.")
			self.close()

		# Extracting bib entries for each doc
		self.LBibDict = self.doc_df.iloc[0]
		self.RBibDict = self.doc_df.iloc[1]

		self.populateFields()

		# Connecting the ok/cancel buttons (so they do more than just close the window)
		self.ui.buttonBox.accepted.connect(self.acceptSelection)
		self.ui.buttonBox.rejected.connect(self.rejectSelection)


	def populateFields(self):
		# This function initializes all the fields in the dialog
		# fields = ['title', 'author_lasts', 'year', 'journal']
		fields = list(self.doc_df.columns)
		self.widget_dict = {}
		field_dict = {}
		curr_row = 2

		for field in fields:
			# Creating the various widgets
			field_dict['FieldLabel'] = QtWidgets.QLabel(field, self.ui.scrollAreaWidgetContents)
			field_dict['LValue'] = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents)
			field_dict['RValue'] = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents)
			field_dict['bGroup']  = QtWidgets.QButtonGroup(self)
			field_dict['LCheckbox'] = QtWidgets.QCheckBox(self.ui.scrollAreaWidgetContents)
			field_dict['RCheckbox'] = QtWidgets.QCheckBox(self.ui.scrollAreaWidgetContents)

			# Setting their values
			field_dict['LValue'].setText(str(self.LBibDict[field]))
			field_dict['RValue'].setText(str(self.RBibDict[field]))

			# Adding to button group
			field_dict['bGroup'].addButton(field_dict['LCheckbox'])
			field_dict['bGroup'].addButton(field_dict['RCheckbox'])

			# Adding the widgets to layouts
			self.ui.gridLayout.addWidget(field_dict['FieldLabel'], curr_row, 0, 1, 1)
			self.ui.gridLayout.addWidget(field_dict['LValue'], curr_row, 1, 1, 1)
			self.ui.gridLayout.addWidget(field_dict['LCheckbox'], curr_row, 2, 1, 1)
			self.ui.gridLayout.addWidget(field_dict['RCheckbox'], curr_row, 3, 1, 1)
			self.ui.gridLayout.addWidget(field_dict['RValue'], curr_row, 4, 1, 1)

			# Increment row
			curr_row+=1


		# Setting values in main fields
		return

	def acceptSelection(self):
		self.parent.filter_field = self.ui.comboBox_Field.currentText()
		self.parent.filter_choices = [str(x.text()) for x in \
									self.ui.listWidget.selectedItems()]

	def rejectSelection(self):
		return # Nothing else is done for the time being
