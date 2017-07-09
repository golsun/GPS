import os, sys, math
import matplotlib.pyplot as plt
import numpy as np
#from scipy.misc import imsave
import cantera as ct



def find_strY(soln, mass_fraction, crit=1e-20):
	strY = []
	for sp_id in range(soln.n_species):
		if mass_fraction[sp_id] > crit:
			strY.append(soln.species_names[sp_id]+':'+str(mass_fraction[sp_id]))
	return ','.join(strY)





def DNS2raw(filename, soln):

	raw = dict()
	raw['axis0'] = []
	raw['axis1'] = []
	raw['axis2'] = []
	raw['temperature'] = []
	raw['pressure'] = []
	raw['vorticity'] = []
	raw['chi'] = []
	raw['active species'] = []
	raw['active reactions'] = []
	raw['mixture fraction'] = []
	raw['mass_fraction'] = []
	raw['mole_fraction'] = []
	raw['net_reaction_rate'] = []
	raw['ROP_mass'] = []
	raw['ROP_mass_DNS'] = []
	raw['heat_release_rate'] = []
	raw['cp'] = []
	raw['axis0_type'] = 'distance'

	n_sp = soln.n_species

	i_pnt = 0
	i_line = 0
	section = 'none'
	with open(filename,'r') as f:
		while True:
			line = f.readline()
			i_line += 1

			# identify section ---------------------

			if 'VARIABLES' in line:
				#print 'start reading header at line'+str(i_line)+': '+str(line)
				section = 'header'
				header = []

			if (section == 'header') and (line.replace('VARIABLES = ','').strip()[0]!='"'):
				#print 'stop reading header at line'+str(i_line)+': '+str(line)
				print 'header = '+str(header)
				section = 'header2data'

			if (section == 'header2data') and ('DT=(' in line):

				i_try = 0
				while True:
					line = f.readline()
					#print 'trying to find data in: '+str(line)
					i_line += 1
					i_try += 1
					ss = line.strip().split(' ')
					if len(ss) == len(header):
						break
					else:
						print 'failed as len(ss) = '+str(len(ss))+', but len(header)='+str(len(header))
					if i_try > 10:
						print 'cannot find data'
						sys.exit()

				#print 'start reading data at line'+str(i_line)+': '+str(line)[:25]+'...'
				section = 'data'

			if (section == 'data'):
				ss = line.strip().split(' ')
				if len(ss) < len(header):
					print 'stop reading data at line'+str(i_line)+': '+str(line)
					break


			# reading header -----------------
			# header is a list of (var_type, var_name)

			if section == 'header':
				s = line.replace('VARIABLES = ','').replace('"','').strip()
				
				identified = False
				coords = ['X','Y','Z']
				for coord in coords:
					if coord == s:
						header.append(('coord','axis'+str(coords.index(s))))
						identified = True
						break

				if not identified:
					basics = ['TEMPERATURE','PRESSURE','VORTICITY',
						'CHI','ACTIVE SPECIES','ACTIVE REACTIONS','MIXTURE FRACTION']
					for basic in basics:
						if basic == s:
							header.append(('basic',s.lower()))
							identified = True
							break

				if not identified:
					if 'YK-' in s:
						sp_id = int(s.replace('YK-','').strip())-1
						header.append(('mass_fraction', sp_id))
						identified = True


					if 'WDOT-' in s:
						sp_id = int(s.replace('WDOT-','').strip())-1
						header.append(('ROP_mass_DNS', sp_id))
						identified = True

				if not identified:
					header.append(('other',s))


			# reading data --------------------
			if section == 'data':
				if i_pnt%100 == 0:
					print 'i_pnt = '+str(i_pnt)
				raw['mass_fraction'].append([0]*n_sp)
				raw['ROP_mass_DNS'].append([0]*n_sp)

				for i_var in range(len(header)):
					var_type, var_name = header[i_var]

					if var_type in ['coord','basic']:
						raw[var_name].append(float(ss[i_var]))

					if var_type == 'mass_fraction':
						sp_id = var_name						
						raw['mass_fraction'][i_pnt][sp_id] = float(ss[i_var])

					if var_type == 'ROP_mass_DNS':
						sp_id = var_name						
						raw['ROP_mass_DNS'][i_pnt][sp_id] = float(ss[i_var])

				# build soln based on TPY ---------------
				Y = find_strY(soln, raw['mass_fraction'][i_pnt])
				T = raw['temperature'][i_pnt]
				P = raw['pressure'][i_pnt]
				soln.TPY = T, P, Y

				raw['mole_fraction'].append(soln.X)
				raw['cp'].append(soln.cp)

				ROP = soln.net_production_rates
				MW = soln.molecular_weights

				ROP_mass = [ROP[i]*MW[i] for i in range(len(ROP))]

				raw['ROP_mass'].append(ROP_mass)	# kg/m3-s
				raw['net_reaction_rate'].append(soln.net_rates_of_progress * 1e3)
				raw['heat_release_rate'].append(-sum(soln.delta_enthalpy * soln.net_rates_of_progress))

				i_pnt += 1




	return raw


def find_coord(raw, key, max_len=200, lim=None):
	print 'computing coord'

	#if 'axis' in key:
	#	x = raw[key]
	#	xx = sorted(list(set(x)))
	#else:
	if isinstance(key, str):
		if 'axis' in key:
			minx = min(raw[key])
			x_raw = [xi-minx for xi in raw[key]]
		else:
			x_raw = raw[key]
			if key.lower() == 'chi':
				x_raw = [np.log(chi) for chi in x_raw]
	else:
		x_raw = raw[key[0]][:, key[1]] 


	if lim is None:
		maxx = max(x_raw)
		minx = min(x_raw)
	else:
		maxx = lim[1]
		minx = lim[0]

	if 'axis' in key:
		dx = 0.0001
		xx = list(np.arange(int(minx/0.0001)*dx, int(maxx/0.0001)*dx, dx))
	else:
		dx = 1.0*(maxx-minx)/(max_len-1)
		xx = list(np.arange(minx, maxx, dx))+[maxx]

	x = []
	ii = []
	for xi in x_raw:
		diff = [abs(xi-xxi) for xxi in xx]
		ix = diff.index(min(diff))
		ii.append(ix)
		x.append(xx[ix])

		#print x_raw[:20]
		#print x[:20]
		

	# xx is ticks for the axis
	# x is coord for each pnt

	return x, xx, ii


def find_labels(ticks, vv):
	labels = []
	nv = len(vv)
	for tick in ticks:
		if tick>=0 and tick<nv:
			v = vv[int(tick)]
			if v == int(v):
				labels.append(str(int(v)))
			else:
				labels.append(str(v))

		else:
			labels.append('')
	return labels


def show_2D(raw, key_show, 
	GPSA_data_list=None, Z_cut=None, Z_contour=None,
	key_x='axis0',key_y='axis1', xlim=None, ylim=None,
	clim=None, ax=None, 
	colorbar=True, cmap='jet',
	mutiplier=1.0):

	if ax is None:
		f, ax = plt.subplot(1,1)

	"""
	if key_x == 'axis0':
	x = raw[key_x]
	xx = sorted(list(set(x)))
	y = raw[key_y]
	yy = sorted(list(set(y)))
	"""

	x, xx, trash = find_coord(raw, key_x, lim=xlim)
	y, yy, trash = find_coord(raw, key_y, lim=ylim)
	Z = raw['mixture fraction']

	n_x = len(xx)
	n_y = len(yy)

	print 'n_x = '+str(n_x)
	print 'n_y = '+str(n_y)

	if n_x*n_y == 0:
		print 'cannot build as n_x = '+str(n_x)+', n_y = '+str(n_y)
		print 'raw = '+str(raw)
		return


	print 'building matrix'
	data = np.zeros((n_y,n_x))+float('nan')
	Zmat = np.zeros((n_y,n_x))+float('nan')
	for i in range(len(x)):
		i_y = yy.index(y[i])
		i_x = xx.index(x[i])

		if math.isnan(data[i_y,i_x]):
			if key_show == 'GPSA':
				data[i_y, i_x] = GPSA_data_list[i] * mutiplier
			else:
				if isinstance(key_show, str):
					data[i_y, i_x] = raw[key_show][i] * mutiplier
				else:
					data[i_y, i_x] = raw[key_show[0]][i, key_show[1]] * mutiplier

		if Z_cut is not None and Z[i]<Z_cut:
			data[i_y, i_x] = float('nan')
		else:
			if math.isnan(data[i_y, i_x]):
				data[i_y, i_x] = 0
		Zmat[i_y, i_x] = Z[i]


	print 'plotting'

	colors = ['k','w']
	lw = [1,2]
	if Z_contour is not None:
		for i_v in range(len(Z_contour)):
			ax.contour(Zmat, [Z_contour[0][i_v]], colors=colors[i_v], linewidths=lw[i_v])


	#imsave(key_show+'.png',data)
	print 'cmap = '+str(cmap)	
	if clim is None:
		im = ax.imshow(data, cmap=cmap)
	else:
		im = ax.imshow(data, clim=clim, cmap=cmap)

	ax.set_xlim(0,len(xx))
	ax.set_ylim(0,len(yy))

	if 'axis' in key_x:
		xx = [1000*xi for xi in xx]

	if 'axis' in key_y:
		yy = [1000*yi for yi in yy]

	ax.set_xticklabels(find_labels(ax.get_xticks(), xx))
	ax.set_yticklabels(find_labels(ax.get_yticks(), yy))

	return im

	#if colorbar:
	#	ax.set_colorbar()
	
	#return data.min(), data.max()
	#plt.show()







def show_2D_GPSA(raw, GPSA_data_list, 
	key_x='axis0', key_y='axis1',
	clim=None, cmap='jet', 
	mutiplier=1.0,
	Z_cut=None,
	Z_contour=([],[]),
	):

	x = raw[key_x]
	y = raw[key_y]
	Z = raw['mixture fraction']

	xx = sorted(list(set(x)))
	yy = sorted(list(set(y)))

	n_x = len(xx)
	n_y = len(yy)

	print 'n_x = '+str(n_x)
	print 'n_y = '+str(n_y)

	if n_x*n_y == 0:
		print 'cannot build as n_x = '+str(n_x)+', n_y = '+str(n_y)
		print 'raw = '+str(raw)
		return


	print 'building matrix'
	data = np.zeros((n_y,n_x))
	Zmat = np.zeros((n_y,n_x))

	for i in range(len(x)):
		i_y = yy.index(y[i])
		i_x = xx.index(x[i])
		#if raw['active species'][i]>5:
		if Z_cut is not None and Z[i]<Z_cut:
			data[i_y, i_x] = float('nan')
		else:
			data[i_y, i_x] = GPSA_data_list[i] * mutiplier
		Zmat[i_y, i_x] = Z[i]

	print 'plotting'


	colors = ['k','w']
	lw = [1,3]
	if len(Z_contour)>0:
		for i_v in range(len(Z_contour)):
			CS = plt.contour(Zmat, [Z_contour[0][i_v]], colors=colors[i_v], linewidths=lw[i_v])
			#plt.clabel(CS, fontsize=10, inline=1, fmt=Z_contour[1][i_v])
	#plt.legend(Z_contour[1])

	#imsave(key_show+'.png',data)
	if clim is None:
		plt.imshow(data, cmap=cmap)
	else:
		plt.imshow(data, clim=clim, cmap=cmap)

	plt.colorbar()
	
	#plt.show()








if __name__ == '__main__':

	prj_name = 'GRI'
	#name = 'SKEext2D'
	name = 'GRIign2D'

	cti = os.path.join(prj_name,'detailed','mech','chem.cti')
	soln = ct.Solution(cti)

	sp = 'N2'; key = ('mass_fraction',soln.species_names.index(sp)); s_key = key[0]+'_'+sp


	filename = os.path.join(prj_name,'detailed','raw',name+'.dat')
	raw = DNS2raw(filename, soln)
	#show_2D(raw, 'temperature', clim=(400,2000))
	show_2D(raw, key)

	fld_plot = os.path.join(prj_name,'plot')
	if not os.path.exists(fld_plot):
		os.makedirs(fld_plot)
	plt.savefig(os.path.join(fld_plot,name+'_'+s_key+'.png'))
