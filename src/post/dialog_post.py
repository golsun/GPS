
import sys
import os
import cantera as ct
import json
import time
import copy
import matplotlib.pyplot as plt

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from src.core.def_tools import keys_sorted

from src.gui.def_dialog import *
from src.gui.dialog_mech import dialog_mech

from dialog_subplot import *
from def_painter import *


from def_plt_tools import *
















""" >>>>>>>>>>>>>------------------------------------------------

dP                oo dP       dP                   
88                   88       88                   
88d888b. dP    dP dP 88 .d888b88 .d8888b. 88d888b. 
88'  `88 88    88 88 88 88'  `88 88ooood8 88'  `88 
88.  .88 88.  .88 88 88 88.  .88 88.  ... 88       
88Y8888' `88888P' dP dP `88888P8 `88888P' dP       
                                                   
                                                 
"""



class dialog_plot_builder(base_dialog):


	def set_enable(self, pop_msg=True):
		db = self.data['db']
		db_ok = (db is not None) and (db['db_name'] in self.parent.project['database'].keys())

		if db_ok:
			self.w.txt_db.setText(db['db_name'])
		else:
			self.w.txt_db.setText('')

		self.w.gb_x.setEnabled(db_ok)
		self.w.gb_subplot.setEnabled(db_ok)
		self.w.gb_2nd.setEnabled(db_ok)
		self.w.gb_subplot.setEnabled(db_ok)
		self.w.gb_mech.setEnabled(db_ok)
		self.w.btn_db.setDefault(not db_ok)

		# set items -------------------------

		if db_ok:
			items_varying = []
			if self.data['db']['T0'] == 'varying':
				items_varying.append('Initial temperature (K)')
			if self.data['db']['atm'] == 'varying':
				items_varying.append('Pressure (atm)')
			if self.data['db']['fuel'] == 'varying':
				for fuel_name in self.parent.project['database'][db['db_name']]['fuel']:
					fuel = self.parent.project['fuel'][fuel_name]
					for sp in fuel['composition'].keys():
						item = 'Initial ' + sp + ' concnetration (%) in fuel'
						if item not in items_varying:
							items_varying.append(item)

			# set the x-axis options

			if ('ign_evolve' in self.key):
				self.w_cbs['items'][0] = ['Time (s)', 'Time (ms)', 'Temperature (K)','Normalized time']
				self.w_cbs['items'][1] = copy.copy(items_varying)


			elif ('premix_evolve' in self.key):
				self.w_cbs['items'][0] = ['Distance (cm)', 'Temperature (K)']
				self.w_cbs['items'][1] = copy.copy(items_varying)

			elif ('psr_state' in self.key):
				self.w_cbs['items'][0] = ['Residence time (s)']
				self.w_cbs['items'][1] = copy.copy(items_varying)


			elif ('ign_state' in self.key):
				self.w_cbs['items'][0] = copy.copy(items_varying)
				self.w_cbs['items'][1] = copy.copy(items_varying)
		
		else:
			self.w_cbs['items'][0] = ['']
			self.w_cbs['items'][1] = ['']

		self.set_cb()





	# ====================
	# act

	def act_plot(self):
		for reader in self.readers:
			if reader() == False:
				return None

		self.w.btn_plot.setText('plotting...')
		self.parent.app.processEvents()

		plt.rc('font', **{'family':'Times New Roman'})
		subplots = self.data[self.subkey]
		n_sub = len(subplots)
		W = self.data['fig_w'][0]
		H = self.data['sub_h'][0] * n_sub
		f, axarr = plt.subplots(n_sub, 1, sharex='all', figsize=(W,H))

		i_sub = 0
		for subplot_name in subplots:
			subplot = self.parent.project[self.subkey][subplot_name]
			tp = subplot['type']
			index = self.subplot['type'].index(tp)
			painter = self.subplot['painter'][index]
			if n_sub>1:
				ax = axarr[i_sub]
			else:
				ax = axarr
			
			painter_OK = painter(parent=self.parent, fig_opt=self.data, sub_opt=subplot, ax=ax, tp=tp)
			if not painter_OK:				
				self.w.btn_plot.setText('plot')
				self.parent.app.processEvents()
				return False
			i_sub += 1


		if n_sub>1:
			ax = axarr[-1]
		else:
			ax = axarr

		xlim = self.data['xlim']
		xtick = self.data['xtick']
		if bool(xlim):
			ax.set_xlim(xlim)
		else:
			xlim = opt_lim(ax, 'x', self.data['xscale'])
			ax.set_xlim(xlim)


		if bool(xtick):
			ax.set_xticks(xtick)

		xlabel = self.data['xtype'].replace('(','[').replace(')',']')
		if 'initial t' in xlabel.lower():
			xlabel = r'$T_0$'+' [K]'
		if 'Pressure [atm]' == xlabel:
			xlabel = r'$P$' + ' [atm]'
		xlabel = xlabel.replace('Time',r'$t$')
		ax.set_xlabel(xlabel)


		dir_plot = os.path.join(self.parent.project['dir_public'], 'plot')
		if not os.path.exists(dir_plot):
			os.makedirs(dir_plot)

		path_save = os.path.join(dir_plot,self.data['name']+'.pdf')
		#plt.subplots_adjust(bottom=0.15)
		#plt.subplots_adjust(left=0.25)
		plt.tight_layout()
		plt.subplots_adjust(hspace=0)
		plt.savefig(path_save)#, format='eps', dpi=1000, bbox_inches='tight')

		self.w.btn_plot.setText('plot')
		self.parent.app.processEvents()

		dir_public = self.parent.project['dir_public']
		msg = 'figure saved to \n\n' + path_save.replace(dir_public,'[working dir/]')
		QMessageBox.information(QWidget(),'',msg)
		self.act_save()




	def act_up(self):
		self.read_list(pop_msg=False)
		obj = self.w.list_subplot
		subplot_name = self.read_item(obj)
		subs = self.data[self.subkey]

		if subplot_name == subs[0]:
			return None

		if subplot_name not in subs:
			return None

		index = self.data[self.subkey].index(subplot_name)
		subs[index-1], subs[index] = subs[index], subs[index - 1]
		self.set_list()



	def act_down(self):
		self.read_list(pop_msg=False)
		obj = self.w.list_subplot
		subplot_name = self.read_item(obj)
		subs = self.data[self.subkey]

		if subplot_name == subs[-1]:
			return None

		if subplot_name not in subs:
			return None

		index = self.data[self.subkey].index(subplot_name)
		subs[index+1], subs[index] = subs[index], subs[index + 1]
		self.set_list()





	def act_db(self):
		db = dialog_plot_db(parent=self.parent, extra=self.data).data
		if db !=None:
			self.data['db'] = db
			self.set_enable()


	def act_add_subplot(self):
		name = str(self.w.cb_subplot.currentText())
		index = self.subplot['name'].index(name)
		dialog = self.subplot['dialog'][index]
		self.data['current_subplot'] = name

		self.sub['dialog'][1] = dialog
		self.act_add(self.subkey)


	def act_edit_subplot(self):
		subplot_name = self.read_item(self.w.list_subplot)
		subplot = self.parent.project[self.subkey][subplot_name]
		index = self.subplot['type'].index(subplot['type'])
		dialog = self.subplot['dialog'][index]

		self.sub['dialog'][1] = dialog
		self.act_edit(self.subkey)


	def act_copy_subplot(self):
		obj = self.w.list_subplot
		data_name = self.read_item(obj)

		if data_name == None:
			return None

		key = self.subkey
		occupied = self.init_occupied(key=key)
		print 'plot_builder: occupied = '+str(occupied)

		copy_name, ok = QInputDialog.getText(QWidget(), '', 
			'Name the copy of ' + data_name + ' as:',text=data_name)
		copy_name = str(copy_name)
  
		if ok:
			if self.read_name(name0=copy_name, save=False, occupied0=occupied):
				data_copied = copy.copy(self.parent.project[key][data_name])
				data_copied['name'] = copy_name
				self.parent.project[key][copy_name] = data_copied
				self.set_list()




	def act_del_subplot(self): self.act_del(self.subkey)
	def act_add_mech(self): self.act_add('mech')
	def act_edit_mech(self): self.act_edit('mech')
	def act_del_mech(self): self.act_del('mech')


	# ====================
	# init

	def init_data_default(self):
		self.data = dict()
		self.data['name'] = self.new_name(self.key, self.occupied)
		self.data['db'] = None
		self.data['xtype'] = ''
		#self.data['scale'] = 'linear'
		self.data['2nd_var'] = ''
		self.data['xlim'] = []
		self.data['xtick'] = []
		self.data['xscale'] = 'linear'
		self.data['mech'] = ['detailed']
		self.data['fig_w'] = [5.6]
		self.data['sub_h'] = [2.2]
		self.data['subkey'] = self.subkey
		self.data[self.subkey] = []



	def init(self):

		self.sort_list = False

		self.subplot = dict()

		if self.key == 'plot_ign_evolve':
			self.subplot['name'] 	= ['T-t relation', 'heat release', 'species concentration', 'global pathway','node analysis','radical rop']
			self.subplot['dialog'] 	= [dialog_plot_single, dialog_plot_single, dialog_plot_sp, dialog_plot_GP, dialog_plot_node, dialog_plot_Rrop]
			self.subplot['type'] 	= ['T', 'Qdot', 'sp', 'GP','node','Rrop']

		elif self.key == 'plot_ign_state':
			self.subplot['name'] 	= ['ignition delay', 'species concentration']
			self.subplot['dialog'] 	= [dialog_plot_single, dialog_plot_sp]
			self.subplot['type'] 	= ['tau-ign', 'sp']
			self.subplot['painter'] = [painter] * len(self.subplot['name'])

		elif self.key == 'plot_psr_state':
			self.subplot['name'] 	= ['PSR temperature', 'species concentration', 'global pathway','node analysis','radical rop']
			self.subplot['dialog'] 	= [dialog_plot_single, dialog_plot_sp, dialog_plot_GP, dialog_plot_node, dialog_plot_Rrop]
			self.subplot['type'] 	= ['psr-T', 'sp', 'GP','node','Rrop']

		elif self.key == 'plot_premix_evolve':
			self.subplot['name'] 	= ['T-x relation', 'species concentration', 'global pathway','reactions of GP','node analysis']
			self.subplot['dialog'] 	= [dialog_plot_single, dialog_plot_sp, dialog_plot_GP, dialog_plot_GPrxn, dialog_plot_node]
			self.subplot['type'] 	= ['T', 'sp', 'GP','GPrxn','node']

		
		self.subplot['painter'] = [painter] * len(self.subplot['name'])

		for index in range(len(self.subplot['type'])):
			self.subplot['type'][index] = 'sub' + self.key + '_' + self.subplot['type'][index]


		self.subkey = 'sub'+self.key
		if self.subkey not in self.parent.project.keys():
			self.parent.project[self.subkey] = dict()


		#  ====================

		self.ui_name = 'plot_builder.ui'
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()



		# set connection ====================

		self.w.btn_add_mech.clicked.connect(self.act_add_mech)
		self.w.btn_del_mech.clicked.connect(self.act_del_mech)
		self.w.btn_edit_mech.clicked.connect(self.act_edit_mech)
		self.w.list_mech.doubleClicked.connect(self.act_edit_mech)

		self.w.btn_add_subplot.clicked.connect(self.act_add_subplot)
		self.w.btn_del_subplot.clicked.connect(self.act_del_subplot)
		self.w.btn_copy_subplot.clicked.connect(self.act_copy_subplot)
		self.w.btn_edit_subplot.clicked.connect(self.act_edit_subplot)
		self.w.list_subplot.doubleClicked.connect(self.act_edit_subplot)

		self.w.btn_up.clicked.connect(self.act_up)
		self.w.btn_down.clicked.connect(self.act_down)

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.btn_plot.clicked.connect(self.act_plot)
		self.w.btn_db.clicked.connect(self.act_db)

		# set obj IO ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_xlim, self.w.txt_xtick, self.w.txt_fig_w, self.w.txt_sub_h]
		self.w_txts['key'] = ['xlim', 'xtick', 'fig_w', 'sub_h']
		self.w_txts['name'] = ['limits', 'ticks', 'figure width', 'figure height (per sub)']	
		self.w_txts['vali'] = [self.is_float]*2 + [self.is_float] * 2
		self.w_txts['empty'] = [True, True, False, False]
		self.w_txts['len'] = [2, None, 1, 1]


		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_xtype, self.w.cb_2nd_var, self.w.cb_xscale]
		self.w_cbs['key'] = ['xtype','2nd_var', 'xscale', 'cmap']
		self.w_cbs['name'] = ['horizontal axis type','secondary variable','horizontal axis scale']
		self.w_cbs['items'] = [[],[],['linear','log']]
		self.w_cbs['empty'] = [False, True, False]



		self.w_lists = dict()
		self.w_lists['obj'] = [self.w.list_mech, self.w.list_subplot]
		self.w_lists['key'] = ['mech',self.subkey]
		self.w_lists['name'] = ['mech','subplots']

		self.sub = self.w_lists
		self.sub['dialog'] = [dialog_mech, None]
		self.sub['viewer'] = [self.set_list] * 2
		self.sub['reader'] = [self.read_list] * 2
		self.sub['single'] = [False] * 2

		# set ui obj ==============================

		for item in self.subplot['name']:
			self.w.cb_subplot.addItem(item)

		self.set_name()
		self.set_txt()
		self.set_cb()
		self.set_list()
		self.set_enable()


		# exec ==============================

		self.readers = [self.read_name, self.read_txt, \
			self.read_cb, self.read_list]

		if self.w.exec_() == QDialog.Rejected:
			self.data = None





























class dialog_plot_GPedge(base_dialog):

	"""




	 .88888.   888888ba                              dP                   
	d8'   `88  88    `8b                             88                   
	88        a88aaaa8P'              .d8888b. .d888b88 .d8888b. .d8888b. 
	88   YP88  88                     88ooood8 88'  `88 88'  `88 88ooood8 
	Y8.   .88  88                     88.  ... 88.  .88 88.  .88 88.  ... 
	 `88888'   dP                     `88888P' `88888P8 `8888P88 `88888P' 
	                     oooooooooooo                        .88          
	                                                     d8888P           


	"""


	def set_enable(self, pop_msg=True):
		db = self.data['db']
		db_ok = (db is not None) and (db['db_name'] in self.parent.project['database'].keys())
		if db_ok:
			self.w.txt_db.setText(self.data['db']['db_name'])
			self.w_cbs['items'][0] = [str(phi) for phi in self.parent.project['database'][db['db_name']]['phi']	]
			self.set_cb(which=[0])		
		else:
			self.w.txt_db.setText('')

		self.w.gb_core.setEnabled(db_ok)
		self.w.btn_db.setDefault(not db_ok)



	def set_GPs(self):
		print 'set_GPs triggered'
		traced = str(self.w.cb_traced.currentText())
		if bool(traced):
			items = []
			for GP_name in self.parent.project['GP_'+traced].keys():
				items.append(self.parent.project['GP_'+traced][GP_name]['alias'])
			self.w_cbs['items'][2] = sorted(items)
		else:
			self.w_cbs['items'][2] = []
		self.set_cb(which=[2])



	# ====================
	# act

	def act_plot(self):
		for reader in self.readers:
			if reader() == False:
				return None

		self.w.btn_plot.setText('plotting...')
		self.parent.app.processEvents()


		dir_desk = self.parent.project['mech']['detailed']['desk']
		dir_raw = cond2dir(dir_desk, self.data['db']['fuel'], self.data['db']['oxid'], \
				float(self.data['phi']), float(self.data['db']['atm']), float(self.data['db']['T0']),\
				self.data['db']['reactor'], self.parent.n_digit)

		path_raw = os.path.join(dir_raw,'raw.npz')
		raw = load_raw(path_raw)

		GPs = self.parent.project['GP_'+self.data['traced']]
		GP_dir = None
		GP_alias = self.data['GP_alias']
		for GP_name in GPs.keys():
			if GPs[GP_name]['alias'] == GP_alias:
				GP_dir = GPs[GP_name]
				break

		if GP_dir is None:
			msg = 'cannot find GP whose alias is '+str(GP_alias)
			QMessageBox.information(QWidget(),'',msg)
			self.w.btn_plot.setText('plot')
			self.parent.app.processEvents()
			return False


		GP_dir = self.parent.project['GP_'+self.data['traced']][GP_name]
		dir_plot = os.path.join(self.parent.project['dir_public'], 'plot')
		if not os.path.exists(dir_plot):
			os.makedirs(dir_plot)
		path_save = os.path.join(dir_plot,self.data['name']+'.pdf')

		soln = self.parent.soln['detailed']
		rename = self.parent.project['rename']


		if self.data['method'] == 'concentration':
			ok = plot_GPedge_mf(soln, GP_dir, self.data, raw, path_save, rename)
		else:
		
			GPSA_data = load_GPSA(dir_raw, GP_dir, self.data['method'])
			if GPSA_data is None:
				msg = 'could not find GPSA data for: \n\n'+GP_name+'\n\nin:\n\n'+str(dir_raw)+\
						'\n\ntry to run GPSA first'
				QMessageBox.information(QWidget(),'',msg)			
				self.w.btn_plot.setText('plot')
				self.parent.app.processEvents()
				return False

			ok = plot_GPedge(soln, GPSA_data, self.data, raw, path_save, rename)

		self.w.btn_plot.setText('plot')
		self.parent.app.processEvents()
		
		if ok:
			dir_public = self.parent.project['dir_public']
			msg = 'figure saved to \n\n' + path_save.replace(dir_public,'[working dir/]')
			QMessageBox.information(QWidget(),'',msg)
			self.act_save()








	def act_db(self):
		db = dialog_plot_db(parent=self.parent, extra=self.data).data
		if db !=None:
			self.data['db'] = db
			self.set_enable()




	# ====================
	# init

	def init_data_default(self):
		self.data = dict()
		self.data['name'] = self.new_name(self.key, self.occupied)
		self.data['db'] = None
		self.data['fig_w'] = [7.0]
		self.data['fig_h'] = [10.0]
		self.data['n_rxn'] = [2]
		self.data['sample_loc'] = [400]
		self.data['sample_by'] = 'T rised (K)'
		self.data['xscale'] = 'log'
		self.data['xlim'] =  []
		self.data['phi'] = ''
		self.data['traced'] = ''
		self.data['GP_alias'] = ''
		self.data['GP_name'] = ''
		self.data['subkey'] = self.subkey
		self.data['method'] = 'R_ij'



	def init(self):

		self.key = 'plot_GPedge'
		self.subkey = 'sub'+self.key

		#  ====================

		self.ui_name = 'plot_Dij.ui'
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connection ====================

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.btn_plot.clicked.connect(self.act_plot)
		self.w.btn_db.clicked.connect(self.act_db)
		self.w.cb_traced.currentIndexChanged.connect(self.set_GPs)

		# set obj IO ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_fig_w, self.w.txt_fig_h, self.w.txt_n_rxn, self.w.txt_sample, self.w.txt_xlim]
		self.w_txts['key'] = ['fig_w', 'fig_h', 'n_rxn', 'sample_loc', 'xlim']
		self.w_txts['name'] = ['figure width', 'figure height', 'max reaction #', 'sampling location', 'axis limits']	
		self.w_txts['vali'] = [self.is_float] * 2 + [self.is_pos_float] * 2 + [self.is_float]
		self.w_txts['empty'] = [False, False, False, False, True]
		self.w_txts['len'] = [1, 1, 1, 1, 2]

		soln = self.parent.soln['detailed']

		print
		print 'soln.element_names = '+str(soln.element_names)
		print

		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_phi, self.w.cb_traced, self.w.cb_GP, self.w.cb_xscale, self.w.cb_method, self.w.cb_sample]
		self.w_cbs['key'] = ['phi', 'traced','GP_alias','xscale','method','sample_by']
		self.w_cbs['name'] = ['equiv. ratio', 'traced','global pathway','axis scale','method','sampling by']
		self.w_cbs['items'] = [
			[], 
			soln.element_names, [], 
			['log','linear'], 
			['R_ij','a_iji','concentration'], 
			['T (K)', 'T rised (K)','t passed (s)','norm t passed']
			]

		self.w_cbs['empty'] = [False] * len(self.w_cbs['obj'])

		# set ui obj ==============================

		self.set_name()
		self.set_txt()
		self.set_cb()
		self.set_enable()


		# exec ==============================

		self.readers = [self.read_name, self.read_txt, self.read_cb]

		if self.w.exec_() == QDialog.Rejected:
			self.data = None
















































































class dialog_post(common):

	""" >>>>>>>>>>>>>------------------------------------------------
	1. dialog_post
	     called by: window_main
                                                     
	"""

	# set ==============================

	
	def set_list(self, key):

		obj = self.w.list_plot
		model = QStandardItemModel()

		if key not in self.parent.project.keys():
			self.parent.project[key] = dict()

		for item_name in sorted(self.parent.project[key].keys()):
			item = self.parent.project[key][item_name]
			Qitem = QStandardItem(item_name)
			Qitem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
			model.appendRow(Qitem)

		obj.setModel(model)
		self.parent.app.processEvents()


	# act ==============================

	def act_add(self, key):

		if key == 'plot_GPedge':
			dialog = dialog_plot_GPedge
		else:
			dialog = dialog_plot_builder

		data = dialog(parent=self.parent, data_name=None, key=key).data
		if data is not None:
			self.parent.project[key][data['name']] = data
			self.set_list(key=key)


	def act_del(self, key):
		obj = self.w.list_plot
		data_name = self.read_item(obj)
		if data_name == None:
			return None

		msg = 'are you sure to delete "'+data_name+'""?\n\n'+\
			'(you can uncheck it if you only donnot want to use it right now)'
		Qanswer = QMessageBox.question(QWidget(),'',msg, \
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

		if Qanswer == QMessageBox.Yes:
			del self.parent.project[key][data_name]
			self.set_list(key=key)




	def act_edit(self, key):
		obj = self.w.list_plot
		data_name = self.read_item(obj)
		if data_name == None:
			return None


		if key == 'plot_GPedge':
			dialog = dialog_plot_GPedge
		else:
			dialog = dialog_plot_builder

		data = dialog(parent=self.parent, data_name=data_name, key=key).data	
		if data is not None:
			del self.parent.project[key][data_name]
			self.parent.project[key][data['name']] = data
			self.set_list(key=key)



	def act_copy(self, key):
		obj = self.w.list_plot
		data_name = self.read_item(obj)

		if data_name == None:
			return None

		occupied = self.init_occupied(key=key)

		copy_name, ok = QInputDialog.getText(QWidget(), '', 
			'Name the copy of ' + data_name + ' as:',text=data_name)
		copy_name = str(copy_name)
  
		if ok:
			if self.read_name(name0=copy_name, save=False, occupied0=occupied):
				data_copied = copy.copy(self.parent.project[key][data_name])
				data_copied['name'] = copy_name
				self.parent.project[key][copy_name] = data_copied
				self.set_list(key=key)



	def act_add_plot(self):
		plot = str(self.w.cb_plot.currentText())
		index = self.cb_items.index(plot)
		self.act_add(self.plot_type[index])


	def act_edit_plot(self):
		plot = str(self.w.cb_plot.currentText())
		index = self.cb_items.index(plot)
		self.act_edit(self.plot_type[index])


	def act_del_plot(self):
		plot = str(self.w.cb_plot.currentText())
		index = self.cb_items.index(plot)
		self.act_del(self.plot_type[index])


	def act_copy_plot(self): 
		plot = str(self.w.cb_plot.currentText())
		index = self.cb_items.index(plot)
		self.act_copy(self.plot_type[index])


	def act_cb(self):
		plot = str(self.w.cb_plot.currentText())
		index = self.cb_items.index(plot)
		self.set_list(self.plot_type[index])


	def act_ok(self):
		self.w.accept()


	# init ============================



	def __init__(self, parent):

		self.ui_name = 'post.ui'
		self.parent = parent
		self.w = uic.loadUi(os.path.join(self.parent.dir_ui, self.ui_name))
		self.w.setFixedSize(self.w.width(), self.w.height())	

		# set connection ====================

		self.w.btn_ok.clicked.connect(self.act_ok)

		self.w.btn_add.clicked.connect(self.act_add_plot)
		self.w.btn_del.clicked.connect(self.act_del_plot)
		self.w.btn_edit.clicked.connect(self.act_edit_plot)
		self.w.list_plot.doubleClicked.connect(self.act_edit_plot)
		self.w.btn_copy.clicked.connect(self.act_copy_plot)

		self.w.cb_plot.currentIndexChanged.connect(self.act_cb)


		# set variables ==============================

		self.cb_items = ['autoignition process','autoignition delay','1D flame structure','PSR S-cruve','GP edge analysis']
		self.plot_type = ['plot_ign_evolve','plot_ign_state','plot_premix_evolve','plot_psr_state','plot_GPedge']


		# set ui obj ==============================

		for item in self.cb_items:
			self.w.cb_plot.addItem(item)


		# exec ==============================

		self.w.exec_()

