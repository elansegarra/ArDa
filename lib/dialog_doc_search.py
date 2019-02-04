from PyQt5 import QtCore, QtGui, QtWidgets
from layout_doc_search_dialog import Ui_Dialog
import sqlite3
import pandas as pd
import warnings
import pdb
from habanero import Crossref

class DocSearchDialog(QtWidgets.QDialog):
	def __init__(self, parent, arda_app, search_value = None, search_field = None):
		# Initializing the dialog and the layout
		super().__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)

		# Setting class level variables
		self.parent_window = parent
		self.arda_app = arda_app
		self.search_value = search_value
		self.search_field = search_field
		self.results_per_search = 50
		self.results_offset = 0
		# self.db_path = db_path

		# Querying Crossref
		self.cr = Crossref(mailto = "elanster@gmail.com")

		if search_value != None:
			self.ui.lineEdit_Search.setText(self.search_value)
			# self.ui.comboBox.setText(self.search_field)
			self.queryCrossref()
			self.populateTable()
		else:
			self.ui.label_TotalResults.setText(f"Total results: -")
			self.ui.label_ResultsShowing.setText(f"Showing results -")


		# Connecting the buttons
		self.ui.pushButton_Merge.clicked.connect(lambda: self.acceptSelection("merge"))
		self.ui.pushButton_Compare.clicked.connect(lambda: self.acceptSelection("compare"))
		self.ui.pushButton_Cancel.clicked.connect(self.rejectSelection)
		self.ui.pushButton_PageForward.clicked.connect(lambda: self.loadOtherResults('forward'))
		self.ui.pushButton_PageBack.clicked.connect(lambda: self.loadOtherResults('backward'))
		self.ui.pushButton_Search.clicked.connect(lambda: self.loadOtherResults('new'))

	def queryCrossref(self):
		# This function queries cross ref given the search string/field
		if self.search_field is None:
			x = self.cr.works(query =self.search_value, offset = self.results_offset,
							limit = self.results_per_search)
		else:
			print("Have not yet implemented field specific queries.")
			x = self.cr.works(query = self.search_value, offset = self.results_offset,
							limit = self.results_per_search)

		# Gathering the search result numbers
		self.num_all_results = x['message']['total-results']
		self.num_curr_results = len(x['message']['items'])

		self.curr_results = x['message']['items']

	def populateTable(self):
		# This function fills in the table with the query results

		# Updating labels referring to result counts
		self.ui.label_TotalResults.setText(f"Total results: {self.num_all_results}")
		num_start = self.results_offset + 1
		num_end = num_start + min(self.results_per_search, self.num_curr_results) - 1
		if self.num_all_results == 0:
			num_start = ""
			num_end = ""
		self.ui.label_ResultsShowing.setText(f"Showing results {num_start}-{num_end}")


		# Clearing the table
		self.ui.tableWidget_SearchResults.clear()

		# Setting the table dims
		self.ui.tableWidget_SearchResults.setRowCount(self.num_curr_results)
		self.ui.tableWidget_SearchResults.setColumnCount(3)

		for i in range(len(self.curr_results)):
			# Extracting the author list (and last names)
			authors = self.curr_results[i].get('author',[])
			author_lasts = [auth_dict.get('family', '') for auth_dict in authors]
			author_lasts = ', '.join(author_lasts)
			# Extracting the year (and subbing blank for none)
			year = self.curr_results[i]['issued']['date-parts'][0][0]
			year = str(year) if year != None else ""

			# Extracting the title (and subbing blank for none)
			title = self.curr_results[i].get('title', [''])[0]
			title = "" if title is None else title

			# Inserting elements into the row
			self.ui.tableWidget_SearchResults.setItem(i, 0, QtWidgets.QTableWidgetItem(author_lasts))
			self.ui.tableWidget_SearchResults.setItem(i, 1, QtWidgets.QTableWidgetItem(year))
			self.ui.tableWidget_SearchResults.setItem(i, 2, QtWidgets.QTableWidgetItem(title))

		# Labeling and resizing the columns
		col_names = ['Author', 'Year', 'Title']
		col_width = [250, 75, 600]
		for i in range(3):
			# self.ui.tableWidget_SearchResults.resizeColumnToContents(i)
			self.ui.tableWidget_SearchResults.setColumnWidth(i, col_width[i])
			t_item = QtWidgets.QTableWidgetItem(col_names[i])
			self.ui.tableWidget_SearchResults.setHorizontalHeaderItem(i, t_item)

		# Hiding the row labels
		self.ui.tableWidget_SearchResults.verticalHeader().setVisible(False)

		# Some additional table characteristics
		self.ui.tableWidget_SearchResults.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.ui.tableWidget_SearchResults.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

	def loadOtherResults(self, which_results):
		"""
			This function searches for another set of results going Either
			forward or bacward (depending on parameter passed)
			:param which_results: str either "forward" or "backward"
		"""
		if which_results == "forward":
			self.results_offset = self.results_offset + self.results_per_search
		elif which_results == "backward":
			self.results_offset = self.results_offset - self.results_per_search
		elif which_results == "new":
			self.results_offset = 0
			self.search_value = self.ui.lineEdit_Search.text()
		else:
			print(f"Unrecognized parameter value, {which_results}.")
			return


		self.queryCrossref()

		# Disable/enable buttons (depending if this is the first or last page)
		self.ui.pushButton_PageBack.setEnabled((self.results_offset != 0))
		self.ui.pushButton_PageForward.setEnabled((self.results_offset+self.results_per_search < self.num_all_results))

		self.populateTable()

	def acceptSelection(self, mode):
		# Check if all fields have had a selection chosen
		selected_row = self.ui.tableWidget_SearchResults.selectionModel().selectedRows()
		if len(selected_row) == 0:
			# Put up message saying some variables are not checked
			msg = "No document selected."
			msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
									"Incomplete selection", msg,
									QtWidgets.QMessageBox.Ok)
			msg_diag.exec_()
			return
		else:
			self.bib_dict = self.gatherSelection()
			if mode == "merge":
				print("Immediately merge")
			elif mode == "compare":
				print("Compare then maybe merge")
			self.accept()

	def rejectSelection(self):
		# Set merged to none (so we know th answer)
		self.bib_dict = None
		self.reject()

	def gatherSelection(self):
		# This function will create a dictionary with all the relevant data in the selected row

		# Get the selected row and corresponding dictionary
		selected_row = self.ui.tableWidget_SearchResults.selectionModel().selectedRows()
		id = selected_row[0].row()
		self.sel_doc = self.curr_results[id]

		# Checking for any new keys
		used_keys = {'institution', 'URL', 'title', 'author', 'DOI', 'publisher', 'type',
					 'ISSN', 'container-title', 'issue', 'volume', 'page', 'ISBN'}
		ignored_keys = {'deposited', 'issued', 'indexed', 'created', 'approved',
						'content-domain', 'degree', 'is-referenced-by-count', 'prefix',
						'references-count', 'reference-count', 'score', 'source',  'link',
						'short-container-title', 'issn-type', 'journal-issue', 'license',
						'published-print', 'language','published-online', 'relation',
						'isbn-type', 'subtitle', 'subject'}
		maybe_keys = {'member', 'alternative-id', 'reference', 'publisher-location'}
		if len(set(self.sel_doc.keys()) - used_keys - ignored_keys - maybe_keys)>0:
			new_keys = set(self.sel_doc.keys()) - used_keys - ignored_keys - maybe_keys
			warnings.warn(f"New keys found: {new_keys}.")

		# Convert this to a bib entry dict
		bib_dict = {}
		bib_dict['isbn'] = self.sel_doc.get('isbn-type', [{'value':None}])[0]['value']
		# bib_dict['isbn'] = self.sel_doc.get('ISBN', [None])[0]
		bib_dict['doi'] = self.sel_doc.get('DOI', None)
		bib_dict['issn'] = self.sel_doc.get('ISSN', None)
		bib_dict['title'] = self.sel_doc.get('title', None)
		bib_dict['journal'] = self.sel_doc.get('container-title', None)
		bib_dict['url'] = self.sel_doc.get('URL', None)
		bib_dict['number'] = self.sel_doc.get('issue', None)
		bib_dict['volume'] = self.sel_doc.get('volume', None)
		bib_dict['pages'] = self.sel_doc.get('page', None)
		bib_dict['publisher'] = self.sel_doc.get('publisher', None)

		bib_dict['year'] = self.sel_doc['issued']['date-parts'][0][0]
		bib_dict['year'] = str(bib_dict['year']) if bib_dict['year'] != None else None

		if 'institution' in self.sel_doc:
			bib_dict['institution'] = self.sel_doc['institution']['name']
			bib_dict['department'] = self.sel_doc['institution'].get('name', None)

		if 'author' in self.sel_doc:
			authors = self.sel_doc['author']
			authors = [auth.get('family', '')+", "+auth.get('given', '') for auth in authors]
			bib_dict['author'] = ' and '.join(authors)

		# Getting and converting the document type
		cr_type_dict = {'dissertation': 'unpublished',
						'journal-article': 'article',
						'component': 'inbook',
						'book-chapter': 'inbook',
						'report': 'report',
						'book': 'book',
						'other': 'misc',
						'proceedings-article': 'inproceedings',
						'report-series': 'report',
						'standard': 'misc',
						None: None}
		bib_dict['doc_type'] = self.sel_doc.get('type', None)
		if bib_dict['doc_type'] not in cr_type_dict:
			warnings.warn(f"A new unrecognized document type, {bib_dict['doc_type']}, was found.")
		bib_dict['doc_type'] = cr_type_dict.get(bib_dict['doc_type'], None)

		# Removing all parts with a value of none
		bib_dict = {key:value for key, value in bib_dict.items() if value != None}

		# Extracting all elements out of lists (just the first)
		bib_dict = {key:(value[0] if isinstance(value, list) else value) for key, value in bib_dict.items()}

		return bib_dict
