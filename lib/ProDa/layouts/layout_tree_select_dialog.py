# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_tree_select_dialog.ui'
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
        self.label_Directions = QtWidgets.QLabel(Dialog)
        self.label_Directions.setObjectName("label_Directions")
        self.verticalLayout.addWidget(self.label_Directions)
        self.lineEdit_Search = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_Search.setObjectName("lineEdit_Search")
        self.verticalLayout.addWidget(self.lineEdit_Search)
        self.treeWidget_Items = QtWidgets.QTreeWidget(Dialog)
        self.treeWidget_Items.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeWidget_Items.setHeaderHidden(True)
        self.treeWidget_Items.setObjectName("treeWidget_Items")
        self.treeWidget_Items.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget_Items)
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
        self.label_Directions.setText(_translate("Dialog", "Select the project(s)"))
        self.lineEdit_Search.setPlaceholderText(_translate("Dialog", "Search Filter"))

