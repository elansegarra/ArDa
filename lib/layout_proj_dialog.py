# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_proj_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(587, 418)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidgetPage1 = QtWidgets.QWidget()
        self.tabWidgetPage1.setObjectName("tabWidgetPage1")
        self.gridLayout = QtWidgets.QGridLayout(self.tabWidgetPage1)
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.lineEdit_ProjName = QtWidgets.QLineEdit(self.tabWidgetPage1)
        self.lineEdit_ProjName.setObjectName("lineEdit_ProjName")
        self.gridLayout.addWidget(self.lineEdit_ProjName, 0, 2, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit_ProjPath = QtWidgets.QLineEdit(self.tabWidgetPage1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_ProjPath.sizePolicy().hasHeightForWidth())
        self.lineEdit_ProjPath.setSizePolicy(sizePolicy)
        self.lineEdit_ProjPath.setReadOnly(True)
        self.lineEdit_ProjPath.setObjectName("lineEdit_ProjPath")
        self.horizontalLayout_2.addWidget(self.lineEdit_ProjPath)
        self.pushButton_ProjFolderPath = QtWidgets.QPushButton(self.tabWidgetPage1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_ProjFolderPath.sizePolicy().hasHeightForWidth())
        self.pushButton_ProjFolderPath.setSizePolicy(sizePolicy)
        self.pushButton_ProjFolderPath.setMaximumSize(QtCore.QSize(35, 33))
        self.pushButton_ProjFolderPath.setBaseSize(QtCore.QSize(0, 0))
        self.pushButton_ProjFolderPath.setObjectName("pushButton_ProjFolderPath")
        self.horizontalLayout_2.addWidget(self.pushButton_ProjFolderPath)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.comboBox_ProjParent = QtWidgets.QComboBox(self.tabWidgetPage1)
        self.comboBox_ProjParent.setObjectName("comboBox_ProjParent")
        self.gridLayout.addWidget(self.comboBox_ProjParent, 1, 2, 1, 1)
        self.textEdit_ProjDesc = QtWidgets.QTextEdit(self.tabWidgetPage1)
        self.textEdit_ProjDesc.setObjectName("textEdit_ProjDesc")
        self.gridLayout.addWidget(self.textEdit_ProjDesc, 2, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)
        self.label_BibFileBuiltDate = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_BibFileBuiltDate.setObjectName("label_BibFileBuiltDate")
        self.gridLayout.addWidget(self.label_BibFileBuiltDate, 4, 2, 1, 1)
        self.tabWidget.addTab(self.tabWidgetPage1, "")
        self.tabWidgetPage2 = QtWidgets.QWidget()
        self.tabWidgetPage2.setObjectName("tabWidgetPage2")
        self.tabWidget.addTab(self.tabWidgetPage2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_SaveClose = QtWidgets.QPushButton(Dialog)
        self.pushButton_SaveClose.setObjectName("pushButton_SaveClose")
        self.horizontalLayout.addWidget(self.pushButton_SaveClose)
        self.pushButton_Close = QtWidgets.QPushButton(Dialog)
        self.pushButton_Close.setObjectName("pushButton_Close")
        self.horizontalLayout.addWidget(self.pushButton_Close)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Project Properties"))
        self.label_3.setText(_translate("Dialog", "Description"))
        self.label_2.setText(_translate("Dialog", "Parent"))
        self.lineEdit_ProjName.setToolTip(_translate("Dialog", "A name for this project (no punctuation)"))
        self.lineEdit_ProjPath.setToolTip(_translate("Dialog", "Folder where other files related to this project are kept."))
        self.pushButton_ProjFolderPath.setText(_translate("Dialog", "..."))
        self.label_4.setText(_translate("Dialog", "Folder Path"))
        self.label.setText(_translate("Dialog", "Project Name"))
        self.label_5.setText(_translate("Dialog", "Bib File Last Built"))
        self.label_BibFileBuiltDate.setText(_translate("Dialog", "TextLabel"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage1), _translate("Dialog", "General"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage2), _translate("Dialog", "Advanced"))
        self.pushButton_SaveClose.setText(_translate("Dialog", "Save and Close"))
        self.pushButton_Close.setText(_translate("Dialog", "Close"))

