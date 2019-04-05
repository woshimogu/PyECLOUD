import sys
if '../..' not in sys.path:
    sys.path.append('../..')
import numpy as np
import matplotlib.pyplot as plt
import sec_emission_model_furman_pivi as fp
import mystyle as ms
from scipy.constants import e as qe

plt.close('all')
ms.mystyle(12)
linewid = 2

me = 9.10938356e-31


def del_elas_ECLOUD(energy, R_0=0.7, E_max=332., E_0=150.):
    del_elas = R_0 * ((np.sqrt(energy) - np.sqrt(energy + E_0)) / (np.sqrt(energy) + np.sqrt(energy + E_0)))**2
    return del_elas


def del_true_ECLOUD(energy, del_max, s=1.35, E_max=332.):
    x = energy / E_max
    del_true = del_max * s * x / (s - 1 + x**s)
    return del_true


furman_pivi_surface_tweaked = {'conserve_energy': True,
                               'exclude_rediffused': False,
                               'choice': 'poisson',
                               'M_cut': 10,
                               'p_n': np.array([2.5, 3.3, 2.5, 2.5, 2.8, 1.3, 1.5, 1.5, 1.5, 1.5]),
                               'eps_n': np.array([1.5, 1.75, 1., 3.75, 8.5, 11.5, 2.5, 3., 2.5, 3.]),
                               # Parameters for backscattered electrons
                               'p1EInf': 0.002158,  # Changed this
                               'p1Ehat': 0.709633,  # Changed this
                               'eEHat': 0.,
                               'w': 46.028959,  # Changed this
                               'p': 0.468907,  # Changed this
                               'e1': 0.,  # Changed this
                               'e2': 2.,
                               'sigmaE': 2.,
                               # Parameters for rediffused electrons
                               'p1RInf': 0.2,
                               'eR': 0.041,
                               'r': 0.104,
                               'q': 0.5,
                               'r1': 0.26,
                               'r2': 2.,
                               # Parameters for true secondaries
                               'deltaTSHat': 1.8848,
                               'eHat0': 332.,
                               's': 1.35,
                               't1': 0.727814,  # Changed this
                               't2': 0.69333,  # Changed this
                               't3': 0.7,
                               't4': 1.,
                               }

furman_pivi_surface_LHC = {'conserve_energy': False,
                           'exclude_rediffused': False,
                           'choice': 'poisson',
                           'M_cut': 10,
                           'p_n': np.array([2.5, 3.3, 2.5, 2.5, 2.8, 1.3, 1.5, 1.5, 1.5, 1.5]),
                           'eps_n': np.array([1.5, 1.75, 1., 3.75, 8.5, 11.5, 2.5, 3., 2.5, 3.]),
                           # Parameters for backscattered electrons
                           'p1EInf': 0.02,
                           'p1Ehat': 0.496,
                           'eEHat': 0.,
                           'w': 60.86,
                           'p': 1.,
                           'e1': 0.26,
                           'e2': 2.,
                           'sigmaE': 2.,
                           # Parameters for rediffused electrons
                           'p1RInf': 0.2,
                           'eR': 0.041,
                           'r': 0.104,
                           'q': 0.5,
                           'r1': 0.26,
                           'r2': 2.,
                           # Parameters for true secondaries
                           'deltaTSHat': 1.8848,
                           'eHat0': 332.,
                           's': 1.35,
                           't1': 0.5,  # t1 and t2 based on taylor expansion
                           't2': 1.,   # of PyECLOUD formula for E_max(theta)
                           't3': 0.7,
                           't4': 1.,
                           }

furman_pivi_surface = {'conserve_energy': False,
                       'exclude_rediffused': False,
                       'choice': 'poisson',
                       'M_cut': 10,
                       'p_n': np.array([2.5, 3.3, 2.5, 2.5, 2.8, 1.3, 1.5, 1.5, 1.5, 1.5]),
                       'eps_n': np.array([1.5, 1.75, 1., 3.75, 8.5, 11.5, 2.5, 3., 2.5, 3.]),
                       'p1EInf': 0.02,
                       'p1Ehat': 0.496,
                       'eEHat': 0.,
                       'w': 60.86,
                       'p': 1.,
                       'e1': 0.26,
                       'e2': 2.,
                       'sigmaE': 2.,
                       'p1RInf': 0.2,
                       'eR': 0.041,
                       'r': 0.104,
                       'q': 0.5,
                       'r1': 0.26,
                       'r2': 2.,
                       'deltaTSHat': 1.8848,
                       'eHat0': 276.8,
                       's': 1.54,
                       't1': 0.66,
                       't2': 0.8,
                       't3': 0.7,
                       't4': 1.,
                       }


secondary_angle_distribution = 'cosine_3D'

sey_mod = fp.SEY_model_furman_pivi(E_th=35., sigmafit=1.0828, mufit=1.6636, secondary_angle_distribution=secondary_angle_distribution,
                                   switch_no_increase_energy=0, thresh_low_energy=-1,
                                   furman_pivi_surface=furman_pivi_surface_tweaked)


def extract_emission_angles(n_rep, E_impact_eV_test, cos_theta_test, charge, mass):
    """
    This function should be used for testing and development. It calculates the
    emision angles when impacting on a surface in the y-z plane. Returns an
    array containing n_rep emission angles corresponding to n_rep MPs that have
    been allowed to impact on the surface.
    """
    print('Extracting Emission angles...')
    for i_ct, ct in enumerate(cos_theta_test):
        for i_ene, Ene in enumerate(E_impact_eV_test):

            nel_impact = np.ones(n_rep)
            # Assuming normal is along x
            v_mod = np.sqrt(2 * Ene * qe / mass) * np.ones_like(nel_impact)
            vx = v_mod * ct
            vy = v_mod * np.sqrt(1 - ct * ct)

            nel_emit_tot_events, event_type, event_info,\
                nel_replace, x_replace, y_replace, z_replace, vx_replace, vy_replace, vz_replace, i_seg_replace,\
                nel_new_MPs, x_new_MPs, y_new_MPs, z_new_MPs, vx_new_MPs, vy_new_MPs, vz_new_MPs, i_seg_new_MPs =\
                sey_mod.impacts_on_surface(
                    mass=mass, nel_impact=nel_impact, x_impact=nel_impact * 0, y_impact=nel_impact * 0, z_impact=nel_impact * 0,
                    vx_impact=vx * np.ones_like(nel_impact),
                    vy_impact=vy * np.ones_like(nel_impact),
                    vz_impact=nel_impact * 0,
                    Norm_x=np.ones_like(nel_impact), Norm_y=np.zeros_like(nel_impact),
                    i_found=np.int_(np.ones_like(nel_impact)),
                    v_impact_n=vx * np.ones_like(nel_impact),
                    E_impact_eV=Ene * np.ones_like(nel_impact),
                    costheta_impact=ct * np.ones_like(nel_impact),
                    nel_mp_th=1,
                    flag_seg=True)

            # Computing emission angles
            vx_all = np.concatenate((vx_replace, vx_new_MPs))
            vy_all = np.concatenate((vy_replace, vy_new_MPs))
            vz_all = np.concatenate((vz_replace, vz_new_MPs))

            Norm_x = np.ones_like(vx_all)
            Norm_y = np.zeros_like(vx_all)

            divider = np.sqrt(
                (vx_all * vx_all + vy_all * vy_all + vz_all * vz_all) * (Norm_x * Norm_x + Norm_y * Norm_y))
            flag_divide_by_zero = divider != 0
            # import pdb; pdb.set_trace()
            cos_theta_emit = (vx_all[flag_divide_by_zero] * Norm_x[flag_divide_by_zero] + vy_all[flag_divide_by_zero] * Norm_y[flag_divide_by_zero]) / np.sqrt(
                (vx_all[flag_divide_by_zero]**2 + vy_all[flag_divide_by_zero]**2 + vz_all[flag_divide_by_zero]**2) * (Norm_x[flag_divide_by_zero]**2 + Norm_y[flag_divide_by_zero]**2))

    print('Done extracting emission angles.')

    return cos_theta_emit


cos_theta_test = np.array([0.7])
E_impact_eV_test = np.array(list(np.arange(0, 499., 5.)) + list(np.arange(500., 2000, 25.)))
E_impact_eV_test = np.array([300.])
n_rep = int(5e5)

cos_theta_emit = extract_emission_angles(n_rep, E_impact_eV_test, cos_theta_test, charge=qe, mass=me)


plt.close('all')
ms.mystyle_arial(25)

# Emission angles
plt.figure(1, facecolor='white', figsize=(12, 9))
plt.hist(cos_theta_emit, density=True, bins=60)
plt.xlabel(r'cos($\theta_{emit}$)')
plt.title('cos_theta_imp=%.2f' % cos_theta_test)
plt.ylabel('Normalized emission angle spectrum')

plt.figure(2, facecolor='white', figsize=(12, 9))
plt.hist(np.arccos(cos_theta_emit), density=True, bins=60)
plt.xlabel(r'$\theta_{emit}$')
plt.ylabel('Normalized emission angle spectrum')
plt.title('cos_theta_imp=%.2f' % cos_theta_test)


plt.show()