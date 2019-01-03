# This file contains my custom extension of the view and model objects
#from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from datetime import date
import aux_functions as aux
import math, pdb, sqlite3, warnings
import numpy as np

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

		# Grabbing cell value and checking if empty or null
		cell_val = self.arraydata.iloc[index.row()][index.column()]
		if (cell_val==None) | (cell_val==''): # Handling null values
			return QVariant()
		if isinstance(cell_val, float) or isinstance(cell_val, int):
			if math.isnan(cell_val):
				return QVariant()

		# Handling different column data types
		col_name = self.headerdata[index.column()]
		if col_name == 'Year':
			return QVariant(str(int(cell_val)))
		elif col_name in ['Added', 'Read']:
			if isinstance(cell_val, float): # Converting to int
				cell_val = int(cell_val)
			# Converting to date
			cell_date = date(cell_val//10000, (cell_val%10000)//100, cell_val%100)
			return QVariant(str(cell_date))
		elif col_name == 'ID':
			return QVariant(int(cell_val))  #QVariant(self.arraydata[index.row()][index.column()])
		else:
			return QVariant(str(cell_val))  #QVariant(self.arraydata[index.row()][index.column()])

	def headerData(self, col, orientation, role):
		## For debugging the header out of bounds issue
		# if orientation == Qt.Horizontal:
		# 	print(f"headerData, orient = horizontal, role = {role}, col = {col}")
		# if orientation == Qt.Vertical:
		# 	print(f"headerData, orient = vertical, role = {role}, col = {col}")

		if (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
			if col >= self.headerdata.shape[0]:
				warnings.warn(f"Out of bounds header data called (col={col}), maybe problem?")
				return QVariant("OUT OF BOUNDS")
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
			if self.data(index, Qt.DisplayRole).value() == doc_id:
				return i
			# if self.item(i,0).text() == doc_id:
			# 	return i
		return -1

	def mimeTypes(self):
		return ['text/xml']

	def mimeData(self, indexes):
		print("mimData was called in document view!")
		mimedata = QMimeData()
		# Extracting the dragged data
		data = [self.data(index, 0) for index in indexes]
		# Extracting the document id (I think...)
		text = data[0]

		# Encoding the data (may not be required)
		encoded_data = QByteArray()
		# stream = QDataStream(encoded_data, QIODevice.WriteOnly)
		# stream << text # stream << QByteArray(text.encode('utf-8'))
		mimedata.setData('text/xml', encoded_data)

		mimedata.setText(str(text.value()))
		print(f'Dragging document: {text.value()}')
		return mimedata

# Class to represent the tree items in the tree model
class treeItem(object):
	def __init__(self, data, uid, parent=None):
		self.parentItem = parent
		self.itemData = data
		self.uid = uid
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
	def __init__(self, data_in, db_path, parent=None):
		# QAbstractItemModel.__init__(self)
		super(projTreeModel, self).__init__(parent)

		self.db_path = db_path

		self.cols_to_show = ['proj_text', 'proj_id']#, 'description']
		self.rootItem = treeItem(['Project', 'ID'], -1)

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
		return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled

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

	def indexFromProjID(self, proj_id):
		# This returns the QModel index associated with the passed project ID
		if not proj_id in self.tree_nodes:
			return QModelIndex()
		node = self.tree_nodes[proj_id]
		row = node.row()
		ind = self.createIndex(row,0,node)
		return ind

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
		self.tree_nodes = {x['proj_id']: \
							treeItem([x[col] for col in self.cols_to_show ],x['proj_id']) \
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

	def dropMimeData(self, data, action, row, column, parent):
		# This decodes the data  (maybe I don't need all this?)
		# encoded_data = data.data('text/xml')
		# stream = QDataStream(encoded_data, QIODevice.ReadOnly)
		#
		# new_items = []
		# rows = 0
		# while not stream.atEnd():
		# 	text = QByteArray()
		# 	stream >> text
		# 	# text = bytes(text).decode('utf-8')
		# 	# index = self.nodes.index(text)
		# 	new_items.append(text)
		# 	rows += 1
		doc_id = int(data.text())
		proj_id = parent.internalPointer().uid
		print(f"Document ID = {doc_id} dropped on project ID = {proj_id}")

		# Selecting all doc IDs that are in this project
		conn = sqlite3.connect(self.db_path)
		curs = conn.cursor()
		curs.execute(f'SELECT doc_id FROM Doc_Proj WHERE proj_id == "{proj_id}"')
		docs_in_proj = set([x[0] for x in curs.fetchall()])

		# Check if the document is already in that project
		if doc_id in docs_in_proj:
			print(f"Document ID = {doc_id} is already in project ID = {proj_id}.")
		else:
			print(f"Document ID = {doc_id} is not in project ID = {proj_id}. Adding now.")
			command = f'INSERT INTO Doc_proj (doc_id, proj_id) VALUES'+\
							f'({doc_id}, {proj_id})'
			print(command)
			curs.execute(command)

			try: # Saving changes
				conn.commit()
			except sqlite3.OperationalError:
				print("Unable to save the DB changes (DB may be open elsewhere)")
				conn.close()
				return
			result = curs.fetchall()
		conn.close()
		return True

	def mimeTypes(self):
		return ['text/xml']

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
