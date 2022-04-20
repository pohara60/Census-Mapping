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

# Panel

local_authorities = geography['LAD11CD'].unique()
granularities = ['Local Authorities', 'Wards']

empty_map = pn.pane.Markdown('''
### Select Table name and Categories to display map...
''')


class MapViewer(param.Parameterized):

    placeholder = 'Select...'
    table_name = param.Selector(
        objects=[placeholder]+[table[1] for table in table_names], precedence=1)
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

    def __init__(self, **params):
        super().__init__(**params)
        self.tdf = None                     # DataFrame for current table
        self.categories = None              # Category name and options for current table
        self.london_lads_data_gdf = None    # Local authority data for current selection
        self.london_wards_data_gdf = None   # Ward  data for current selection

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
        for p in self.category_names:
            setattr(self, p, self.placeholder)
        self.update_categories(False)

        if self.table_name == self.placeholder:
            return

        self.table_code = [
            table[0] for table in table_names if table[1] == self.table_name][0]
        self.tdf = crd.read_table(self.table_code)
        self.categories = crd.get_table_column_names_and_values(self.tdf)
        df = crd.read_data(self.table_code)
        # Add names to data
        df = pd.merge(df, geography, on=locationcol)

        # Merge the data table (all data items) with the geo data
        self.london_lads_data_gdf = london_lads_gdf.merge(
            df, left_on='lad11cd', right_on=locationcol)
        self.london_wards_data_gdf = london_wards_gdf.merge(
            df, left_on='cmwd11cd', right_on=locationcol)

        for p in self.category_names:
            index = int(p[-1]) - 1
            if index < len(self.categories):
                self.param[p].objects = [self.placeholder] + \
                    self.categories[index][1]
                self.param[p].label = self.categories[index][0]
        self.update_categories(True)

    @param.depends('category1', 'category2', 'category3', 'category4', 'granularity', 'local_authority_name')
    def view(self):

        # Check for unspecified categories
        if self.table_name == self.placeholder or \
                self.placeholder in [getattr(self, p)
                                     for p in self.param if p in self.active_categories()]:
            return empty_map

        # Get category values as query string
        query_categories = []
        for i, category in enumerate(self.categories):
            category_param = f'category{i+1}'
            category_value = getattr(self, category_param)
            query_categories.append(f'`{category[0]}` == "{category_value}"')
        query_string = " & ".join(query_categories)

        trow = self.tdf.query(query_string)
        datacol = self.table_code + trow.iloc[0, -1]
        lad_max_value = self.london_lads_data_gdf[datacol].max()
        ward_max_value = self.london_wards_data_gdf[datacol].max()
        title = datacol + " by Local Authority"

        if self.granularity == 'Local Authorities':
            gdf = self.london_lads_data_gdf
            max_value = lad_max_value
            title = datacol + " by Local Authority"
        else:
            max_value = ward_max_value
            if self.local_authority_name == 'All':
                gdf = self.london_wards_data_gdf
                title = datacol + " by Ward"
            else:
                local_authority_id = geography[geography['Name'] ==
                                               self.local_authority_name].iloc[0]['GeographyCode']
                gdf = self.london_wards_data_gdf[self.london_wards_data_gdf['lad11cd'].str.match(
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
