import numpy as np
import pandas as pd
import sys
import calendar

import numpy.ma as ma

from glob import glob
from datetime import date, datetime, timedelta

from rpn.rpn import RPN
from rpn.domains.rotated_lat_lon import RotatedLatLon
from rpn import level_kinds

from netCDF4 import Dataset
import time

'''
Check the inversions in each output step, separating by inversions from radiative cooling and others (warm-air advection, subsidence, and others)
Saves the mean value for each output time. 0h/3h/6h/9h/12h/15h/18h/21h Z

Read:
    - LW
    - SW
    - HeatFlux
    - Clouds
    - TT

Saves:
   - Inversion between 925hpa and 1000hPa. Inversion between 925hPa and 2m temperature
   - For all times, 00UTC and 12UTC

Check:
    - if a inversion is present, check for radiative cooling and if SW is positive or 0. if yes, add to the radiative cooling type. if not, add to other types
    - if a inversion is present, also check for cloud. if cloud fraction less than 0.2, count as clear sky. Add LW value to the clear sky type.

    - Relationship between inversions and wind: % and value for Inversions when wind higher/lower than X (define the X value) (to do)
'''


datai = 1985
dataf = 2015

# simulation
exp = "PanArctic_0.5d_ERAINT_NOCTEM_RUN"
#exp = "PanArctic_0.5d_CanHisto_NOCTEM_RUN"

main_folder = "/home/cruman/scratch/glacier2/GEM/Output/{0}".format(exp)
#main_folder = "/home/cruman/scratch/glacier/GEM/Output/{0}".format(exp)

eticket = "PAN_ERAI_DEF"
#eticket = "PAN_CAN85_CT"

#exp = "PanArctic_0.5d_CanHisto_NOCTEM_RUN"
#main_folder = "/glacier/caioruman/GEM/Output/{0}".format(exp)
#eticket = "PAN_CAN85_CT"

#r_MF = RPN("/glacier/caioruman/Data/Geophys/PanArctic0.5/pan_artic_mf_0.5")

#Z_surface = np.squeeze(r_MF.variables['MF'][:])

#r_MF.close()

def replace_nan(data):

    data[data == np.nan] = -999

    return data

def inversion_calculations(base_level_tt, top_level_tt):
    """
        Calculate Inversion Strengh, Inversion Frequency
    """

    # Inversion calculation, without other addons
    delta_T = top_level_tt - base_level_tt

    mean_dt_time = []
    mean_fr_time = []

    trange = np.arange(0,24,3)

    #Calculate means for each timestep output
    for i in trange:
        #print(i/3)
        ii = int(i/3)        

        aux = delta_T[ii::8,:,:]

        aux_fr_count = np.less_equal(aux, 0)
        aux_fr = np.count_nonzero(aux_fr_count.astype(np.int), axis=0)
        aux_fr = aux_fr/float(aux.shape[0])

        np.copyto(aux, aux.copy()*np.nan, where=aux_fr_count)
        aux = np.nanmean(aux, axis=0)
        mean_dt_time.append(aux)

        count_bool_dt = np.greater_equal(aux, 0)

        aux2 = count_bool_dt.copy()*np.nan
        np.copyto(aux_fr, aux2, where=~count_bool_dt)
        mean_fr_time.append(aux_fr)


    return mean_dt_time, mean_fr_time



def save_netcdf(fname, vars, datefield, lat, lon):

    # model to get lat/lon
    #file = "/HOME/caioruman/Scripts/PBL/Inversion/ERA/netcdf/netcdf_model.nc"
    file = "/home/cruman/Documents/HomeUQAM/Scripts/PBL/Inversion/ERA/netcdf/netcdf_model.nc"
    
    data = Dataset(file)
    # read lat,lon
    #lat = data.variables['lat'][:]
    #lon = data.variables['lon'][:]

    #print lon
    #lon = np.where(lon > 0, lon, lon + 360)

    nx = 172
    ny = 172
    tempo = 8
    data_tipo = "hours"

    # Precisa mudar para utilizar o caminho completo
    ncfile = Dataset('{0}'.format(fname), 'w')
    #varcontent.shape = (nlats, nlons)

    # Crio as dimensoes latitude, longitude e tempo
    ncfile.createDimension('x', nx)
    ncfile.createDimension('y', ny)
    ncfile.createDimension('time', tempo)

    # Crio as variaveis latitude, longitude e tempo
    # createVariable( NOMEVAR, TIPOVAR, DIMENSOES )
    lats_nc = ncfile.createVariable('lat', np.dtype("float32").char, ('y','x'))
    lons_nc = ncfile.createVariable('lon', np.dtype("float32").char, ('y','x'))
    time = ncfile.createVariable('time', np.dtype("float32").char, ('time',))

    # Unidades
    lats_nc.units = 'degrees_north'
    lats_nc._CoordinateAxisType = "Lat"
    lons_nc.units = 'degrees_east'
    lons_nc._CoordinateAxisType = "Lon"
    time.units = '{1} since {0}'.format(datefield.strftime('%Y-%m-%d %H:%M'), data_tipo)

    #Writing lat and lon
    lats_nc[:] = lat
    lons_nc[:] = lon

    # write data to variables along record (unlimited) dimension.
    # same data is written for each record.
    for var in vars:

        var_nc = ncfile.createVariable(var[0], np.dtype('float32').char, ('time', 'y', 'x'))
        var_nc.units = "some unit"
        var_nc.coordinates = "lat lon"
        var_nc.grid_desc = "rotated_pole"
        var_nc.cell_methods = "time: point"
        var_nc.missing_value = np.nan
        var_nc[:,:,:] = var[1]

    # close the file.
    ncfile.close()
    data.close()


# Open the monthly files
for yy in range(datai, dataf+1):

    for mm in range(1,13):

        # Pressure level file
        print(yy, mm)
        #if yy == 1979 and mm == 1:
        #    k = 1
        #else:
        k = 0

        print("{0}/Samples/{1}_{2}{3:02d}/dp*".format(main_folder, exp, yy, mm))
#        print k
        arq_dp = glob("{0}/Samples/{1}_{2}{3:02d}/dp*".format(main_folder, exp, yy, mm))[k]
        #print "{0}/Samples/{1}_{2}{3:02d}/dp*".format(main_folder, exp, yy, mm)
        #print arq_dp
        #sys.exit()

        # Surface file
        print("{0}/Samples/{1}_{2}{3:02d}/dm*".format(main_folder, exp, yy, mm))
        arq_dm = glob("{0}/Samples/{1}_{2}{3:02d}/dm*".format(main_folder, exp, yy, mm))[k]

        # Physics file
        arq_pm = glob("{0}/Samples/{1}_{2}{3:02d}/pm*".format(main_folder, exp, yy, mm))[k]


        r_dp = RPN(arq_dp)
#        r_pm = RPN(arq_pm)
        r_dm = RPN(arq_dm)


        # Temperature
        var = r_dp.get_4d_field('TT')
        dates_tt = list(sorted(var.keys()))
        #print(var[dates_tt[0]].keys())
        level_tt = [*var[dates_tt[0]].keys()]
        
        var_3d = []
        for key in level_tt:
          var_3d.append(np.asarray([var[d][key] for d in dates_tt]))
        tt = np.array(var_3d) + 273.15
        #print(tt.shape)
        #sys.exit()
        #tt = r_dp.variables['TT']

        #levels = [lev for lev in tt.sorted_levels]

        # Temperature on pressure levels
        #tt = np.squeeze(tt[:])+273.15

        # 2m Temperature
        var = r_dm.get_4d_field('TT', label=eticket)
        dates_tt = list(sorted(var.keys()))
        #key = var[dates_tt[0]].keys()[0]
        key = [*var[dates_tt[0]].keys()][0]
        var_3d = np.asarray([var[d][key] for d in dates_tt])
        tt_dm = var_3d.copy() + 273.15

        lons2d, lats2d = r_dm.get_longitudes_and_latitudes_for_the_last_read_rec()

        tim = tt.shape[1]
        ii = tt.shape[2]
        jj = tt.shape[3]

        # Array containing the inversion base level


        #start_time = time.time()
#        mean_dz, mean_deltaT, frequency, mean_deltaT_rad, frequency_rad, mean_deltaT_cloud, frequency_cloud, lw_cl_net, lw_cl_toa, lw_cl_down = inversion_calculations(base_level, top_level, tt_dm, tt[3,:,:,:], lw_net, lw_toa, lw_down, cloud_cover)
#        mean_dz0, mean_deltaT0, frequency0, mean_deltaT_rad0, frequency_rad0, mean_deltaT_cloud0, frequency_cloud0, lw_cl_net0, lw_cl_toa0, lw_cl_down0 = inversion_calculations(base_level[0::8,:,:], top_level[0::8,:,:], tt_dm[0::8,:,:], tt[3,0::8,:,:], lw_net[0::8,:,:], lw_toa[0::8,:,:], lw_down[0::8,:,:], cloud_cover[0::8,:,:])
#        mean_dz12, mean_deltaT12, frequency12, mean_deltaT_rad12, frequency_rad12, mean_deltaT_cloud12, frequency_cloud12, lw_cl_net12, lw_cl_toa12, lw_cl_down12 = inversion_calculations(base_level[4::8,:,:], top_level[4::8,:,:], tt_dm[4::8,:,:], tt[3,4::8,:,:], lw_net[4::8,:,:], lw_toa[4::8,:,:], lw_down[4::8,:,:], cloud_cover[4::8,:,:])

        mean_dt, mean_fr = inversion_calculations(tt_dm, tt[3,:,:,:])

        datefield = datetime(yy, mm, 1, 0, 0, 0)

        #outFILE = RPN("{2}/Inversion/Inversion_925_ERA_{0}{1:02d}v2.rpn".format(yy, mm, main_folder), mode="w")
        fname = "{2}/InversionV2/Inversion_925_ERA_dailycycle_{0}{1:02d}.nc".format(yy, mm, main_folder)
        vars=[("FREQ", mean_fr), ("DT", mean_dt)]
        save_netcdf(fname, vars, datefield, lats2d, lons2d)

#        mean_dz, mean_deltaT, frequency, mean_deltaT_rad, frequency_rad, mean_deltaT_cloud, frequency_cloud, lw_cl_net, lw_cl_toa, lw_cl_down = inversion_calculations(base_level, top_level, tt[0,:,:,:], tt[3,:,:,:], lw_net, lw_toa, lw_down, cloud_cover)
#        mean_dz0, mean_deltaT0, frequency0, mean_deltaT_rad0, frequency_rad0, mean_deltaT_cloud0, frequency_cloud0, lw_cl_net0, lw_cl_toa0, lw_cl_down0 = inversion_calculations(base_level[0::8,:,:], top_level[0::8,:,:], tt[0,0::8,:,:], tt[3,0::8,:,:], lw_net[0::8,:,:], lw_toa[0::8,:,:], lw_down[0::8,:,:], cloud_cover[0::8,:,:])
#        mean_dz12, mean_deltaT12, frequency12, mean_deltaT_rad12, frequency_rad12, mean_deltaT_cloud12, frequency_cloud12, lw_cl_net12, lw_cl_toa12, lw_cl_down12 = inversion_calculations(base_level[4::8,:,:], top_level[4::8,:,:], tt[0,4::8,:,:], tt[3,4::8,:,:], lw_net[4::8,:,:], lw_toa[4::8,:,:], lw_down[4::8,:,:], cloud_cover[4::8,:,:])

        mean_dt, mean_fr = inversion_calculations(tt[0,:,:,:], tt[3,:,:,:])

        fname = "{2}/InversionV2/Inversion_925_1000_ERA_dailycycle_{0}{1:02d}.nc".format(yy, mm, main_folder)
        vars=[("FREQ", mean_fr), ("DT", mean_dt)]
        save_netcdf(fname, vars, datefield, lats2d, lons2d)
        
        r_dp.close()
        #r_pm.close()
        r_dm.close()

        #sys.exit()
