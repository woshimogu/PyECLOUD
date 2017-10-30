import numpy as np
import sec_emission
import hist_for as histf
import seg_impact as segi
import impact_management_class


class impact_management_furman_pivi(impact_management_class.impact_management):
    def __init__(self, switch_no_increase_energy, chamb, sey_mod, E_th, sigmafit, mufit,
                 Dx_hist, scrub_en_th, Nbin_En_hist, En_hist_max, thresh_low_energy=None, flag_seg=False,
                 cos_angle_width=0.05, flag_cos_angle_hist=True,  secondary_angle_distribution=None):

        super(self, impact_management_furman_pivi).__init__(
            self, switch_no_increase_energy, chamb, sey_mod, E_th, sigmafit, mufit, Dx_hist, scrub_en_th,
            Nbin_En_hist, En_hist_max, thresh_low_energy, flag_seg, cos_angle_width, flag_cos_angle_hist,
            secondary_angle_distribution)


    def backtrack_and_second_emiss(self, old_pos, MP_e):
        self.Nel_impact_last_step=0.
        self.Nel_emit_last_step=0.
        self.En_imp_last_step_eV=0.
        self.En_emit_last_step_eV=0.

        if MP_e.N_mp>0:

            switch_no_increase_energy = self.switch_no_increase_energy
            x_mp_old = old_pos.x_mp
            y_mp_old = old_pos.y_mp
            z_mp_old = old_pos.z_mp
            x_mp = MP_e.x_mp
            y_mp = MP_e.y_mp
            z_mp = MP_e.z_mp
            vx_mp = MP_e.vx_mp
            vy_mp = MP_e.vy_mp
            vz_mp = MP_e.vz_mp
            nel_mp = MP_e.nel_mp
            N_mp_old = MP_e.N_mp
            nel_mp_th = MP_e.nel_mp_split
            chamb = self.chamb
            sey_mod = self.sey_mod
            E_th = self.E_th
            sigmafit = self.sigmafit
            mufit = self.mufit
            bias_x_hist = self.bias_x_hist
            Dx_hist = self.Dx_hist
            En_hist_max = self.En_hist_max
            DEn_hist = self.DEn_hist
            flag_seg = self.flag_seg
            scrub_en_th = self.scrub_en_th
            thresh_low_energy = self.thresh_low_energy

            me = MP_e.mass
            qe = np.abs(MP_e.charge)
            qm = qe/me

            ## impact management

            flag_impact = np.zeros_like(x_mp, dtype=bool)
            self.flag_impact = flag_impact

            # detect impact
            flag_impact[:N_mp_old]=chamb.is_outside(x_mp[0:N_mp_old],y_mp[0:N_mp_old])

            Nimpact=int(np.sum(flag_impact))

            if Nimpact>0:

                if flag_seg:
                    i_found_new_mp = 0*x_mp

                # load segment endpoints
                x_in=x_mp_old[flag_impact[:N_mp_old]]
                y_in=y_mp_old[flag_impact[:N_mp_old]]
                z_in=z_mp_old[flag_impact[:N_mp_old]]
                x_out=x_mp[flag_impact]
                y_out=y_mp[flag_impact]
                z_out=z_mp[flag_impact]

                # backtracking and surface normal generation
                [x_emit,y_emit,z_emit,Norm_x,Norm_y, i_found]=\
                    chamb.impact_point_and_normal(x_in, y_in, z_in, x_out, y_out, z_out)

                # load velocities and charges
                vx_impact = vx_mp[flag_impact]
                vy_impact = vy_mp[flag_impact]
                vz_impact = vz_mp[flag_impact]
                vx_emit   = np.zeros_like(vx_impact)
                vy_emit   = np.zeros_like(vy_impact)
                vz_emit   = np.zeros_like(vz_impact)
                nel_impact = nel_mp[flag_impact]

                # compute impact velocities, energy and angle
                v_impact_mod=np.sqrt(vx_impact*vx_impact+vy_impact*vy_impact+vz_impact*vz_impact)
                E_impact_eV=0.5/qm*v_impact_mod*v_impact_mod
                v_impact_n=vx_impact*Norm_x+vy_impact*Norm_y
                # Use np.abs to rule out negative values, which can happen in very seldom fringe cases.
                # Mathematically correct would be -(v_impact_n)/v_impact_mod
                costheta_impact = np.abs(v_impact_n/v_impact_mod)

                #electron histogram
                histf.compute_hist(x_emit, nel_impact,bias_x_hist,Dx_hist,self.nel_impact_hist_tot)
                histf.compute_hist(x_emit, nel_impact*(E_impact_eV>scrub_en_th),bias_x_hist,Dx_hist,self.nel_impact_hist_scrub)
                histf.compute_hist(x_emit, nel_impact*E_impact_eV,bias_x_hist,Dx_hist,self.energ_eV_impact_hist)

                # angle histogram
                if self.flag_cos_angle_hist:
                    histf.compute_hist(costheta_impact, nel_impact, 0., self.cos_angle_width, self.cos_angle_hist)

                if flag_seg:
                    segi.update_seg_impact(i_found,nel_impact,self.nel_hist_impact_seg)#riga incriminata???
                    segi.update_seg_impact(i_found,nel_impact*E_impact_eV,self.energ_eV_impact_seg)


                En_imp_hist=E_impact_eV.copy()
                En_imp_hist[En_imp_hist>En_hist_max]=En_hist_max
                histf.compute_hist(En_imp_hist,nel_impact,0.,DEn_hist,self.En_hist_line)

                nel_emit, flag_elast, flag_backscattered, flag_truesec = \
                    sey_mod.SEY_process(nel_impact,E_impact_eV, costheta_impact, i_found)

                self.Nel_impact_last_step=np.sum(nel_impact)
                self.Nel_emit_last_step=np.sum(nel_emit)

                self.En_imp_last_step_eV=np.sum(E_impact_eV*nel_impact)


                # elastic reflection (only velocities are affected)
                vx_emit[flag_elast]=vx_impact[flag_elast]-2*v_impact_n[flag_elast]*Norm_x[flag_elast]
                vy_emit[flag_elast]=vy_impact[flag_elast]-2*v_impact_n[flag_elast]*Norm_y[flag_elast]
                vz_emit[flag_elast]=vz_impact[flag_elast]


                # true secondary
                N_true_sec = np.sum(flag_truesec)
                if N_true_sec == 0:
                    n_add_total = 0
                    N_mp_new = N_mp_old
                else:
                    n_add = np.zeros_like(flag_truesec, dtype=int)
                    n_add[flag_truesec]=np.ceil(nel_emit[flag_truesec]/nel_mp_th)-1
                    n_add[n_add<0]=0. #in case of underflow
                    nel_emit[flag_truesec]=nel_emit[flag_truesec]/(n_add[flag_truesec]+1.)

                    n_add_total = np.sum(n_add)
                    N_mp_new = N_mp_old + n_add_total

                    # replace impacted MPs that are not reflected
                    En_truesec_eV = sec_emission.hilleret_model2(
                        switch_no_increase_energy, N_true_sec, sigmafit, mufit, E_th, E_impact_eV[flag_truesec], thresh_low_energy)
                    vx_emit[flag_truesec], vy_emit[flag_truesec], vz_emit[flag_truesec] = self.angle_dist_func(
                        N_true_sec, En_truesec_eV, Norm_x[flag_truesec], Norm_y[flag_truesec])

                    # Add new MPs
                    if n_add_total != 0:
                        # Clone MPs
                        x_mp_add = np.repeat(x_emit, n_add)
                        y_mp_add = np.repeat(y_emit, n_add)
                        z_mp_add = np.repeat(z_emit, n_add)
                        norm_x_add = np.repeat(Norm_x, n_add)
                        norm_y_add = np.repeat(Norm_y, n_add)
                        nel_mp_add = np.repeat(nel_emit, n_add)
                        E_impact_eV_add = np.repeat(E_impact_eV, n_add)

                        # Generate new MP properties, angles and energies
                        En_truesec_eV_add = sec_emission.hilleret_model2(
                            switch_no_increase_energy, n_add_total, sigmafit, mufit, E_th, E_impact_eV_add, thresh_low_energy)
                        vx_mp_add, vy_mp_add, vz_mp_add = self.angle_dist_func(
                            n_add_total, En_truesec_eV_add, norm_x_add, norm_y_add)

                        MP_e.add_new_MPs(n_add_total, nel_mp_add, x_mp_add, y_mp_add, z_mp_add,
                                         vx_mp_add, vy_mp_add, vz_mp_add)

                        if flag_seg:
                            i_found_new_mp[N_mp_old:N_mp_new] = np.repeat(i_found, n_add)


                x_mp[flag_impact]  = x_emit
                y_mp[flag_impact]  = y_emit
                z_mp[flag_impact]  = z_emit
                vx_mp[flag_impact] = vx_emit
                vy_mp[flag_impact] = vy_emit
                vz_mp[flag_impact] = vz_emit
                nel_mp[flag_impact]= nel_emit

                #subtract replaced macroparticles
                v_emit_mod = np.sqrt(vx_emit**2+vy_emit**2+vz_emit**2)
                E_emit_eV=0.5/qm*v_emit_mod*v_emit_mod
                histf.compute_hist(x_emit,-nel_emit*E_emit_eV,bias_x_hist,Dx_hist,self.energ_eV_impact_hist)

                if flag_seg:
                    segi.update_seg_impact(i_found,-nel_emit*E_emit_eV,self.energ_eV_impact_seg)

                self.En_emit_last_step_eV=np.sum(E_emit_eV*nel_emit)

                #subtract new macroparticles
                if n_add_total > 0:
                    wei =-nel_mp_add*En_truesec_eV_add
                    histf.compute_hist(x_mp_add,wei,bias_x_hist,Dx_hist,self.energ_eV_impact_hist)

                    if flag_seg:
                        segi.update_seg_impact(i_found_new_mp[N_mp_old:N_mp_new],wei,self.energ_eV_impact_seg)

                    self.En_emit_last_step_eV += np.sum(En_truesec_eV_add*nel_mp_add)

        return MP_e
