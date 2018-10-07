# This file contains my custom extension of the view and model objects
#from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from datetime import date
import math, pdb

class docTableModel(QAbstractTableModel):
	def __init__(self, datain, headerdata, parent=None, *args):
		QAbstractTableModel.__init__(self, parent, *args)
		self.arraydata = datain
		self.headerdata = headerdata

	def rowCount(self, parent):
		return self.arraydata.shape[0]

	def columnCount(self, parent):
		return self.arraydata.shape[1]

	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		elif role != Qt.DisplayRole:
			return QVariant()

		# Handling different column data types
		if self.headerdata[index.column()] == 'Year':
			if math.isnan(self.arraydata.iloc[index.row()][index.column()]): # Handling null values
				return QVariant()
			return QVariant(str(int(self.arraydata.iloc[index.row()][index.column()])))  #QVariant(self.arraydata[index.row()][index.column()])
		elif self.headerdata[index.column()] == 'DateRead':
			if self.arraydata.iloc[index.row()][index.column()] == date(1000, 1, 1): # Handling null values (this is the null date)
				return QVariant()
			return QVariant(str(self.arraydata.iloc[index.row()][index.column()]))
		elif self.headerdata[index.column()] == 'DateAdded':
			if self.arraydata.iloc[index.row()][index.column()] == date(1000, 1, 1): # Handling null values (this is the null date)
				return QVariant()
			# Converting to date
			date_int = self.arraydata.iloc[index.row()][index.column()]
			cell_date = date(date_int//10000, (date_int%10000)//100, date_int%100)
			return QVariant(str(cell_date))
		elif self.headerdata[index.column()] == 'ID':
			if math.isnan(self.arraydata.iloc[index.row()][index.column()]): # Handling null values
				return QVariant()
			return QVariant(int(self.arraydata.iloc[index.row()][index.column()]))  #QVariant(self.arraydata[index.row()][index.column()])
		else:
			return QVariant(str(self.arraydata.iloc[index.row()][index.column()]))  #QVariant(self.arraydata[index.row()][index.column()])

	def headerData(self, col, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return QVariant(self.headerdata[col])
		return QVariant()

	def getRowOfDocID(self, doc_id):
		# This function returns the row that contains the passed document id
		for i in range(self.arraydata.shape[0]):
			index = self.index(i, 0)
			#index = QModelIndex(i, 0)
			# pdb.set_trace()
			if self.data(index, Qt.DisplayRole).value() == doc_id:
				return i
			# if self.item(i,0).text() == doc_id:
			# 	return i
		return -1


# Customize a sort/filter proxy by making its filterAcceptsRow method
# test the character in that row against a filter function in the parent.
class mySortFilterProxy(QSortFilterProxyModel):
	def __init__(self, parent=None, table_model=None): #, table_model=None):
		QSortFilterProxyModel.__init__(self, parent)
		# Saving pointer to table model
		self.table_model = table_model
		# Initializing the doc_ID_show list
		self.show_list = None # Empty list indicates showing all documents
		# super(mySortFilterProxy, self).__init__(parent)
		# self.panelRef = parent # save pointer to the panel widget
		# self.setSortLocaleAware(True) # make sort respect accents? Defaults to off!

	def filterAcceptsRow(self, row, parent_index):
		# Grab the doc_id of this row
		qmi = self.table_model.index(row, 0, parent_index)
		doc_id = self.table_model.data(qmi,Qt.DisplayRole).value()
		# Checking if the row should be shown given the current filter
		if self.show_list is None:
			return True # Showing everything initially
		else:
			return (doc_id in self.show_list)

	def getRowFromDocID(self, doc_id):
		# This functions returns the row (given filter/sort) containing
		#	document with the passed document ID

		# Finding the index in the table model
		source_row = self.table_model.getRowOfDocID(doc_id)
		index = self.table_model.index(source_row,0)
		# Returning the row this corresponds to
		return self.mapFromSource(index).row()
