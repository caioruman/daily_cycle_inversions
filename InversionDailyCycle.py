import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib as mpl # in p

# Jan - Feb - Mar
months = [1, 2, 3]
season = 'winter'
# Jul - Ago - Sep
months = [7, 8, 9]
season = 'summmer'

yeari = 1986
yearf = 2015

inv_data = []
freq_data = []
folder = "/home/caioruman/Documents/McGill/InversionData"
level = "925_1000"
for yy in range(yeari, yearf+1):
    # Read file and add
    for mm in months:
        file = '{0}/Inversion_{1}_ERA_dailycycle_{2}{3:02d}.nc'.format(folder, level, yy, mm)
        #print(file)
        data = Dataset(file)
        inv_data.append(data.variables["DT"][:])
        freq_data.append(data.variables["FREQ"][:])

aux = np.array(inv_data)
dt_data = np.nanmean(aux, axis=0)

aux = np.array(freq_data)
freq_data = np.nanmean(aux, axis=0)

# lat and lon
lons2d = data.variables['lon'][:]
lats2d = data.variables['lat'][:]

# list of stations
ff = "/home/caioruman/Documents/McGill/daily_cycle_inversions/latlonlist_NA.txt"

# Add the "local time" in the title too
arq = open(ff, 'r')

tim = np.arange(0,24,3)

for line in arq:
    aa = line.replace('\n','').replace('_', ' ').split(';')
    print(aa)
    lat = float(aa[3])
    lon = float(aa[5])

    # Getting the points in the grid for the station
    a = abs( lats2d-lat ) + abs(  np.where(lons2d <= 180, lons2d, lons2d - 360) - lon )
    i,j = np.unravel_index(a.argmin(), a.shape)

    # Select the data from the stations and plot the time series
    freq = 1-freq_data[:, i, j]
    delta_t = dt_data[:, i, j]

    #Plot the data
    fig, ax1 = plt.subplots(figsize=(4*3,3*3))
    plt.title("{0} - {1};{2}".format(aa[1][7:], lat, lon), size=20)

    ax1.plot(tim, delta_t, '.-', markersize=12, color="navy")
    ax1.set_xlabel('Time (h)', size=22)
    ax1.set_xticks(tim)
    # Make the y-axis label, ticks and tick labels match the line color.
    ax1.set_ylabel('Inversion Strength (K)', color="navy", size=22)
    ax1.tick_params('y', colors="navy")
    if season == 'winter' and (aa[0] == "71917" or aa[0] == "70261" or aa[0] == "71945" or aa[0] == "71043"):
        ax1.set_ylim(5,15)
        plt.yticks(np.arange(5,16,2))
    else:
        ax1.set_ylim(0,10)
    #ax1.set_ylim(4,8)


    plt.setp(ax1.get_xticklabels(), fontsize=18)
    plt.setp(ax1.get_yticklabels(), fontsize=18)

    plt.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(tim, freq*100, '.-', markersize=12, color="crimson")
    ax2.set_ylabel('Inversion Frequency (%)', color="crimson", size=22)
    ax2.tick_params('y', colors="crimson")
    ax2.set_ylim(0,100)
    #ax2.set_ylim(40,80)

    plt.setp(ax2.get_yticklabels(), fontsize=18)


    fig.tight_layout()
    plt.savefig('{0}_{1}_{2}.png'.format(aa[0], aa[1][7:17].replace(',','').replace(' ','_'), season))
    plt.close()
