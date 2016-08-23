# Single station viewer

The Single station viewer is a python command line tool to generate interactive bokeh graphs of long time series from several netCDF files. The generated plots are stored in a html file and are based on the information available in the THREDDS Data Server (TDS) Catalog managed by SOCIB.

## Example output
Esporles Air Temperature

![](/img/esporles_air_temp.png?raw=true "HTML bokeh output")

Or try the interactive example here:

Buoy Canal de Ibiza SCB_SBE37006 Water Temperature

<a href="http://htmlpreview.github.io/?https://github.com/kriete/singleStationTimeSeries/blob/master/example/buoy_canaldeibiza-scb_sbe37006_combined_QCed_WTR_TEM_SBE37.html">Rendered HTML</a>

## Dependencies
- numpy
- pandas
- bokeh
- matplotlib
- pytz
- lxml
- netCDF4

Furthermore, the developer tools of the following packages are required:
- libxml2-dev
- libxslt-dev

Install them by running:

`sudo apt-get install libxml2-dev libxslt-dev`

The package has been developed and tested using Ubuntu 14 and is currently only supported by python 2.7.

## Install
Clone this repository using git. To install the dependencies, first install the packages libxml2-dev and libxslt-dev. Then run pip install -r requirement.txt to install the python packages or install them manually.

Last but not least, after configurating (see next section), start the processing by running the singleStationGenerator.py:

 `python singleStationGenerator.py`

## Usage
To specify the platform and time range, modify the config.ini.

The following configurations are possible:

> start_year, end_year, start_month, end_month: self-explanatory

> base_html: the catalog.html address of the instrument inside thredds (e.g. http://thredds.socib.es/thredds/catalog/mooring/conductivity_and_temperature_recorder/catalog.html)

> station_names: name(s) of the stations to be processed together, because it might happen that the instrument has changed (e.g. buoy_canaldeibiza-scb_sbe37006, buoy_canaldeibiza-scb_sbe37005)

> variable_name: the variable name to be processed (e.g. WTR_TEM_SBE37)

> output_path: self-explanatory

> use_good_data_only: flag to set to True or False in case the QC variable should be regarded

