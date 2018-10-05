import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from layout_proj_dialog import Ui_Form
import sqlite3, os
import pandas as pd
import numpy as np
from datetime import date
import aux_functions as aux

class ProjectDialog(Ui_Form):

	#def __init__(self, dialog):
	def __init__(self, parent, doc_id):
		#super(ProjectDialog, self).__init__(parent)
		Ui_Form.__init__(self)
		self.setupUi(parent)

		self.lineEdit_ProjName.setText(str(doc_id))
