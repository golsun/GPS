name = 'chem.inp'

with open(name,'r') as f:
	lines = f.readlines()

with open(name+'.upper','w') as f:
	for line in lines:
		f.write(line.upper())