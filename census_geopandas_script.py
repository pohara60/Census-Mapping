from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import census_read_data as crd
import census_read_geopandas as crg

# Get LAD GeoPandas DataFrame
london_lads_gdf = crg.read_london_lad_geopandas()

# Default GeoPandas plot
london_lads_gdf.plot()
plt.show()

# Get Census data index and its table_names
index = crd.read_index()
table_names = crd.get_table_names(index)

# Get first data table
table_name = table_names[0][0]
tdf = crd.read_table(table_name)

# Get first row data item (all categories All)
datacol = table_name + tdf.iloc[0, -1]

# Read the data table (all data items) and merge with the LAD geo data
df = crd.read_data(table_name)
gdf = london_lads_gdf.merge(df, left_on='lad11cd', right_on='GeographyCode')

# Create a Matplotlib plot, turn off axes, position color bar, and plot
fig, ax = plt.subplots(1, 1)
ax.set_axis_off()
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.0)
gdf.plot(column=datacol, ax=ax, legend=True, cax=cax)
plt.show()
