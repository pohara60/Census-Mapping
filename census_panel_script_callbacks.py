import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
import geoviews as gv
from bokeh.models import PrintfTickFormatter
import panel as pn

# Get Census Merged Ward and Local Authority Data
geography = crd.read_geography()
locationcol = "GeographyCode"
namecol = "Name"

# Get London Ward GeoPandas DataFrame
london_wards_gdf = crg.read_london_ward_geopandas()

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

# Merge the data table (all data items) with the geo data
london_lads_data_gdf = london_lads_gdf.merge(
    df, left_on='lad11cd', right_on=locationcol)
london_wards_data_gdf = london_wards_gdf.merge(
    df, left_on='cmwd11cd', right_on=locationcol)

# Panel
# pn.extension('bokeh')
# gv.extension('bokeh')

lad_max_value = london_lads_data_gdf[datacol].max()
ward_max_value = london_wards_data_gdf[datacol].max()
title = datacol + " by Local Authority"

local_authorities = geography['LAD11CD'].unique()
granularities = ['Local Authorities', 'Wards']

# Create Widgets
granularity_widget = pn.widgets.RadioButtonGroup(options=granularities)
local_authority_widget = pn.widgets.Select(name='Wards for Local Authority',
                                           options=['All'] +
                                           [geography[geography[locationcol] == lad][namecol].iat[0]
                                            for lad in local_authorities],
                                           value='All')
widgets = pn.Column(granularity_widget, local_authority_widget)
layout = widgets


def update_graph(event):
    # Callback recreates map when granularity or local_authority are changed
    global layout
    granularity = granularity_widget.value
    local_authority_name = local_authority_widget.value

    if granularity == 'Local Authorities':
        gdf = london_lads_data_gdf
        max_value = lad_max_value
        title = datacol + " by Local Authority"
    else:
        max_value = ward_max_value
        if local_authority_name == 'All':
            gdf = london_wards_data_gdf
            title = datacol + " by Ward"
        else:
            local_authority_id = geography[geography['Name'] ==
                                           local_authority_name].iloc[0]['GeographyCode']
            gdf = london_wards_data_gdf[london_wards_data_gdf['lad11cd'].str.match(
                local_authority_id)]
            title = datacol + " by Ward for " + local_authority_name

    map = gv.Polygons(gdf, vdims=[locationcol, namecol, datacol])
    map.opts(title=title,
             width=900, height=600,
             toolbar=None,
             tools=['hover'],
             aspect='equal',
             color=gv.dim(datacol),
             colorbar=True,
             cmap='Viridis',
             clim=(0, max_value),
             colorbar_opts={'formatter': PrintfTickFormatter(format='%f')},
             line_color='black', line_width=0.25, fill_alpha=1,
             xaxis=None,
             yaxis=None)

    layout = pn.Column(widgets, map)
    # layout.servable()


granularity_widget.param.watch(update_graph, 'value')
local_authority_widget.param.watch(update_graph, 'value')
update_graph(None)
layout.show()

# panel serve census_panel_simple_script.py --show
