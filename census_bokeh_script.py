import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
import json
from bokeh.models import GeoJSONDataSource
from bokeh.models import LinearColorMapper, ColorBar, PrintfTickFormatter
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.io import show

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
# Bokeh

max_value = gdf[datacol].max()
title = datacol + " by Local Authority"

# Input GeoJSON source that contains features for plotting
gdf_json = json.loads(gdf.to_json())
json_data = json.dumps(gdf_json)
geosource = GeoJSONDataSource(geojson=json_data)

# Create color bar
color_mapper = LinearColorMapper(palette='Viridis256', low=0, high=max_value)
formatter = PrintfTickFormatter(format='%f')
color_bar = ColorBar(color_mapper=color_mapper,
                     title=datacol,
                     label_standoff=12,
                     formatter=formatter)

# Add hover tool
tooltips = [(locationcol, '@'+locationcol),
            (namecol, '@'+namecol),
            (datacol, '@'+datacol)]
hover = HoverTool(tooltips=tooltips)

# Create figure object
p = figure(title=title,
           plot_height=600,
           plot_width=1200,
           match_aspect=True,
           toolbar_location=None,
           tools=[hover])
p.title.align = "center"
p.axis.visible = False
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Add patch renderer to figure
p.patches('xs', 'ys', source=geosource,
          fill_color={'field': datacol, 'transform': color_mapper},
          line_color='black', line_width=0.25, fill_alpha=1)

p.add_layout(color_bar, 'right')

# Display plot
show(p)
