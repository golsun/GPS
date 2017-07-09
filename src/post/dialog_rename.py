import sys
import os
import cantera as ct
import json
import time
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from src.gui.def_dialog import *

class dialog_rename(common):


	""" >>>>>>>>>-------------------------
	0.0.0. dialog_database_mixture
		   called by: dialog_database

	"""

	# this class is inherited from helper, rather than base_dialog
	# because most methods in base_dialog is not used here





	def set_table_sp(self):
		model = QStandardItemModel()
		n_row = 0

		for sp in self.parent.project['rename'].keys():
			Qitem_sp = QStandardItem(sp)
			Qitem_sp.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

			Qitem_new = QStandardItem(self.parent.project['rename'][sp])
			Qitem_new.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

			model.setItem(n_row,0, Qitem_sp)
			model.setItem(n_row,1, Qitem_new)
			n_row += 1

		self.w.table_rename.setModel(model)
		for i_row in range(n_row):
			self.w.table_rename.setRowHeight(i_row,20)




	# acts ============================

	def act_cell(self):
		j = self.w.table_rename.currentIndex().row()
		if j>=0:
			sp = str(self.w.table_rename.model().item(j,0).text())
			index = self.sp_list.index(sp)
			self.w.cb_sp.setCurrentIndex(index)
			self.w.txt_new.setText(str(self.parent.project['rename'][sp]))


	def act_del_sp(self):
		j = self.w.table_rename.currentIndex().row()
		if j>=0:
			sp = str(self.w.table_rename.model().item(j,0).text())			
			del self.parent.project['rename'][sp]
			self.set_table_sp()


	def act_add_sp(self):
		sp = str(self.w.cb_sp.currentText())
		if sp in self.sp_list:
			new = self.w.txt_new.text()
			if bool(new):
				self.parent.project['rename'][sp] = str(str(new))
				self.set_table_sp()

	def act_show_comp(self):
		sp = str(self.w.cb_sp.currentText())
		s_comp = ''
		if sp in self.sp_list:
			comp = self.parent.soln['detailed'].species(sp).composition
			for e in self.e_list:
				n = 0
				if e in comp.keys():
					n = comp[e]
				if e.lower() in comp.keys():
					n = comp[e.lower()]
				if n>0:
					if int(n)==n:
						s_comp+=e+str(int(n))
					else:
						s_comp+=e+str(n)

		self.w.txt_comp.setText(s_comp)




	# init ============================

	def __init__(self, parent):

		ui_name = 'rename.ui'
		self.parent = parent
		if 'rename' not in self.parent.project.keys():
			self.parent.project['rename'] = dict()


		element_names = self.parent.soln['detailed'].element_names
		self.e_list = ['C','H','O']
		for e in element_names:
			e = e.upper()
			if e not in self.e_list:
				self.e_list.append(e)

		# load ui and set connection ====================

		self.w = uic.loadUi(os.path.join(self.parent.dir_ui, ui_name))	
		self.w.setFixedSize(self.w.width(), self.w.height())	
		self.w.btn_add_sp.clicked.connect(self.act_add_sp)
		self.w.btn_del_sp.clicked.connect(self.act_del_sp)
		self.w.table_rename.clicked.connect(self.act_cell)
		self.w.btn_ok.clicked.connect(self.act_cancel)
		self.w.cb_sp.currentIndexChanged.connect(self.act_show_comp)


		# set initial values =============================

		self.sp_list = self.parent.soln['detailed'].species_names
		for sp in self.sp_list:
			self.w.cb_sp.addItem(sp)


		self.set_table_sp()
		self.w.table_rename.setColumnWidth(0, 190)
		self.w.table_rename.setColumnWidth(1, 100)


		# exec and return =============================

		self.w.exec_()

	""" 
	end of 0.0.0. dialog_database_mixture
	--------------------------<<<<<<<<<<< """



