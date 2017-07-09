# -*- coding: utf-8 -*-

import sys
import os
import cantera as ct
import json
import time
import copy
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph

from src.core.def_tools import cond2dir, keys_sorted
from src.core.def_GPSA import *
from src.ct.def_ct_tools import load_raw
from src.gui.def_run import load_dR
import sys
import os
import cantera as ct
import json
import time
import copy
import numpy as np


from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from def_plt_tools import *








def	find_node_edges(dir_raw, node, extra):

	n_edge = extra['n_edge']
	species = extra['species']
	traced = extra['traced']


	i_pnt = 0
	s = node
	mat_flux = dict()
	for t in species:
		mat_flux[t] = []

	dir_graph = os.path.join(dir_raw,'graph')
	while True:
		path_graph = os.path.join(dir_graph, traced+'_'+str(i_pnt) + '.json')
		print path_graph

		if os.path.exists(path_graph):
			data = json.load(open(path_graph, 'r'))
			flux_graph = json_graph.node_link_graph(data)

			sum_flux = 0
			for t in species:
				try:
					flux = max(0, flux_graph[s][t]['flux'])
				except KeyError:
					flux = 0
				mat_flux[t].append(flux)
				sum_flux += flux
			
			for t in species:
				mat_flux[t][-1] = 100.0 * mat_flux[t][-1] / sum_flux


		else:
			break
		i_pnt += 1


	peak_flux = dict()
	for t in mat_flux.keys():
		peak_flux[t] = max(mat_flux[t])

	tt = keys_sorted(peak_flux)
	cc_all = []
	ff_all = []
	for i_t in range(n_edge):
		t = tt[i_t]
		cc = mat_flux[t]
		cc_all.append(cc)
		ff_all.append(t)


	return cc_all, ff_all








"""

def	find_Rrop(dir_raw, n_rxn, role, parent, sample):

	soln = parent.soln['detailed']

	dir_desk = parent.project['mech']['detailed']['desk']
	path_R_npz = os.path.join(dir_desk,'mech','radical.npz')
	dnR = load_dR(path_R_npz, soln)

	rename = parent.project['rename']

	i_pnt = 0
	raw = load_raw(os.path.join(dir_raw,'raw.npz'))
	n_pnt = len(raw['axis0'])
	rr_mat = raw['net_reaction_rate']


	mat_rop = dict()
	rop_sample = dict()
	for i_pnt in range(n_pnt):
		max_rop = 0
		for id_rxn in range(len(dnR)):
			if i_pnt == 0:
				rop_sample[id_rxn] = 0
				mat_rop[id_rxn] = []
		
			rop = rr_mat[i_pnt, id_rxn] * dnR[id_rxn]
			if role == 'production':
				rop = max(0, rop)				
			else:
				rop = max(0, -rop)
			max_rop = max(max_rop, rop)
			mat_rop[id_rxn].append(rop)

		for id_rxn in range(len(dnR)):
			if sample['by'] == 'max':
				rop = mat_rop[id_rxn][-1]
				rop_sample[id_rxn] = max(rop_sample[id_rxn], 1.0*rop/max_rop)
	

	if sample['by'] != 'max':
		i_sample = find_i_plot(sample['at'], raw, sample_by=sample['by'])
		print 'Rrop: i_sample = '+str(i_sample)+', T = '+str(raw['temperature'][i_sample])
		for id_rxn in range(len(dnR)):
			rop_sample[id_rxn] = mat_rop[id_rxn][i_sample]

	cc_all = []
	ff_all = []
	rxns = keys_sorted(rop_sample)
	for i_rxn in range(n_rxn):
		id_rxn = rxns[i_rxn]
		eqn = soln.reaction_equation(id_rxn).replace('<','').replace('>','')
		#eqn = rename_reaction(soln.reaction_equation(id_rxn), rename)
		rr = rr_mat[:,id_rxn]
		if abs(min(rr)) > abs(max(rr)):
			A,B = eqn.split('=')
			eqn = B+'='+A

		cc_all.append(mat_rop[id_rxn])
		ff_all.append(eqn)


	return cc_all, ff_all



"""























def find_yy(soln, dir_raw, parent, fig_opt, sub_opt, tp):

	# tp is type 

	"""

	.8888b oo                dP                                
	88   "                   88                                
	88aaa  dP 88d888b. .d888b88              dP    dP dP    dP 
	88     88 88'  `88 88'  `88              88    88 88    88 
	88     88 88    88 88.  .88              88.  .88 88.  .88 
	dP     dP dP    dP `88888P8              `8888P88 `8888P88 
	                            oooooooooooo      .88      .88 
	                                          d8888P   d8888P  

	"""


	#dnR = load_dR(path_R_npz, soln)

	path_raw = os.path.join(dir_raw,'raw.npz')
	raw = load_raw(path_raw)

	xtype = fig_opt['xtype']
	mf = raw['mole_fraction']
	mole = [float(v) for v in raw['mole']]
	xx = [float(v) for v in raw['axis0']]
	TT = [float(v) for v in raw['temperature']]

	# ==========================================
	if '_T' in tp:
		if xtype == 'Temperature (K)':
			yy = [xx]
		else:
			yy = [TT]
		
		ff = ['']

	elif '_Qdot' in tp:
		yy = [raw['heat_release_rate']] 
		ff = ['']


	# ==========================================
	elif '_tau-ign' in tp:
		yy = [xx]
		ff = ['']


	# ==========================================
	elif '_psr-T' in tp:
		yy = [TT]
		ff = ['']


	# ==========================================
	elif '_sp' in tp:
		yy = []
		ff = []

		for i_sp in range(len(sub_opt['sp'])):
			sp = sub_opt['sp'][i_sp]	
			yy.append([])
			ff.append(sp)

		for i_pnt in range(len(raw['axis0'])):
			soln = raw2soln(soln, raw, i_pnt)

			for i_sp in range(len(sub_opt['sp'])):
				sp = sub_opt['sp'][i_sp]
				if sp != 'radical':
					sp_id_list = [soln.species_index(sp)]
				else:
					sp_id_list = [soln.species_index(R) for R in ['O','H','OH']]

				yi = 0
				for sp_id in sp_id_list:
					if sub_opt['task'] == 'mole fraction':
						yi += float(mf[i_pnt,sp_id])
					else:
						yi += soln.net_production_rates[sp_id]
				yy[i_sp].append(yi)


			


	# ==========================================
	elif '_GP' in tp:
		key = 'GP_' + sub_opt['traced']
		method = sub_opt['method']
		traced = sub_opt['traced']
		yy = []
		ff = []

		for i_GP in range(len(sub_opt[key])):
			GP_name = sub_opt[key][i_GP]
			GP_dir = parent.project[key][GP_name]
			GP_alias = GP_dir['alias']

			y = load_GPSA(dir_raw, GP_dir, method)
			if y is None:
				msg = 'could not find GPSA data for: \n'+GP_alias+' \nin:\n '+str(dir_raw)[-20:]+\
					'try to run GPSA first'
				QMessageBox.information(QWidget(),'',msg)
				return False, False, False, False

			yy.append(y)
			ff.append(GP_alias)


	# ==========================================
	elif '_node' in tp:
		extra = {'n_edge':int(sub_opt['n_edge'][0]), 'traced':sub_opt['traced'], 'species':soln.species_names}
		yy, ff = find_node_edges(dir_raw, sub_opt['node'], extra)




	ff_sorted = sorted(ff)
	yy_sorted = []
	for f in ff_sorted:
		i_f = ff.index(f)
		yy_sorted.append(yy[i_f])



	# ff is the label
	return yy_sorted, xx, TT, ff_sorted














def fun_comp0(varying, parent, db):
	ss = varying.split(' ')
	sp = ss[1]
	fo_key = ss[-1]

	num = []
	for fo_name in db[fo_key]:
		fo = parent.project[fo_key][fo_name]
		comp = fo['composition']
		if sp in comp.keys():
			num.append(100.0 * comp[sp]/sum(comp.values()))
		else:
			num.append(0.0)

	return num






def find_x_tran(x,mid):

	minx = min(x)
	maxx = max(x)

	dx = 0.1*(maxx-minx)

	labs = []
	locs = []
	locs_all = []

	for xi in x:
		if xi<mid:	
			norm = 1.0*(xi-minx)/(mid-minx)	# belongs to 0~1
			norm_tran = norm**2
			xi_tran = norm_tran * (mid-minx) + minx

		elif xi == mid:
			xi_tran = mid

		else:
			norm = 1.0*(xi-mid)/(maxx-mid) # belongs to 0~1
			norm_tran = 1.0 - (1-norm)**2
			xi_tran = mid + norm_tran*(maxx-mid)

		locs_all.append(xi_tran)
		if not bool(locs) or xi_tran>=locs[-1]+dx:
			labs.append(xi)
			locs.append(xi_tran)
	
	return locs_all, locs, labs







def refine_log(log, linear, fake=float('nan')):
	new_log = []
	new_linear = []
	for i in range(len(log)):
		if log[i]<=0:
			new_log.append(fake)
			new_linear.append(linear[i])
			"""
			if i>0 and log[i-1]>0:
				j = i-1
			elif i<len(log)-1 and log[i+1]>0:
				j = i+1
			else:
				j = i
			new_linear.append(0.5*(linear[j]+linear[i]))
			"""
		else:
			new_log.append(log[i])
			new_linear.append(linear[i])

	return new_log, new_linear










def painter(parent, fig_opt, sub_opt, ax, tp):

	"""


	                  oo            dP                 
	                                88                   
	88d888b. .d8888b. dP 88d888b. d8888P                 
	88'  `88 88'  `88 88 88'  `88   88                  
	88.  .88 88.  .88 88 88    88   88                 
	88Y888P' `88888P8 dP dP    dP   dP   
	88                                 
	dP                                                     



	"""

	print '@'*20
	print 'plotting '+str(sub_opt['name'])

	dir_public = parent.project['dir_public']

	ls = sub_opt['ls']
	ls_by = sub_opt['ls_by']
	color = sub_opt['color']
	color_by = sub_opt['color_by']
	marker = sub_opt['marker']
	marker_by = sub_opt['marker_by']

	ytick = sub_opt['ytick']
	ylim = sub_opt['ylim']
	yscale = sub_opt['scale']
	
	xtick = fig_opt['xtick']
	xlim = fig_opt['xlim']
	xscale = fig_opt['xscale']

	xtype = fig_opt['xtype']
	sec_var = fig_opt['2nd_var']
	reactor = fig_opt['db']['reactor']
	db = parent.project['database'][fig_opt['db']['db_name']]

	cond = dict()
	cond['fuel'] = fig_opt['db']['fuel']
	cond['oxid'] = fig_opt['db']['oxid']
	cond['phi'] = sub_opt['phi']
	cond['atm'] = fig_opt['db']['atm']
	cond['T0'] = fig_opt['db']['T0']
	cond['None'] = None

	# ========================================

	if sec_var == 'Pressure (atm)':
		sec_var_key = 'atm'
		sec_var_val = db['atm']
		sec_str = 'atm'
	elif sec_var == 'Initial temperature (K)' or sec_var == 'Inlet temperature (K)' :
		sec_var_key = 'T0'
		sec_var_val = db['T0']
		sec_str = 'K'
	elif 'concnetration (%) in fuel' in sec_var:
		sec_var_key = 'fuel'
		sec_var_val = db['fuel']
		sec_str = ''
		sec_var_val_num = fun_comp0(sec_var, parent, db)
	else:
		sec_var_key = 'None'
		sec_var_val = [None]
		sec_str = ''


	if ('ign_state' in fig_opt['subkey']):
		if xtype == 'Pressure (atm)':
			xtype_key = 'atm'
			xtype_val = db['atm']
		elif xtype == 'Initial temperature (K)' or sec_var == 'Inlet temperature (K)' :
			xtype_key = 'T0'
			xtype_val = db['T0']
		elif 'concnetration (%) in fuel' in xtype:
			xtype_key = 'fuel'
			xtype_val = db['fuel']
			xtype_val_num = fun_comp0(xtype, parent, db)

	elif ('ign_evolve' in fig_opt['subkey']) or ('premix_evolve' in fig_opt['subkey']) \
		or ('psr_state' in fig_opt['subkey']):
		xtype_key = 'None'
		xtype_val = [None]


	# ========================================

	for i_mech in range(len(fig_opt['mech'])):
		mech = fig_opt['mech'][i_mech]
		dir_desk = parent.project['mech'][mech]['desk']

		if mech == 'detailed':
			soln = parent.soln['detailed']
		else:
			if mech in parent.soln.keys():
				soln = parent.soln[mech]
			else:
				path_cti = os.path.join(dir_desk,'mech','chem.cti')
				soln = ct.Solution(path_cti)
				parent.soln[mech] = ct.Solution(path_cti)

		
		# ========================================

		for i_sec in range(len(sec_var_val)):
			cond[sec_var_key] = sec_var_val[i_sec]
			if 'ign_state' in fig_opt['subkey']: x = []
			yy = [[]]
			sec = str(sec_var_val[i_sec]) + sec_str

			# ========================================

			for i_x in range(len(xtype_val)):
				cond[xtype_key] = xtype_val[i_x]
				dir_raw = cond2dir(dir_desk, cond['fuel'], cond['oxid'], \
					float(cond['phi']), float(cond['atm']), float(cond['T0']),\
					reactor, parent.n_digit)
				path_raw = os.path.join(dir_raw,'raw.npz')


				if os.path.exists(path_raw):
					yy_inst, xx_inst, TT_inst, ff = find_yy(soln, dir_raw, parent, fig_opt, sub_opt, tp)

					if yy_inst is False:
						return False

					if 'ign_state' in fig_opt['subkey']: 
						if 'concnetration' in xtype:
							x.append(xtype_val_num[i_x])
						else:
							x.append(xtype_val[i_x])

						for i_feature in range(len(yy_inst)):
							if len(yy) < i_feature + 1:
								yy.append([])
							yy[i_feature].append(yy_inst[i_feature][-1])

					elif ('ign_evolve' in fig_opt['subkey']) or ('premix_evolve' in fig_opt['subkey']) or ('psr_state' in fig_opt['subkey']): 
						yy = yy_inst
						if xtype == 'Temperature (K)':
							x = TT_inst
						elif xtype == 'Normalized time':		
							tau_ign = find_tau_ign_raw({'temperature':TT_inst, 'axis0':xx_inst})
							x = [1.0*t/tau_ign for t in xx_inst]
						elif xtype == 'Time (ms)':
							x = [1000.0*t for t in xx_inst]
						else:
							x = xx_inst
				else:
					msg = 'does not exists: '+str(path_raw)
					QMessageBox.information(QWidget(),'',msg)
					return False


			print 'n_feature = '+str(len(yy))
			for i_feature in range(len(yy)):

				y = yy[i_feature]
				i_by = [i_mech, i_sec, i_feature]
				by = ['mech','2nd var','feature']

				i_color = i_by[by.index(color_by)]
				i_marker = i_by[by.index(marker_by)]
				i_ls = i_by[by.index(ls_by)]



				#if 'color' not in str(sub_opt.get('method')):

				msg = ''
				if i_color < len(color):
					C = color[i_color]
				else:
					msg = 'no enough color provided in subplot ' + sub_opt['name']

				if i_ls < len(ls):
					LS = ls[i_ls]
				else:
					msg = 'no enough line style provided in subplot ' + sub_opt['name']

				if i_marker < len(marker):
					M = marker[i_marker]
				else:
					msg = 'no enough marker provided in subplot ' + sub_opt['name']

				if bool(msg):					
					QMessageBox.information(QWidget(),'',msg)
					return False


				if 'ign_state' in fig_opt['subkey']:
					ind = np.argsort(x)
					x_sorted = [x[i] for i in ind]
					y_sorted = [y[i] for i in ind]
				else:
					x_sorted = copy.copy(x)
					y_sorted = copy.copy(y)


				if 'color' in str(sub_opt.get('method')):

					opt = dict()
					opt['crit_y'] = fig_opt['crit_y']
					opt['ff'] = ff
					opt['n_feature'] = len(yy)
					plot_color(x_sorted, y_sorted, ax, i_feature, opt)
					continue



				if xscale == 'linear' and yscale == 'linear':
					plot = ax.plot
				elif xscale == 'linear' and yscale == 'log':
					plot = ax.semilogy
				elif xscale == 'log' and yscale == 'linear':
					plot = ax.semilogx
				elif xscale == 'log' and yscale == 'log':
					plot = ax.loglog	



				if yscale == 'log':
					y_sorted, x_sorted = refine_log(y_sorted, x_sorted, 1e-20)
				if xscale == 'log':
					x_sorted, y_sorted = refine_log(x_sorted, y_sorted, 1e-20)


				if len(y_sorted) == 0:
					print 'len(y_sorted) === 0'
					return True

				print 'plotting feature '+str(i_feature)

				label = []
				if sub_opt['lg_mech']:
					label.append(mech)
				if sub_opt['lg_sec']:
					label.append(sec)
				if sub_opt['lg_feature']:
					sf = ff[i_feature]
					if '_sp' in tp or '_node' in tp:
						sf = rename_species(sf, parent.project['rename'])
					label.append(sf)

				s_label = ', '.join(label)
				plot(x_sorted, y_sorted, marker=M, linestyle=LS, color=C,fillstyle='none',label=s_label)

				print '-'*10
				print sub_opt['name']
				print s_label
				print x_sorted
				print y_sorted
				print '-'*10	


				if sub_opt['word_show']:
					word = ''
					if sub_opt['word_mech']:
						word += (mech + ', ')
					if sub_opt['word_2nd']:
						word += (sec + ', ')
					if sub_opt['word_feature']:
						word += (ff[i_feature] + ', ')
					word = word.strip(', ')
							

					if i_mech == 0 or sub_opt['word_mech']:
						if i_sec == 0 or sub_opt['word_2nd']:
							if i_feature == 0 or sub_opt['word_feature']:

								word_x = min(x) + 1.0/100 * sub_opt['word_loc'][0] * (max(x)-min(x))
								i_x = np.argmin(np.abs(np.array(x) - word_x))
								ax.text(word_x, y[i_x], word, color=color[i_color], fontsize=10)



	if 'color' in str(sub_opt.get('method')):
		return True



	if bool(ylim):
		ax.set_ylim(ylim)
		print 'setting ylim = '+str(ylim)
	else:
		ylim = opt_lim(ax, 'y', yscale)
		ax.set_ylim(ylim)



	str_unit = '[mole/m'+r'$^3$'+'-s]'



	if bool(xlim):
		ax.set_xlim(xlim)
	else:
		xlim = opt_lim(ax, 'x', yscale)
		ax.set_xlim(xlim)


	if bool(ytick):
		ax.set_yticks(ytick)
	if bool(xtick):
		ax.set_xticks(xtick)

	#ax.ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
	if '_GP' in tp:
		import matplotlib.ticker as mtick
		ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
	

	if '_T' in tp or '_psr-T' in tp:
		if xtype == 'Temperature (K)':
			ax.set_ylabel(r'$t$'+' [s]')
		else:
			ax.set_ylabel(r'$T$'+' [K]')

	elif '_sp' in tp:
		if sub_opt['task'] == 'mole fraction':
			ax.set_ylabel('Mole fraction [-]')
		else:
			ax.set_ylabel(sub_opt['task']+' '+str_unit)


	elif '_GP' in tp:
		method = sub_opt['method']
		if method == 'R_GP production':
			ax.set_ylabel('')
		elif method == 'R_GP consumption':		
			ax.set_ylabel(' '*40+r'$R_{GP}$ '+str_unit)
		elif method == 'D_GP':
			ax.set_ylabel(r'$D_{GP}$'+' [-]')
		else:
			ax.set_ylabel(sub_opt['method'])

	elif '_tau-ign' in tp:
		#ax.set_ylabel('Autoignition delay [s]')
		ax.set_ylabel(r'$\tau _{ign}$' + ' [s]')

	elif '_node' in tp:
		ylabel = 'distribution [%] of\n'+\
			'outgoing '+sub_opt['traced'].upper()+' fluxes of\n'+\
			rename_species(sub_opt['node'], parent.project['rename'])
		ax.set_ylabel(ylabel)

	elif '_Rrop' in tp:
		ax.set_ylabel('reaction rate '+str_unit)

	elif 'Qdot' in tp:
		ax.set_ylabel('HRR [J/m'+r'$^3$'+'-s]')

	else:
		ax.set_ylabel(sub_opt['name'])




	if sub_opt['lg_show']:
		if sub_opt['lg_mech'] or sub_opt['lg_sec'] or sub_opt['lg_feature']:
			ax.legend(loc=sub_opt['lg_loc'],frameon=False, fontsize=10, handlelength=3, labelspacing=0.1)

		"""

		by = ['mech','2nd var','feature']
		vv = [str(v) + sec_str for v in sec_var_val]
		lists = [fig_opt['mech'], vv, ff]

		if sub_opt['lg_marker']:
			lg_marker = marker
			lg_marker_ss = lists[by.index(marker_by)]
		else:
			lg_marker = ['None']
			lg_marker_ss = ['']

		if sub_opt['lg_ls']:
			lg_ls = ls
			lg_ls_ss = lists[by.index(ls_by)]
		else:
			lg_ls = ['none']
			lg_ls_ss = ['']

		if sub_opt['lg_color']:
			lg_color = color
			lg_color_ss = lists[by.index(color_by)]
		else:
			lg_color = ['k']
			lg_color_ss = ['']

		if bool(lg_marker_ss) or bool(lg_ls_ss) or bool(lg_color_ss):

			for i_M in range(len(lg_marker_ss)):
				M = lg_marker[i_M]
				Ms = lg_marker_ss[i_M]
				for i_LS in range(len(lg_ls_ss)):
					LS = lg_ls[i_LS]
					LSs = lg_ls_ss[i_LS]
					for i_C in range(len(lg_color_ss)):
						C = lg_color[i_C]
						Cs = lg_color_ss[i_C]

						lg_s = ''
						if bool(Ms):
							lg_s += (Ms + ', ')
						if bool(LSs):
							lg_s += (LSs + ', ')
						if bool(Cs):
							lg_s += (Cs + ', ')
						lg_s = lg_s.strip(', ')

						#lg_s = rename_species(lg_s, parent.project['rename'])


						if xscale == 'log':

							if yscale == 'linear':
								ax.semilogx(0, ylim[0]-1e5, marker=M, linestyle=LS, color=C,fillstyle='none',label=lg_s)
							else:
								ax.loglog(0, 1e-100, marker=M, linestyle=LS, color=C,fillstyle='none',label=lg_s)

						else:

							if yscale == 'linear':
								ax.plot(0, ylim[0]-1e5, marker=M, linestyle=LS, color=C,fillstyle='none',label=lg_s)
							else:
								ax.semilogy(0, 1e-100, marker=M, linestyle=LS, color=C,fillstyle='none',label=lg_s)
			
			ax.legend(loc=sub_opt['lg_loc'],frameon=False, fontsize=10, handlelength=3, labelspacing=0.1)
			"""
	

	reverse = ('consumption' in str(sub_opt.get('method')) + str(sub_opt.get('role')))
	if yscale == 'log':		
		ax = modify_log(ax, reverse)
	else:
		ax = modify_linear(ax, reverse)


	return True





def modify_linear(ax, reverse, xy='y'):

	if xy == 'y':
		lim_now = ax.get_ylim()
		locs = ax.get_yticks()
	else:
		lim_now = ax.get_xlim()
		locs = ax.get_xticks()

	if len(locs)>5:
		dn = max(2, int(len(locs)/5))
		locs_new = []
		for i in range(len(locs)):
			if i%dn==0:
				locs_new.append(locs[i])
		locs = locs_new


	print 'lim_now = '+str(lim_now)

	if reverse:
		prefix = -1.0
	else:		
		prefix = 1.0

	labs = [ticklabel_str(prefix*tick) for tick in locs]


	if xy == 'y':
		set_ticks = ax.set_yticks
		set_ticklabels = ax.set_yticklabels
	else:
		set_ticks = ax.set_xticks
		set_ticklabels = ax.set_xticklabels

	if reverse:
		set_ticks(locs[1:])
		set_ticklabels(labs[1:])
	else:
		set_ticks(locs)
		set_ticklabels(labs)


	if reverse:
		if xy == 'y':
			ax.set_ylim(max(lim_now),min(lim_now))
		else:
			ax.set_xlim(max(lim_now),min(lim_now))
	else:		
		if xy == 'y':
			ax.set_ylim(min(lim_now),max(lim_now))
		else:
			ax.set_xlim(min(lim_now),max(lim_now))

	if xy == 'y':
		print 'after modify, lim = '+str(ax.get_ylim())
	else:
		print 'after modify, lim = '+str(ax.get_xlim())

	return ax




def ticklabel_str(x):
	if x==int(x):
		return str(int(x))
	else:
		return str(x)


def modify_log(ax, reverse, xy='y'):

	if xy == 'y':
		lim_now = ax.get_ylim()
	else:
		lim_now = ax.get_xlim()

	min_pow = int(np.ceil(np.log10(min(lim_now))))
	max_pow = int(np.floor(np.log10(max(lim_now))))

	d_pow = max(1,int((max_pow - min_pow)/4))

	pp = range(min_pow, max_pow+1, d_pow)
	locs = [10**p for p in pp] 

	if reverse:
		if xy == 'y':
			ax.set_ylim(max(lim_now),min(lim_now))
		else:
			ax.set_xlim(max(lim_now),min(lim_now))
		prefix = '-'
	else:
		prefix = ''

	labs = ['$'+prefix+'10^{'+ticklabel_str(p)+'}$' for p in pp]

	if xy == 'y':
		set_ticks = ax.set_yticks
		set_ticklabels = ax.set_yticklabels
	else:
		set_ticks = ax.set_xticks
		set_ticklabels = ax.set_xticklabels

	if reverse:
		set_ticks(locs[1:])
		set_ticklabels(labs[1:])
	else:
		set_ticks(locs)
		set_ticklabels(labs)

	return ax



def find_tau_ign_raw(raw):
	T = raw['temperature']
	for i in range(len(T)):
		if T[i]-T[0]>=400:
			return raw['axis0'][i]




def find_i_plot(sample_loc, raw, sample_by='T rised (K)'):
	T = raw['temperature']
	if sample_by == 'T rised (K)':
		xx = [T[i]-T[0] for i in range(len(T))]
	elif sample_by == 'norm t passed':
		tau_ign = find_tau_ign_raw(raw)
		xx = [1.0*t/tau_ign for t in raw['axis0']]
	elif sample_by == 'T (K)':
		xx = T
	else:
		xx = raw['axis0']

	i_plot = None
	if xx[-1]>xx[0]:
		for i in range(len(xx)):
			if xx[i] >= sample_loc:
				i_plot = i
				break
	else:
		print 'find_i_plot: reversed, sample_by = '+str(sample_by)
		for i in range(len(xx)):
			if xx[i] <= sample_loc:
				i_plot = i
				break


	if i_plot is None:
		print 'cannot find i_plot, sample_by = '+str(sample_by)+' max(xx) - min(xx) = '+str(max(xx)-min(xx))+', but sample_loc = '+str(sample_loc)
	return i_plot







def plot_GPedge_mf(soln, GP_dir, opt, raw, path_save, rename, i_plot=None, title=None):
	plt.rc('font', **{'family':'Times New Roman'})

	if i_plot is None:
		sample_loc = float(opt['sample_loc'][0])
		sample_by = opt['sample_by']
		i_plot = find_i_plot(sample_loc, raw, sample_by)


	if opt['xscale'] == 'log':
		plot = plt.semilogx
		print 'using log as xscale = '+str(opt['xscale']) 
	else:
		plot = plt.plot
		print 'using linear as xscale = '+str(opt['xscale']) 

	i = 0
	for sp in GP_dir['member']:
		id_sp = soln.species_names.index(sp)
		mf = raw['mole_fraction'][i_plot, id_sp]
		#plot([0, mf], [-i,-i], color='k')
		#plt.text(0,-i, rename_species(sp, rename), horizontalalignment='right')

		plot(mf,-i, color='k', marker='o')
		plt.text(mf,-i, rename_species(sp, rename), horizontalalignment='right')


		i += 1


	T = raw['temperature']
	x = raw['axis0']
	tau_ign = find_tau_ign_raw(raw)

	if title is None:
	 	title = 'T = '+str(T[i_plot])+', axis0 = '+str(x[i_plot])
	 	if tau_ign is not None:
		 	title +=', norm_x = '+str(1.0*x[i_plot]/tau_ign)
		title+='\n'
	plt.title(title)



	plt.savefig(path_save)
	return True





def plot_GPedge(soln, data, opt, raw, path_save, rename, i_plot=None, title=None):

	print 'plot_GPedge: rename = '+str(rename)

	plt.rc('font', **{'family':'Times New Roman'})
	fig_w = float(opt['fig_w'][0])
	fig_h = float(opt['fig_h'][0])
	xscale = opt['xscale']
	xlim = opt['xlim']

	edges = sorted(data.keys())
	fig, axs = plt.subplots(1,2,sharey=True, 
		figsize=(fig_w, fig_h))
	ax_pos = axs[1]
	ax_neg = axs[0]
	#ax_rr  = axs[2]

	if i_plot is None:
		sample_loc = float(opt['sample_loc'][0])
		sample_by = opt['sample_by']
		i_plot = find_i_plot(sample_loc, raw, sample_by)
 
	T = raw['temperature']
	x = raw['axis0']
	tau_ign = find_tau_ign_raw(raw)
	if title is None:
	 	title = 'T = '+str(T[i_plot])+', axis0 = '+str(x[i_plot])
 		if tau_ign is not None:
	 		title +=', norm_x = '+str(1.0*x[i_plot]/tau_ign)
		title+='\n'

	

	if i_plot is None:
		msg = 'cannot find i_plot at '+sample_by + ' of '+str(sample_loc)
		QMessageBox.information(QWidget(),'',msg)
		return False

	if xscale == 'log':
		if bool(xlim):
			minx = xlim[0]			
		else:
			minx = 10**(-8.9)
		x_txt =  minx*5
	else:		
		if bool(xlim):
			minx = xlim[0]
			x_txt = xlim[0] + 0.05*(xlim[1] - xlim[0])
		else:
			minx = 0
			x_txt = 0


	n_rxn = int(opt['n_rxn'][0])
	dy = 0.8/(1+n_rxn)

	for i_edge in range(len(edges)):
		edge = edges[i_edge]
		A,B = edge.split('.')[1].strip().replace('-->',',').split(',')
		txt0 = rename_species(A, rename) + r' $\rightarrow$ ' + rename_species(B, rename)
		

		c_list = []
		txt_list = []


		c_list.append(data[edge]['net'][i_plot])
		txt_list.append(txt0)


		mm = data[edge]['member'][i_plot]
		mm_abs = dict()
		for id_rxn_s in mm.keys():
			mm_abs[id_rxn_s] = abs(mm[id_rxn_s])

		top_rxns = keys_sorted(mm_abs)
		for id_rxn_s in top_rxns[:min(len(top_rxns), n_rxn)]:
			c_list.append(mm[id_rxn_s])

			id_rxn = int(id_rxn_s)
			rxn = soln.reaction_equation(abs(id_rxn))
			rxn_new = rename_reaction(rxn, rename)
			if id_rxn<0:
				A,B = rxn_new.split('=')
				rxn_new = B+'='+A
			#txt_list.append(id_rxn_s+'. '+rxn_new)
			txt_list.append(rxn_new)


		light_gray = [0.8,0.8,0.8]
		dark_gray = [0.4,0.4,0.4]

		for i_c in range(len(c_list)):
			c = c_list[i_c]
			txt = txt_list[i_c]

			if i_c == 0:
				color_bar = 'k'	
				color_txt = 'k'	
				lw = 4
				weight = 'bold'
			else:
				color_bar = light_gray
				color_txt = dark_gray	
				lw = 2
				weight = 'light'

			y_i = i_edge + dy*(i_c)#+1.5)
			y = [y_i]*2
			x = (minx, abs(c))

			if c>=0:
				ax_bar = ax_pos	
				ax_txt = ax_neg
				align = 'right'		
			else:
				ax_bar = ax_neg
				ax_txt = ax_pos
				align = 'left'

			if xscale == 'log':
				plot = ax_bar.semilogx
			else:
				plot = ax_bar.plot

			if x[1]>minx:
				plot(x, y, color=color_bar,linewidth=lw)
				plot(x[1], y_i, color=color_bar,marker='s',linewidth=3, markeredgecolor=color_bar)
			ax_txt.text(x_txt, y_i+0.3*dy, txt, horizontalalignment=align, 
				fontsize=10, color=color_txt, weight=weight)
	


	if not bool(xlim):
		lim_pos = ax_pos.get_xlim()
		lim_neg = ax_neg.get_xlim()
		xlim = (min(lim_pos[0], lim_neg[0]), max(lim_pos[1], lim_neg[1]))
	
	ax_neg.set_xlim(xlim)
	ax_pos.set_xlim(xlim)

	if xscale == 'log':
		modify_log(ax_pos, False, xy='x')
		modify_log(ax_neg, True, xy='x')
	else:
		modify_linear(ax_pos, False, xy='x')
		modify_linear(ax_neg, True, xy='x')

	ax_pos.set_ylim(len(edges), -0.5)
	plt.subplots_adjust(wspace=0)
	ax_neg.get_yaxis().set_visible(False)
	ax_pos.get_yaxis().set_visible(False)

	n_space = int(60 * fig_w / 5.6)

	s_unit = '[mole/m'+r'$^3$'+'-s]'
	if opt['method'] == 'R_ij':
		ax_neg.set_xlabel(' '*n_space+r'$R_{i\rightarrow j}$ '+s_unit)
	else:
		ax_neg.set_xlabel(' '*n_space+r'$A_{i\rightarrow j}-A_{j\rightarrow i}$ '+s_unit)

	ax_neg.set_title(title)
	plt.subplots_adjust(wspace=0)
	plt.savefig(path_save)#, format='eps', dpi=1000, bbox_inches='tight')
	return True



