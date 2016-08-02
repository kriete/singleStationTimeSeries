from __future__ import division
from urllib2 import Request, urlopen, URLError
from lxml import html
from netCDF4 import Dataset
import ConfigParser
import numpy as np
import matplotlib.dates as md
from datetime import datetime
from bokeh.io import output_file, show, save
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import PanTool, Range1d, LinearAxis, CustomJS, HoverTool
from collections import OrderedDict
import pandas as pd
import os
import pytz
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = logging.FileHandler('utils.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s p%(process)s {%(pathname)s:%(lineno)d} - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_min_max_ranges(data):
    cur_min = np.nanmin(data)
    cur_max = np.nanmax(data)
    difference = cur_max - cur_min
    cur_buffer = difference / 10.
    cur_min -= cur_buffer
    cur_max += cur_buffer
    return cur_min, cur_max


def get_bokeh_plot(data, conv_time, units, cur_title):
    cur_min, cur_max = get_min_max_ranges(data)
    p = figure(plot_width=1200, plot_height=300, tools=["pan, xwheel_zoom, hover, reset"], x_axis_type="datetime",
               y_range=(cur_min, cur_max), y_axis_label=units, toolbar_location=None, logo=None,
               active_scroll='xwheel_zoom', webgl=False, title=cur_title)
    time_strings = map(str, conv_time)
    data_source = ColumnDataSource(
        data=dict(
            time=time_strings,
            data=data,
        )
    )
    p.line(conv_time, data, name="data", source=data_source)
    hover = p.select(dict(type=HoverTool))
    hover.names = ["data"]
    hover.tooltips = OrderedDict([
        ('time', '@time'),
        ('value', '@data{0.0}')
    ])
    pan_tool_standard = p.select(dict(type=PanTool))
    pan_tool_standard.dimensions = ["width"]
    return p


def sort_data(time_array, data_array):
    """
    Uses quick-sort to sort the extended arrays
    :param time_array:
    :param data_array:
    :return:
    """
    idx = np.argsort(time_array)
    return time_array[idx], data_array[idx], idx


def automatic_range_jscode_defintion():
    jscode = """
    function isNumeric(n) {
      return !isNaN(parseFloat(n)) && isFinite(n);
    }
    var data = source.get('data');
    var start = yrange.get('start');
    var end = yrange.get('end');

    var time_start = xrange.get('start')/1000;
    var time_end = xrange.get('end')/1000;

    var pre_max_old = end;
    var pre_min_old = start;

    var time = data['x'];
    var pre = data['y'];
    t_idx_start = time.filter(function(st){return st>=time_start})[0];
    t_idx_start = time.indexOf(t_idx_start);

    t_idx_end = time.filter(function(st){return st>=time_end})[0];
    t_idx_end = time.indexOf(t_idx_end);

    var pre_interval = pre.slice(t_idx_start, t_idx_end);
    pre_interval = pre_interval.filter(function(st){return !isNaN(st)});
    var pre_max = Math.max.apply(null, pre_interval);
    var pre_min = Math.min.apply(null, pre_interval);
    var ten_percent = (pre_max-pre_min)*0.1;

    pre_max = pre_max + ten_percent;
    pre_min = pre_min - ten_percent;

    if((!isNumeric(pre_max)) || (!isNumeric(pre_min))) {
        pre_max = pre_max_old;
        pre_min = pre_min_old;
    }

    yrange.set('start', pre_min);
    yrange.set('end', pre_max);

    source.trigger('change');
    """
    return jscode


def totimestamp(dt, epoch=datetime(1970, 1, 1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


def get_pandas_timestamp_series(datetime_array):
    out = pd.Series(np.zeros(len(datetime_array)))
    counter = 0
    for i in datetime_array:
        out[counter] = pd.tslib.Timestamp(i)
        counter += 1
    return out


def get_md_datenum(obs_time):
    dates = [datetime.fromtimestamp(ts, tz=pytz.utc) for ts in obs_time]
    return md.date2num(dates)


def get_data_array(data_array):
    if type(data_array.__array__()) is np.ma.masked_array:
        return data_array.__array__().data
    else:
        return data_array.__array__()


def find_all_instances(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]


def get_mooring_stations(base_url, year, month, only_single_stations=None):
    # Please note this was originally meant to be used for _latest datasets only. I adapted this to specify month and
    # year.
    # Added single stations bypass.
    # TODO: refine to have a month selection here.
    # TODO: replace self -- haha very sacrificing
    # TODO: use logger instead of print s**t
    name_list = []
    URLBuilder = []
    req = Request(base_url)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
        elif hasattr(e, 'code'):
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
    else:
        url_builder = []
        tree = html.fromstring(response.read())
        link_path = tree.xpath('//a')
        for x in range(1, len(link_path)):
            url_builder.append(link_path[x].values())
        URLLister = []
        for n in range(0, len(url_builder) - 4):
            string = str(url_builder[n])
            idx = string.find("/")
            # url = "http://thredds.socib.es/thredds/catalog/mooring/weather_station/" + URLBuilder[n][0][0:idx-1] + "/L1/catalog.html"
            url = "http://thredds.socib.es/thredds/catalog/mooring/weather_station/" + url_builder[n][0][
                                                                                       0:idx - 1] + "L1/catalog.html"
            name = url_builder[n][0][0:idx - 2]
            if only_single_stations != [] and name not in only_single_stations:
                logger.info('Skipping station ' + name + '. (Single station bypass).')
                continue
            req = Request(url)
            try:
                response = urlopen(req)
            except URLError as e:
                if hasattr(e, 'reason'):
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                elif hasattr(e, 'code'):
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
            else:
                URLLister.append(url)
                name_list.append(name)

        for m in URLLister:
            req = Request(m)
            try:
                response = urlopen(req)
            except URLError as e:
                if hasattr(e, 'reason'):
                    print 'We failed to reach a server.'
                    print 'Reason: ', e.reason
                elif hasattr(e, 'code'):
                    print 'The server couldn\'t fulfill the request.'
                    print 'Error code: ', e.code
            else:
                tree = html.fromstring(response.read())
                link_path = tree.xpath('//a')
                for x in range(1, len(link_path)):
                    string = str(link_path[x].values())
                    idx = string.find("=")

                    out_string = "http://thredds.socib.es/thredds/dodsC/" + str(link_path[x].values()[0][idx - 1:len(string)])
                    idx = out_string.find("L1/")
                    out_string = out_string[0:idx] + 'L1/' + str(year) + '' + out_string[idx+2::]
                    idx = out_string.find("_latest")
                    out_string = out_string[0:idx] + '_' + str(year) + '-' + str(month).zfill(2) + '.nc'
                    URLBuilder.append(out_string)
                    break
    return URLBuilder


def read_key_value_config(section, variable):
    config_handler = ConfigParser.ConfigParser()
    config_handler.read(os.getcwd() + '/config.ini')
    out = dict()
    if config_handler.has_section(section):
        full = config_handler.get(section, variable)
        idx = find_all_instances(full, ';')
        start_counter = 0
        for i in idx:
            pair = full[start_counter:i]
            comma_idx = find_all_instances(pair, ',')
            key = pair[0:comma_idx[0]]
            value = pair[comma_idx[0]+1::]
            out[key] = value.strip()
            start_counter = i + 1
    else:
        logger.warning('Specified section ' + section + ' not found in config.ini.')
    return out


def read_value_config(section, variable):
    config_handler = ConfigParser.ConfigParser()
    config_handler.read(os.getcwd() + '/config.ini')
    if config_handler.has_section(section):
        return config_handler.get(section, variable)
    else:
        logger.warning('Specified section ' + section + ' not found.')
        return ''


def read_year_month_config():
    year = int(read_value_config('General', 'year'))
    month = int(read_value_config('General', 'month'))
    return year, month


def read_single_stations_config():
    single_stations = []
    decision = read_value_config('General', 'use_only_single_stations')
    if decision == 'True':
        single_stations_strings = read_value_config('General', 'single_stations')
        comma_idx = find_all_instances(single_stations_strings, ',')
        start_idx = 0
        for i in comma_idx:
            single_stations.append(single_stations_strings[start_idx:i])
            start_idx = i + 1
        single_stations.append(single_stations_strings[start_idx+1::])
    return single_stations


def check_link_availability(link):
    assert isinstance(link, str)
    try:
        Dataset(link)
    except RuntimeError:
        logger.debug('We failed to reach a server.')
        return False
    else:
        return True


def get_station_name_from_link(prior_string, posterior_string, cur_link):
        assert cur_link, str
        start_str = prior_string
        idx_start = cur_link.find(start_str)
        idx_end = cur_link.find(posterior_string)
        return cur_link[idx_start+len(start_str):idx_end]
