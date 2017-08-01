import os
from src.ck.def_cheminp import skeletal

detailed_folder = os.path.join('ignored','usc ii')
sk_folder = os.path.join('ignored','usc ii 14')
species_kept = ['CH4', 'CH3', 'CH2O', 'HCO', 'CO', 'H', 'O', 'O2', 'OH', 'H2O', 'CO2', 'H2O2', 'HO2']

skeletal(detailed_folder, sk_folder, species_kept)
