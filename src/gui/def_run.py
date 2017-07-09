
import sys
import os
import json
import time
import cantera as ct
import shutil
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from src.core.def_tools import *
from src.ct.def_ct_tools import Xstr
from src.ct.senkin import senkin
from src.ct.psr import S_curve
from src.ck.def_cheminp import skeletal
from src.ct.ck2cti_GPS import ck2cti

from dialog_GPS import dialog_GPS
#from dialog_PFA import dialog_PFA
from dialog_database import dialog_database
from dialog_mech import dialog_mech
from dialog_view_mech import dialog_view_mech

from find_tau_ign import find_tau_ign


from src.ct.def_ct_tools import load_raw
from src.core.def_GPS import GPS_algo
from src.core.def_build_graph import build_flux_graph
from networkx.readwrite import json_graph
from src.core.def_tools import st2name
from src.core.def_GPSA import find_GPSA

""" >>>>>>>>>>>>>------------------------------------------------
0.3. run
     called by: window_main
"""


class dialog_progress(object):

	def set_value(self, task, value):
		tasks = ['train','GPS','test','GPSA']
		bars = [self.w.bar_train, self.w.bar_GPS, self.w.bar_test, self.w.bar_GPSA]
		bar = bars[tasks.index(task)]
		bar.setValue(int(value))
		self.parent.app.processEvents()

	def set_info(self, new_info):
		str_time = '[' + time.strftime("%H:%M:%S") + '] '
		new_info = str_time + new_info.replace(self.dir_public,'').strip('/') + '\n'
		#self.f.write(str(new_info))

		old_info = self.w.txt_info.toPlainText()
		self.w.txt_info.setText(old_info + new_info)
		self.w.txt_info.moveCursor(QTextCursor.End)
		self.parent.app.processEvents()

	def act_verbose(self):
		if self.verbose:
			self.w.btn_verbose.setText('verbose')
			self.verbose = False
		else:
			self.w.btn_verbose.setText('concise')
			self.verbose = True


	def act_stop(self):
		self.stop = True
		msg = 'will stop after finishing current sub-task'
		QMessageBox.information(QWidget(),'',msg)

	def close(self):
		self.w.accept()

	def __init__(self, parent):
		ui_name = 'progress.ui'
		self.parent = parent		
		self.stop = False
		self.verbose = False
		self.dir_public = self.parent.project['dir_public']
		self.f = open(os.path.join(self.dir_public,'log.txt'),'w')

		self.w = uic.loadUi(os.path.join(parent.dir_ui, ui_name))
		self.w.btn_stop.clicked.connect(self.act_stop)
		self.w.btn_verbose.clicked.connect(self.act_verbose)

		tasks = ['train','GPS','test']
		for task in tasks:
			self.set_value(task,0)

		self.parent.app.processEvents()
		self.w.show()





""" >>>>>>>>>>>>>------------------------------------------------
"""






def write_sk_inp(species_kept, dir_mech_de, dir_mech_sk, notes):

	species_kept = list(species_kept)
	n_sp = len(species_kept)
	print 'total: '+str(n_sp)

	notes.append('! number of species = '+str(n_sp))
	skeletal(dir_mech_de, dir_mech_sk, species_kept, notes=notes)
	ck2cti(dir_mech_sk)

	f = open(os.path.join(dir_mech_sk,'ns.txt'),'w')
	f.write(str(n_sp))
	f.close()






""" >>>>>>>>>>>>>------------------------------------------------
"""



def find_raw(soln, soln_in, dir_desk, fuel, \
	oxid, phi, atm, T0, reactor, n_digit):
	
	dir_raw = cond2dir(dir_desk, fuel['name'], oxid['name'], phi, atm, T0, reactor, n_digit)
	if not os.path.exists(dir_raw):
		os.makedirs(dir_raw)

	X0 = Xstr(soln, fuel['composition'], phi, oxid['composition'])	
	if reactor == 'autoignition':
		senkin(soln, atm, T0, X0, if_half=True, dir_raw=dir_raw, if_fine=False)
	elif reactor == 'autoignition fine':
		senkin(soln, atm, T0, X0, if_half=True, dir_raw=dir_raw, if_fine=True)
	elif reactor == 'autoignition full':
		senkin(soln, atm, T0, X0, if_half=False, dir_raw=dir_raw, if_fine=False)
	elif reactor == 'PSR extinction':
		S_curve(soln_in, soln, atm, T0, X0, dir_raw=dir_raw)














""" ------------------------------------------------------
	training


	  dP                     oo          
	  88                                 
	d8888P 88d888b. .d8888b. dP 88d888b. 
	  88   88'  `88 88'  `88 88 88'  `88 
	  88   88       88.  .88 88 88    88 
	  dP   dP       `88888P8 dP dP    dP 
	                                     

	"""


def run_train(parent, progress):

	dir_de = os.path.join(parent.project['dir_public'],'detailed')
	soln = parent.soln['detailed']
	soln_in = parent.soln_in['detailed']

	list_train = []
	for db_name in parent.project['database'].keys():
		if parent.project['database'][db_name]['train']:
			list_train.append(db_name)

	list_train = sorted(list_train)

	v = 0
	progress.set_value('train', v)
	raw_single_mech(progress, list_train, parent, 100, v, dir_de, soln, soln_in)
	progress.set_value('train', 100)
	return True



""" >>>>>>>>>>>>>------------------------------------------------
"""





def raw_single_mech(progress, list_db, parent, dv_mech, v, dir_desk, soln, soln_in, bar='train'):

	dv_db = 1.0 * dv_mech /len(list_db)

	for db_name in list_db:

		database = parent.project['database'][db_name]
		phi_list = database['phi']
		T0_list = database['T0']
		atm_list = database['atm']
		fuel_list = database['fuel']
		oxid_list = database['oxid']
		reactor = database['reactor']

		dv_raw = 1.0 * dv_db / (len(phi_list) * len(atm_list) * len(T0_list) *\
				 len(fuel_list) * len(oxid_list))
		
		progress.set_info('\n' + '-'*10 + ' database: ' + db_name + ' ' + '-'*10)

		for fuel_name in fuel_list:
			for oxid_name in oxid_list:
				for phi in phi_list:
					for atm in atm_list:
						for T0 in T0_list:

							if progress.stop:
								progress.close()
								return False

							fuel = parent.project['fuel'][fuel_name]
							oxid = parent.project['oxid'][oxid_name]

							dir_raw = cond2dir(dir_desk, fuel_name, oxid_name, phi, atm, T0, \
								reactor, parent.n_digit)
							path_raw = os.path.join(dir_raw,'raw.npz')

							if os.path.exists(path_raw):
								progress.set_info('<already exists, skipped> '+dir_raw)
							else:
								progress.set_info(dir_raw)
								find_raw(soln, soln_in,\
									dir_desk, fuel,	oxid, phi, atm, T0, reactor, parent.n_digit)

							v += dv_raw
							progress.set_value(bar, v)

				#print '@'*20
				if 'autoignition' in reactor:
					fld = os.path.join(dir_desk,'raw',
						'['+fuel_name.strip('[').strip(']')+'] + ['+oxid_name.strip('[').strip(']')+']')
					find_tau_ign(fld)
					print
					print 'find_tau_ign'
					print 'fld = '+str(fld)
					print

				#print dir_desk
				#print '@'*20
	#sys.exit()
	#fld = os.path.join(dir_desk,)




	return v















def run_graph(parent, progress, task):
	if task == 'GPS':
		obj = progress.w.label_GPS
	elif task == 'GPSA':
		obj = progress.w.label_GPSA

	obj.setText('building graph')

		
	dir_public = parent.project['dir_public']
	soln = parent.soln['detailed']

	list_train = []
	train_name = parent.train_name
	for db_name in parent.project['database'].keys():
		if parent.project['database'][db_name]['train']:
			list_train.append(db_name)

	traced_list = []
	for GPS_name in parent.project['GPS'].keys():
		if parent.project['GPS'][GPS_name]['checked']:
			GPS = parent.project['GPS'][GPS_name]
			es_name = GPS['es']
			es = parent.project['es'][es_name]
			for e in es['element'].keys():
				if es['element'][e]['traced']:
					if e not in traced_list:
						traced_list.append(e)

	if not bool(traced_list):
		msg = 'no traced element in selected GPS'
		QMessageBox.information(QWidget(),'',msg)
		return False

	v = 0.0
	dv_db = 100.0/len(list_train)
	for db_name in list_train:

		database = parent.project['database'][db_name]
		phi_list = database['phi']
		T0_list = database['T0']
		atm_list = database['atm']
		fuel_list = database['fuel']
		oxid_list = database['oxid']
		reactor = database['reactor']

		dv_raw = dv_db / (len(phi_list) * len(atm_list) * len(T0_list) *\
			len(fuel_list) * len(oxid_list))
		
		for fuel_name in fuel_list:
			for oxid_name in oxid_list:
				for phi in phi_list:
					for atm in atm_list:
						for T0 in T0_list:

							if progress.stop:
								progress.close()
								return False

							dir_de = os.path.join(dir_public,'detailed')
							dir_raw = cond2dir(dir_de, fuel_name, \
								oxid_name, phi, atm, T0, \
								reactor, parent.n_digit)							
							if 'DNS' in reactor:
								dir_raw = os.path.join(dir_raw, database['case'][0])
							raw = load_raw(os.path.join(dir_raw,'raw.npz'))
							dir_graph = os.path.join(dir_raw,'graph')
							if not os.path.exists(dir_graph):
								os.makedirs(dir_graph)

							n_pnt = len(raw['axis0'])
							dv_pnt = 1.0 * dv_raw / n_pnt

							print 'dir_raw = '+str(dir_raw)
							print 'n_point = '+str(len(raw['axis0']))

							for i_pnt in range(len(raw['axis0'])):
								if 'active reactions' in raw.keys() and len(raw['active reactions'])>0:
									if raw['active reactions'][i_pnt] == 0:
										print 'skipped pnt '+str(i_pnt)+' as no active reaction'
										continue
								
								for e in traced_list:
									path_graph = os.path.join(dir_graph, e+'_'+str(i_pnt)+'.json')
									if not os.path.exists(path_graph):
										info = 'building '+e+'-graph for pnt'+str(i_pnt)+' of '+\
											str(dir_raw.replace(dir_de,''))
										if i_pnt%10==0:
											print info
										if n_pnt<100:
											progress.set_info(info)
										flux_graph = build_flux_graph(soln, raw, e, \
											path_save=path_graph, overwrite=False, \
											i0=i_pnt, i1=i_pnt, constV=False)
									else:
										print 'already exists '+str(path_graph)
										

								v += dv_pnt
								if n_pnt<100:
									progress.set_value(task,v)

	obj.setText(task)
	progress.set_value(task,0.0)
	return True













""" ------------------------------------------------------


	 .88888.   888888ba  .d88888b  
	d8'   `88  88    `8b 88.    "' 
	88        a88aaaa8P' `Y88888b. 
	88   YP88  88              `8b 
	Y8.   .88  88        d8'   .8P 
	 `88888'   dP         Y88888P  
	                               
	                               

	"""

def run_GPS(parent, progress):
	if not run_graph(parent, progress,'GPS'):
		return False


	min_dT = parent.min_dT

	dir_public = parent.project['dir_public']
	soln = parent.soln['detailed']

	list_train = []
	train_name = parent.train_name
	for db_name in parent.project['database'].keys():
		if parent.project['database'][db_name]['train']:
			list_train.append(db_name)

	list_GPS = []
	for GPS_name in parent.project['GPS'].keys():
		if parent.project['GPS'][GPS_name]['checked']:
			list_GPS.append(GPS_name)

	v = 0
	if bool(list_GPS) == False:
		return False
	dv_GPS = 100.0/len(list_GPS)

	# for different GPS settings ============================

	for GPS_name in list_GPS:

		GPS = parent.project['GPS'][GPS_name]
		alpha_list = GPS['alpha']
		beta_list = GPS['beta']
		K_list = GPS['K']
		must_keep = GPS['must_keep']


		es_name = GPS['es']
		es = parent.project['es'][es_name]
		traced_list = []
		for e in es['element'].keys():
			if es['element'][e]['traced']:
				traced_list.append(e)


		if GPS['iso_enable']:
			iso_name = GPS['iso']
			iso = parent.project['iso'][iso_name]
			gamma_list = GPS['gamma']
		else:
			iso_name = None
			iso = None
			gamma_list = [None]


		dv_kab = 1.0 * dv_GPS/ (len(K_list) * len(beta_list) * len(alpha_list) * len(gamma_list))

		for K in K_list:
			for beta in beta_list:
				for alpha in alpha_list:
					for gamma in gamma_list:


						dir_sk = para2dir_GPS(dir_public, train_name, \
					    	alpha=alpha, K=K, beta=beta, \
					    	es_name=es_name, iso_name=iso_name, \
					    	d=parent.n_digit, gamma=gamma)

						progress.set_info('\n' + '-'*10 + dir_sk + ' ' + '-'*10)

						dir_mech_sk = os.path.join(dir_sk,'mech')
						path_cti_sk = os.path.join(dir_mech_sk,'chem.cti')

						if os.path.exists(path_cti_sk):
							progress.set_info('<already exists, skipped> '+path_cti_sk)
							v += dv_kab
							progress.set_value('GPS',v)
							continue

						dir_de = os.path.join(dir_public,'detailed')
						dir_mech_de = os.path.join(dir_de,'mech')
						path_cti_de = os.path.join(dir_mech_de,'chem.cti')

						species_kept = set(must_keep)

						notes = ['! generated by global pathway selection, Gao et al,'+\
							' Combustion and flame, 167 (2016) 238-247']
						notes.append('! alpha = ' + str(alpha) + ', K = ' + str(K) + \
							', beta = ' + str(beta))
						notes.append('! training database: '+train_name)



						# for different training database ============================

						dv_db = 1.0 * dv_kab / len(list_train)

						for db_name in list_train:

							database = parent.project['database'][db_name]
							phi_list = database['phi']
							T0_list = database['T0']
							atm_list = database['atm']
							fuel_list = database['fuel']
							oxid_list = database['oxid']
							reactor = database['reactor']

							dv_raw = 1.0 * dv_db / (len(phi_list) * len(atm_list) * len(T0_list) *\
								len(fuel_list) * len(oxid_list))
							
							for fuel_name in fuel_list:
								for oxid_name in oxid_list:
									for phi in phi_list:
										for atm in atm_list:
											for T0 in T0_list:

												if progress.stop:
													progress.close()
													return False

												fuel = parent.project['fuel'][fuel_name]
												oxid = parent.project['oxid'][oxid_name]
												species_kept |= set(fuel['composition'].keys())
												species_kept |= set(oxid['composition'].keys())

												e_available = set()
												for sp in fuel['composition'].keys():
													e_available |= set(soln.species(sp).composition.keys())												
												for sp in oxid['composition'].keys():
													e_available |= set(soln.species(sp).composition.keys())



												dir_raw = cond2dir(dir_de, fuel_name, \
													oxid_name, phi, atm, T0, \
													reactor, parent.n_digit)
												if 'DNS' in reactor:
													dir_raw = os.path.join(dir_raw, database['case'][0])

												progress.set_info('raw = '+\
													dir_raw.replace(os.path.join(dir_de,'raw'),'').strip('/'))


												dir_graph = os.path.join(dir_raw,'graph')



												#raw_name = dir_raw.replace(\
												#	os.path.join(dir_de,'raw'),'').strip('/')

												raw_name = cond2dir('', fuel_name, \
													oxid_name, phi, atm, T0, \
													reactor, parent.n_digit)
												
												if 'DNS' in reactor:
													raw_name = os.path.join(dir_raw, database['case'][0])


												dir_how = os.path.join(dir_sk,raw_name.replace('raw','how'))

												if not os.path.exists(dir_how):
													os.makedirs(dir_how)

												raw = load_raw(os.path.join(dir_raw,'raw.npz'))
												T = raw['temperature']
												axis0 = raw['axis0']

												


												# for different time instance ================

												flag = False
												# -----------------------------------------------
												# I only consider the points where T and T0 has
												# some difference, which means there're reactions
												# performing GPS on chemically frozen state, or
												# equilibirum state (for PSR), does not give too
												# much useful information
												#
												# once a point is sampled, flag = True
												# -----------------------------------------------

												dv_pnt = 1.0 * dv_raw / len(T)
												for i_pnt in range(len(T)):

													if 'active reactions' in raw.keys():
														if raw['active reactions'][i_pnt] == 0:
															print 'skipped pnt '+str(i_pnt)+' as no active reaction'
															continue

													if flag == False:
														if abs(T[i_pnt]-T[0])>min_dT:
															flag = True


													# for different source->target ==============

													for e in traced_list:

														if e not in e_available:
															continue

														sources = copy.copy(es['element'][e]['source'])

														if bool(sources) == False:
															sources = [None]
														if parent.alias_fuel in sources:
															del sources[sources.index(parent.alias_fuel)]

															for sp in fuel['composition'].keys():
																atoms = soln.species(sp).composition.keys()
																#print 'atms of ' + sp + ' = ' +str(atoms)
																if e in atoms:
																	sources += [sp]


														targets = es['element'][e]['target']
														if bool(targets) == False:
															targets = [None]

														for target in targets:
															for source in sources:
																name_how = st2name(i_pnt, e, source, target)
																if progress.verbose:
																	progress.set_info(' '*5 + name_how)

																path_gps = os.path.join(dir_how, name_how+'.json')
																path_graph = os.path.join(dir_graph, e+'_'+str(i_pnt)+'.json')
																
																if os.path.exists(path_graph):
																	data = json.load(\
																		open(path_graph, 'r'))
																	flux_graph = json_graph.node_link_graph(data)

																else:
																	if progress.verbose:
																		progress.set_info(' '*10 + 'building graph...')
																	dir_graph = os.path.join(dir_raw,'graph')
																	if not os.path.exists(dir_graph):
																		os.makedirs(dir_graph)

																	flux_graph = build_flux_graph(soln, raw, e, \
																		path_save=path_graph, overwrite=False, \
																		i0=i_pnt, i1=i_pnt, constV=False)


																if flag == False:
																	continue

																GPS_notes = 'T = '+str(T[i_pnt])+', axis0 = '+str(axis0[i_pnt])+\
																		' ('+str(min(axis0))+' ~ '+str(max(axis0))+')'

																GPS_results = GPS_algo(soln, flux_graph, source, target, \
																	path_save=path_gps, K=K, alpha=alpha, beta=beta, \
																	normal='max', iso=iso, overwrite=True, raw=dir_raw, \
																	notes=GPS_notes, gamma=gamma)

																new_kept = set(GPS_results['species'].keys())
																species_kept |= new_kept



													v += dv_pnt
													progress.set_value('GPS', v)

						# generate chem.inp ***************
						write_sk_inp(species_kept, dir_mech_de, dir_mech_sk, notes)
						#"""
	
	progress.set_value('GPS', 100)
	return True




















"""
---------------------------------------------


 .88888.   888888ba  .d88888b   .d888888  
d8'   `88  88    `8b 88.    "' d8'    88  
88        a88aaaa8P' `Y88888b. 88aaaaa88a 
88   YP88  88              `8b 88     88  
Y8.   .88  88        d8'   .8P 88     88  
 `88888'   dP         Y88888P  88     88  
                                          
---------------------------------------------                                         

"""





def load_dR(path_save, soln, overwrite=False):

	if overwrite == False:
		if os.path.exists(path_save):
			npz_file = np.load(open(path_save, 'rb'))
			npz = dict()
			for key in npz_file.keys():
				npz[key] = npz_file[key]
			return npz['dnR']

	R = []
	sp_list = soln.species_names
	R_cand = ['O','H','OH']
	for R_cand_i in R_cand:
		if R_cand_i in sp_list:
			R.append(R_cand_i)
		elif R_cand_i.lower() in sp_list:
			R.append(R_cand_i.lower())


	rxn = soln.reaction
	dnR = []
	for id_rxn in range(soln.n_reactions):
		reactants = rxn(id_rxn).reactants.keys()
		products = rxn(id_rxn).products.keys()

		dnR_i = 0
		for R_i in R:
			if R_i in reactants:
				dnR_i -= rxn(id_rxn).reactants[R_i]
			if R_i in products:
				dnR_i += rxn(id_rxn).products[R_i]

		dnR.append(dnR_i)

	np.savez(path_save,dnR=dnR)
	return dnR







def run_GPSA(parent, progress):
	if not run_graph(parent, progress, 'GPSA'):
		return False


	min_dT = parent.min_dT

	dir_public = parent.project['dir_public']
	soln = parent.soln['detailed']

	list_train = []
	train_name = parent.train_name
	for db_name in parent.project['database'].keys():
		if parent.project['database'][db_name]['train']:
			list_train.append(db_name)

	list_GPS = []
	for GPS_name in parent.project['GPS'].keys():
		if parent.project['GPS'][GPS_name]['checked']:
			list_GPS.append(GPS_name)

	if bool(list_GPS):

	# for different GPS settings ============================
	# add new GP

		print 'run_GPSA: here0'
		for GPS_name in list_GPS:

			GPS = parent.project['GPS'][GPS_name]
			alpha_list = GPS['alpha']
			beta_list = GPS['beta']
			K_list = GPS['K']


			es_name = GPS['es']
			es = parent.project['es'][es_name]
			traced_list = []
			for e in es['element'].keys():
				if es['element'][e]['traced']:
					traced_list.append(e)


			if GPS['iso_enable']:
				iso_name = GPS['iso']
				iso = parent.project['iso'][iso_name]
				gamma_list = GPS['gamma']
			else:
				iso_name = None
				iso = None
				gamma_list = [None]


			for K in K_list:
				for beta in beta_list:
					for alpha in alpha_list:
						for gamma in gamma_list:

							dir_sk = para2dir_GPS(dir_public, train_name, \
						    	alpha=alpha, K=K, beta=beta, \
						    	es_name=es_name, iso_name=iso_name, \
						    	d=parent.n_digit, gamma=gamma)

							dir_how = os.path.join(dir_sk,'how')
							if not os.path.exists(dir_how):
								continue

							for fo in os.listdir(dir_how):
								dir_fo = os.path.join(dir_how,fo)
								if ('+' not in fo) or (not os.path.isdir(dir_fo)): continue							
								for reactor in os.listdir(dir_fo):
									dir_reactor = os.path.join(dir_fo,reactor)
									if (not os.path.isdir(dir_reactor)): continue
									for fat in os.listdir(dir_reactor):
										dir_fat = os.path.join(dir_reactor, fat)
										if ('phi' not in fat) or (not os.path.isdir(dir_fat)): continue	
										for file in os.listdir(dir_fat):
											if 'graph' not in file: continue
											file_GP = os.path.join(dir_fat,file)
											traced = file.split(',')[1].replace('graph','').strip().upper()
											GP_traced = 'GP_' + traced
											if GP_traced not in parent.project.keys():
												parent.project[GP_traced] = dict()
											GPS_results = json.load(open(file_GP,'r'))
											for GP_name in GPS_results['global_path'].keys():
												if GP_name not in parent.project[GP_traced].keys():

													GP_dict = dict()
													GP_dict['alias'] = GP_name
													GP_dict['name'] = GP_name
													GP_dict['member'] = GPS_results['global_path'][GP_name]['member']
													GP_dict['traced'] = traced
													parent.project[GP_traced][GP_name] = GP_dict

													progress.set_info('added '+traced+'-traced global pathway: '+str(GP_name))
	

	print 'run_GPSA: here1'
	# find all GP ==============================
	GP_list = []

	filter_traced = str(parent.w.cb_GPSA_traced.currentText())
	print 'filter_traced = '+str(filter_traced)
	if filter_traced == 'no filter':
		ee = parent.soln['detailed'].element_names
	else:
		ee = [filter_traced]

	alias_only = (str(parent.w.cb_GPSA_alias.currentText()) == 'with alias only')

	source_str = str(parent.w.cb_GPSA_source.currentText())
	if source_str == 'no filter':
		sources = parent.soln['detailed'].species_names
	else:
		sources = [source_str]

	for traced in ee:
		traced = traced.upper()
		if 'GP_'+traced in parent.project.keys():
			for GP_name in parent.project['GP_'+traced].keys():
				GP_dir = parent.project['GP_'+traced][GP_name]
				if GP_dir['member'][0] not in sources:
					continue
				if (not alias_only) or (alias_only and (GP_dir['alias'] != GP_name)):
					GP_list.append((traced, GP_name))





	if not bool(GP_list):
		msg = 'GP_list is empty!\nTry to run GPS first or loose GPSA settings'
		QMessageBox.information(QWidget(),'',msg)
		return False

	print 'len(GP_list) = '+str(len(GP_list))


	# for different training set ============================
	# to compute GPSA quantities

	dir_desk = parent.project['mech']['detailed']['desk']
	path_R_npz = os.path.join(dir_desk,'mech','radical.npz')
	dnR = load_dR(path_R_npz, soln)
	soln = parent.soln['detailed']

	v = 0.0
	dv_db = 100.0 / len(list_train)
	for db_name in list_train:

		database = parent.project['database'][db_name]
		phi_list = database['phi']
		T0_list = database['T0']
		atm_list = database['atm']
		fuel_list = database['fuel']
		oxid_list = database['oxid']
		reactor = database['reactor']

		dv_raw = 1.0 * dv_db / (len(phi_list) * len(atm_list) * len(T0_list) * len(fuel_list) * len(oxid_list))
		dv_GP = 1.0 * dv_raw / len(GP_list)

		
		for fuel_name in fuel_list:
			for oxid_name in oxid_list:
				for phi in phi_list:
					for atm in atm_list:
						for T0 in T0_list:

							if progress.stop:
								progress.close()
								return False

							fuel = parent.project['fuel'][fuel_name]
							oxid = parent.project['oxid'][oxid_name]

							fuel_comp = parent.project['fuel'][fuel_name]['composition']

							dir_de = os.path.join(dir_public,'detailed')
							dir_raw = cond2dir(dir_de, fuel_name, \
								oxid_name, phi, atm, T0, \
								reactor, parent.n_digit)
							if 'DNS' in reactor:
								dir_raw = os.path.join(dir_raw, database['case'][0])
								raw = load_raw(os.path.join(dir_raw,'raw.npz'))
								n_break = len(raw['axis0'])
							else:
								n_break = 0

							dir_graph = os.path.join(dir_raw,'graph')
							no_graph = True
							if os.path.exists(dir_graph):
								for file in os.listdir(dir_graph):
									if file.endswith('.json'):
										no_graph = False
										break
							if no_graph:
								msg = 'no graph file found for: \n\n'+str(dir_raw.replace(dir_public,'[working dir]'))
								QMessageBox.information(QWidget(),'',msg)
								return False


							progress.set_info(str(dir_raw))

							
							for traced, GP_name in GP_list:
								msg = ' '*4+'computing GPSA for '+str(GP_name)
								print msg
								progress.set_info(msg)
								GP_dir = parent.project['GP_'+traced][GP_name]									
								find_GPSA(dir_raw, GP_dir, soln, dnR, fuel_comp, n_break)

								v += dv_GP
								progress.set_value('GPSA', v)
												
	return True









































""" ------------------------------------------------------


		  dP                       dP   
		  88                       88   
		d8888P .d8888b. .d8888b. d8888P 
		  88   88ooood8 Y8ooooo.   88   
		  88   88.  ...       88   88   
		  dP   `88888P' `88888P'   dP   
		                                
		                                
	                               

	"""


def run_test(parent, progress):



	dir_public = parent.project['dir_public']

	list_test = []
	for db_name in parent.project['database'].keys():
		if parent.project['database'][db_name]['test']:
			list_test.append(db_name)

	list_train = []
	train_name = parent.train_name
	for db_name in parent.project['database'].keys():
		if parent.project['database'][db_name]['train']:
			list_train.append(db_name)



	#  ============================

	#	      dP            dP            oo dP                dP 
	#	      88            88               88                88 
	#	.d888b88 .d8888b. d8888P .d8888b. dP 88 .d8888b. .d888b88 
	#	88'  `88 88ooood8   88   88'  `88 88 88 88ooood8 88'  `88 
	#	88.  .88 88.  ...   88   88.  .88 88 88 88.  ... 88.  .88 
	#	`88888P8 `88888P'   dP   `88888P8 dP dP `88888P' `88888P8 
                                                          


	progress.w.label_test.setText('calculating detailed...')

	dir_de = os.path.join(dir_public,'detailed')
	soln = parent.soln['detailed']
	soln_in = parent.soln_in['detailed']

	v = 0
	progress.set_value('test', v)
	raw_single_mech(progress, list_test, parent, 100, v, dir_de, soln, soln_in, 'test')










	#  ============================


	#	 .88888.   888888ba  .d88888b  
	#	d8'   `88  88    `8b 88.    "' 
	#	88        a88aaaa8P' `Y88888b. 
	#	88   YP88  88              `8b 
	#	Y8.   .88  88        d8'   .8P 
	#	 `88888'   dP         Y88888P  
		                               
	                               

	progress.w.label_test.setText('testing GPS...')

	list_GPS = []
	for GPS_name in parent.project['GPS'].keys():
		if parent.project['GPS'][GPS_name]['checked']:
			list_GPS.append(GPS_name)

	v = 0
	progress.set_value('test', v)

	if bool(list_GPS):

		dv_GPS = 100.0/len(list_GPS)

		for GPS_name in list_GPS:

			GPS = parent.project['GPS'][GPS_name]
			alpha_list = GPS['alpha']
			beta_list = GPS['beta']
			K_list = GPS['K']
			es_name = GPS['es']
			if GPS['iso_enable']:
				iso_name = GPS['iso']
				gamma_list = GPS['gamma']
			else:
				iso_name = None
				gamma_list = [None]


			dv_kab = 1.0 * dv_GPS/ (len(K_list) * len(beta_list) * len(alpha_list) * len(gamma_list))

			for K in K_list:
				for beta in beta_list:
					for alpha in alpha_list:
						for gamma in gamma_list:

							dir_sk = para2dir_GPS(dir_public, train_name, \
							    	alpha=alpha, K=K, beta=beta, \
							    	es_name=es_name, iso_name=iso_name, \
							    	d=parent.n_digit, gamma=gamma)

							progress.set_info('\n' + '-'*10 + dir_sk + ' ' + '-'*10)

							path_cti = os.path.join(dir_sk,'mech','chem.cti')
							soln = ct.Solution(path_cti)
							soln_in = ct.Solution(path_cti)

							v = raw_single_mech(progress, list_test, parent, dv_kab, v, dir_sk, soln, soln_in,'test')



	#  ============================

	#               dP   dP                         
	#               88   88                         
	#    .d8888b. d8888P 88d888b. .d8888b. 88d888b. 
	#    88'  `88   88   88'  `88 88ooood8 88'  `88 
	#    88.  .88   88   88    88 88.  ... 88       
	#    `88888P'   dP   dP    dP `88888P' dP       
                                           
                                           
	
	

	for name in parent.project['mech'].keys():
		sk = parent.project['mech'][name]
		if name != 'detailed' and sk['checked']:
			dir_sk = sk['desk']
			path_cti = os.path.join(dir_sk,'mech','chem.cti')
			if name not in parent.soln.keys():
				parent.soln[name] = ct.Solution(path_cti)
				parent.soln_in[name] = ct.Solution(path_cti)

			soln = parent.soln[name]
			soln_in = parent.soln_in[name]

			v = 0
			progress.w.label_test.setText('testing '+name)
			progress.set_value('test', v)
			raw_single_mech(progress, list_test, parent, 100, v, dir_sk, soln, soln_in, 'test')











