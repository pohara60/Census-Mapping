import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
import geoviews as gv
from bokeh.models import PrintfTickFormatter
import panel as pn
import param

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

lad_max_value = london_lads_data_gdf[datacol].max()
ward_max_value = london_wards_data_gdf[datacol].max()
title = datacol + " by Local Authority"

local_authorities = geography['LAD11CD'].unique()
granularities = ['Local Authorities', 'Wards']


class MapViewer(param.Parameterized):

    granularity = param.Selector(
        default=granularities[0], objects=granularities)
    local_authority_name = param.Selector(
        default='All', objects=['All'] +
        [geography[geography[locationcol] == lad][namecol].iat[0]
         for lad in local_authorities])

    @param.depends('granularity', 'local_authority_name')
    def view(self):

        if self.granularity == 'Local Authorities':
            gdf = london_lads_data_gdf
            max_value = lad_max_value
            title = datacol + " by Local Authority"
        else:
            max_value = ward_max_value
            if self.local_authority_name == 'All':
                gdf = london_wards_data_gdf
                title = datacol + " by Ward"
            else:
                local_authority_id = geography[geography['Name'] ==
                                               self.local_authority_name].iloc[0]['GeographyCode']
                gdf = london_wards_data_gdf[london_wards_data_gdf['lad11cd'].str.match(
                    local_authority_id)]
                title = datacol + " by Ward for " + self.local_authority_name

        map = gv.Polygons(
            gdf, vdims=[locationcol, namecol, datacol, 'LAD11NM'])
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

        return map


viewer = MapViewer(name='Map Viewer')
widgets = pn.Param(viewer.param, name='Census Data', widgets={
    'granularity': pn.widgets.RadioButtonGroup,
    'local_authority_name': pn.widgets.Select
})
pn.Column(widgets, viewer.view).show()
