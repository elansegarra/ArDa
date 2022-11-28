from PyQt5 import QtCore, QtGui, QtWidgets
from ArDa.layouts.layout_compare_dialog import Ui_Dialog
from util.my_widgets import QTextEditExt
import sqlite3
import pandas as pd
import warnings
import pdb

class CompareDialog(QtWidgets.QDialog):
    def __init__(self, parent, doc_id_L, doc_id_R, only_diff=True):
        # Initializing the dialog and the layout
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Setting class level variables
        self.parent_window = parent
        self.only_diff = only_diff
        self.doc_id_L = doc_id_L
        self.doc_id_R = doc_id_R

        # Grabbing the field data
        self.field_df = self.parent_window.adb.get_table("Fields")
        self.field_df = self.field_df[self.field_df.table_name=="Documents"]
        
        # Grabbing any file path data
        self.doc_path_df = self.parent_window.adb.get_table("Doc_Paths")
        self.doc_path_df = self.doc_path_df[self.doc_path_df.doc_id.isin([self.doc_id_L, self.doc_id_R])]

        # Extracting bib entries for each doc
        self.LBibDict = self.parent_window.adb.get_doc_record(self.doc_id_L)
        self.RBibDict = self.parent_window.adb.get_doc_record(self.doc_id_R)

        # Adding the filepath information
        doc_1_files = self.doc_path_df[self.doc_path_df['doc_id']==doc_id_L]['full_path'].tolist()
        doc_2_files = self.doc_path_df[self.doc_path_df['doc_id']==doc_id_R]['full_path'].tolist()
        self.LBibDict['file_path'] = "\n".join(doc_1_files)
        self.RBibDict['file_path'] = "\n".join(doc_2_files)

        # Adding file path to fields df (so row is generated automatically)
        self.field_df = self.field_df.append({'field':'file_path',
                                                'header_text':'File Paths',
                                                'meta_widget_name':'textEditExt'},
                                            ignore_index=True)

        self.populateFields()

        # Connecting the ok/cancel buttons (so they do more than just close the window)
        self.ui.buttonBox.accepted.disconnect()
        self.ui.buttonBox.accepted.connect(self.acceptSelection)
        self.ui.buttonBox.rejected.connect(self.rejectSelection)
        # self.ui.pushButton.clicked.connect(self.acceptSelection)

        # Connecting the all/nothing toggles
        self.ui.checkBox_AllLeft.stateChanged.connect(lambda: self.checkUncheckAll('L'))
        self.ui.checkBox_AllRight.stateChanged.connect(lambda: self.checkUncheckAll('R'))


    def populateFields(self):
        # This function initializes all the fields in the dialog
        self.widget_dict = {}
        field_dict = {}
        curr_row = 2

        for index, row in self.field_df.iterrows():
            field = row['field']
            # Filling in blanks if either is missing this key
            if field not in self.LBibDict: self.LBibDict[field] = ""
            if field not in self.RBibDict: self.RBibDict[field] = ""

            # Checking if values are same (then can skip)
            if (self.only_diff) and (self.LBibDict[field] == self.RBibDict[field]):
                continue

            # Creating the various widgets
            field_dict['FieldLabel'] = QtWidgets.QLabel(self.ui.scrollAreaWidgetContents)
            if row['meta_widget_name'].startswith('textEditExt'):
                field_dict['LValue'] = QTextEditExt(self.ui.scrollAreaWidgetContents, self)
                field_dict['RValue'] = QTextEditExt(self.ui.scrollAreaWidgetContents, self)
            else:
                field_dict['LValue'] = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents)
                field_dict['RValue'] = QtWidgets.QLineEdit(self.ui.scrollAreaWidgetContents)
            field_dict['bGroup']  = QtWidgets.QButtonGroup(self)
            field_dict['LCheckbox'] = QtWidgets.QCheckBox(self.ui.scrollAreaWidgetContents)
            field_dict['RCheckbox'] = QtWidgets.QCheckBox(self.ui.scrollAreaWidgetContents)

            # Setting color toggling
            # field_dict['LCheckbox'].setStyleSheet("QCheckBox::indicator:unchecked {background-color: red;}")

            # Saving them in the class dictionary
            self.widget_dict[field] = field_dict.copy()

            # Setting their values and other properties
            field_dict['FieldLabel'].setText(row['header_text']+":")
            field_dict['LValue'].setText(str(self.LBibDict[field]))
            field_dict['RValue'].setText(str(self.RBibDict[field]))
            field_dict['FieldLabel'].setAlignment(QtCore.Qt.AlignRight)
            if row['meta_widget_name'].startswith('textEditExt'):
                # Calculating the max height among the two widgets' text
                max_height = max(field_dict['LValue'].document().size().height(),
                                    field_dict['RValue'].document().size().height())
                field_dict['LValue'].setMinimumHeight(max_height)
                field_dict['RValue'].setMinimumHeight(max_height)
            # Setting to uneditable for doc id field
            if field == 'doc_id':
                field_dict['LValue'].setEnabled(False)
                field_dict['RValue'].setEnabled(False)

            # Turning check box on if other side is empty
            if (str(self.LBibDict[field]) == "") and (str(self.RBibDict[field]) != ""):
                field_dict['RCheckbox'].toggle()
            elif (str(self.LBibDict[field]) != "") and (str(self.RBibDict[field]) == ""):
                field_dict['LCheckbox'].toggle()

            # Auto toggling choices for max modified date, min added date, and min doc_id
            if field == 'modified_date':
                if int(self.LBibDict[field]) > int(self.RBibDict[field]):
                    field_dict['LCheckbox'].toggle()
                else:
                    field_dict['RCheckbox'].toggle()
            elif field == 'add_date':
                if int(self.LBibDict[field]) < int(self.RBibDict[field]):
                    field_dict['LCheckbox'].toggle()
                else:
                    field_dict['RCheckbox'].toggle()
            elif field == 'doc_id':
                if int(self.LBibDict[field]) < int(self.RBibDict[field]):
                    field_dict['LCheckbox'].toggle()
                else:
                    field_dict['RCheckbox'].toggle()

            # Adding to button group
            field_dict['bGroup'].addButton(field_dict['LCheckbox'])
            field_dict['bGroup'].addButton(field_dict['RCheckbox'])

            # Adding the widgets to layouts
            self.ui.gridLayout.addWidget(field_dict['LValue'], curr_row, 1, 1, 1)
            self.ui.gridLayout.addWidget(field_dict['LCheckbox'], curr_row, 2, 1, 1)
            self.ui.gridLayout.addWidget(field_dict['FieldLabel'], curr_row, 0, 1, 1)
            self.ui.gridLayout.addWidget(field_dict['RCheckbox'], curr_row, 3, 1, 1)
            self.ui.gridLayout.addWidget(field_dict['RValue'], curr_row, 4, 1, 1)

            # Increment row
            curr_row+=1

        # Adding a spacer at the bottom
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.ui.gridLayout.addItem(spacerItem, curr_row, 2, 1, 1)

    def acceptSelection(self):
        # Check if all fields have had a selection chosen
        unsel_fields = self.fieldsWithoutSelection()
        if len(unsel_fields) != 0:
            # Put up message saying some variables are not checked
            msg = "Selections missing. A choice must be selected for each " +\
                    "field presented."
            msg_diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                    "Incomplete selection", msg,
                                    QtWidgets.QMessageBox.Ok)
            msg_diag.setInformativeText(f"Unselected fields: {', '.join(unsel_fields)}")
            msg_diag.exec_()
        else:
            # Set the selected values to a class variable
            self.merged_bib_dict, self.doc_id_dict = self.gatherSelection()
            self.accept()

        # Gather the checked fields into a new dictionary

    def rejectSelection(self):
        # Set merged to none (so we know th answer)
        self.merged_bib_dict = None
        return # Nothing else is done for the time being

    def gatherSelection(self):
        # This function will create a dictionary with all the selections made
        #	(one with the actual values and one with which doc_id was chosen)
        if len(self.fieldsWithoutSelection()) != 0:
            print("Aborting collection of selections since not all have been made.")
            return

        sel_dict = {}
        doc_id_dict = {}
        for index, row in self.field_df.iterrows():
            field = row['field']
            # Checking if values are the same (in which case the checkbox shouldn't exist)
            if (self.only_diff) and (self.LBibDict[field] == self.RBibDict[field]):
                continue
            # Select appropriate widget (depending on which box is selected)
            if self.widget_dict[field]['LCheckbox'].isChecked():
                curr_widget = self.widget_dict[field]['LValue']
                sel_doc_id = self.doc_id_L
            elif self.widget_dict[field]['RCheckbox'].isChecked():
                curr_widget = self.widget_dict[field]['RValue']
                sel_doc_id = self.doc_id_R
            else:
                warnings.warn("You should never reach here since at least one must be selected.")
                curr_widget = None
            # Gather text out of the widget (depends on widget type)
            if row['meta_widget_name'].startswith('textEditExt'):
                sel_dict[field] = curr_widget.toPlainText()
                doc_id_dict[field] = sel_doc_id
            elif curr_widget == None:
                sel_dict[field] = None
                doc_id_dict[field] = None
            else:
                sel_dict[field] = curr_widget.text()
                doc_id_dict[field] = sel_doc_id
        return sel_dict, doc_id_dict

    def fieldsWithoutSelection(self):
        # This function returns a list of the fields that remain unselected
        unsel_fields = []
        for key, value in self.widget_dict.items():
            LChecked = self.widget_dict[key]['LCheckbox'].isChecked()
            RChecked = self.widget_dict[key]['RCheckbox'].isChecked()
            if (not LChecked) and (not RChecked):
                unsel_fields.append(key)
        return unsel_fields

    def checkUncheckAll(self, L_or_R):
        # Either toggles all the L or R checks on or off depending on the primary check box.

        # Gather the state of the group checkBox (to mirror it below)
        if L_or_R == "L":
            main_checked = self.ui.checkBox_AllLeft.checkState()
        elif L_or_R == "R":
            main_checked = self.ui.checkBox_AllRight.checkState()
        else:
            warnings.warn(f"Unrecognized value ({L_or_R}) sent to function.")
            return

        # If main is unchecked then don't do anything
        if not main_checked:
            return

        # Set all the values on this side accordingly
        if L_or_R == "L":
            for key, value in self.widget_dict.items():
                if main_checked == 0:
                    self.widget_dict[key]['RCheckbox'].setChecked(True)
                else:
                    self.widget_dict[key]['LCheckbox'].setChecked(True)
        else:
            for key, value in self.widget_dict.items():
                if main_checked == 0:
                    self.widget_dict[key]['LCheckbox'].setChecked(True)
                else:
                    self.widget_dict[key]['RCheckbox'].setChecked(True)
                    # self.widget_dict[key]['RCheckbox'].setCheckState(main_state)
