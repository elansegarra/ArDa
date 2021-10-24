# This file contains my custom extension of the view and model objects
#from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QLabel, QApplication, QAction, QTableView, QInputDialog
# from PyQt5.QtGui import QPainter, QFontMetrics, QTextDocument
import datetime
import ArDa.aux_functions as aux
import math, pdb, sqlite3, warnings
import numpy as np

class QSqlTreeProxyModel(QSortFilterProxyModel):
	def __init__(self, parent=None, table_model=None): #, table_model=None):
		super().__init__(parent)
		self.table_model = table_model
		# aux.debugTrace()

	def mapFromSource(self, sourceIndex):
		if not sourceIndex.isValid():
			return QModelIndex()
		cell_inds = [sourceIndex.row(), sourceIndex.column()]
		print(f"From source, {cell_inds}: {sourceIndex.data()}")
		# if sourceIndex.column() > 1:
		# aux.debugTrace()
		return super().mapFromSource(sourceIndex)

	def mapToSource(self, proxyIndex):
		if not proxyIndex.isValid():
			return QModelIndex()
		# cell_inds = [proxyIndex.row(), proxyIndex.column()]
		# print(f"To source, {cell_inds}: ") #{proxyIndex.data()}")
		# if proxyIndex.column() > 1:
		# 	aux.debugTrace()
		return super().mapToSource(proxyIndex)

	# def rowCount(self, index):
	# 	return 3
	#
	# def columnCount(self, index):
	# 	return 10
