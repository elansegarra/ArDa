# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_settings_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1164, 680)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidgetPage1 = QtWidgets.QWidget()
        self.tabWidgetPage1.setObjectName("tabWidgetPage1")
        self.gridLayout = QtWidgets.QGridLayout(self.tabWidgetPage1)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtWidgets.QGroupBox(self.tabWidgetPage1)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.gridLayout_2.addWidget(self.label_6, 0, 0, 1, 1)
        self.comboBox_BackupsFreq = QtWidgets.QComboBox(self.groupBox)
        self.comboBox_BackupsFreq.setObjectName("comboBox_BackupsFreq")
        self.comboBox_BackupsFreq.addItem("")
        self.comboBox_BackupsFreq.addItem("")
        self.comboBox_BackupsFreq.addItem("")
        self.comboBox_BackupsFreq.addItem("")
        self.gridLayout_2.addWidget(self.comboBox_BackupsFreq, 1, 3, 1, 1)
        self.spinBox_BackupsNumber = QtWidgets.QSpinBox(self.groupBox)
        self.spinBox_BackupsNumber.setMaximum(10)
        self.spinBox_BackupsNumber.setProperty("value", 3)
        self.spinBox_BackupsNumber.setObjectName("spinBox_BackupsNumber")
        self.gridLayout_2.addWidget(self.spinBox_BackupsNumber, 0, 3, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setObjectName("label_7")
        self.gridLayout_2.addWidget(self.label_7, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 4, 1, 1)
        self.gridLayout.addWidget(self.groupBox, 4, 0, 1, 2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 5, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.lineEdit_DBPath = QtWidgets.QLineEdit(self.tabWidgetPage1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_DBPath.sizePolicy().hasHeightForWidth())
        self.lineEdit_DBPath.setSizePolicy(sizePolicy)
        self.lineEdit_DBPath.setReadOnly(True)
        self.lineEdit_DBPath.setClearButtonEnabled(False)
        self.lineEdit_DBPath.setObjectName("lineEdit_DBPath")
        self.horizontalLayout_3.addWidget(self.lineEdit_DBPath)
        self.pushButton_DBPath = QtWidgets.QPushButton(self.tabWidgetPage1)
        self.pushButton_DBPath.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_DBPath.sizePolicy().hasHeightForWidth())
        self.pushButton_DBPath.setSizePolicy(sizePolicy)
        self.pushButton_DBPath.setMaximumSize(QtCore.QSize(35, 33))
        self.pushButton_DBPath.setBaseSize(QtCore.QSize(0, 0))
        self.pushButton_DBPath.setObjectName("pushButton_DBPath")
        self.horizontalLayout_3.addWidget(self.pushButton_DBPath)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 1, 1, 1)
        self.groupBox_5 = QtWidgets.QGroupBox(self.tabWidgetPage1)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.groupBox_5)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.comboBox_FileFoundAction = QtWidgets.QComboBox(self.groupBox_5)
        self.comboBox_FileFoundAction.setObjectName("comboBox_FileFoundAction")
        self.comboBox_FileFoundAction.addItem("")
        self.comboBox_FileFoundAction.addItem("")
        self.comboBox_FileFoundAction.addItem("")
        self.comboBox_FileFoundAction.addItem("")
        self.gridLayout_6.addWidget(self.comboBox_FileFoundAction, 2, 2, 1, 1)
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.pushButton_AddWatchFolder = QtWidgets.QPushButton(self.groupBox_5)
        self.pushButton_AddWatchFolder.setObjectName("pushButton_AddWatchFolder")
        self.gridLayout_5.addWidget(self.pushButton_AddWatchFolder, 2, 0, 1, 1)
        self.label_8 = QtWidgets.QLabel(self.groupBox_5)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label_8.setFont(font)
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        self.gridLayout_5.addWidget(self.label_8, 0, 0, 1, 2)
        self.pushButton_RemoveWatchFolder = QtWidgets.QPushButton(self.groupBox_5)
        self.pushButton_RemoveWatchFolder.setEnabled(False)
        self.pushButton_RemoveWatchFolder.setObjectName("pushButton_RemoveWatchFolder")
        self.gridLayout_5.addWidget(self.pushButton_RemoveWatchFolder, 2, 1, 1, 1)
        self.listWidget_WatchedFolders = QtWidgets.QListWidget(self.groupBox_5)
        self.listWidget_WatchedFolders.setObjectName("listWidget_WatchedFolders")
        self.gridLayout_5.addWidget(self.listWidget_WatchedFolders, 1, 0, 1, 2)
        self.gridLayout_6.addLayout(self.gridLayout_5, 0, 0, 4, 1)
        self.checkBox_CheckWatchStartup = QtWidgets.QCheckBox(self.groupBox_5)
        self.checkBox_CheckWatchStartup.setObjectName("checkBox_CheckWatchStartup")
        self.gridLayout_6.addWidget(self.checkBox_CheckWatchStartup, 0, 2, 1, 2)
        self.label_9 = QtWidgets.QLabel(self.groupBox_5)
        self.label_9.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_9.setObjectName("label_9")
        self.gridLayout_6.addWidget(self.label_9, 1, 2, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_6.addItem(spacerItem2, 3, 2, 1, 1)
        self.gridLayout_6.setColumnStretch(0, 1)
        self.gridLayout.addWidget(self.groupBox_5, 1, 0, 1, 2)
        self.tabWidget.addTab(self.tabWidgetPage1, "")
        self.tabWidgetPage2 = QtWidgets.QWidget()
        self.tabWidgetPage2.setObjectName("tabWidgetPage2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.tabWidgetPage2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox_3 = QtWidgets.QGroupBox(self.tabWidgetPage2)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.listWidget_HiddenCols = QtWidgets.QListWidget(self.groupBox_3)
        self.listWidget_HiddenCols.setAcceptDrops(True)
        self.listWidget_HiddenCols.setDragEnabled(True)
        self.listWidget_HiddenCols.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.listWidget_HiddenCols.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget_HiddenCols.setObjectName("listWidget_HiddenCols")
        self.verticalLayout_2.addWidget(self.listWidget_HiddenCols)
        self.horizontalLayout_2.addWidget(self.groupBox_3)
        self.label_4 = QtWidgets.QLabel(self.tabWidgetPage2)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tabWidgetPage2)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.listWidget_VisibleCols = QtWidgets.QListWidget(self.groupBox_4)
        self.listWidget_VisibleCols.setAcceptDrops(True)
        self.listWidget_VisibleCols.setDragEnabled(True)
        self.listWidget_VisibleCols.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.listWidget_VisibleCols.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget_VisibleCols.setObjectName("listWidget_VisibleCols")
        self.verticalLayout_3.addWidget(self.listWidget_VisibleCols)
        self.horizontalLayout_2.addWidget(self.groupBox_4)
        self.tabWidget.addTab(self.tabWidgetPage2, "")
        self.tabWidgetPage3 = QtWidgets.QWidget()
        self.tabWidgetPage3.setObjectName("tabWidgetPage3")
        self.checkBox_Cascade = QtWidgets.QCheckBox(self.tabWidgetPage3)
        self.checkBox_Cascade.setGeometry(QtCore.QRect(40, 60, 271, 29))
        self.checkBox_Cascade.setObjectName("checkBox_Cascade")
        self.tabWidget.addTab(self.tabWidgetPage3, "")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.listWidget_CustomFilters = QtWidgets.QListWidget(self.tab)
        self.listWidget_CustomFilters.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.listWidget_CustomFilters.setDragEnabled(False)
        self.listWidget_CustomFilters.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.listWidget_CustomFilters.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget_CustomFilters.setObjectName("listWidget_CustomFilters")
        self.horizontalLayout_6.addWidget(self.listWidget_CustomFilters)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.pushButton_AddFilter = QtWidgets.QPushButton(self.tab)
        self.pushButton_AddFilter.setObjectName("pushButton_AddFilter")
        self.verticalLayout_5.addWidget(self.pushButton_AddFilter)
        self.pushButton_DeleteFilter = QtWidgets.QPushButton(self.tab)
        self.pushButton_DeleteFilter.setEnabled(False)
        self.pushButton_DeleteFilter.setObjectName("pushButton_DeleteFilter")
        self.verticalLayout_5.addWidget(self.pushButton_DeleteFilter)
        self.pushButton_MoveFilterUp = QtWidgets.QPushButton(self.tab)
        self.pushButton_MoveFilterUp.setEnabled(False)
        self.pushButton_MoveFilterUp.setObjectName("pushButton_MoveFilterUp")
        self.verticalLayout_5.addWidget(self.pushButton_MoveFilterUp)
        self.pushButton_MoveFilterDown = QtWidgets.QPushButton(self.tab)
        self.pushButton_MoveFilterDown.setEnabled(False)
        self.pushButton_MoveFilterDown.setObjectName("pushButton_MoveFilterDown")
        self.verticalLayout_5.addWidget(self.pushButton_MoveFilterDown)
        self.horizontalLayout_6.addLayout(self.verticalLayout_5)
        self.verticalLayout_4.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_10 = QtWidgets.QLabel(self.tab)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_5.addWidget(self.label_10)
        self.lineEdit_FilterNameField = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_FilterNameField.setEnabled(False)
        self.lineEdit_FilterNameField.setObjectName("lineEdit_FilterNameField")
        self.horizontalLayout_5.addWidget(self.lineEdit_FilterNameField)
        self.verticalLayout_4.addLayout(self.horizontalLayout_5)
        self.label_2 = QtWidgets.QLabel(self.tab)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_4.addWidget(self.label_2)
        self.plainTextEdit_FilterCommand = QtWidgets.QPlainTextEdit(self.tab)
        self.plainTextEdit_FilterCommand.setEnabled(False)
        self.plainTextEdit_FilterCommand.setObjectName("plainTextEdit_FilterCommand")
        self.verticalLayout_4.addWidget(self.plainTextEdit_FilterCommand)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem3)
        self.tabWidget.addTab(self.tab, "")
        self.tabWidgetPage4 = QtWidgets.QWidget()
        self.tabWidgetPage4.setObjectName("tabWidgetPage4")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tabWidgetPage4)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.groupBox_2 = QtWidgets.QGroupBox(self.tabWidgetPage4)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_4.addWidget(self.groupBox_2, 2, 0, 1, 2)
        self.comboBox_BibGenFreq = QtWidgets.QComboBox(self.tabWidgetPage4)
        self.comboBox_BibGenFreq.setObjectName("comboBox_BibGenFreq")
        self.comboBox_BibGenFreq.addItem("")
        self.comboBox_BibGenFreq.addItem("")
        self.comboBox_BibGenFreq.addItem("")
        self.gridLayout_4.addWidget(self.comboBox_BibGenFreq, 1, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.tabWidgetPage4)
        self.label_5.setObjectName("label_5")
        self.gridLayout_4.addWidget(self.label_5, 1, 0, 1, 1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.lineEdit_BibPath = QtWidgets.QLineEdit(self.tabWidgetPage4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_BibPath.sizePolicy().hasHeightForWidth())
        self.lineEdit_BibPath.setSizePolicy(sizePolicy)
        self.lineEdit_BibPath.setReadOnly(True)
        self.lineEdit_BibPath.setObjectName("lineEdit_BibPath")
        self.horizontalLayout_4.addWidget(self.lineEdit_BibPath)
        self.pushButton_BibPath = QtWidgets.QPushButton(self.tabWidgetPage4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_BibPath.sizePolicy().hasHeightForWidth())
        self.pushButton_BibPath.setSizePolicy(sizePolicy)
        self.pushButton_BibPath.setMaximumSize(QtCore.QSize(35, 33))
        self.pushButton_BibPath.setBaseSize(QtCore.QSize(0, 0))
        self.pushButton_BibPath.setObjectName("pushButton_BibPath")
        self.horizontalLayout_4.addWidget(self.pushButton_BibPath)
        self.gridLayout_4.addLayout(self.horizontalLayout_4, 0, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.tabWidgetPage4)
        self.label.setObjectName("label")
        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem4, 3, 0, 1, 1)
        self.tabWidget.addTab(self.tabWidgetPage4, "")
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
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "Backups"))
        self.label_6.setText(_translate("Dialog", "Number:"))
        self.comboBox_BackupsFreq.setToolTip(_translate("Dialog", "Frequency with which a new backup is to be created."))
        self.comboBox_BackupsFreq.setItemText(0, _translate("Dialog", "On App Start"))
        self.comboBox_BackupsFreq.setItemText(1, _translate("Dialog", "Daily"))
        self.comboBox_BackupsFreq.setItemText(2, _translate("Dialog", "Weekly"))
        self.comboBox_BackupsFreq.setItemText(3, _translate("Dialog", "Monthly"))
        self.spinBox_BackupsNumber.setToolTip(_translate("Dialog", "Number of backups to be stored at any given time."))
        self.label_7.setText(_translate("Dialog", "Frequency:"))
        self.label_3.setText(_translate("Dialog", "Database File:"))
        self.pushButton_DBPath.setText(_translate("Dialog", "..."))
        self.groupBox_5.setTitle(_translate("Dialog", "Watched Folders"))
        self.comboBox_FileFoundAction.setItemText(0, _translate("Dialog", "Do Nothing"))
        self.comboBox_FileFoundAction.setItemText(1, _translate("Dialog", "Add Empty Bib Entry (with file path)"))
        self.comboBox_FileFoundAction.setItemText(2, _translate("Dialog", "Attempt Meta Recovery (from file only)"))
        self.comboBox_FileFoundAction.setItemText(3, _translate("Dialog", "Attempt Meta Recovery (from file and online)"))
        self.pushButton_AddWatchFolder.setText(_translate("Dialog", "Add Folder"))
        self.label_8.setText(_translate("Dialog", "Folder Paths"))
        self.pushButton_RemoveWatchFolder.setText(_translate("Dialog", "Remove Folder"))
        self.checkBox_CheckWatchStartup.setText(_translate("Dialog", "Check Watched Folders on Startup"))
        self.label_9.setText(_translate("Dialog", "New File Found Action:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage1), _translate("Dialog", "General"))
        self.groupBox_3.setTitle(_translate("Dialog", "Default Hidden"))
        self.label_4.setText(_translate("Dialog", "<- Drag Between ->"))
        self.groupBox_4.setTitle(_translate("Dialog", "Default Visible"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage2), _translate("Dialog", "Fields"))
        self.checkBox_Cascade.setText(_translate("Dialog", "Cascading Membership"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage3), _translate("Dialog", "Projects"))
        self.pushButton_AddFilter.setText(_translate("Dialog", "Add Filter"))
        self.pushButton_DeleteFilter.setText(_translate("Dialog", "Delete Filter"))
        self.pushButton_MoveFilterUp.setText(_translate("Dialog", "Move Up"))
        self.pushButton_MoveFilterDown.setText(_translate("Dialog", "Move Down"))
        self.label_10.setText(_translate("Dialog", "Filter Name:"))
        self.label_2.setText(_translate("Dialog", "Filter Command:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Dialog", "Filters"))
        self.groupBox_2.setTitle(_translate("Dialog", "Included Fields (Default)"))
        self.comboBox_BibGenFreq.setItemText(0, _translate("Dialog", "Only Manually"))
        self.comboBox_BibGenFreq.setItemText(1, _translate("Dialog", "On App Start"))
        self.comboBox_BibGenFreq.setItemText(2, _translate("Dialog", "Every Bib Entry Edit"))
        self.label_5.setText(_translate("Dialog", "Generation Frequency:"))
        self.pushButton_BibPath.setText(_translate("Dialog", "..."))
        self.label.setText(_translate("Dialog", "General Bib File Location:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage4), _translate("Dialog", "Bib Files"))
        self.pushButton_SaveClose.setText(_translate("Dialog", "Save and Close"))
        self.pushButton_Close.setText(_translate("Dialog", "Close"))

