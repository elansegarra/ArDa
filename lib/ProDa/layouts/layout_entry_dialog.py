# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_entry_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(968, 578)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_Title = QtWidgets.QLabel(Dialog)
        self.label_Title.setObjectName("label_Title")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_Title)
        self.lineEdit_Title = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_Title.setObjectName("lineEdit_Title")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit_Title)
        self.label_ID = QtWidgets.QLabel(Dialog)
        self.label_ID.setObjectName("label_ID")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_ID)
        self.lineEdit_ID = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_ID.setObjectName("lineEdit_ID")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_ID)
        self.label_Date = QtWidgets.QLabel(Dialog)
        self.label_Date.setObjectName("label_Date")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_Date)
        self.dateEdit_Date = QtWidgets.QDateEdit(Dialog)
        self.dateEdit_Date.setCurrentSection(QtWidgets.QDateTimeEdit.MonthSection)
        self.dateEdit_Date.setCalendarPopup(True)
        self.dateEdit_Date.setObjectName("dateEdit_Date")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.dateEdit_Date)
        self.label_Project = QtWidgets.QLabel(Dialog)
        self.label_Project.setObjectName("label_Project")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_Project)
        self.pushButton_Project = QtWidgets.QPushButton(Dialog)
        self.pushButton_Project.setIconSize(QtCore.QSize(32, 32))
        self.pushButton_Project.setFlat(True)
        self.pushButton_Project.setObjectName("pushButton_Project")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.pushButton_Project)
        self.label_Parent = QtWidgets.QLabel(Dialog)
        self.label_Parent.setObjectName("label_Parent")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_Parent)
        self.pushButton_Parent = QtWidgets.QPushButton(Dialog)
        self.pushButton_Parent.setFlat(True)
        self.pushButton_Parent.setObjectName("pushButton_Parent")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.pushButton_Parent)
        self.label_Completed = QtWidgets.QLabel(Dialog)
        self.label_Completed.setObjectName("label_Completed")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_Completed)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.checkBox_Completed = QtWidgets.QCheckBox(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_Completed.sizePolicy().hasHeightForWidth())
        self.checkBox_Completed.setSizePolicy(sizePolicy)
        self.checkBox_Completed.setText("")
        self.checkBox_Completed.setObjectName("checkBox_Completed")
        self.horizontalLayout_2.addWidget(self.checkBox_Completed)
        self.dateEdit_Completed = QtWidgets.QDateEdit(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.dateEdit_Completed.sizePolicy().hasHeightForWidth())
        self.dateEdit_Completed.setSizePolicy(sizePolicy)
        self.dateEdit_Completed.setCalendarPopup(True)
        self.dateEdit_Completed.setObjectName("dateEdit_Completed")
        self.horizontalLayout_2.addWidget(self.dateEdit_Completed)
        self.formLayout.setLayout(5, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.formLayout)
        self.label_Description = QtWidgets.QLabel(Dialog)
        self.label_Description.setObjectName("label_Description")
        self.verticalLayout.addWidget(self.label_Description)
        self.plainTextEdit_Description = QtWidgets.QPlainTextEdit(Dialog)
        self.plainTextEdit_Description.setObjectName("plainTextEdit_Description")
        self.verticalLayout.addWidget(self.plainTextEdit_Description)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_Save = QtWidgets.QPushButton(Dialog)
        self.pushButton_Save.setObjectName("pushButton_Save")
        self.horizontalLayout.addWidget(self.pushButton_Save)
        self.pushButton_Cancel = QtWidgets.QPushButton(Dialog)
        self.pushButton_Cancel.setObjectName("pushButton_Cancel")
        self.horizontalLayout.addWidget(self.pushButton_Cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_Title.setText(_translate("Dialog", "Title:"))
        self.label_ID.setText(_translate("Dialog", "ID"))
        self.label_Date.setText(_translate("Dialog", "Due Date:"))
        self.label_Project.setText(_translate("Dialog", "Project:"))
        self.pushButton_Project.setText(_translate("Dialog", "PROJECT NAME"))
        self.label_Parent.setText(_translate("Dialog", "Parent Task:"))
        self.pushButton_Parent.setText(_translate("Dialog", "PARENT TASK"))
        self.label_Completed.setText(_translate("Dialog", "Completed:"))
        self.label_Description.setText(_translate("Dialog", "Description:"))
        self.pushButton_Save.setText(_translate("Dialog", "Save"))
        self.pushButton_Cancel.setText(_translate("Dialog", "Cancel"))

