import param
import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
import geopandas as gpd
import geoviews as gv
from bokeh.plotting import show
from bokeh.models import PrintfTickFormatter
import panel as pn

import hvplot.pandas

# Get Census Merged Ward and Local Authority Data
# Replaced by test DataFrame
geography = pd.DataFrame(data=[
    ['E36007378', 'Chiswick Riverside', 'E09000018', 'Hounslow'],
    ['E36007379', 'Cranford', 'E09000018', 'Hounslow'],
    ['E36007202', 'Ealing Broadway', 'E09000009', 'Ealing'],
    ['E36007203', 'Ealing Common', 'E09000009', 'Ealing'],
    ['E36007204', 'East Acton', 'E09000009', 'Ealing'],
    ['E09000018', 'Hounslow', 'E09000018', 'Hounslow'],
    ['E09000009', 'Ealing', 'E09000009', 'Ealing']
], columns=["GeographyCode", "Name", "LAD11CD", "LAD11NM"])

# Get London Ward GeoPandas DataFrame
# Replaced by test DataFrame
london_wards_data_gdf = pd.DataFrame(data=[
    ['E36007378', 'E09000018', 378],
    ['E36007379', 'E09000018', 379],
    ['E36007202', 'E09000009', 202],
    ['E36007203', 'E09000009', 203],
    ['E36007204', 'E09000009', 204]
], columns=["cmwd11cd", "lad11cd", "data"])

# Get LAD GeoPandas DataFrame
# Replaced by test DataFrame
london_lads_data_gdf = pd.DataFrame(data=[
    ['E09000018', 757],
    ['E09000009', 609]
], columns=["lad11cd", "data"])

locationcol = "GeographyCode"
namecol = "Name"
datacol = 'data'

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

        # Replace gv.Polygons with hvplot.bar for test purposes
        map = gdf.hvplot.bar(y=datacol, height=500)
        return map


viewer = MapViewer(name='Map Viewer')
widgets = pn.Param(viewer.param, name='Census Data', widgets={
    'granularity': pn.widgets.RadioButtonGroup,
    'local_authority_name': pn.widgets.Select
})
pn.Column(widgets, viewer.view).show()
