# Interactive Mapping in Python with UK Census Data

This is the code for my Medium article on this subject.

## Files

The files in the order they are discussed are:

`census_read_data.py` - read Census Index, Table and Data, also Geography lookup

`census_read_geopandas.py` - read local Shapefile for Wards and LADs

`census_geopandas_script.py` - plot map using GeoPandas and Matplotlib

`census_read_geojson.py` - read cached GeoJSON for Wards and LADs

`census_plotly_script.py` - plot map using GeoJSON and Plotly

`census_plotly_script_better.py` - plot map using GeoJSON and Plotly, improved layout

`census_dash_script_simple.py` - simple interactive map using GeoJSON and Plotly Dash

`census_dash_script_full.py` - full interactive map using GeoJSON and Plotly Dash

## Python Packages

I used Python 3.9 on Windows 11 and normally use `pip` to install packages. However, `geopandas` depends on packages that are implemented in C/C++, so special procedures are required to install it on Windows. (Apparently the install is straightforward on Linux and Mac.)

These are the steps I followed:

```
    pip install wheel
    pip install pipwin
    pipwin install numpy
    pipwin install pandas
    pipwin install gdal
    # Add the new GDAL path to the Windows PATH environment variable, e.g.:
    # C:\Users\<username>\AppData\Local\Programs\Python\Python39\Lib\site-packages\osgeo
    # It seems this must be done before installing Fiona.
    pipwin install fiona
    pipwin install pyproj
    pipwin install rtree
    pipwin install shapely
    pipwin install six
    pip install geopandas
```
