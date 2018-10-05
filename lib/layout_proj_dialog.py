# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'layout_proj_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(692, 715)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidgetPage1 = QtWidgets.QWidget()
        self.tabWidgetPage1.setObjectName("tabWidgetPage1")
        self.gridLayout = QtWidgets.QGridLayout(self.tabWidgetPage1)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton_ProjFolderPath = QtWidgets.QPushButton(self.tabWidgetPage1)
        self.pushButton_ProjFolderPath.setObjectName("pushButton_ProjFolderPath")
        self.gridLayout.addWidget(self.pushButton_ProjFolderPath, 3, 2, 1, 1)
        self.lineEdit_ProjName = QtWidgets.QLineEdit(self.tabWidgetPage1)
        self.lineEdit_ProjName.setObjectName("lineEdit_ProjName")
        self.gridLayout.addWidget(self.lineEdit_ProjName, 0, 2, 1, 1)
        self.label = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.comboBox_ProjParent = QtWidgets.QComboBox(self.tabWidgetPage1)
        self.comboBox_ProjParent.setObjectName("comboBox_ProjParent")
        self.gridLayout.addWidget(self.comboBox_ProjParent, 1, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.tabWidgetPage1)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.textEdit_ProjDesc = QtWidgets.QTextEdit(self.tabWidgetPage1)
        self.textEdit_ProjDesc.setObjectName("textEdit_ProjDesc")
        self.gridLayout.addWidget(self.textEdit_ProjDesc, 2, 2, 1, 1)
        self.tabWidget.addTab(self.tabWidgetPage1, "")
        self.tabWidgetPage2 = QtWidgets.QWidget()
        self.tabWidgetPage2.setObjectName("tabWidgetPage2")
        self.tabWidget.addTab(self.tabWidgetPage2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_SaveClose = QtWidgets.QPushButton(Form)
        self.pushButton_SaveClose.setObjectName("pushButton_SaveClose")
        self.horizontalLayout.addWidget(self.pushButton_SaveClose)
        self.pushButton_Close = QtWidgets.QPushButton(Form)
        self.pushButton_Close.setObjectName("pushButton_Close")
        self.horizontalLayout.addWidget(self.pushButton_Close)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton_ProjFolderPath.setText(_translate("Form", "PushButton"))
        self.label.setText(_translate("Form", "Project Name"))
        self.label_2.setText(_translate("Form", "Parent"))
        self.label_4.setText(_translate("Form", "Folder Path"))
        self.label_3.setText(_translate("Form", "Description"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage1), _translate("Form", "General"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabWidgetPage2), _translate("Form", "Advanced"))
        self.pushButton_SaveClose.setText(_translate("Form", "Save and Close"))
        self.pushButton_Close.setText(_translate("Form", "Close"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
