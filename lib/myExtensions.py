# This file contains my custom extension of the view and model objects
#from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from datetime import date
import aux_functions as aux
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

	def flags(self, index):
		# Need to reimplement to make items draggable (or editable)
		if not index.isValid():
			return Qt.ItemIsEnabled
		return Qt.ItemFlags(QAbstractTableModel.flags(self, index) | Qt.ItemIsDragEnabled)
		# Add the additional flag to make cell editable: Qt.ItemIsEditable

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

	### When these functions are not included I can drag to treeview, however when they are included I cannot
	# def mimeTypes(self):
	# 	return ['text/xml']

	# def mimeData(self, indexes):
	# 	print("mimData was called in document view!")
	# 	# mimedata = QMimeData()
	# 	# mimedata.setData('text/xml', 'mimeData')
	# 	mimedata = QMimeData()
	# 	encoded_data = QByteArray()
	# 	stream = QDataStream(encoded_data, QIODevice.WriteOnly)
	# 	for index in indexes:
	# 		if index.isValid():
	# 			text = self.data(index, 0)
	# 	stream << text # stream << QByteArray(text.encode('utf-8'))
	# 	mimedata.setData('text/xml', encoded_data)
	# 	print(text)
	# 	return mimedata

# Class to represent the tree items in the tree model
class treeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def setParent(self, parent):
        self.parentItem = parent

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

class projTreeModel(QAbstractItemModel):
	def __init__(self, data_in, parent=None):
		# QAbstractItemModel.__init__(self)
		super(projTreeModel, self).__init__(parent)

		self.cols_to_show = ['proj_text']#, 'description']
		self.rootItem = treeItem(['Project'])

		self.setupModelData(data_in, self.rootItem)

	def columnCount(self, parent):
		if parent.isValid():
			return parent.internalPointer().columnCount()
		else:
			return self.rootItem.columnCount()

	def data(self, index, role):
		if (not index.isValid()) | (role != Qt.DisplayRole):
			return None
		item = index.internalPointer()
		return item.data(index.column())

	def flags(self, index):
		if not index.isValid():
			return Qt.NoItemFlags
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self.rootItem.data(section)
		return None

	def index(self, row, column, parent):
		if not self.hasIndex(row, column, parent):
			return QModelIndex()
		if not parent.isValid():
			parentItem = self.rootItem
		else:
			parentItem = parent.internalPointer()
		childItem = parentItem.child(row)
		if childItem:
			return self.createIndex(row, column, childItem)
		else:
			return QModelIndex()

	def parent(self, index):
		if not index.isValid():
			return QModelIndex()

		childItem = index.internalPointer()
		parentItem = childItem.parent()

		if parentItem == self.rootItem:
			return QModelIndex()
		return self.createIndex(parentItem.row(), 0, parentItem)

	def rowCount(self, parent):
		if parent.column() > 0:
			return 0

		if not parent.isValid():
			parentItem = self.rootItem
		else:
			parentItem = parent.internalPointer()

		return parentItem.childCount()

	def setupModelData(self, data_df, root_parent):
		temp_df = data_df.copy()

		# First we order rows so parents always precede their children
		aux.setTreeLevels(temp_df, 'proj_id', 'parent_id', 0)
		temp_df.sort_values(['tree_level', 'proj_text'], inplace=True)

		# Make a dictionary of treeItems whose keys are the proj_ids
		self.tree_nodes = {x['proj_id']: treeItem([x[col] for col in self.cols_to_show ]) \
											for index, x in temp_df.iterrows()}

		# Assigning parents and children to all the nodes
		for index, row in temp_df.iterrows():
			proj_id = row['proj_id']
			parent_id = row['parent_id']
			# Assigning this row as the child of it's parent
			if parent_id == 0:
				self.tree_nodes[proj_id].setParent(root_parent)
				root_parent.appendChild(self.tree_nodes[proj_id])
			else:
				self.tree_nodes[proj_id].setParent(self.tree_nodes[parent_id])
				self.tree_nodes[parent_id].appendChild(self.tree_nodes[proj_id])
	
	## Everything below is from the previous incarnation of this class
	#
	# def index(self, row, column, parent):
	# 	return self.createIndex(row, column, self.nodes[row])
	#
	# def parent(self, index):
	# 	return QModelIndex()
	#
	# def rowCount(self, index):
	# 	if index.internalPointer() in self.nodes:
	# 		return 0
	# 	return len(self.nodes)
	#
	# def columnCount(self, index):
	# 	return 1
	#
	# def data(self, index, role):
	# 	if role == 0:
	# 		return index.internalPointer()
	# 	else:
	# 		return None
	# #
	# # def supportedDropActions(self):
	# # 	return None #Qt.CopyAction | Qt.MoveAction
	# #
	# # def dropMimeData(self, data, action, row, column, parent):
	# # 	print(f"Data Dropped on row: {row}, column: {column}, data: {data.data('text/xml')}")
	# # 	# print('dropMimeData %s %s %s %s' % (data.data('text/xml'), action, row, parent))
	# # 	return True
	# # #
	# # # def flags(self, index):
	# # #     if not index.isValid():
	# # #         return Qt.ItemIsEnabled
	# # #     return Qt.ItemIsEnabled | Qt.ItemIsSelectable | \
	# # #            Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
	# # #
	# # def mimeTypes(self):
	# # 	return ['text/xml']
	# #
	# # def mimeData(self, indexes):
	# # 	print("mimData was called in project view!")
	# # 	mimedata = QMimeData()
	# # 	mimedata.setData('text/xml', 'mimeData')
	# # 	return mimedata
	# # #
	# # def dropEvent(self, e):
	# # 	item=self.itemAt(e.pos())
	# # 	# if item: self.addHere(item)
	# # 	print(item)
	# # 	e.accept()

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
