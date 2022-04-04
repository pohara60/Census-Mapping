from bokeh.models import Select
from bokeh.models.widgets import RadioButtonGroup
import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
from bokeh.models import GeoJSONDataSource
from bokeh.models import LinearColorMapper, ColorBar, PrintfTickFormatter
from bokeh.models import HoverTool
from bokeh.plotting import figure, curdoc
from bokeh.layouts import column

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

# Bokeh

lad_max_value = london_lads_data_gdf[datacol].max()
ward_max_value = london_wards_data_gdf[datacol].max()
title = datacol + " by Local Authority"

local_authorities = geography['LAD11CD'].unique()
granularities = ['Local Authorities', 'Wards']

# Create Widgets
granularity_widget = RadioButtonGroup(labels=granularities,
                                      active=0)
local_authority_widget = Select(title='Wards for Local Authority',
                                options=[('All', 'All')] +
                                [(lad, geography[geography[locationcol] == lad][namecol].iat[0])
                                 for lad in local_authorities],
                                value='All')


def update_graph(attr, old, new):
    # Callback recreates map when granularity or local_authority are changed
    granularity = granularities[granularity_widget.active]
    local_authority = local_authority_widget.value

    if granularity == 'Local Authorities':
        gdf = london_lads_data_gdf
        max_value = lad_max_value
        title = datacol + " by Local Authority"
    else:
        max_value = ward_max_value
        if local_authority == 'All':
            gdf = london_wards_data_gdf
            title = datacol + " by Ward"
        else:
            gdf = london_wards_data_gdf[london_wards_data_gdf['lad11cd'].str.match(
                local_authority)]
            local_authority_name = geography[geography['GeographyCode'] ==
                                             local_authority].iloc[0]['Name']
            title = datacol + " by Ward for " + local_authority_name

    # Input GeoJSON source that contains features for plotting
    geosource = GeoJSONDataSource(geojson=gdf.to_json())

    # Create color bar
    color_mapper = LinearColorMapper(
        palette='Viridis256', low=0, high=max_value)
    formatter = PrintfTickFormatter(format='%f')
    color_bar = ColorBar(color_mapper=color_mapper,
                         title=datacol,
                         label_standoff=12,
                         formatter=formatter)

    # Add hover tool
    tooltips = [(locationcol, '@'+locationcol),
                (namecol, '@'+namecol),
                (datacol, '@'+datacol)]
    if granularity == 'Wards':
        tooltips.insert(2, ('LAD', '@LAD11NM'))
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

    layout = column(granularity_widget, local_authority_widget, p)
    curdoc().clear()
    curdoc().add_root(layout)


granularity_widget.on_change('active', update_graph)
local_authority_widget.on_change('value', update_graph)
update_graph(None, None, None)
# Start Bokeh server:
# bokeh serve census_bokeh_script_simple.py
