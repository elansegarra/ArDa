# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_compare_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(738, 724)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(Dialog)
        self.plainTextEdit.setMaximumSize(QtCore.QSize(16777215, 75))
        self.plainTextEdit.setAcceptDrops(False)
        self.plainTextEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.plainTextEdit.setReadOnly(True)
        self.plainTextEdit.setBackgroundVisible(False)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.scrollArea = QtWidgets.QScrollArea(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 700, 541))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.label_RightTitle = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_RightTitle.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_RightTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.label_RightTitle.setObjectName("label_RightTitle")
        self.gridLayout.addWidget(self.label_RightTitle, 0, 4, 1, 1)
        self.label_LeftTitle = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_LeftTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.label_LeftTitle.setObjectName("label_LeftTitle")
        self.gridLayout.addWidget(self.label_LeftTitle, 0, 1, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.checkBox.setText("")
        self.checkBox.setObjectName("checkBox")
        self.buttonGroup_2 = QtWidgets.QButtonGroup(Dialog)
        self.buttonGroup_2.setObjectName("buttonGroup_2")
        self.buttonGroup_2.addButton(self.checkBox)
        self.gridLayout.addWidget(self.checkBox, 1, 2, 1, 1)
        self.label_Field = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Field.setObjectName("label_Field")
        self.gridLayout.addWidget(self.label_Field, 1, 0, 1, 1)
        self.lineEdit_Left = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_Left.setObjectName("lineEdit_Left")
        self.gridLayout.addWidget(self.lineEdit_Left, 1, 1, 1, 1)
        self.checkBox_2 = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.checkBox_2.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.checkBox_2.setText("")
        self.checkBox_2.setObjectName("checkBox_2")
        self.buttonGroup_2.addButton(self.checkBox_2)
        self.gridLayout.addWidget(self.checkBox_2, 1, 3, 1, 1)
        self.lineEdit_Right = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_Right.setObjectName("lineEdit_Right")
        self.gridLayout.addWidget(self.lineEdit_Right, 1, 4, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
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
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.plainTextEdit.setPlainText(_translate("Dialog", "Something something (directions)"))
        self.label_RightTitle.setText(_translate("Dialog", "TextLabel"))
        self.label_LeftTitle.setText(_translate("Dialog", "TextLabel"))
        self.label_Field.setText(_translate("Dialog", "TextLabel"))

