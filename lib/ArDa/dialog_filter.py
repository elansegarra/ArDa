from PyQt5 import QtCore, QtGui, QtWidgets
from ArDa.layouts.layout_filter_dialog import Ui_Dialog
import sqlite3
import pandas as pd
import warnings
import pdb

class FilterDialog(QtWidgets.QDialog):
    def __init__(self, parent, init_filter_field, db_path, doc_id_subset = None):
        # Initializing the dialog and the layout
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Setting class level variables
        self.db_path = db_path
        self.parent = parent
        self.doc_id_subset = doc_id_subset

        # Set combo box to initial field value and connect to listener
        self.ui.comboBox_Field.setCurrentText(init_filter_field)
        self.ui.comboBox_Field.currentIndexChanged.connect(self.fieldChanged)

        # Set up the base model and filtering model behind the list view
        self.qsfp_model = QtCore.QSortFilterProxyModel()
        self.list_model = QtGui.QStandardItemModel(self.ui.listView_FilterVals)
        self.qsfp_model.setSourceModel(self.list_model)
        self.ui.listView_FilterVals.setModel(self.qsfp_model)

        # Connect the serach field to the proxy model (and make case insensitive)
        self.ui.lineEdit_Search.textChanged.connect(self.qsfp_model.setFilterRegExp)
        self.qsfp_model.setFilterCaseSensitivity(0) # 0 = insensitive, 1 = sensitive

        self.ui.lineEdit_Search.setFocus()

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
            if self.doc_id_subset != None:
                self.temp_df = self.temp_df[self.temp_df['doc_id'].isin(self.doc_id_subset)]
            series_vals = self.temp_df['full_name']
        elif field_value == "Journal":
            curs.execute("SELECT * FROM Documents")
            cols = [description[0] for description in curs.description]
            self.temp_df = pd.DataFrame(curs.fetchall(),columns=cols)
            if self.doc_id_subset != None:
                self.temp_df = self.temp_df[self.temp_df['doc_id'].isin(self.doc_id_subset)]
            series_vals = self.temp_df['journal']
        elif field_value == "Keyword":
            curs.execute("SELECT * FROM Documents")
            cols = [description[0] for description in curs.description]
            self.temp_df = pd.DataFrame(curs.fetchall(),columns=cols)
            if self.doc_id_subset != None:
                self.temp_df = self.temp_df[self.temp_df['doc_id'].isin(self.doc_id_subset)]
            series_vals = self.temp_df['keyword'].dropna()
            series_vals = pd.Series([elt for list_ in series_vals.str.split(";") for elt in list_])
        else:
            print(f"Filter field ({field_value}) was not recognized.")
            return
        conn.close()

        # Deduplicating and sorting the values
        val_list = series_vals.drop_duplicates()
        val_list = val_list.loc[val_list.str.lower().sort_values().index]

        # Clearing list and adding new items to the list model (and thus view)
        self.list_model.clear()
        for val in val_list:
            item = QtGui.QStandardItem(val)
            self.list_model.appendRow(item)

    def acceptSelection(self):
        self.parent.filter_field = self.ui.comboBox_Field.currentText()
        self.parent.filter_choices = [str(x.data()) for x in \
                                    self.ui.listView_FilterVals.selectionModel().selectedRows()]
        # self.parent.filter_choices = [str(x.text()) for x in \
        # 							self.ui.listWidget.selectedItems()]

    def rejectSelection(self):
        return # Nothing else is done for the time being
