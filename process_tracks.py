import geopandas as gpd
from datetime import datetime
import numpy as np
import matplotlib as mpl
from matplotlib import patheffects
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import gridspec
import rioxarray

### SET UP PLOT PARAMETERS ###
BACKGROUND_COLOR = '#012454'
FOREGROUND_COLOR = 'white'
mpl.rcParams['text.color'] = FOREGROUND_COLOR
mpl.rcParams['axes.labelcolor'] = FOREGROUND_COLOR
mpl.rcParams['xtick.color'] = FOREGROUND_COLOR
mpl.rcParams['ytick.color'] = FOREGROUND_COLOR
plt.rcParams['axes.facecolor'] = BACKGROUND_COLOR
mpl.rc('font', family='DIN Alternate')
fig = plt.figure(dpi=300)
fig.patch.set_facecolor(BACKGROUND_COLOR)
# relative positions of sub plots [left, bottom, width, height]
route_plot = plt.axes([-0.2,0,0.9,1])
elev_plot = plt.axes([0.60,0.05,0.3,0.87])
fig.subplots_adjust(hspace=0, wspace=0)

### READ IN DATA TO PLOT ###
crs = "EPSG:4326"
dem = rioxarray.open_rasterio('ben_nevis_elevation.tif', masked=True).rio.reproject(crs) # click and download from: https://dwtkns.com/srtm30m/
contours_50 = gpd.read_file(f'./ben_nevis_contours_50m.shp').to_crs(crs) # make using 'contour' tool in QGIS using the DEM data
contours_100 = gpd.read_file(f'./ben_nevis_contours_100m.shp').to_crs(crs) # make using 'contour' tool in QGIS using the DEM data
journey = gpd.read_file(f'./strava_data/ben_nevis.shp').to_crs(crs) # download .gpx data from Strava and export the 'tracks_points' file as its own shapefile
journey = journey.iloc[::100].reset_index() # sample points to reduce processing

# Calculate how much time has passed at each point in your track relative to the start
start_datetime = journey["time"].iloc[0]
for ind in journey.index:
    journey.at[ind, "time_change"] = int((datetime.strptime(journey.at[ind, "time"][:-4],'%Y/%m/%d %H:%M:%S') - datetime.strptime(start_datetime[:-4],'%Y/%m/%d %H:%M:%S')).total_seconds())

# Extract latitude and longitude of points
lon = journey["geometry"].x
lat = journey["geometry"].y

# Set up variables for plotting
x,y,y_ele,t = [], [], [], []

def animate(i):
    """
        Main animation function to generate each iterative frame (plot) of
        the output gif.
    """
    # Clearing previous frame 
    route_plot.clear()
    elev_plot.clear()
    print('frame: ',i)
    
    ### ROUTE PLOT ###
    # Append data to this point in sequence
    x.append(lon[i])
    y.append(lat[i])
    
    # If you wanted to clip your route plot to the bounding box of your route
    # route_plot.set_ylim(lat.min(), lat.max())
    # route_plot.set_xlim(lon.min(), lon.max())
    dem.plot(ax=route_plot, cmap='cividis', add_colorbar=False, add_labels=False, zorder=2) # DEM
    contours_50.plot(ax=route_plot, color='#A0A0A0', alpha=0.2, zorder=3) # 50m contour lines
    contours_100.plot(ax=route_plot, color='white', alpha=0.5, zorder=3) # 100m contour lines
    route_plot.plot(x,y, scaley=True, scalex=True, color="white", linewidth=3.5, zorder=4) # white outline
    route_plot.plot(x,y, scaley=True, scalex=True, color="#A35E85", linewidth=2, zorder=5) # main line
    route_plot.plot(lon[i],lat[i], scaley=True, scalex=True, color="#D82F90", markeredgecolor='white', markersize=9, marker="o", zorder=7) # spot leading line
    
    route_plot.axis("off")

    ### ELEVATION PLOT ###
    # Append data to this point in sequence
    t.append(journey["time_change"][i])
    y_ele.append(journey["ele"][i])
    
    elev_plot.plot(t,y_ele, scaley=True, scalex=True, color="white", linewidth=3.5) # white outline
    elev_plot.plot(t,y_ele, scaley=True, scalex=True, color="#A35E85", linewidth=2) # main line
    elev_plot.plot(journey["time_change"][i],journey["ele"][i], scaley=True, scalex=True, color="#D82F90", markeredgecolor='white', markersize=9, marker="o")
    elev_plot.yaxis.set_label_position("right")
    elev_plot.yaxis.tick_right()
    elev_plot.set_ylim(0)
    for spine_side in ['left', 'top','bottom']:
        elev_plot.spines[spine_side].set_visible(False)

    elev_plot.get_xaxis().set_visible(False)
    elev_plot.spines['right'].set_color('#A0A0A0')
    
    # Custom text and symbols
    buffer = [patheffects.withStroke(linewidth=1.5, foreground="w")]
    plt.text(-0.82,0.98, 'BEN', fontsize=40, color="#012454", transform=plt.gca().transAxes,  zorder=10)
    plt.text(-0.28,0.98, 'NEVIS', fontsize=40, color="#fde434", transform=plt.gca().transAxes,  zorder=10)
    plt.text(-0.27,0.3, 'ELEVATION', fontsize=20, color="#D82F90", path_effects=buffer, transform=plt.gca().transAxes, rotation=90, zorder=10)
    plt.text(1.1,-0.01, 'm', fontsize=10, transform=plt.gca().transAxes, zorder=10)
    a, b, arrow_length = -1.9, 1.075, 0.05
    route_plot.annotate('', xy=(a, b), xytext=(a, b-arrow_length),
                arrowprops=dict(facecolor='white', edgecolor='white', width=5, headwidth=10),
                ha='center', va='center', fontsize=20,
                xycoords=plt.gca().transAxes, zorder=10)

### GENERATE PLOT AND EXPORT ###
ani = animation.FuncAnimation(fig=fig, func=animate, frames=len(journey.index), interval=125)
writergif = animation.PillowWriter(fps=10) 
ani.save('route_and_elevation.gif', writer=writergif)
plt.close()