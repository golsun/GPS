
import matplotlib.pyplot as plt
import numpy as np







def rename_species(sp, rename={}):
	sp = str(sp).strip()#.strip('-')
	kk = [str(k) for k in rename.keys()]
	if sp in kk:
		sp = rename[sp]
	else:
		ever_upper = False
		for c in sp:
			if c.isalpha() and c.upper() == c:
				ever_upper = True
				break
		if not ever_upper:
			sp = sp.upper()

	s = ''
	started = False
	for c in sp:
		a = c
		if c.isdigit():
			if started:
				a = r'$_'+c+'$'
		else:
			started = True
		s += a
	return s


def rename_reaction(rxn, rename={}):
	rxn = str(rxn).replace('<','').replace('>','').strip('-')
	ss = rxn.split(' ')
	rxn_new = ''
	for sp in ss:
		rxn_new += rename_species(sp,rename)
	return rxn_new






def opt_lim(ax, axis, scale):

	if axis == 'x':
		lim_auto = ax.get_xlim()
	else:
		lim_auto = ax.get_ylim()

	if scale == 'linear':
		l = lim_auto[1] - lim_auto[0]
		if axis == 'x':
			lim0 = lim_auto[0] - l * 0.14
			lim1 = lim_auto[1] + l * 0.09
		else:
			lim0 = lim_auto[0] - l * 0.09
			lim1 = lim_auto[1] + l * 0.14


	else:
		l = np.log(lim_auto[1]) - np.log(lim_auto[0])

		if axis == 'x':
			lim0 = lim_auto[0] / np.exp(l * 0.14)
			lim1 = lim_auto[1] * np.exp(l * 0.09)
		else:
			lim0 = lim_auto[0] / np.exp(l * 0.09)
			lim1 = lim_auto[1] * np.exp(l * 0.14)


	lim = [lim0, lim1]
	return lim





def test_lim():
	f, axarr = plt.subplots(2, 1, sharex='all')
	axarr[0].plot([1,2,3],[10,20,30])
	axarr[1].semilogy([1,2,3],[10,2000,300])

	plt.savefig('before_opt.eps')

	axarr[0].set_ylim(opt_lim(axarr[0],'y','linear'))
	axarr[1].set_ylim(opt_lim(axarr[1],'y','log'))
	axarr[1].set_xlim(opt_lim(axarr[1],'x','linear'))


	plt.savefig('after_opt.eps')





def opt_str(s0, max_l=15):

	ss = s0.split(' ')
	if bool(ss) == False:
		return ''

	s1 = ''
	ln = ''
	for s in ss:
		if len(ln) + len(s) <= max_l:
			ln += (' ' + s)
		else:
			s1 += ('\n' + ln.strip())
			ln = s
		
	ln = ln.strip()
	if bool(ln):
		s1 += ('\n' + ln)

	s1 = s1[1:]
	return s1



def test_str():
	s0 = 'GP radical net production rate (mole/cm3-s)'
	print opt_str(s0)


if __name__ == '__main__':
	rename = {
	
	'NC7H16':'nC7H16',
	'C7H15-2':'C7H15',
	'C7H15O2-2':'C7H15O2',
	'C7H14OOH2-4':'C7H14OOH',
	'C7H14OOH2-4O2':'C7H14OOHO2',
	'NC7KET24':'NC7KET',

	}

	rxn = 'NC7H16 + OH => C7H15-2 + H2O'.lower()
	rxn_show = rename_reaction(rxn, rename)
	plt.text(0,0,rxn_show)
	plt.show()

