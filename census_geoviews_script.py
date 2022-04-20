import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
import geoviews as gv
from bokeh.plotting import show
from bokeh.models import PrintfTickFormatter

# Get Census Merged Ward and Local Authority Data
geography = crd.read_geography()
locationcol = "GeographyCode"
namecol = "Name"

# Get LAD GeoPandas DataFrame
london_lads_gdf = crg.read_london_lad_geopandas()

# Get Census data index and its table_names
index = crd.read_index()
table_names = crd.get_table_names(index)

# Get first data table
table_name = table_names[0][0]
tdf = crd.read_table(table_name)

# Get first row data item (all categories All)
datacol = table_name + tdf.iloc[0, -1]

# Read the data table (all data items) and merge with the geography names
df = crd.read_data(table_name)
# Add names to data
df = pd.merge(df, geography, on=locationcol)

# Merge the data table (all data items) with the LAD geo data
gdf = london_lads_gdf.merge(df, left_on='lad11cd', right_on=locationcol)

# Map data by LAD
# Geoviews

title = datacol + " by Local Authority"

map = gv.Polygons(gdf, vdims=[locationcol, namecol, datacol])
map.opts(title=title,
         width=900, height=600,
         toolbar=None,
         tools=['hover'],
         aspect='equal',
         color=gv.dim(datacol),
         colorbar=True,
         cmap='Viridis',
         colorbar_opts={'formatter': PrintfTickFormatter(format='%f')},
         line_color='black', line_width=0.25, fill_alpha=1,
         xaxis=None,
         yaxis=None)

show(gv.render(map))
