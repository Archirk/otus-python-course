#!/usr/bin/env python
# -*- coding: utf-8 -*-
# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import os
import sys
import json
import logging
import gzip
import re
from string import Template
from statistics import median


def create_app_logger(logpath):
    fmt, dfmt = '[%(asctime)s] %(levelname).1s %(message)s', '%Y.%m.%d %H:%M:%S'
    if logpath is None:
        logging.basicConfig(stream=sys.stdout, format=fmt, datefmt=dfmt, level=logging.INFO)
    else:
        logging.basicConfig(filename=logpath, format=fmt, datefmt=dfmt, level=logging.INFO)


def read_config(args=[]):
    # Set default config in case config is not provided
    config = {'REPORT_SIZE': 1000, 'APP_LOG': None}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config['LOG_DIR'], config['REPORT_DIR'], config['CACHE'] = map(lambda x: os.path.join(base_dir, x),
                                                                   ['log_dir', 'reports', 'output.json'])

    # Read config if it is provided
    if len(args) == 3 and args[1] == '--config':
        with open(args[2], 'r') as c:
            for k, v in json.load(c).items():
                if k in config and v != '':
                    config[k] = v

    # Create report directory if it does not exist
    if not os.path.isdir(config['REPORT_DIR']):
        os.mkdir(config['REPORT_DIR'])

    # Check if log folder exist
    if not os.path.isdir(config['LOG_DIR']):
        f = config['LOG_DIR']
        logging.error(f'Log folder not found: {f}')
        return None

    return config['REPORT_SIZE'], config['REPORT_DIR'], config['LOG_DIR'], config['APP_LOG'], config['CACHE']


def get_last_log(dirpath, log_type='nginx-access-ui'):
    regx = re.compile(r'.gz$|.log-\d\d\d\d\d\d\d\d$')
    try:
        log = max(
            ((j, j.split('.')[1].split('-')[1], j.split('.')[-1]) for x in os.walk(dirpath)
             for j in [s for s in x[2] if regx.search(s)] if log_type in j.split('.')[0]))
        # If exist .gz and plain text log with same date - gz log is returned
    except ValueError:  # If log_type logs does not exist in folder
        logging.error(f'{log_type} logs not found in {dirpath}')
        return None
    logging.info(f'Got log: {log[0]} from {dirpath}')
    return os.path.join(dirpath, log[0]), log[0], log[1], log[2]


def is_parsed(log_date):
    if not os.path.isfile('last_update'):
        return False
    with open('last_update', 'r') as f:
        return f.readline() >= log_date


def parse(log, extension):
    err_level, total_rows, unparsed_rows = 0.2, 0, 0
    if extension == 'gz':
        f = gzip.open(log, 'rb')
    else:
        f = open(log, 'rb')
    for line in f:
        total_rows += 1
        try:
            line = line.decode('utf8').rstrip('\n').split(' ')
            # Request is first "string" attribute with spaces, consisting of $METHOD, $URL, $PROTOCOL.
            # So if method not found at line[6] app is unable to get URL
            if line[6].replace('\"', '') not in ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE']:
                unparsed_rows += 1
                continue
            row = (line[7], float(line[-1]))  # (url, request_time)
            yield row
        except Exception as e:
            unparsed_rows += 1
            continue
    f.close()
    try:
        err_share = round(unparsed_rows / total_rows, 2)
    except ZeroDivisionError:
        logging.error(f'Log is empty: {log} ')
        err_share = 1.0
    if err_share >= err_level:
        logging.error(f'{err_share * 100}% ({unparsed_rows}) log were not parsed.')
        yield None


def analyze(*gen):
    # Aggregate absolute metrics by url
    data = {'report': {}, 'total_time': 0.0, 'count_total': 0}
    for log_row in gen:
        # Return None if error share during parsing above recommended level
        if log_row is None:
            return None
        url, t = log_row
        data['total_time'] += t
        data['count_total'] += 1

        if url not in data['report']:
            data['report'][url] = {'count': 1, 'time_avg': t, 'time_max': t, 'time_sum': t, 'url': url,
                                   'time_med': t, 'durations': [t]}

        else:
            data['report'][url]['count'] += 1
            data['report'][url]['time_sum'] += t
            data['report'][url]['durations'].append(t)
            data['report'][url]['time_avg'] = data['report'][url]['time_sum'] / data['report'][url]['count']
            if t > data['report'][url]['time_max']:
                data['report'][url]['time_max'] = t

    # Calculate averages
    rows = []
    for k, v in data['report'].items():
        v['time_perc'] = v['time_sum'] / data['total_time']
        v['count_perc'] = v['count'] / data['count_total']
        v['time_med'] = median(v['durations'])
        del v['durations']

        # Formatting
        for metric in v:
            if metric in ['count_perc', 'time_perc']:
                v[metric] = '{:.1%}'.format(v[metric])
            elif metric in ['time_avg', 'time_sum', 'time_med']:
                v[metric] = round(v[metric], 3)

        rows.append(v)
    return rows


def create_report(data, report_dir, date):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template, report = os.path.join(base_dir, 'report.html'), os.path.join(report_dir, f'report-{date}.html')
    if not os.path.isfile(template):
        logging.error('report.html TEMPLATE not found. Report was not created')
        return 0

    with open(template, 'r') as tmp, open(report, 'w') as report:
        report.write(Template(tmp.read()).safe_substitute(table_json=json.dumps(data)))


def main(args):
    # Set config
    try:
        config = read_config(args)  # Returns None if log folder is not found
        if config is None:
            sys.exit(f'Log folder does not exist. Check config.')
        size, report_dir, log_dir, app_log, cache = config
    except Exception as e:
        sys.exit(f'Unable to get config: {e}')

    # Initialize logging (have to do here do because need app_log path from config)
    create_app_logger(app_log)

    # Get and analyze log data
    log_data = get_last_log(log_dir)
    if log_data is not None:
        log, log_name, log_date, extension = log_data
        if not is_parsed(log_date):
            logging.info(f'Parsing {log}')
            parsed_log = parse(log, extension)
            logging.info(f'Analysis is launched')
            data = analyze(*parsed_log)
            logging.info(f'Analysis is finished')
            with open(cache, 'w') as c:
                logging.info(f'Saving results...')
                c.write(json.dumps(data))
        else:
            logging.info(f'Log was already parsed. Loading cache.')
            if os.path.isfile(cache):
                with open(cache, 'r') as c:
                    data = json.load(c)
            else:
                logging.error('Cached data not found. Delete last_update file to parse log.')
                data = None

        if data is None:  # None returns from analyze() if many rows are not parsed or cached data not found
            sys.exit('Quality data is not provided')
        data = sorted(data, key=lambda x: x['count'], reverse=True)[0:int(size)]  # In case size in config as str

        with open('last_update', 'w') as f:
            f.write(str(log_date))
        try:
            create_report(data, report_dir, log_date)
        except Exception as e:
            logging.error(f'Failed to create report for {log}: {e}')


if __name__ == "__main__":
    try:
        main(sys.argv)
    except Exception as e:
        logging.exception('Unknown error')
