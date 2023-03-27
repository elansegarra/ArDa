# This file contains my custom extension of the view and model objects
#from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QLabel, QApplication, QAction, QTableView, QInputDialog, QCompleter
from PyQt5.QtGui import QFont, QTextCursor , QPainter, QFontMetrics, QTextDocument
import ArDa.aux_functions as aux
import util.my_functions as myfun
from ArDa.dialog_doc_search import DocSearchDialog
import util.pdf_meta_functions as pmeta

class QTextEditExt(QTextEdit):
	"""
	This extension of QTextEdit includes a number of features:
	 - Context menu with querying, capitalizing, meta extraction
	 - Enter to expand the text box size
	 - editingFinished signal (based off: https://gist.github.com/hahastudio/4345418)
	 - tab completion (based off: https://stackoverflow.com/questions/28956693/pyqt5-qtextedit-auto-completion)
	 """
	editingFinished = pyqtSignal()
	receivedFocus = pyqtSignal()

	def __init__(self, parent, arda_app, queriable = False, enter_resize = False,
					capitalize = False, meta_extract = False):
		QLineEdit.__init__(self)

		# Setting class level variables
		self.arda_app = arda_app
		self.queriable = queriable # Determines whether to include a query context menu choice
		self.enter_resize = enter_resize # Enter resizes the widget
		self.capitalize = capitalize # Whether capitalize action is available
		self.meta_extract = meta_extract # Whether meta extract (from pdf) is available
		# For auto completion
		self.completer = None
		# For editingFinshed signal
		self._changed = False
		self.setTabChangesFocus( True )
		self.textChanged.connect( self._handle_text_changed )

		# Setting a context menu
		self.setContextMenuPolicy(Qt.CustomContextMenu) #Qt.ActionsContextMenu) #2
		self.customContextMenuRequested.connect(self.openContextMenu)

	def setCompleter(self, completer):
		if self.completer:
			self.disconnect(self.completer, 0, self, 0)
		if not completer:
			return

		completer.setWidget(self)
		self.completer = completer
		self.completer.insertText.connect(self.insertCompletion)

	def insertCompletion(self, completion):
		tc = self.textCursor()
		if (self.completer.filterMode() == QtCore.Qt.MatchContains):
			# Delete line and insert the completion
			tc.select(QTextCursor.LineUnderCursor)
			tc.removeSelectedText()
			tc.insertText(completion)
		else:  # Just add the remainder of the completion
			extra = (len(completion) - len(self.completer.completionPrefix()))
			tc.movePosition(QTextCursor.Left)
			tc.movePosition(QTextCursor.EndOfWord)
			tc.insertText(completion[-extra:])
		self.setTextCursor(tc)

	def _handle_text_changed(self):
		self._changed = True

	def setTextChanged(self, state=True):
		self._changed = state

	def setHtml(self, html):
		QtGui.QTextEdit.setHtml(self, html)
		self._changed = False

	def textUnderCursor(self):
		tc = self.textCursor()
		# tc.select(QTextCursor.WordUnderCursor)
		tc.select(QTextCursor.LineUnderCursor)
		return tc.selectedText()

	def focusInEvent(self, event):
		# For completer
		if self.completer:
			self.completer.setWidget(self);
		# For emitting editingFinished event
		self.receivedFocus.emit()
		# Passing on the event to anything else
		QTextEdit.focusInEvent(self, event)

	def focusOutEvent(self, event):
		# Emit editingFinished if it was changed
		if self._changed:
			self.editingFinished.emit()
		# Pass on the event to anything else
		QTextEdit.focusOutEvent(self, event)
		# super(QTextEditExt, self).focusOutEvent( event )

	def keyPressEvent(self, event):
		if self.completer and self.completer.popup() and self.completer.popup().isVisible():
			if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return,
								QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab,
								QtCore.Qt.Key_Backtab):
				event.ignore()
				return # let the completer handle these events

		# Checking for enter pressed (and if resize was toggled to on)
		if (event.key() == Qt.Key_Return) and (self.enter_resize):
			self.setFixedHeight(int(self.document().size().height())+10)
			print("Return was pressed, resizing text box.")

		# Checking if Ctrl-e has been pressed (for inline completion)
		inline = (event.modifiers() == QtCore.Qt.ControlModifier and \
				  event.key() == QtCore.Qt.Key_E)
		if inline:
			# set completion mode as inline
			self.completer.setCompletionMode(QCompleter.InlineCompletion)
			completionPrefix = self.textUnderCursor()
			if (completionPrefix != self.completer.completionPrefix()):
				self.completer.setCompletionPrefix(completionPrefix)
			self.completer.complete()
			# set the current suggestion in the text box
			self.completer.insertText.emit(self.completer.currentCompletion())
			# reset the completion mode
			self.completer.setCompletionMode(QCompleter.PopupCompletion)
			return

		# Checking if Ctrl-Space has been pressed (or if there is no completer)
		# isShortcut = (event.modifiers() == QtCore.Qt.ControlModifier and\
		# 				event.key() == QtCore.Qt.Key_Space)

		# If there is no completer set, then simply exit after processing key
		QTextEdit.keyPressEvent(self, event)
		if (not self.completer): #or (not isShortcut):
			return

		# Checking if Ctrl or Shift on their own
		ctrlOrShift = event.modifiers() in (QtCore.Qt.ControlModifier, QtCore.Qt.ShiftModifier)
		if ctrlOrShift and event.text()== '':
			return

		completionPrefix = self.textUnderCursor()
		if completionPrefix=="": #not isShortcut:
			if self.completer.popup():
				self.completer.popup().hide()
				return

		# Updating the prefix
		if (completionPrefix != self.completer.completionPrefix()):
			self.completer.setCompletionPrefix(completionPrefix)
			popup = self.completer.popup()
			popup.setCurrentIndex(self.completer.completionModel().index(0,0))

		# Getting width for completer and popping it up
		cr = self.cursorRect()
		cr.setWidth(self.completer.popup().sizeHintForColumn(0)
			+ self.completer.popup().verticalScrollBar().sizeHint().width())
		self.completer.complete(cr) ## popup it up!

	def openContextMenu(self, position):
		menu = self.createStandardContextMenu()

		if self.capitalize:	# Adding camel case action
			action_capitalize = QAction("Capitalize")
			menu.addAction(action_capitalize)

		if self.meta_extract: # Adding an option to extract meta from pdf
			action_meta_extract = QAction("Extract from File(s)")
			menu.addAction(action_meta_extract)

		if self.queriable: # Adding cross ref search
			action_crossref = QAction("Search Crossref")
			menu.addAction(action_crossref)

		# Executing the menu
		action = menu.exec_(self.mapToGlobal(position))
		# Checking the action
		if self.capitalize and (action == action_capitalize):
			self.setText(myfun.title_except(self.toPlainText()))
			self.editingFinished.emit()
		elif self.queriable and (action == action_crossref):
			self.d_diag = DocSearchDialog(self.arda_app, search_value = self.toPlainText())
			result = self.d_diag.exec_()
			if result:
				print("Doc Query accepted and merged")
				# Extracting the field that this widget is associated with (commenting out for now)
				# ind = self.arda_app.field_df[self.arda_app.field_df.meta_widget == self].index
				# if len(ind) == 1:
				# 	self.field_name = self.arda_app.field_df.at[ind[0], 'field']
				# else:
				# 	warnings.warn(f"The widget created does not seem to relate to a regular field.")
				# 	self.field_name = None
				# Reloading the meta data (this fixes the issue of rewriting over
				#	the title because after the context menu closes it issues a field changed event)
				self.arda_app.loadMetaData([self.arda_app.c_diag.doc_id_dict['doc_id']])
			else:
				print("Doc Query Canceled")
		elif self.meta_extract and (action == action_meta_extract):
			# First we gather all the file paths associated
			file_paths = [path.toolTip() for path in self.arda_app.meta_file_paths if path.toolTip() != ""]
			# Then we extract some potential titles from each path
			choice_items = []
			for path in file_paths:
				file_values = pmeta.extract_title_from_file(path,
									best_x_candidates = 3, search_x_pages = 2,
				                    length_min = 10)
				# Check if extraction was unsuccessful
				if file_values == None: continue
				# If successful then add extraction to choices
				choice_items = choice_items + file_values
			# Now we specifiy the settings on the input dialog
			msg = "Choose among the extracted potential titles:"
			input_diag = QInputDialog(self)
			input_diag.setLabelText(msg)
			input_diag.setFixedSize(1000, 400)
			input_diag.setWindowTitle("Title Extraction")
			input_diag.setOptions(QInputDialog.UseListViewForComboBoxItems)
			input_diag.setComboBoxItems(choice_items)
			# Check the input dialog response
			if input_diag.exec_() == QInputDialog.Accepted:
				print(f'"{input_diag.textValue()}" was selected.')
				# Set the choice to the current value and emit a text changed event
				self.setText(input_diag.textValue())
				self.editingFinished.emit()
				# Adjusting the height of the object
				self.setFixedHeight(int(self.document().size().height())+5)

class MyDictionaryCompleter(QCompleter):
# class Variables
	insertText = QtCore.pyqtSignal(str)

	def __init__(self, myKeywords=None,parent=None):
		if myKeywords is None:
			myKeywords =['apple', 'banana', 'cat']
		QCompleter.__init__(self, myKeywords, parent)
		self.activated.connect(self.changeCompletion)

	def changeCompletion(self, completion):
		# Not sure what this if clause is for...
		if completion.find("(") != -1:
			completion = completion[:completion.find("(")]
		print(completion)
		self.insertText.emit(completion)

class QLabelElided(QLabel):
	def __init__(self, parent=None):
		QLabel.__init__(self, parent)

	def paintEvent( self, event ):
		painter = QPainter(self)

		# Grabbing HTML text (just what is visible)
		doc = QTextDocument()
		doc.setHtml(self.text())
		vis_text = doc.toPlainText()

		# Making text elided
		metrics = QFontMetrics(self.font())
		elided  = metrics.elidedText(vis_text, Qt.ElideRight, self.width())

		painter.drawText(self.rect(), self.alignment(), elided)
