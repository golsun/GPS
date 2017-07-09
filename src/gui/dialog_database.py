import sys
import os
import cantera as ct
import json
import time
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from src.core.def_tools import keys_sorted

from def_dialog import base_dialog
from dialog_database_mixture import dialog_database_mixture


class dialog_database(base_dialog):

	""" >>>>>>>>>>>>>------------------------------------------------
	0.0. dialog_database
	     called by: window_main
	"""



	# acts ==============================

	def act_add_fuel(self):
		self.act_add('fuel')


	def act_edit_fuel(self):
		self.act_edit('fuel')


	def act_del_fuel(self):
		self.act_del('fuel')


	def act_add_oxid(self):
		self.act_add('oxid')


	def act_edit_oxid(self):
		self.act_edit('oxid')


	def act_del_oxid(self):
		self.act_del('oxid')


	def act_reactor(self):
		reactor = self.w.cb_reactor.currentText()
		if reactor[0:3] == 'DNS':
			self.w.txt_case.setEnabled(True)
			self.w_txts['empty'][-1] = False
		else:
			self.w.txt_case.setEnabled(False)
			self.w_txts['empty'][-1] = True

			if reactor[0:3] == 'aut': 
				if not bool(self.w.txt_T0.text()):
					self.data['T0'] = [1000, 1200, 1500, 1800]
					self.set_txt()
			elif reactor[0:3] == 'PSR': 
				if not bool(self.w.txt_T0.text()):
					self.data['T0'] = [500]
					self.set_txt()




	# inits ==============================

	def init_data_default(self):
		self.data = dict()
		self.data['fuel'] = []	
		self.data['oxid'] = []	
		self.data['reactor'] = ''
		self.data['phi'] = [0.5, 1, 1.5]
		self.data['T0'] = []
		self.data['atm'] = [1, 5, 30]
		self.data['train'] = True
		self.data['test'] = True
		self.data['name'] = self.new_name('database', self.occupied)
		self.data['case'] = []



	def init(self):

		self.ui_name = 'database.ui'
		self.key = 'database'
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connections ==============================

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)

		self.w.btn_add_fuel.clicked.connect(self.act_add_fuel)
		self.w.btn_del_fuel.clicked.connect(self.act_del_fuel)
		self.w.btn_edit_fuel.clicked.connect(self.act_edit_fuel)
		self.w.list_fuel.doubleClicked.connect(self.act_edit_fuel)

		self.w.btn_add_oxid.clicked.connect(self.act_add_oxid)
		self.w.btn_del_oxid.clicked.connect(self.act_del_oxid)
		self.w.btn_edit_oxid.clicked.connect(self.act_edit_oxid)
		self.w.list_oxid.doubleClicked.connect(self.act_edit_oxid)

		self.w.cb_reactor.currentIndexChanged.connect(self.act_reactor)

		# set variables ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_phi, self.w.txt_atm, self.w.txt_T0, self.w.txt_case]
		self.w_txts['key'] = ['phi', 'atm', 'T0', 'case']
		self.w_txts['name'] = ['equivalence ratio', 'pressure', 'initial temperature','case name']		
		self.w_txts['vali'] = [self.is_pos_float] * 3 + [self.is_any]
		self.w_txts['empty'] = [False] * 3 + [True]
		self.w_txts['len'] = [None] * 3 + [1]

		self.sub = dict()
		self.sub['obj'] = [self.w.list_fuel, self.w.list_oxid]
		self.sub['key'] = ['fuel','oxid']
		self.sub['name'] = ['fuel','oxidizer']
		self.sub['dialog'] = [dialog_database_mixture] * 2
		self.sub['viewer'] = [self.set_list] * 2
		self.sub['reader'] = [self.read_list] * 2
		self.sub['single'] = [False] * 2

		self.w_lists = self.sub

		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_reactor]
		self.w_cbs['key'] = ['reactor']
		self.w_cbs['name'] = ['reactor']
		self.w_cbs['items'] = [self.parent.reactor_list]

		# set ui obj ==============================

		self.set_name()
		self.set_txt()
		self.set_list()
		self.set_cb()

		# exec ==============================

		self.readers = [self.read_name, self.read_cb, self.read_list, self.read_txt]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None













