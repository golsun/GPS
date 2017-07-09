name = 'therm_PRF.dat'
fin = open(name,'r')
fout = open(name+'_upper','w')

for line in fin:
	fout.write(line.upper())

