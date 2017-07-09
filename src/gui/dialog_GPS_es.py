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
from def_tools_gui import *
from src.core.def_tools import keys_sorted, num2str


class dialog_GPS_element(object):


	""" >>>>>>>>>-------------------------
	0.1.0.0. dialog_GPS_element
		   called by: dialog_GPS_traced

	"""

	
	# display ============================

	def set_all(self):

		self.w.gb_cust.setEnabled(self.element['cust'])
		if (not self.element['only_hub']) and self.element['cust']:
			self.w.gb_gp.setEnabled(True)
		else:
			self.w.gb_gp.setEnabled(False)

		if self.element['cust']:
			self.w.rbtn_cust.setChecked(True)
		else:
			self.w.rbtn_def.setChecked(True)

		self.w.ck_hub_only.setChecked(self.element['only_hub'])
		self.w.txt_source.setText(', '.join(self.element['source']))
		self.w.txt_target.setText(', '.join(self.element['target']))

	# get ============================

	def read_txt_st(self):
		txt_list = [self.w.txt_source, self.w.txt_target]
		key_list = ['source', 'target']
		para_list = key_list
		soln = self.parent.soln['detailed']
		species = soln.species_names
		alias_fuel = self.parent.alias_fuel
		e = self.element['name']

		for i_txt in range(len(txt_list)):
			txt = txt_list[i_txt]
			key = key_list[i_txt]
			para = para_list[i_txt]
			ss = txt.text().split(',')
			nn = []

			if len(ss):
				for Qs in ss:
					s = str(Qs).strip()
					if bool(s):

						if s == alias_fuel:
							if key == 'source':
								nn.append(s)
								continue
							else:
								msg = 'fuel components can only be source'
								QMessageBox.information(QWidget(),'',msg)
								return False

						if s in species:
							atoms = soln.species(s).composition
							if e in atoms.keys():
								nn.append(s)
							else:
								msg = 'error in '+ para +' inputs\n' + \
									'species "'+s+'" does not contain element "'+\
									e + '"\n\n'
								QMessageBox.information(QWidget(),'',msg)
								return False

						else:
							msg = 'error in '+ para +' inputs\nno species named "'+s+'" \n\n'
							QMessageBox.information(QWidget(),'',msg)
							return False

			if self.element['only_hub'] == False and bool(nn) == False:
				msg = 'no value provided for '+para
				QMessageBox.information(QWidget(),'',msg)
				return False
			
			self.element[key] = nn

		return True


	# acts ============================

	def act_def_or_cust(self):
		self.element['cust'] = self.w.rbtn_cust.isChecked()

		if self.element['cust'] == False:
			e_setting_def = self.parent.e_setting_def
			if self.element['name'] in e_setting_def.keys():
				copy_name = self.element['name']
			else:
				copy_name = '!other!'

			self.element['only_hub'] = e_setting_def[copy_name]['only_hub']
			self.element['source'] = copy.copy(e_setting_def[copy_name]['source'])
			self.element['target'] = copy.copy(e_setting_def[copy_name]['target'])

		else:
			self.element['only_hub'] = self.only_hub_old
			self.element['source'] = self.source_old
			self.element['target'] = self.target_old

		self.set_all()


	def act_hub_only(self):
		self.element['only_hub'] = self.w.ck_hub_only.isChecked()

		if self.element['only_hub']:
			self.element['source'] = []
			self.element['target'] = []
		else:
			self.element['source'] = self.source_old
			self.element['target'] = self.target_old

		self.set_all()


	def act_save(self):
		if self.read_txt_st():
			self.w.accept() 

	def act_cancel(self):
		self.w.reject()


	# init ============================

	def __init__(self, parent, element, title):

		ui_name = 'GPS_element.ui'
		self.element = copy.copy(element)
		self.parent = parent

		# load ui and set connection ====================

		self.w = uic.loadUi(os.path.join(self.parent.dir_ui, ui_name))	
		self.w.setFixedSize(self.w.width(), self.w.height())	
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.rbtn_def.clicked.connect(self.act_def_or_cust)
		self.w.rbtn_cust.clicked.connect(self.act_def_or_cust)
		self.w.ck_hub_only.clicked.connect(self.act_hub_only)


		# set initial values =============================

		self.only_hub_old = self.element['only_hub']
		self.source_old = copy.copy(self.element['source'])
		self.target_old = copy.copy(self.element['target'])

		self.w.txt_title.setText(title)
		self.set_all()

		# exec and return =============================

		if self.w.exec_() == QDialog.Rejected:
			self.element = None

















class dialog_GPS_traced(common):

	""" >>>>>>>>>-------------------------
	0.1.0. dialog_GPS_traced
		   called by: dialog_GPS

	"""


	# display ============================

	def set_table_traced(self):
		model = QStandardItemModel()

		n_row = 0
		for e in self.data['element'].keys():

			# colume 0: name of the element
			Qitem = QStandardItem(e)
			Qitem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
			if self.data['element'][e]['traced']:
				Qitem.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
			else:			
				Qitem.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
			model.setItem(n_row,0, Qitem)

			# colume 1: settings
			if self.data['element'][e]['only_hub']:
				Qitem = QStandardItem('hubs')
			else:
				s = ','.join(self.data['element'][e]['source'])
				t = ','.join(self.data['element'][e]['target'])
				Qitem = QStandardItem(s + ' --> hubs --> ' + t)
			Qitem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable )
			model.setItem(n_row,1, Qitem)

			n_row += 1

		self.w.table_traced.setModel(model)
		self.w.table_traced.setColumnWidth(0, 70)
		self.w.table_traced.setColumnWidth(1, 180)

		for i_row in range(n_row):
			self.w.table_traced.setRowHeight(i_row,20)



	# get ============================


	def read_traced(self):
		model = self.w.table_traced.model()
		traced_any = False
		for j in range(model.rowCount()):
			e = str(model.item(j).text())
			if model.item(j,0).checkState():
				self.data['element'][e]['traced'] = True
				traced_any = True
			else:
				self.data['element'][e]['traced'] = False

		if traced_any:
			return True
		else:
			msg = 'no traced element selected'
			QMessageBox.information(QWidget(),'',msg)
			return False



	# acts ============================

	def act_edit(self):
		j = self.w.table_traced.currentIndex().row()
		if j>=0:
			e = str(self.w.table_traced.model().item(j,0).text())
			element_old = self.data['element'][e]
			title = e+' in setting '+self.w.txt_name.text()
			element_new = dialog_GPS_element(self.parent, element_old, title).element
			if element_new is not None:
				self.data['element'][e] = element_new
				self.set_table_traced()



	def act_save(self):
		if self.read_name() and self.read_traced():

			if self.old_name != None:
				msg = 'warning: if you modified this setting, then\n'+\
					'1. if this setting is used in previous calculations of the'+\
					'current project, modifications will make data files inconsistent;\n'+\
					'2. modifications will be applied to all GPS using this element setting'+\
					'\n\ncontinue to save?'

				Qanswer = QMessageBox.question(QWidget(),'',msg, \
					QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

				if Qanswer == QMessageBox.No:
					return None

			self.w.accept() 



	def act_cancel(self):
		self.w.reject()



	def __init__(self, parent, data_name=None, extra=None):
		ui_name = 'GPS_traced.ui'
		self.parent = parent
		self.key = 'es'
		soln = self.parent.soln['detailed']
		self.old_name = data_name

		self.occupied = self.init_occupied()

		self.w = uic.loadUi(os.path.join(self.parent.dir_ui, ui_name))	
		self.w.setFixedSize(self.w.width(), self.w.height())	
		self.w.btn_edit.clicked.connect(self.act_edit)
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.table_traced.doubleClicked.connect(self.act_edit)

		if data_name is None:
			self.data = copy.copy(self.parent.project['es']['default'])
			self.data['name'] = self.new_name('customized', self.occupied)
		else:
			self.data = copy.copy(self.parent.project['es'][data_name])

		if data_name == 'default':
			self.w.btn_save.setEnabled(False)

		self.w.txt_name.setText(self.data['name'])
		self.set_table_traced()

		if self.w.exec_() == QDialog.Rejected:
			self.data = None


