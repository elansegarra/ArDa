from PyQt5 import QtCore, QtGui, QtWidgets
from ProDa.layouts.layout_tree_select_dialog import Ui_Dialog
from ArDa.myExtensions import projTreeModel
import sqlite3
import pandas as pd
import warnings
import pdb
import ArDa.aux_functions as aux

class TreeSelectDialog(QtWidgets.QDialog):
	def __init__(self, parent, db_path, tree_data, sel_ids = []):
		# Initializing the dialog and the layout
		super().__init__()
		self.ui = Ui_Dialog()
		self.ui.setupUi(self)

		# Setting class level variables
		self.db_path = db_path
		self.parent = parent
		self.tree_data = tree_data

		# Verifying that proper column names exist
		for col_name in ['item_id', 'item_text', 'parent_id', 'expand_default']:
			if col_name not in self.tree_data:
				print(f"{col_name} not found in passed dataframe.")

		# Set up the base model and filtering model behind the list view
		# self.qsfp_model = QtCore.QSortFilterProxyModel()
		# self.list_model = QtGui.QStandardItemModel(self.ui.listView_FilterVals)
		# self.qsfp_model.setSourceModel(self.list_model)
		# self.ui.listView_FilterVals.setModel(self.qsfp_model)

		# Connect the search field to the proxy model (and make case insensitive)
		# self.ui.lineEdit_Search.textChanged.connect(self.qsfp_model.setFilterRegExp)
		# self.qsfp_model.setFilterCaseSensitivity(0) # 0 = insensitive, 1 = sensitive

		self.ui.lineEdit_Search.setFocus()

		# Populate the list widget with the choices
		self.populateTreeValues(sel_item_ids=sel_ids)

		# self.project_tree_model = projTreeModel(self.tree_data, self.db_path)
		# self.treeView_Items.setModel(self.project_tree_model)

		# Connecting the ok/cancel buttons (so they do more than just close the window)
		self.ui.buttonBox.accepted.connect(self.acceptSelection)
		self.ui.buttonBox.rejected.connect(self.rejectSelection)

	def fieldChanged(self):
		# This function repopulates the list values
		self.populateTreeValues()

	def addChildrenOf(self, parent_tree_item, parent_id, sel_item_ids = []):
		''' This function adds all items (whose parent is parent_id) as children
			of tree_item

			:param QTreeWidgetItem parent_tree_item:
			:param int parent_id:
			:param list sel_item_ids:
			:return: list of QModelIndexes of all rows with selected IDs
		'''
		sel_inds = [] # This will hold the QModelIndexes of selected rows
		# Select just those with this parent_id
		child_df = self.tree_data[self.tree_data['parent_id']==parent_id]
		# Iterate over their children and add each in turn
		for index, row in child_df.iterrows():
			row_vals = [row['item_text'], str(row['item_id'])]
			item = QtWidgets.QTreeWidgetItem(parent_tree_item, row_vals)
			parent_tree_item.addChild(item)
			# Expanding if specified
			item.setExpanded(row['expand_default']==1)
			# Gathering the index if this item is selected
			if row['item_id'] in sel_item_ids:
				print(f"Saving {row['item_id']}")
				sel_inds.append(self.ui.treeWidget_Items.indexFromItem(item))
			# Now call again over any children of this child (meanwhile collecting selected indexes)
			sel_inds = sel_inds + self.addChildrenOf(item, row['item_id'],
															sel_item_ids)
		return sel_inds

	def populateTreeValues(self, sel_item_ids = [], show_ids = False):
		# This function populates all the values in the list view

		self.ui.treeWidget_Items.setColumnCount(2)
		sel_inds = [] # This holds QModelIndexes of rows to select

		# Adding an "All Projects" row
		root_item = QtWidgets.QTreeWidgetItem(self.ui.treeWidget_Items,
												["All Projects", "-1"])

		# Adding each upper level node to TreeWidget
		root_df = self.tree_data[self.tree_data['parent_id']==0]
		for index, row in root_df.iterrows():
			row_vals = [row['item_text'], str(row['item_id'])]
			root_item = QtWidgets.QTreeWidgetItem(self.ui.treeWidget_Items, row_vals)
			# Expanding if specified
			root_item.setExpanded(row['expand_default']==1)
			# Selecting if specified
			if row['item_id'] in sel_item_ids:
				sel_inds.append(self.ui.treeWidget_Items.indexFromItem(root_item))
			# Add all the children of this node
			sel_inds = sel_inds + self.addChildrenOf(root_item, row['item_id'],
													sel_item_ids=sel_item_ids)

		# Selecting any of the rows passed
		for sel_ind in sel_inds:
			sel_mode = QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.Select
			self.ui.treeWidget_Items.selectionModel().select(sel_ind, sel_mode)

		# Hide the ID column as specified
		if not show_ids:			self.ui.treeWidget_Items.hideColumn(1)

		# Resize all the columns
		self.ui.treeWidget_Items.resizeColumnToContents(0)

	def acceptSelection(self):
		sel_model = self.ui.treeWidget_Items.selectionModel()
		self.sel_ids = [int(x.data()) for x in sel_model.selectedRows(column=1)]
		self.sel_texts = [str(x.data()) for x in sel_model.selectedRows(column=0)]
		# print(self.sel_ids)
		# print(self.sel_texts)
		# Adjusting indexes if "All Projects" was selected
		if -1 in self.sel_ids:
			self.sel_ids = []

	def rejectSelection(self):
		return # Nothing else is done for the time being
