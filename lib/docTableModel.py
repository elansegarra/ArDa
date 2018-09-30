#from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
import math

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
