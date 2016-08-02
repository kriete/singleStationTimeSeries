from utils import *


class SingleStationViewer:
    def __init__(self):
        self.base_html = None
        self.start_year = None
        self.end_year = None
        self.start_month = None
        self.end_month = None
        self.station_name = None
        self.variable_name = None
        self.sorted_idx = None
        self.converted_time = None
        self.converted_time_backward = None
        self.output_path = None
        self.station_links = []
        self.time = []
        self.values = []
        self.read_config_params()
        self.read_station_links_from_thredds()
        self.read_data_from_links()
        self.create_bokeh_plot()

    def read_config_params(self):
        general_section_name = 'General'
        self.base_html = read_value_config(general_section_name, 'base_html')
        self.start_year = int(read_value_config(general_section_name, 'start_year'))
        self.end_year = int(read_value_config(general_section_name, 'end_year'))
        self.start_month = int(read_value_config(general_section_name, 'start_month'))
        self.end_month = int(read_value_config(general_section_name, 'end_month'))
        self.station_name = read_value_config(general_section_name, 'station_name')
        self.variable_name = read_value_config(general_section_name, 'variable_name')
        self.output_path = read_value_config(general_section_name, 'output_path')

    def read_station_links_from_thredds(self):
        # TODO: bypass eventually different deployments -.- very annoying for processing!
        year_difference = self.end_year - self.start_year
        month_difference = self.end_month - self.start_month
        counter_difference = year_difference * 12 + month_difference
        cur_year = self.start_year
        for x in range(0, counter_difference + 1):
            cur_month = (self.start_month + x - 1) % 12 + 1
            if ((self.start_month + x) % 12) == 1:
                cur_year += 1
            logger.debug(str(cur_month) + ' ' + str(cur_year))
            self.station_links.extend(get_mooring_stations(self.base_html, cur_year, cur_month,
                                                           only_single_stations=self.station_name))

    def read_data_from_links(self):
        # handle non-existent data sources
        for station_link in self.station_links:
            logger.info('Reading {0}'.format(station_link))
            cur_root = Dataset(station_link)
            self.time.extend(get_data_array(cur_root["time"]))
            self.values.extend(get_data_array(cur_root[self.variable_name]))
        self.time = np.asarray(self.time)
        self.values = np.asarray(self.values)
        logger.info('Sorting... Just in case we bypass something later inside here.')
        self.time, self.values, self.sorted_idx = sort_data(self.time, self.values)

    def create_bokeh_plot(self):
        logger.info('Converting time...')
        date_converted = [datetime.fromtimestamp(ts) for ts in self.time]
        self.converted_time = get_pandas_timestamp_series(date_converted)
        logger.info('Create bokeh plot...')
        cur_root = Dataset(self.station_links[0])
        cur_var = cur_root[self.variable_name]
        cur_unit = cur_var.units
        p = get_bokeh_plot(self.values, self.converted_time, cur_unit, self.station_name)
        logger.info('Save bokeh plot...')
        output_file(self.output_path + self.station_name + '_' + self.variable_name + '.html')
        save(p)

