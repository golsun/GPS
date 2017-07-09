import cantera as ct
import numpy as np
import matplotlib.pyplot as plt
import copy
from def_ct_tools import *
import sys
import os


def psr_ss(soln_in, soln_out, p, T0, T, X0, X, tau):

    """
    find the steady state of a PSR

    :param mech:    mechanism
    :param p:       pressure (Pa)
    :param T0:      temperature (K) of the inlet flow
    :param T:       initial temperature (K) of the reactor
    :param tau:     residence time (s) of the reactor

    :return reactor:

    """

    vol = 1.0     # unit: m3
    K = 1.0
    t_end = tau * 100.0

    #print 't_end = '+str(t_end)

    soln_out.TPX = T, p, X
    soln_in.TPX = T0, p, X0

    inlet = ct.Reservoir(soln_in)
    reactor = ct.IdealGasReactor(soln_out)
    reactor.volume = vol

    vdot = vol/tau
    mdot = soln_out.density * vdot
    mfc = ct.MassFlowController(inlet, reactor, mdot=mdot)

    exhaust = ct.Reservoir(soln_out)
    valve = ct.Valve(reactor, exhaust, K=K)

    network = ct.ReactorNet([reactor])
    try:
        network.advance(t_end)
    except RuntimeError as e:

        print '@'*10+'\nct.exceptions = \n'+str(e)
        #sys.exit()
        return None

    return soln_out


def S_curve(soln_in, soln_out, atm, T0, X0, dir_raw=None):

    #raise

    print '>'*30
    print 'psr for ['+ X0 + '] at '+ str(atm)+'atm' + ' and '+str(T0)+'K'
    print '<'*30

    if soln_in.n_species > 100:
        verbose = True
    else:
        verbose = False


    p = ct.one_atm * atm

    dT_turn = 500.0
    dT_froze = 50.0
    dT_try = 10.0

    status = 0

    tau = 1
    #tt = []
    #TT = []
    raw = None
    T_ini = 2500
    T_burn = None
    tau_burn = tau
    X_ini = X0

    tau_r = 0.5

    #soln_in = ct.Solution(mech)
    #soln_out = ct.Solution(mech)

    while True:

        soln_i = psr_ss(soln_in, soln_out, p, T0, T_ini, X0, X_ini, tau)
        if soln_i is None:
            break

        T = soln_i.T
        X = soln_i.concentrations
        if verbose:
            print str(int(T_ini)) + ', ' + str(int(T)) + ', ' + str(tau)
        if T_burn is None:
            T_burn = T

        if abs(T_burn - T) > 50:
            # if extinction happens or dT too large
            
            if tau_r > 0.999:
                if verbose:            
                    print 'finished, tau_r = '+str(tau_r)
                break
            else:
                tau = tau_burn
                tau_r = tau_r + (1-tau_r)*0.5
                if verbose:            
                    print 'refined, tau_r = '+str(tau_r)
        else:
            T_burn = T
            X_ini = X
            tau_burn = tau

            raw = soln2raw(tau, 'residence_time', soln_i, raw)
            save_raw_npz(raw, os.path.join(dir_raw,'raw_temp.npz'))

        T_ini = T_burn
        tau *= tau_r

    raw = save_raw_npz(raw, os.path.join(dir_raw,'raw.npz'))
    save_raw_csv(raw, soln_in, dir_raw)

    return raw



def test_single_eq():

    mech = 'gri30.xml'
    p = ct.one_atm * 5;     # Pa
    T0 = 500.0;
    tau = 1;
    T = 3000;
    X = 'CH4:1, O2:2, N2:7.52';

    soln = psr_ss(mech, p, T0, T, X, X, tau)
    print soln.T


def test_S_curve():

    T0 = 500.0;
    X0 = 'CH4:1, O2:2, N2:7.52';
    atm = 1

    soln_in = ct.Solution('gri30.xml')
    soln_out = ct.Solution('gri30.xml')
    raw = S_curve(soln_in, soln_out, atm, T0, X0, path_raw='psr.npz')

    tt = raw['axis0']
    TT = raw['temperature']

    #print raw[0].T
    #print raw[-1].T

    plt.semilogx(tt, TT, marker='o')
    plt.savefig('S_curve.jpg')

if __name__=="__main__":
    #test_single_eq()
    test_S_curve()