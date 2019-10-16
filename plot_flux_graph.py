# author: Xiang Gao (gxiang1228@gmail.com)
# run with python 2.7 and networkx 1.10

import Queue
import json, os
from networkx.readwrite import json_graph
import numpy as np


def load_raw(path_raw):
    raw_file = np.load(open(path_raw, 'rb'))
    raw = dict()
    for key in raw_file.keys():
        if key in ['mole_fraction','net_reaction_rate']:
            raw[key] = np.matrix(raw_file[key])
        else:
            raw[key] = raw_file[key]
    return raw


def get_edges(fld, traced='C'):
	raw = load_raw(os.path.join(fld, 'raw.npz'))
	tt = raw['axis0']

	integral = dict()
	for i_pnt in range(1, len(tt)):
		print 'reading point '+str(i_pnt)

		path_graph = os.path.join(fld, 'graph', traced+'_'+str(i_pnt)+'.json')
		flux_graph = json_graph.node_link_graph(json.load(open(path_graph, 'r')))
		for edge in flux_graph.edges():
			flux = flux_graph[edge[0]][edge[1]]['flux']
			if edge not in integral:
				integral[edge] = 0.
			integral[edge] += flux * (tt[i_pnt] - tt[i_pnt-1])

	return integral


def s2label(s):
	label=''
	for c in s:
		if c.isdigit():
			label+='<font point-size="'+str(SUB_FONTSIZE)+'">'+c+'</font>'
		else:
			label+=c
	return label



def create_gv(edges, path_gv, n_edge, by='width', top=None):

	pq = Queue.PriorityQueue()
	maxflux = 0.
	for edge in edges:
		flux = edges[edge]

		pq.put((-flux, edge))
		maxflux = max(maxflux, flux)

	start = set()
	end = set()
	edges = []

	for i in xrange(n_edge):
		neg_flux, edge = pq.get()
		#print edge
		start.add(edge[0])
		end.add(edge[1])
		edges.append((edge[0], edge[1], -neg_flux))

		#print edge, -neg_flux

	nodes = start & end
	nodes.add('H2')
	#nodes.add('CO2')

	#print path_gv
	#print "nodes",nodes
	#return
	with open(path_gv,'w') as f:
		f.write('digraph FluxGraphByGPS {\n'+\
			'    node [fontsize='+str(FONTSIZE)+\
			', pin=true, style=bold, fontname='+FONTNAME+ ']\n')

		if top is not None:
			for node in top:
				f.write('    '+node+'\n')


		nodes_show = set()
		for start, end, flux in edges:
			if start not in nodes or end not in nodes:
				continue
			# H2 -> H [color = "0,0,0.11081", style=bold]
			w = flux/maxflux*MAX_WIDTH
			if w <= 1e-3:
				continue

			if by == 'color':
				attr = 'color = "0,0,' + '%.4f'%(1.-flux/maxflux)+'", style=bold'
			elif by == 'width':
				attr = 'penwidth = ' + '%.2f'%w+\
					', label="  '+'%.0f'%(flux/maxflux*100)+'", fontsize='+str(FONTSIZE)+', fontname='+FONTNAME
			else:
				attr = ''
			f.write('    '+start+' -> '+end+' ['+attr+']\n'.replace('\*','(a)'))
			nodes_show.add(start)
			nodes_show.add(end)

		for node in nodes_show:
			f.write('    '+str(node)+'[label=<'+s2label(node)+'>];\n')

		f.write('}')



def main(fld_raw, traced, top=None):
	n_edge = 30
	by='width'
	path_gv = fld_raw + '/flux_graph_%s%i.gv'%(traced, n_edge)
	edges = get_edges(fld_raw, traced)
	create_gv(edges, path_gv, n_edge, by=by, top=['H2'])
	print('\n\ngraph file saved to: '+path_gv)
	print('copy the content inside to http://www.webgraphviz.com/ and click "Generate Graph!"')



FONTNAME = 'Calibri'
FONTSIZE = 24
SUB_FONTSIZE = 20
MAX_WIDTH = 12

if __name__ == '__main__':
	fld_raw = 'demo/detailed/raw/[H2] + [air]/autoignition/phi1.0_30.0atm_1000.0K'
	traced = 'H'	# H or C
	top = 'H2'	# can be None. but usually the fuel
	main(fld_raw, traced, top=top)



