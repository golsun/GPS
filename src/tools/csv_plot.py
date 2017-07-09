from ck_data_reader import *
sys.path.append(os.getcwd().replace('tools','post'))
from def_plt_tools import rename_species, rename_reaction

plt.rc('font', **{'family':'Times New Roman'})


def plot_basic(raw, MF, sp_list, x_type, ax_T, ax_sp):

	x = raw['axis0']
	T = raw['temperature']

	x_plot = x
	ax_T.plot(x_plot, T,'k')

	ls = ['-','--']

	for i_sp in range(len(sp_list)):
		sp = sp_list[i_sp]
		ax_sp.plot(x_plot, MF[sp],'k', linestyle=ls[i_sp], label=rename_species(sp))

	return ax_T, ax_sp




def plot_rop(raw, ROP, group, ax, i_end=None):
	n = len(raw['axis0'])
	x = raw['axis0']
	T = raw['temperature']

	if i_end is None:
		i_end = n

	x_plot = x

	ls = ['-','--',':','-.']

	total = []
	for i in range(n):
		total.append(sum([ROP[k][i] for k in ROP.keys()]))

	print 'cutted at i_end = '+str(i_end)

	dx = [x[i]-x[i-1] for i in range(1,n)] + [0]

	n_group = len(group)
	sum_per_group = [0]*n_group
	for i_group in range(n_group):
		y = [0]*n
		for i_rxn in group[i_group]['rxn']:
			if str(i_rxn) in ROP.keys():
				y = [y[i] + 100.0 * ROP[i_rxn][i]/total[i] for i in range(n)]
				sum_per_group[i_group] += sum([ROP[i_rxn][i]*dx[i] for i in range(n)])

		ax.plot(x_plot[:i_end], y[:i_end], label=group[i_group]['label'], color='k', linestyle=ls[i_group])
		

	sum_sum = sum(sum_per_group)
	for i_group in range(n_group):
		print 'total for '+group[i_group]['label']+' = '+str(100.0*sum_per_group[i_group]/sum_sum)

	return ax





def plot_T_vs_fuel():

	fuels = ['C2H4','C3H6','CH4']
	ls = ['-','--',':','-.']

	nsub = 2
	f, axs = plt.subplots(nsub,1, sharex=True, figsize=(5.6, nsub*2.2))

	for i_fuel in range(len(fuels)):
		fuel = fuels[i_fuel]
		path = os.path.join('csv', fuel+'.csv')
		raw, MF, trash, trash = csv2raw(path, 'time')
		T = raw['temperature']
		axs[0].plot(T, [t*1000 for t in raw['axis0']], linestyle=ls[i_fuel], label=rename_species(fuel), color='k')
		axs[1].plot(T, [100.0*(1-mf/MF['O3'][0]) for mf in MF['O3']], linestyle=ls[i_fuel], label=rename_species(fuel), color='k')


	axs[0].text(200,)



	axs[0].legend(frameon=False, loc='upper center', fontsize=10, handlelength=3)
	axs[0].set_ylabel('Time (ms)')
	axs[1].set_ylabel(rename_species('O3')+' consumption (%)')
	axs[1].set_xlabel('Temperature (K)')
	axs[1].set_ylim(0,119)
	plt.tight_layout()
	plt.subplots_adjust(hspace=0)
	plt.savefig(os.path.join('csv','T_vs_fuel.eps'))






def plot_TspROP():

	name = 'plug_O3ign_adiabatic'
	path_basic = os.path.join('csv', name+'.csv')
	path_rop = os.path.join('csv', name+'_O3rop.csv')
	sp_list = ['C2H4','O3']
	x_type = 'Distance (cm)'

	group = [
		{'rxn':[str(i) for i in range(800,804)],'label':'ozonolysis'},
		{'rxn':[str(i) for i in range(785,793)],'label':rename_species('O3')+' decomposition'},
		{'rxn':[str(i) for i in range(793,800)],'label':'other'},
		#{'rxn':['785','786','787','788','791','792'],'label':rename_species('O3')+' decomposition'},
		#{'rxn':[str(i) for i in range(793,800)]+['789','790'],'label':'other'},
		]


	x_type_trim = x_type.split(' ')[0].lower()
	raw, MF, NRR, trash = csv2raw(path_basic, x_type_trim)
	trash1, trash2, trash3, ROP = csv2raw(path_rop, x_type_trim)

	T = raw['temperature']
	O3 = MF['O3']
	for i in range(len(O3)):
		if O3[i] < 0.01*O3[0]:
			i_O3_end = i
			break

	print O3[0]

	print 'cutted at i_O3_end = '+str(i_O3_end)
	print 'O3 = '+str(O3[i_O3_end])
	print 'T = '+str(T[i_O3_end])
	



	nsub = 3
	f, axs = plt.subplots(nsub,1, sharex=True, figsize=(5.6, nsub*1.8))

	plot_basic(raw, MF, sp_list, x_type, axs[0], axs[1])
	plot_rop(raw, ROP['O3'], group, axs[2], i_O3_end)

		
	axs[0].set_ylim(T[0]-90, max(T)+90)
	axs[1].set_ylim(-0.009,0.069)
	axs[-1].set_ylim(0,109)
	axs[-1].set_xlim(-5,35)
	#axs[-1].set_ylim(1e-5,1e-2)

	axs[1].set_yticks([0,0.02,0.04,0.06])


	axs[1].legend(frameon=False, loc='upper right', fontsize=10, handlelength=3)
	axs[2].legend(frameon=False, loc='right', fontsize=10, handlelength=3)

	axs[0].set_ylabel('Temperature (K)')
	axs[1].set_ylabel('Mole fraction')
	axs[2].set_ylabel('Contribution (%)\nto O'+r'$_3$'+' consumption')
	axs[-1].set_xlabel(x_type)

	plt.tight_layout()
	plt.subplots_adjust(hspace=0)
	plt.savefig(path_basic.replace('.csv','new.eps'))




if __name__ == '__main__':
	plot_TspROP()
	#plot_T_vs_fuel()