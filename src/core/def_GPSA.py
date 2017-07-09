# Xiang Gao, Georgia Tech, 2016-2017



import os, json
from src.ct.def_ct_tools import load_raw
from networkx.readwrite import json_graph
from scipy.stats.mstats import gmean
import numpy as np


def shorten_GP_name(GP_name):
	s = GP_name.replace(' ','').replace('-->','>')
	return s



def find_edge_name(GP_member, i):
	s = GP_member[i]
	t = GP_member[i+1]
	ID = str(i+1)
	if len(ID) == 1:
		ID = '0'+ID
	return ID +'. '+ s+' --> '+t



def raw2soln(soln, raw, i_pnt):
	T = raw['temperature'][i_pnt]
	P = raw['pressure'][i_pnt]
	sp = soln.species_names
	mf = raw['mole_fraction'][i_pnt,:]

	X = ''
	for i in range(len(sp)):
		X += sp[i]+':'+str(mf[0,i])+','

	soln.TPX = T, P, X[:-1]
	return soln




def load_GPSA(dir_raw, GP_dict, method):
	GP_name = GP_dict['name']
	traced = GP_dict['traced']
	path_save = os.path.join(dir_raw,'GPSA',traced, shorten_GP_name(GP_name)+'.json')
	if os.path.exists(path_save):
		GPSA_all = json.load(open(path_save,'r'))
		if GP_name not in GPSA_all.keys():
			return None
	else:
		return None

	GPSA = GPSA_all[GP_name]
	data = []
	method0 = method.replace('production','').replace('consumption','').strip()

	if method0 == 'R_ij' or method0 == 'a_iji':
		return GPSA[method0]

	for v in GPSA[method0]:
		if v is None:
			data.append(0)
		else:
			data.append(v)

	if 'production' in method:
		return [max(0,v) for v in data]
	elif 'consumption' in method:
		return [max(0,-v) for v in data]
	else:
		return data




def	find_GPSA(dir_raw, GP_dict, soln, dnR, fuel_comp, n_break=0):

	GP_name = GP_dict['name']
	traced = GP_dict['traced']
	dir_save = os.path.join(dir_raw,'GPSA',traced)
	if not os.path.exists(dir_save):
		os.makedirs(dir_save)
	path_save = os.path.join(dir_save, shorten_GP_name(GP_name)+'.json')

	# =====================================
	# if previously computed, return False

	GPSA_all = dict()
	if os.path.exists(path_save):
		GPSA_all = json.load(open(path_save,'r'))
		if GP_name in GPSA_all.keys():
			return False

	# =====================================
	# if not loaded, compute these results


	print 'computing GPSA for '+GP_name

	traced = GP_dict['traced']
	GP_member = GP_dict['member']
	dir_graph = os.path.join(dir_raw,'graph')	
	path_raw = os.path.join(dir_raw,'raw.npz')
	raw = load_raw(path_raw)
	rr_mat = raw['net_reaction_rate']

	GPSA = dict()
	GPSA['R_GP'] = []		# net radical production rate associated with a Global Pathway (GP)
	GPSA['Q_GP'] = []		# net heat release rate associated with a GP
	GPSA['D_GP'] = []		# dominancy of a GP

	GPSA['R_ij'] = dict()	# net radical production rate associated with a conversion step (from the i-th species to the j-th species)
	GPSA['Q_ij'] = dict()
	GPSA['a_iji'] = dict()
	#GPSA['perc_ij'] = dict()

	for i in range(len(GP_member)-1):
		edge = find_edge_name(GP_member, i)

		GPSA['R_ij'][edge] = dict()
		GPSA['R_ij'][edge]['member'] = []
		GPSA['R_ij'][edge]['net'] = []

		GPSA['Q_ij'][edge] = dict()
		GPSA['Q_ij'][edge]['member'] = []
		GPSA['Q_ij'][edge]['net'] = []

		GPSA['a_iji'][edge] = dict()
		GPSA['a_iji'][edge]['member'] = []
		GPSA['a_iji'][edge]['net'] = []

		#GPSA['perc_ij'][edge] = dict()
		#GPSA['perc_ij'][edge]['member'] = []
		#GPSA['perc_ij'][edge]['net'] = []

	source = GP_dict['member'][0]
	traced = GP_dict['traced']
	if source not in fuel_comp.keys():
		perc_from_source = 0.0
	else:
		total_atom = 0
		for k in fuel_comp.keys():
			sp = soln.species(k)
			atom = 0.0
			if traced in sp.composition.keys():
				atom += fuel_comp[k] * sp.composition[traced]
			if source == k:
				atom_source = atom
			total_atom += atom

		perc_from_source = 1.0 * atom_source / total_atom

		#print 'total '+traced+' atoms for '+str(fuel_comp)+' is '+str(total_atom)
		#print 'source '+str(source)+' has '+str(atom_source)+' atms'
		#print 'so perc_from_source = '+str(perc_from_source)

	#GPSA['perc_ij']['from_source'] = perc_from_source


	# for each point -----------

	i_pnt = 0
	while True:

			

		path_graph = os.path.join(dir_graph, traced+'_'+str(i_pnt) + '.json')
		if not os.path.exists(path_graph): 			
			if i_pnt>n_break:
				print 'break as cannot find: '+str(path_graph)
				break
			
			else:			
				# fill this with None ---------------
				if i_pnt%10 == 0:
					print '   fill None GPSA for '+str(path_graph)

				for i in range(len(GP_member)-1):
					s = GP_member[i]
					t = GP_member[i+1]
					edge = find_edge_name(GP_member, i)
					for k in ['member','net']:
						GPSA['R_ij'][edge][k].append(None)
						GPSA['Q_ij'][edge][k].append(None)
						GPSA['a_iji'][edge][k].append(None)
						#GPSA['perc_ij'][edge][k].append(None)

				GPSA['R_GP'].append(None)
				GPSA['D_GP'].append(None)

				i_pnt += 1
				continue

		soln = raw2soln(soln, raw, i_pnt)	
		if i_pnt%10 == 0:
			print '   finding GPSA for '+str(path_graph)

		# fill this with real value ---------------
		#norm_Rpro = 0.0
		#norm_Rcon = 0.0
		for id_rxn in range(soln.n_reactions):
			dR = dnR[id_rxn] * rr_mat[i_pnt, id_rxn]
			#norm_Rpro += max(0, dR)
			#norm_Rcon += max(0, -dR)


		flux_graph = json_graph.node_link_graph(json.load(open(path_graph, 'r')))
		out_deg = flux_graph.out_degree(weight='flux')
		norm_out_deg = sum([out_deg[m] for m in fuel_comp.keys() if m in out_deg.keys()])

		flux = []
		rxn_involved = []
		sum_OMEGA_R = 0
		sum_OMEGA_Q = 0
		perc_ij_list = []

		# for each edge (conversion step) -----------------


		for i in range(len(GP_member)-1):
			s = GP_member[i]
			t = GP_member[i+1]
			edge = find_edge_name(GP_member, i)
			GPSA['R_ij'][edge]['member'].append(dict())
			GPSA['Q_ij'][edge]['member'].append(dict())
			GPSA['a_iji'][edge]['member'].append(dict())
			#GPSA['perc_ij'][edge]['member'].append(dict())

			# ------------------------------

			try:
				st = flux_graph[s][t]
			except KeyError:
				st = None

			perc_ij = None
			if st is not None:
				flux.append(st['flux'])
				perc_ij = 1.0 * st['flux'] / out_deg[s]
				perc_ij_list.append(perc_ij)

				for id_rxn_s in st['member'].keys():
					id_rxn = int(id_rxn_s)
					rxn = soln.reaction_equation(id_rxn)
					rr = rr_mat[i_pnt, id_rxn]
					if rr < 0:
						sign_rxn = -id_rxn
					else:
						sign_rxn = id_rxn

					GPSA['a_iji'][edge]['member'][i_pnt][sign_rxn] = st['member'][id_rxn_s]
					#GPSA['perc_ij'][edge]['member'][i_pnt][sign_rxn] = 1.0 * st['member'][id_rxn_s]/out_deg[s]

					OMEGA_R = float(rr * dnR[id_rxn])
					GPSA['R_ij'][edge]['member'][i_pnt][sign_rxn] = OMEGA_R					

					OMEGA_Q = float(rr * soln.delta_enthalpy[id_rxn])
					GPSA['Q_ij'][edge]['member'][i_pnt][sign_rxn] = OMEGA_Q

					if id_rxn not in rxn_involved:
						sum_OMEGA_R += OMEGA_R
						sum_OMEGA_Q += OMEGA_Q
						rxn_involved.append(id_rxn)




			# ------------------------------

			try:
				ts = flux_graph[t][s]
			except KeyError:
				ts = None

			if ts is not None:
				for id_rxn_s in ts['member'].keys():
					id_rxn = int(id_rxn_s)
					rxn = soln.reaction_equation(id_rxn)
					rr = rr_mat[i_pnt, id_rxn]
					if rr < 0:
						sign_rxn = -id_rxn
					else:
						sign_rxn = id_rxn
					GPSA['a_iji'][edge]['member'][i_pnt][sign_rxn] = - ts['member'][id_rxn_s]

			# ------------------------------

			GPSA['R_ij'][edge]['net'].append(sum(GPSA['R_ij'][edge]['member'][i_pnt].values()))
			GPSA['Q_ij'][edge]['net'].append(sum(GPSA['Q_ij'][edge]['member'][i_pnt].values()))
			GPSA['a_iji'][edge]['net'].append(sum(GPSA['a_iji'][edge]['member'][i_pnt].values()))
			#GPSA['perc_ij'][edge]['net'].append(perc_ij)


		domi_perc = gmean(perc_ij_list)*perc_from_source
		if bool(flux):
			min_flux = min(flux)
			if norm_out_deg>0:
				domi_flux = 1.0 * min_flux/norm_out_deg
			else:
				domi_flux = float('nan')
		else:
			min_flux = 0.0
			domi_flux = 0.0

		R_GP = domi_perc * sum_OMEGA_R
		Q_GP = domi_perc * sum_OMEGA_Q
		GPSA['R_GP'].append(R_GP)
		GPSA['Q_GP'].append(Q_GP)
		GPSA['D_GP'].append(domi_perc)


		i_pnt += 1


	GPSA_all[GP_name] = GPSA
	json.dump(GPSA_all, open(path_save,'w'))
	return True


