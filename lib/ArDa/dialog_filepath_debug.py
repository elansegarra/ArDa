from PyQt5 import QtCore, QtGui, QtWidgets
from ArDa.layouts.layout_filepath_debug_dialog import Ui_Dialog
# import ArDa.aux_functions as aux
# import sqlite3
import pandas as pd
import warnings
from os import path
# import pdb
# from habanero import Crossref

class FilePathDebugDialog(QtWidgets.QDialog):
    def __init__(self, arda_app):
        # Initializing the dialog and the layout
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Setting class level variables
        self.arda_app = arda_app

        # Connecting the buttons
        self.ui.pushButton_MapPaths.clicked.connect(self.mapPaths)
        self.ui.pushButton_ChooseNewPath.clicked.connect(self.chooseNewPath)
        self.ui.pushButton_Cancel.clicked.connect(self.cancelMapping)
        self.ui.radioButton_LevelFolder.toggled.connect(self.populatePathsTable)
        self.ui.radioButton_LevelFile.toggled.connect(self.populatePathsTable)
        
        # Connecting any changes in the old path selection
        self.ui.tableWidget_PathsFound.selectionModel().selectionChanged.connect(self.setOldPathLabel)

        # Populating the table with path data
        self.populatePathsTable()

    def populatePathsTable(self):
        # This function fills in the table with the paths found and counts of files and existing files

        # Grab all the paths
        self.doc_df = self.arda_app.adb.get_doc_files_debugged()

        # Checking which level (folder or file) is indicated to be displayed and creating the corresponding df
        if self.ui.radioButton_LevelFolder.isChecked():
            # Groupby the folder path level
            self.path_df = self.doc_df.groupby('folder_path').agg({'file_exists':'sum','folder_exists':'sum','doc_id':'count'}).reset_index()
            self.path_df.sort_values('doc_id', inplace=True, ignore_index=True, ascending=False)
            # Specifying the column names (in df) and what to display in table (along with widths)
            df_col_names = ['doc_id', 'file_exists', 'folder_path']
            disp_col_names = ['File Ct', "Exist Ct", 'Folder Path']
            disp_col_widths = [100, 100, 600]
        elif self.ui.radioButton_LevelFile.isChecked():
            self.path_df = self.doc_df.copy()
            # Specifying the column names (in df) and what to display in table (along with widths)
            df_col_names = ['doc_id', 'file_exists', 'full_path']
            disp_col_names = ['Doc ID', "Exists", 'File Path']
            disp_col_widths = [100, 100, 600]
        else:
            raise NotImplementedError("Should not be able to get here, since one of the radio buttons should be checked")

        # Clearing the table
        self.ui.tableWidget_PathsFound.clear()

        # Setting the table dims
        self.ui.tableWidget_PathsFound.setRowCount(self.path_df.shape[0])
        self.ui.tableWidget_PathsFound.setColumnCount(len(df_col_names))

        for i, row in self.path_df.iterrows():
            # Inserting elements into the row
            self.ui.tableWidget_PathsFound.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[df_col_names[0]])))
            self.ui.tableWidget_PathsFound.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[df_col_names[1]])))
            self.ui.tableWidget_PathsFound.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row[df_col_names[2]])))

        # Labeling and resizing the columns
        for i in range(len(df_col_names)):
            # self.ui.tableWidget_PathsFound.resizeColumnToContents(i)
            self.ui.tableWidget_PathsFound.setColumnWidth(i, disp_col_widths[i])
            t_item = QtWidgets.QTableWidgetItem(disp_col_names[i])
            self.ui.tableWidget_PathsFound.setHorizontalHeaderItem(i, t_item)

        # Hiding the row labels
        self.ui.tableWidget_PathsFound.verticalHeader().setVisible(False)

    def setOldPathLabel(self):
        # Check if a single row has been selected (and grab the path if so)
        selected_rows = self.ui.tableWidget_PathsFound.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            old_path_text = ""
            paths_ct = 0
        elif len(selected_rows) == 1:
            selected_row = self.path_df.iloc[selected_rows[0].row()]
            # Which text to extract depends on whether file vs folder level is checked
            if self.ui.radioButton_LevelFolder.isChecked():
                old_path_text = selected_row['folder_path']
                paths_ct = selected_row['doc_id'] # This is the count of files with this path
            elif self.ui.radioButton_LevelFile.isChecked():
                old_path_text = selected_row['full_path']
                paths_ct = 1
            else:
                raise NotImplementedError("Should not be able to get here, since one of the radio buttons should be checked")
            
        else:
            raise NotImplementedError("Should not be able to get here")
        # Set this path to the display label
        self.ui.label_OldPath.setText(old_path_text)
        self.paths_ct = paths_ct
    
    def chooseNewPath(self):
        # Open a file dialog at the current DB folder
        dialog_path = self.arda_app.config['Data Sources']['def_pdfs_path']
        new_path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                    'Pick Folder For New Path',
                                    dialog_path, QtWidgets.QFileDialog.ShowDirsOnly)
        # Change the selected DB file if something was chosen
        if new_path != '':
            self.ui.lineEdit_NewPath.setText(new_path)

    def mapPaths(self):
        # Check if either an old path or a new path has not been set
        self.setOldPathLabel()
        if self.ui.label_OldPath.text() == "":
            # Put up message saying no document row has been selected
            msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                    "Cannot Map Paths", "No inital path selected.",
                                    QtWidgets.QMessageBox.Ok)
            msg_diag.exec_()
        elif self.ui.lineEdit_NewPath.text() == "":
            # Put up message saying no "to path" has been designated
            msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                    "Cannot Map Paths", "No new path specified.",
                                    QtWidgets.QMessageBox.Ok)
            msg_diag.exec_()
            return
        else:
            # Get the selected row (for previous path) and new path
            from_path = self.ui.label_OldPath.text()
            to_path = self.ui.lineEdit_NewPath.text()

            # Send up dialog confirming the mapping
            msg = f"Please confirm that you would like to replace \n\n'{from_path}'\
                        \n\nwith\n\n'{to_path}'\n\nacross {self.paths_ct} document file path(s)."
            # Add a warning if the to_path is not a valid directory
            if not path.exists(to_path): msg += "\n\nWARNING: The replacement path is not a valid/existing directory."
            msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,
                                    "Confirm Path Mapping", msg,
                                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            # msg_diag.setBaseSize(QtCore.QSize(1000, 1300)) #setStyleSheet("QLabel{min-width: 700px;}");
            response = msg_diag.exec_()
            if response == QtWidgets.QMessageBox.Ok:
                print("Ok was selected")
                # Map the paths as specified and display a quick result pop-up
                (num_paths, num_changed) = self.arda_app.adb.map_doc_paths(from_path, to_path)
                msg = f"Out of {num_paths} potential paths, {num_changed} paths were successfully changed."
                msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                    "Path Mapping Result", msg,
                                    QtWidgets.QMessageBox.Ok)
                msg_diag.exec_()
                # Repopulate the table to reflect the changes
                self.populatePathsTable()

    def cancelMapping(self):
        # Simply exit the dialog
        self.reject()