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

table_names = ['A', 'B']
table_categories = {
    'A': [
        ('A Cat1', ['A Cat1 A', 'A Cat1 B', 'A Cat1 C']),
        ('A Cat2', ['A Cat2 A', 'A Cat2 B', 'A Cat2 C'])
    ],
    'B': [
        ('B Cat1', ['B Cat1 A', 'B Cat1 B', 'B Cat1 C']),
        ('B Cat2', ['B Cat2 A', 'B Cat2 B', 'B Cat2 C']),
        ('B Cat3', ['B Cat3 A', 'B Cat3 B', 'B Cat3 C'])
    ]
}

# Panel

lad_max_value = london_lads_data_gdf[datacol].max()
ward_max_value = london_wards_data_gdf[datacol].max()
title = datacol + " by Local Authority"

local_authorities = geography['LAD11CD'].unique()
granularities = ['Local Authorities', 'Wards']

widgets = None
empty_map = pn.pane.Markdown('''
### Select Table name and Categories to display map...
''')


class MapViewer(param.Parameterized):

    placeholder = 'Select...'
    table_name = param.Selector(
        objects=[placeholder]+table_names, precedence=1)
    category1 = param.Selector(objects=[placeholder], precedence=-1)
    category2 = param.Selector(objects=[placeholder], precedence=-1)
    category3 = param.Selector(objects=[placeholder], precedence=-1)
    category4 = param.Selector(objects=[placeholder], precedence=-1)
    category_names = ['category1', 'category2', 'category3', 'category4']
    granularity = param.Selector(
        default=granularities[0], objects=granularities, precedence=6)
    local_authority_name = param.Selector(
        default='All', objects=['All'] +
        [geography[geography[locationcol] == lad][namecol].iat[0]
         for lad in local_authorities],
        precedence=7)
    categories = None

    def update_categories(self, visible):
        if self.categories is None:
            return
        for p in [p for p in self.param if p in self.category_names]:
            index = int(p[-1]) - 1
            if index < len(self.categories):
                self.param[p].precedence = 2+index if visible else -1

    def active_categories(self):
        return [] if self.categories is None \
            else ['category'+str(r+1) for r in range(len(self.categories))]

    @param.depends('table_name', watch=True)
    def update_table(self):
        print(f'table_name={self.table_name}')
        for p in self.category_names:
            setattr(self, p, self.placeholder)
        self.update_categories(False)

        if self.table_name == self.placeholder:
            return

        self.categories = table_categories[self.table_name]
        for p in self.category_names:
            index = int(p[-1]) - 1
            if index < len(self.categories):
                self.param[p].objects = [self.placeholder] + \
                    self.categories[index][1]
                self.param[p].label = self.categories[index][0]
        self.update_categories(True)

    @param.depends('category1', 'category2', 'category3', 'category4', 'granularity', 'local_authority_name')
    def view(self):

        for p in self.category_names:
            print(f'{p}={getattr(self,p)}')
        if self.table_name == self.placeholder or \
                self.placeholder in [getattr(self, p)
                                     for p in self.param if p in self.active_categories()]:
            return empty_map

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
    'table_name': pn.widgets.Select,
    'category1': {'widget_type': pn.widgets.Select},
    'category2': {'widget_type': pn.widgets.Select},
    'category3': {'widget_type': pn.widgets.Select},
    'category4': {'widget_type': pn.widgets.Select},
    'granularity': pn.widgets.RadioButtonGroup,
    'local_authority_name': pn.widgets.Select
})
pn.Column(widgets, viewer.view).show()
