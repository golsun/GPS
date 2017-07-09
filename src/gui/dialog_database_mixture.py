import sys
import os
import cantera as ct
import json
import time
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from def_dialog import common
from src.core.def_tools import keys_sorted, num2str

class dialog_database_mixture(common):


	""" >>>>>>>>>-------------------------
	0.0.0. dialog_database_mixture
		   called by: dialog_database

	"""

	# this class is inherited from helper, rather than base_dialog
	# because most methods in base_dialog is not used here




	# helper ============================


	def fun_mix_str(self, composition):
		if len(composition.keys()) == 1:
			return composition.keys()[0]

		spid = dict()
		for sp in composition.keys():
			spid[sp] = self.parent.soln['detailed'].species_index(sp)

		sps = keys_sorted(spid)
		txt = ''
		sum_mole = sum(composition.values())
		for sp in sps:
			if composition[sp]>0:
				mole_str = num2str(100.0*composition[sp]/sum_mole, self.parent.n_digit)
				txt += '['+sp+';'+mole_str+']'
		return txt


	# display ============================

	def set_txt_name(self):
		if self.data['name_cust'] == False:
			txt = self.fun_mix_str(self.data['composition'])
			self.w.txt_name.setText(txt)


	def set_table_sp(self):
		model = QStandardItemModel()
		n_row = 0

		for sp in self.data['composition'].keys():
			Qitem_sp = QStandardItem(sp)
			Qitem_sp.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

			Qitem_mole = QStandardItem(str(self.data['composition'][sp]))
			Qitem_mole.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

			model.setItem(n_row,0, Qitem_sp)
			model.setItem(n_row,1, Qitem_mole)
			n_row += 1

		self.w.table_mix.setModel(model)
		for i_row in range(n_row):
			self.w.table_mix.setRowHeight(i_row,20)


	# get ============================

	def read_comp(self):
		if bool(self.data['composition']):
			return True
		else:
			msg = 'this mixture does not contain any species'
			QMessageBox.information(QWidget(),'',msg)
			return False



	# acts ============================

	def act_cell(self):
		j = self.w.table_mix.currentIndex().row()
		if j>=0:
			sp = str(self.w.table_mix.model().item(j,0).text())
			index = self.sp_list.index(sp)
			self.w.cb_sp.setCurrentIndex(index)
			self.w.txt_mole.setText(str(self.data['composition'][sp]))


	def act_del_sp(self):
		j = self.w.table_mix.currentIndex().row()
		if j>=0:
			sp = str(self.w.table_mix.model().item(j,0).text())			
			del self.data['composition'][sp]
			self.set_txt_name()
			self.set_table_sp()


	def act_add_sp(self):
		sp = str(self.w.cb_sp.currentText())
		if sp in self.sp_list:
			try:
				mole_str = str(self.w.txt_mole.text())
				mole = float(mole_str)
			except ValueError:
				msg = 'can not convert ' + mole_str + ' to numbers'
				QMessageBox.information(QWidget(),'',msg)
				return

			self.data['composition'][sp] = mole
			self.set_table_sp()
			self.set_txt_name()


	def act_deft_cust(self):
		if self.w.rbtn_deft.isChecked():
			self.data['name_cust'] = False
			self.w.txt_name.setReadOnly(True)
			self.set_txt_name()
		
		if self.w.rbtn_cust.isChecked():
			self.data['name_cust'] = True
			self.w.txt_name.setReadOnly(False)
			self.w.txt_name.setText(self.data['name'])


	def act_save(self):
		
		if self.read_name() and self.read_comp():
			new_str = self.fun_mix_str(self.data['composition'])
			if self.old_name != None and new_str != self.old_str:	

				msg = 'warning: you modified composition of this mixture\n'+\
					'1. if this mixture is used in previous calculations of the'+\
					'current project, modifications will make data files inconsistent;\n'+\
					'2. modifications will be applied to all database using this mixture'+\
					'\n\ncontinue to save?'
				Qanswer = QMessageBox.question(QWidget(),'',msg, \
						QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

				if Qanswer == QMessageBox.No:
					return None
			
			self.w.accept() 




	# init ============================

	def __init__(self, parent, data_name=None, extra=None):

		ui_name = 'mixture.ui'
		self.parent = parent
		self.old_name = data_name	

		if data_name in self.parent.project['fuel']:
			self.key = 'fuel'
		else:
			self.key = 'oxid'

		self.occupied = self.init_occupied('fuel') + self.init_occupied('oxid')

		# load ui and set connection ====================

		self.w = uic.loadUi(os.path.join(self.parent.dir_ui, ui_name))	
		self.w.setFixedSize(self.w.width(), self.w.height())	
		self.w.btn_add_sp.clicked.connect(self.act_add_sp)
		self.w.btn_del_sp.clicked.connect(self.act_del_sp)
		self.w.table_mix.clicked.connect(self.act_cell)
		self.w.rbtn_deft.clicked.connect(self.act_deft_cust)
		self.w.rbtn_cust.clicked.connect(self.act_deft_cust)
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)


		# set initial values =============================

		if data_name is None:
			self.data = dict()
			self.data['name'] = ''
			self.data['composition'] = dict()
			self.data['name_cust'] = False
		else:
			self.data = copy.copy(self.parent.project[self.key][data_name])
			self.old_str = self.fun_mix_str(self.data['composition'])

		self.sp_list = self.parent.soln['detailed'].species_names
		for sp in self.sp_list:
			self.w.cb_sp.addItem(sp)

		self.set_table_sp()
		self.w.table_mix.setColumnWidth(0, 190)
		self.w.table_mix.setColumnWidth(1, 100)

		if self.data['name_cust']==True:
			self.w.rbtn_cust.setChecked(True)
		else:
			self.w.rbtn_deft.setChecked(True)
		
		self.act_deft_cust()



		# exec and return =============================

		if self.w.exec_() == QDialog.Rejected:
			self.data = None


	""" 
	end of 0.0.0. dialog_database_mixture
	--------------------------<<<<<<<<<<< """



