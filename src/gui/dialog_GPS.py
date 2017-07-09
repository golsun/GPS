
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
from dialog_GPS_es import dialog_GPS_traced



class dialog_GPS(base_dialog):

	""" >>>>>>>>>>>>>------------------------------------------------
	0.1. dialog_GPS
	     called by: window_main
                                                     
	"""



	# act ==============================

	def act_add_es(self): self.act_add('es')
	def act_edit_es(self): self.act_edit('es')
	def act_add_iso(self): self.act_add('iso')
	def act_edit_iso(self): self.act_edit('iso')

	def act_del_es(self):
		if not self.act_es():
			self.act_del('es')


	def act_del_iso(self):
		if not self.act_iso():
			self.act_del('iso')



	def act_cb(self, key):
		i_cb = self.w_cbs['key'].index(key)
		obj = self.w_cbs['obj'][i_cb]
		btn_del = self.w_cbs['btn_del'][i_cb]
		btn_edit = self.w_cbs['btn_edit'][i_cb]
		name = str(obj.currentText())
		is_default = (name == 'default')
		if is_default:
			btn_edit.setText('view')
			btn_del.setEnabled(False)
		else:
			btn_edit.setText('edit')
			btn_del.setEnabled(True)
		self.parent.app.processEvents()
		return is_default


	def act_es(self): self.act_cb('es')
	def act_iso(self): self.act_cb('iso')


	def act_gb_iso(self):
		self.data['iso_enable'] = self.w.gb_iso.isChecked()


	def act_more(self):
		self.w.setFixedSize(self.w.width(), 346)
		self.w.gb_less.hide()
		self.w.gb_more_data.show()
		self.w.gb_more_btn.show()



	def act_less(self):
		self.w.setFixedSize(self.w.width(), 182)
		self.w.gb_less.show()
		self.w.gb_more_data.hide()
		self.w.gb_more_btn.hide()



	# init ============================

	def init_data_default(self):
		self.data = dict()
		self.data['alpha'] = [0.1, 0.2, 0.5]
		self.data['beta'] = [0.5]
		self.data['gamma'] = [0.5,0.75]
		self.data['K'] = [1]
		self.data['iso_enable'] = False
		self.data['iso'] = 'default'
		self.data['checked'] = True
		self.data['must_keep'] = []
		self.data['name'] = self.new_name('GPS', self.occupied)
		self.data['es'] = 'default'



	def init(self):

		self.ui_name = 'GPS.ui'
		self.key = 'GPS'
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()
		self.sp_list = self.parent.soln['detailed'].species_names

		# set connection ====================

		self.w.btn_save_less.clicked.connect(self.act_save)
		self.w.btn_save_more.clicked.connect(self.act_save)
		self.w.btn_cancel_less.clicked.connect(self.act_cancel)
		self.w.btn_cancel_more.clicked.connect(self.act_cancel)

		self.w.btn_more.clicked.connect(self.act_more)
		self.w.btn_less.clicked.connect(self.act_less)

		self.w.btn_add_es.clicked.connect(self.act_add_es)
		self.w.btn_del_es.clicked.connect(self.act_del_es)
		self.w.btn_edit_es.clicked.connect(self.act_edit_es)

		self.w.btn_add_iso.clicked.connect(self.act_add_iso)
		self.w.btn_del_iso.clicked.connect(self.act_del_iso)
		self.w.btn_edit_iso.clicked.connect(self.act_edit_iso)

		self.w.gb_iso.clicked.connect(self.act_gb_iso)
		self.w.cb_es.currentIndexChanged.connect(self.act_es)
		self.w.cb_iso.currentIndexChanged.connect(self.act_iso)


		# set variables ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_alpha, self.w.txt_beta, self.w.txt_K, self.w.txt_must_keep, self.w.txt_gamma]
		self.w_txts['key'] = ['alpha', 'beta', 'K', 'must_keep', 'gamma']
		self.w_txts['name'] = ['alpha', 'beta', 'K', 'species must keep', 'gamma']	
		self.w_txts['vali'] = [self.is_0to1, self.is_0to1, self.is_pos_int, self.is_sp, self.is_0to1]
		self.w_txts['empty'] = [False] * 3 + [True] + [False]
		self.w_txts['len'] = [None] * len(self.w_txts['obj'])

		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_es]#, self.w.cb_iso]
		self.w_cbs['key'] = ['es']#,'iso']
		self.w_cbs['name'] = ['element setting']#,'isomer detection']
		self.w_cbs['items'] = [self.parent.project['es'].keys()]#, self.parent.project['iso'].keys()]
		self.w_cbs['dialog'] = [dialog_GPS_traced]#, None]
		self.w_cbs['btn_del'] = [self.w.btn_del_es]#, self.w.btn_del_iso]
		self.w_cbs['btn_edit'] = [self.w.btn_edit_es]#, self.w.btn_edit_iso]
		self.w_cbs['viewer'] = [self.set_cb] * 1
		self.w_cbs['reader'] = [self.read_cb] * 1
		self.w_cbs['single'] = [True] * 1

		self.sub = self.w_cbs
	
		# set ui obj ==============================

		self.set_name()
		self.set_txt()
		self.set_cb()
		self.act_es()
		#self.act_iso()
		self.act_less()

		self.w.gb_iso.setChecked(self.data['iso_enable'])

		# exec ==============================

		self.readers = [self.read_name, self.read_txt, self.read_cb]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None

