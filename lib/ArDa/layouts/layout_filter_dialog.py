# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_filter_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(532, 411)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.comboBox_Field = QtWidgets.QComboBox(Dialog)
        self.comboBox_Field.setObjectName("comboBox_Field")
        self.comboBox_Field.addItem("")
        self.comboBox_Field.addItem("")
        self.comboBox_Field.addItem("")
        self.verticalLayout.addWidget(self.comboBox_Field)
        self.lineEdit_Search = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_Search.setObjectName("lineEdit_Search")
        self.verticalLayout.addWidget(self.lineEdit_Search)
        self.listView_FilterVals = QtWidgets.QListView(Dialog)
        self.listView_FilterVals.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listView_FilterVals.setObjectName("listView_FilterVals")
        self.verticalLayout.addWidget(self.listView_FilterVals)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Bib Entry Filter"))
        self.comboBox_Field.setItemText(0, _translate("Dialog", "Author"))
        self.comboBox_Field.setItemText(1, _translate("Dialog", "Journal"))
        self.comboBox_Field.setItemText(2, _translate("Dialog", "Keyword"))
        self.lineEdit_Search.setPlaceholderText(_translate("Dialog", "Search Filter"))

