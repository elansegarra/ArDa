import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from ArDa.layouts.layout_settings_dialog import Ui_Dialog
import sqlite3, os, datetime
import pandas as pd
import numpy as np
from datetime import date
import ArDa.aux_functions as aux
from util.my_widgets import QTextEditExt
import warnings
import pdb

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        # Initializing the dialog and the layout
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.parent_window = parent
        
        # Setting class level variables
        self.db_path_changed = False

        # Grabbing the settings and field data from the DB
        self.field_df = self.parent_window.adb.get_table("Fields")
        self.filter_df = self.parent_window.adb.get_table("Custom_Filters")

        # Transforming the dataframe into a dictionary
        self.settings_dict = parent.config #{k: g["var_value"].tolist() for k, g in self.s_df.groupby('var_name')}

        # Populating all the settings values
        self.populateSettingValues()

        # Setting up the button actions
        self.assignButtonActions()

        # Populate the Bib field checkboxes
        self.populateBibFields()

        # Populate the doc table column
        self.populateDocColumns()

        # Initialize the custom filter tab
        self.initCustomFilterTab()

    def populateSettingValues(self):
        config = self.parent_window.config
        # Setting the current DB path
        self.ui.lineEdit_DBPath.setText(self.parent_window.config['Data Sources']['db_path'])
        # Adding in the current watched folders
        for folder_path in dict(config['Watch Paths']).values():
            self.ui.listWidget_WatchedFolders.addItem(folder_path)
        # Loading other watched folder settings
        temp = (config['General Properties']['start_up_check_watched_folders'] == "True")
        self.ui.checkBox_CheckWatchStartup.setChecked(temp)
        self.ui.comboBox_FileFoundAction.setCurrentText(config['General Properties']['file_found_action'])

        # Loading backup parameters
        self.ui.spinBox_BackupsNumber.setValue(int(config['Backups']['backups_number']))
        self.ui.comboBox_BackupsFreq.setCurrentText(config['Backups']['backups_frequency'])

        # Loading project settings
        temp = (config['General Properties']['project_selection_cascade'] == "True")
        self.ui.checkBox_Cascade.setChecked(temp)

        # Loading bib file settings
        self.ui.lineEdit_BibPath.setText(config['Bib']['all_bib_path'])
        self.ui.comboBox_BibGenFreq.setCurrentText(config['Bib']['bib_gen_frequency'])

    def assignButtonActions(self):
        # Assign reponses to the various buttons in the settings dialog
        self.ui.pushButton_AddWatchFolder.clicked.connect(self.addWatchPath)
        self.ui.pushButton_RemoveWatchFolder.clicked.connect(self.removeWatchPath)
        self.ui.pushButton_DBPath.clicked.connect(self.changeDBPath)
        self.ui.pushButton_SaveClose.clicked.connect(self.closeDialog)
        self.ui.pushButton_Close.clicked.connect(lambda: self.closeDialog(no_save=True))

        # Assign action to watch path selection (enableing the remove button)
        self.ui.listWidget_WatchedFolders.itemSelectionChanged.connect(self.watchPathSelChanged)

    def addWatchPath(self):
        # Open a file dialog and pick a folder 
        dialog_path = self.parent_window.config['Data Sources']['def_pdfs_path']
        watch_folder = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                'Pick Watch Folder',
                                                                dialog_path)
        # Add the watch path if a folder was selected
        if watch_folder != '':
            self.ui.listWidget_WatchedFolders.addItem(watch_folder)

    def removeWatchPath(self):
        # Checks the selected watch path and removes it from the list widget
        sel_row = self.ui.listWidget_WatchedFolders.currentRow()
        # Remove the selected folder (if there's one selected)
        if sel_row != -1:
            self.ui.listWidget_WatchedFolders.takeItem(sel_row)
        # Check the number of items
        if self.ui.listWidget_WatchedFolders.count() == 0:
            self.ui.pushButton_RemoveWatchFolder.setEnabled(False)
    
    def changeDBPath(self):
        # Open a file dialog at the current DB folder
        dialog_path = self.parent_window.config['Data Sources']['db_path']
        db_file_path = QtWidgets.QFileDialog.getOpenFileName(self,
                                    'Pick DB File',
                                    dialog_path, "SqLite3 Files (*.sqlite)")[0]
        # Change the selected DB file if something was chosen
        if db_file_path != '':
            # Update the settings dialog box and flag that DB has changed
            db_file_path = db_file_path.replace("/", "\\")
            self.ui.lineEdit_DBPath.setText(db_file_path)
            self.db_path_changed = True

    def watchPathSelChanged(self):
        # Extract the selected watch paths
        sel_row = self.ui.listWidget_WatchedFolders.currentRow()
        # Enable/disable remove folder button accordingly
        if sel_row != -1:
            self.ui.pushButton_RemoveWatchFolder.setEnabled(True)
        else:
            self.ui.pushButton_RemoveWatchFolder.setEnabled(False)

    def updateLocalSettingsDict(self):
        # Grabbing config object for updating
        config = self.parent_window.config
        # This function updates self.settings_dict
        config['Data Sources']['db_path'] = self.ui.lineEdit_DBPath.text()
        config['General Properties']['start_up_check_watched_folders'] = str(self.ui.checkBox_CheckWatchStartup.isChecked())
        config['General Properties']['project_selection_cascade'] = str(self.ui.checkBox_Cascade.isChecked())
        config['Bib']['all_bib_path'] = self.ui.lineEdit_BibPath.text()
        config['General Properties']['file_found_action'] = self.ui.comboBox_FileFoundAction.currentText()
        config['Backups']['backups_number'] = str(self.ui.spinBox_BackupsNumber.value())
        config['Backups']['backups_frequency'] = self.ui.comboBox_BackupsFreq.currentText()
        config['Bib']['bib_gen_frequency'] = self.ui.comboBox_BibGenFreq.currentText()

        # Deleting all the stored watched folders in current config file
        config['Watch Paths'].clear()
        # Extracting all the watched folders found in the settings dialog
        for i in range(self.ui.listWidget_WatchedFolders.count()):
            config['Watch Paths'][f'path_{str(i+1).zfill(3)}'] = self.ui.listWidget_WatchedFolders.item(i).text()

    def populateDocColumns(self):
        # This function fills in the doc table columns in the list widgets

        temp_df = self.field_df[self.field_df['table_name']=='Documents'].copy()
        temp_df.sort_values(['doc_table_order', 'field'], inplace=True)

        # Iterate over the fields in the document table
        for index, row in temp_df.iterrows():
            # Skipping null rows
            if np.isnan(row['doc_table_order']):
                continue
            # Check if hidden
            if row['doc_table_order'] == -1:
                self.ui.listWidget_HiddenCols.addItem(row['field'])
            else:
                self.ui.listWidget_VisibleCols.addItem(row['field'])

    def populateBibFields(self):
        # This function adds checkboxes for the bib fields (and sets them accordingly)

        temp_df = self.field_df[self.field_df['table_name']=='Documents'].copy()
        temp_df.sort_values('field', inplace=True)
        # Creating dictionary to hold the checkbox widgets
        self.bib_checkboxes = dict()
        # Specifying some parameters for displaying checkboxes
        num_cols = 6		# Number of columns
        vert_order = True	# Indicates vertical ordering (True)
        num_fields = sum(~temp_df['include_bib_field'].isnull())
        num_rows = (num_fields // num_cols) + 1
        curr_index = 0

        # Iterate over the fields
        for index, row in temp_df.iterrows():
            if np.isnan(row['include_bib_field']):
                # print(row['field'])
                continue
            else:
                # Create a checkbox object for this field
                self.bib_checkboxes[row['field']] = QtWidgets.QCheckBox(self.ui.groupBox_2)
                self.bib_checkboxes[row['field']].setText(row['field'])
                # Setting the row and col to insert this checkbox into
                row_ind = (curr_index % num_rows if vert_order else curr_index // num_cols)
                col_ind = (curr_index // num_rows if vert_order else curr_index % num_cols)
                self.ui.gridLayout_3.addWidget(self.bib_checkboxes[row['field']],
                                                row_ind, col_ind, 1, 1)
                # Set to checked if indicated to be
                if row['include_bib_field'] == 1:
                    self.bib_checkboxes[row['field']].setChecked(True)
                # Incrementing position index
                curr_index+= 1

    ####  Custom Filter Tab ####################################################
    def initCustomFilterTab(self):
        # This function initializes the custom filters tab
        # Adding the custom filter names to the list widget
        self.filter_df.sort_values('filter_id', inplace=True)
        self.ui.listWidget_CustomFilters.addItems(list(self.filter_df["filter_name"]))

        # Replacing plainTextEdit with textEditExt widget
        self.ui.textEditExt_FilterCommand = QTextEditExt(self.ui.tab, self.ui)
        self.ui.textEditExt_FilterCommand.setEnabled(False)
        self.ui.textEditExt_FilterCommand.setObjectName("textEditExt_FilterCommand")
        self.ui.verticalLayout_4.addWidget(self.ui.textEditExt_FilterCommand)
        self.ui.plainTextEdit_FilterCommand.hide()

        # Connecting the filter buttons and list widget
        self.ui.pushButton_AddFilter.clicked.connect(self.addNewFilter)
        self.ui.pushButton_DeleteFilter.clicked.connect(self.deleteFilter)
        self.ui.pushButton_MoveFilterUp.clicked.connect(lambda: self.moveFilter("up"))
        self.ui.pushButton_MoveFilterDown.clicked.connect(lambda: self.moveFilter("down"))
        self.ui.listWidget_CustomFilters.itemSelectionChanged.connect(self.loadFilter)
        self.ui.lineEdit_FilterNameField.textEdited.connect(self.saveFilter)
        self.ui.textEditExt_FilterCommand.editingFinished.connect(self.saveFilter)

        # Setting indicator for whether a filter has ben changed
        self.custom_filters_changed = False

    def addNewFilter(self):
        # Create empty filter and add to df and list widget
        next_id = self.filter_df['filter_id'].max()+1
        new_row = {'filter_id':[next_id], 'filter_name':['New Filter'],
                    'filter_code':[""]}
        self.filter_df = pd.concat([self.filter_df, pd.DataFrame(new_row)], ignore_index=True, sort=False)
        self.ui.listWidget_CustomFilters.addItem(self.filter_df.at[next_id,"filter_name"])
        # Select the new filter (which will trigger loading it) and set focus
        self.ui.listWidget_CustomFilters.setCurrentRow(next_id)
        self.ui.lineEdit_FilterNameField.setFocus()
        self.ui.lineEdit_FilterNameField.selectAll()
        self.custom_filters_changed = True

    def deleteFilter(self):
        # Deletes the currently selected filter
        sel_rows = self.ui.listWidget_CustomFilters.selectedIndexes()
        if len(sel_rows) == 1:
            row_id = sel_rows[0].row()
            # Delete the row from the list widget and the df (and reset the index)
            self.ui.listWidget_CustomFilters.takeItem(row_id)
            self.filter_df.drop(row_id, axis=0, inplace=True)
            self.filter_df.reset_index(inplace=True, drop=True)
            self.filter_df['filter_id'] = self.filter_df.index
            # Clear the fields and toggle them off
            self.ui.lineEdit_FilterNameField.setText("")
            self.ui.textEditExt_FilterCommand.setPlainText("")
            self.enableFilterWidgets(toggle_on=False)
            # Deselect a list widget item and set to changed
            self.ui.listWidget_CustomFilters.clearSelection()
            self.custom_filters_changed = True

    def moveFilter(self, direction):
        # Moves the filter in the desired direction ("up" or "down")
        sel_rows = self.ui.listWidget_CustomFilters.selectedIndexes()
        if len(sel_rows) != 1: return
        sel_row = sel_rows[0].row()
        if (direction == "up") and (sel_row != 0):
            row_1 = sel_row-1
            row_2 = sel_row
            new_row = row_1
        elif (direction == "down") and (sel_row != self.filter_df.filter_id.max()):
            row_1 = sel_row
            row_2 = sel_row+1
            new_row = row_2
        else:
            warnings.warn("Move filter function invoked, but something is incorrect.")
            return
        # Swapping order of rows in df
        self.filter_df.at[row_1,"filter_id"] = row_2
        self.filter_df.at[row_2,"filter_id"] = row_1
        self.filter_df.sort_values("filter_id", inplace=True)
        self.filter_df.reset_index(inplace=True, drop=True)
        # Swapping the order in the list widget
        self.ui.listWidget_CustomFilters.insertItem(row_1, self.ui.listWidget_CustomFilters.takeItem(row_2))
        self.ui.listWidget_CustomFilters.setCurrentRow(new_row)
        self.custom_filters_changed = True

    def enableFilterWidgets(self, toggle_on = True):
        # Enables/Disables filter widgets
        filter_widgets = [self.ui.pushButton_DeleteFilter, self.ui.lineEdit_FilterNameField,
                            self.ui.textEditExt_FilterCommand, self.ui.pushButton_MoveFilterUp,
                            self.ui.pushButton_MoveFilterDown]
        for w in filter_widgets:
            w.setEnabled(toggle_on)

    def loadFilter(self):
        # Checks the current selected filter and loads its contents
        sel_rows = self.ui.listWidget_CustomFilters.selectedIndexes()
        if len(sel_rows) == 0:
            self.enableFilterWidgets(toggle_on=False)
        elif len(sel_rows) == 1:
            row_id = sel_rows[0].row()
            # Enable the filter info boxes and populate with values
            self.enableFilterWidgets(toggle_on=True)
            filter_name = self.filter_df.at[row_id, "filter_name"]
            filter_code = self.filter_df.at[row_id, "filter_code"]
            self.ui.lineEdit_FilterNameField.setText(filter_name)
            self.ui.textEditExt_FilterCommand.setPlainText(filter_code)
        else:
            warnings.warn("Mutiple customs filters selected. Should not be possible.")
            return

    def saveFilter(self):
        # Saves the current filter name and text to the filter df (NOT the DB)
        self.custom_filters_changed = True
        sel_rows = self.ui.listWidget_CustomFilters.selectedIndexes()
        if len(sel_rows) == 1:
            row_id = sel_rows[0].row()
            # Grab the name and filter code and save to df
            self.filter_df.at[row_id, "filter_name"] = self.ui.lineEdit_FilterNameField.text()
            self.filter_df.at[row_id, "filter_code"] = self.ui.textEditExt_FilterCommand.document().toPlainText()
            # Update the name in the list widget
            self.ui.listWidget_CustomFilters.selectedItems()[0].setText(self.ui.lineEdit_FilterNameField.text())

    ####  Dialog Settings ######################################################

    def recordSettingsValues(self):
        # This function records (in the config file) all the setting values

        # First we update the local dictionary
        self.updateLocalSettingsDict()

        # Then we save the config file where all the values were stored
        with open("user/config.ini", 'w') as configfile:
            self.parent_window.config.write(configfile)

        # This iterates through bib field defaults and updates DB with checkbox state
        for field, checkbox in self.bib_checkboxes.items():
            val = (1 if checkbox.isChecked() else 0)
            cond_dict = {'table_name':'Documents', 'field':field}
            self.parent_window.adb.update_record(cond_dict, 'include_bib_field', val,
                            table_name='Fields')

        # This iterates through elements of column lists (hidden and visible)
        for i in range(self.ui.listWidget_HiddenCols.count()):
            field = self.ui.listWidget_HiddenCols.item(i).text()
            cond_dict = {'table_name':'Documents', 'field':field}
            self.parent_window.adb.update_record(cond_dict, 'doc_table_order', -1,
                            table_name = "Fields")
        for i in range(self.ui.listWidget_VisibleCols.count()):
            field = self.ui.listWidget_VisibleCols.item(i).text()
            cond_dict = {'table_name':'Documents', 'field':field}
            self.parent_window.adb.update_record(cond_dict, 'doc_table_order', i,
                            table_name = "Fields")

        # This saves the custom filters (if any have changed)
        if self.custom_filters_changed:
            # Overwrite the existing custom filter table
            conn = sqlite3.connect(self.parent_window.adb.db_path)
            self.filter_df.to_sql('Custom_Filters', conn, if_exists = "replace", index = False)
            conn.close()

    def closeDialog(self, no_save = False):
        """
            This function will save any of the information that has been entered
            into the dialog.
        """
        if no_save:
            self.reject()
        else:
            self.recordSettingsValues()
            self.accept()
