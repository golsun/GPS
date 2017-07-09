from networkx import DiGraph
from networkx.readwrite import json_graph
import cantera as ct
import numpy as np
import json
#from src.core.def_tools import *
import os

__author__ = 'Xiang Gao'


""" ----------------------------------------------
 construction of the  element flux graph
-----------------------------------------------"""


def build_flux_graph(soln, raw, traced_element, path_save=None, overwrite=False, i0=0, i1='eq', constV=False):

	"""
	:param mechanism:        type = dict, keys include "species", "reaction", "element", etc
	:param raw:              type = dict, keys include "mole_fraction", "net_reaction_rate", etc
	:param traced_element:   type = str
	:param i0:               type = int, specifying the starting point of the considered interval of the raw data
	:param i1:               type = int or str, specifying the ending point of the considered interval of the raw data
	:return flux graph:      type = networkx object, will be also saved as a .json file,
	"""

	element = soln.element_names
	species = soln.species
	reaction = soln.reaction
	n_rxn = soln.n_reactions

	""" --------------------------------
	check if results already exist, if so, load
	-------------------------------- """

	if path_save is not None:
		if overwrite is False:
			try:
				data = json.load(open(path_save, 'r'))
				flux_graph = json_graph.node_link_graph(data)
				return flux_graph
			except IOError:
				pass

	""" --------------------------------
	if not, then compute, and save
	-------------------------------- """

	# ---------------------------------------------
	# check if traced_element is legal

	if traced_element not in element:
		raise('traced element ' + traced_element + ' is not listed in mechanism')

	# ---------------------------------------------
	# find the reaction rate during the considered interval
	# unit will be converted to mole/sec


	rr = np.reshape(raw['net_reaction_rate'][i0,:],[n_rxn,1]) 
	flux_graph = DiGraph()

	# -------------------------------------
	# adding edge from reactions
	# one edge may contribute from multiple reactions, the list of the contributors will be stored in edge['member']

	# note though in .cti id_rxn starts from 1, in soln.reaction, id_rxn starts from 0
	for id_rxn in range(n_rxn):


		# sp_mu is a dict, where key is species, val is net stoichiometric coefficient
		sp_mu = reaction(id_rxn).products
		for sp in reaction(id_rxn).reactants.keys():
			mu = reaction(id_rxn).reactants[sp]
			if sp in sp_mu.keys():
				sp_mu[sp] -= mu
			else:
				sp_mu[sp] = -mu

	   
		# -----------------------
		# produced is a dict, where key is sp, val is number of traced atoms
		# being transferred when this sp is produced
		produced = {}
		consumed = {}

		for sp in sp_mu.keys():
			atoms = species(sp).composition
			if traced_element in atoms.keys():
				n = int(sp_mu[sp] * atoms[traced_element] * np.sign(rr[id_rxn]))
				if n > 0:
					produced[sp] = abs(n)
				elif n < 0:
					consumed[sp] = abs(n)

		# -----------------------
		# consider this reaction only when traced element is transferred
		# note "if bool(consumed)" works the same way
		if bool(produced):
			n_sum = sum(produced.values())
			for target in produced.keys():
				for source in consumed.keys():

					n_i2j = 1.0 * produced[target] * consumed[source] / n_sum

					# note that the direction (source-->target) is already assured
					# therefore we use abs(RR) here
					dw = float(n_i2j * abs(rr[id_rxn]))

					try:
						flux_graph[source][target]['flux'] += dw
					except KeyError:
						# if this edge doesn't exist, create it
						flux_graph.add_edge(source, target)
						flux_graph[source][target]['flux'] = dw
						flux_graph[source][target]['member'] = {}

					flux_graph[source][target]['member'][str(id_rxn)] = dw
					flux_graph[source][target]['1/flux'] = 1.0 / flux_graph[source][target]['flux']

	# -------------------------------------
	# save the graph using json, which is fast, and human-readable

	data = json_graph.node_link_data(flux_graph)
	json.dump(data, open(path_save, 'w'))
	#print 'graph saved as',path_save

	return flux_graph
