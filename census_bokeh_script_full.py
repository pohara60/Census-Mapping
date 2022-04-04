from bokeh.models import Select, Div
from bokeh.models.widgets import RadioButtonGroup
import census_read_data as crd
import census_read_geopandas as crg
import pandas as pd
import json
from bokeh.models import GeoJSONDataSource
from bokeh.models import LinearColorMapper, ColorBar, PrintfTickFormatter
from bokeh.models import HoverTool
from bokeh.plotting import figure, curdoc
from bokeh.layouts import row, column

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

# Get table names
index = crd.read_index()
table_names = crd.get_table_names(index)


# Bokeh

# Create Widgets
table_label = Div(text='Table Name', width=200)
table_name_widget = Select(title='',
                           options=[('', 'Select...')] +
                                   [(table_name[0], table_name[1]) for table_name in table_names])
category_labels, category_widgets = [], []
for i in range(4):
    category_labels.append(Div(text='Category', width=200, visible=False))
    category_widgets.append(Select(title='', options=[], visible=False))
granularities = ['Local Authorities', 'Wards']
granularity_widget = RadioButtonGroup(labels=granularities, active=0)
local_authority_label = Div(text='Wards for Local Authority', width=200)
local_authorities = geography['LAD11CD'].unique()
local_authority_widget = Select(title='',
                                options=[('All', 'All')] +
                                [(lad, geography[geography[locationcol] == lad][namecol].iat[0])
                                    for lad in local_authorities],
                                value='All')

widgets = column(row(table_label, table_name_widget),
                 row(category_labels[0], category_widgets[0]),
                 row(category_labels[1], category_widgets[1]),
                 row(category_labels[2], category_widgets[2]),
                 row(category_labels[3], category_widgets[3]),
                 granularity_widget,
                 row(local_authority_label, local_authority_widget))

# State between callback functions
table_name = ''         # Current table
categories = []         # Categories for table
tdf = None              # Table description DataFrame
all_categories = False  # All categories specified
query_string = ''       # Category filter string
df = None               # Table data DataFrame
london_lads_data_gdf = None     # London LAD data
london_wards_data_gdf = None    # London Ward data


def update_table(attr, old, new):
    global table_name, categories, tdf, df, london_lads_data_gdf, london_wards_data_gdf

    if old is not None and new == old:
        return

    table_name = table_name_widget.value
    if table_name != '':
        tdf = crd.read_table(table_name)
        categories = crd.get_table_column_names_and_values(tdf)
        df = crd.read_data(table_name)
        # Add names to data
        df = pd.merge(df, geography, on=locationcol)

        # Merge the data table (all data items) with the geo data
        london_lads_data_gdf = london_lads_gdf.merge(
            df, left_on='lad11cd', right_on=locationcol)
        london_wards_data_gdf = london_wards_gdf.merge(
            df, left_on='cmwd11cd', right_on=locationcol)

    else:
        categories = []
    update_categories(attr, old, new)


def update_categories(attr, old, new):
    global all_categories, query_string

    # Update category widgets
    all_categories = len(categories) > 0
    query_categories = []

    def update_category(category, label_widget, category_widget):
        if category is not None:
            category_label = category[0]
            category_values = [('', 'Select...')] + [(cat, cat)
                                                     for cat in category[1]]
            category_visible = True
        else:
            category_label = ''
            category_values = []
            category_visible = False

        label_widget.visible = category_visible
        label_widget.text = category_label
        category_widget.visible = category_visible
        category_widget.options = category_values
        if category_widget.value == '' or \
                not any(category_widget.value == option[0] for option in category_values):
            category_widget.value = ''
        return category is None or category_widget.value != ''

    # Update table categories
    for i, category in enumerate(categories):
        all_categories &= update_category(category,
                                          category_labels[i], category_widgets[i])
        query_categories.append(
            f'`{category_labels[i].text}` == "{category_widgets[i].value}"')
    # Clear remaining category widgets
    for i in range(len(categories), len(category_widgets)):
        all_categories &= update_category(None,
                                          category_labels[i], category_widgets[i])

    query_string = " & ".join(query_categories)
    update_graph(attr, old, new)


def update_graph(attr, old, new):

    # If all categories are specified then get data
    if not all_categories:
        layout = widgets
    else:

        trow = tdf.query(query_string)
        datacol = table_name + trow.iloc[0, -1]
        lad_max_value = london_lads_data_gdf[datacol].max()
        ward_max_value = london_wards_data_gdf[datacol].max()
        title = datacol + " by Local Authority"

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
        gdf_json = json.loads(gdf.to_json())
        json_data = json.dumps(gdf_json)
        geosource = GeoJSONDataSource(geojson=json_data)

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
        layout = column(widgets, p)

    curdoc().clear()
    curdoc().add_root(layout)


# Set callback functions for selection widgets
table_name_widget.on_change('value', update_table)
for widget in category_widgets:
    widget.on_change('value', update_categories)
granularity_widget.on_change('active', update_graph)
local_authority_widget.on_change('value', update_graph)

# Table callback calls other callbacks
update_table(None, None, None)

# Start Bokeh server:
# bokeh serve census_bokeh_script_full.py
