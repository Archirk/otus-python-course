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
from collections import namedtuple
import argparse

def create_app_logger(logpath):
    fmt, dfmt = '[%(asctime)s] %(levelname).1s %(message)s', '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(filename=logpath, format=fmt, datefmt=dfmt, level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config')
    return parser.parse_args()

def read_config(args):
    # Set default config in case config is not provided
    config = {'REPORT_SIZE': 1000, 'APP_LOG': None}
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config['LOG_DIR'], config['REPORT_DIR'], config['CACHE'] = map(lambda x: os.path.join(base_dir, x),
                                                                   ['log_dir', 'reports', 'output.json'])

    # Read config if it is provided
    if args.config is not None:
        with open(args.config, 'r') as c:
            for k, v in json.load(c).items():
                if k in config and v != '':
                    config[k] = v
    return config

def check_config(config):
    # Create report directory if it does not exist
    if not os.path.isdir(config['REPORT_DIR']):
        os.mkdir(config['REPORT_DIR'])
    # Check if log folder exist
    if not os.path.isdir(config['LOG_DIR']):
        f = config['LOG_DIR']
        raise Exception(f'Log folder not found: \"{f}\"')


def get_last_log(dirpath, log_type='nginx-access-ui'):
    Logdata = namedtuple('Log', 'path name date')
    try:
        files = list(os.walk(dirpath))[0][2]
        logs = ([s for s in files if re.compile(r'(\.log-\d{8}\.gz$|\.log-\d{8}$)').search(s)])
        log = max([s for s in logs if log_type in s])
        log = (log, log.split('.')[1].split('-')[1])
        # If exist .gz and plain text log with same date - gz log is returned
    except ValueError:  # If log_type logs does not exist in folder
        logging.error(f'{log_type} logs not found in {dirpath}')
        return None
    logging.info(f'Got log: {log[0]} from {dirpath}')
    return Logdata(os.path.join(dirpath, log[0]), log[0], log[1])


def is_parsed(log_date, report_dir):
    return os.path.isfile(os.path.join(report_dir, f'report-{log_date}.html'))


def parse(log):
    err_level, total_rows, unparsed_rows = 0.2, 0, 0
    f = gzip.open(log, 'rb') if log.endswith('gz') else open(log, 'rb')
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
        except Exception:
            unparsed_rows += 1
            continue
    f.close()
    try:
        err_share = round(unparsed_rows / total_rows, 2)
    except ZeroDivisionError:
        logging.error(f'Log is empty: {log} ')
        err_share = 1.0
    if err_share >= err_level:
        msg = f'{err_share * 100}% ({unparsed_rows}) log were not parsed.'
        logging.error(msg)
        raise Exception(msg)


def analyze(*gen):
    # Aggregate absolute metrics by url
    data = {'report': {}, 'total_time': 0.0, 'count_total': 0}
    for log_row in gen:
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
        msg = 'report.html TEMPLATE not found. Report was not created'
        logging.error(msg)
        raise Exception(msg)

    with open(template, 'r') as tmp, open(report, 'w') as report:
        report.write(Template(tmp.read()).safe_substitute(table_json=json.dumps(data)))


def main(args):
    # Set config
    config = read_config(args)
    try:
        check_config(config)
    except Exception as e:
        sys.exit(f'Unable to get config. {e}')

    # Initialize logging (have to do here do because need app_log path from config)
    create_app_logger(config['APP_LOG'])

    # Get and analyze log data
    log_data = get_last_log(config['LOG_DIR'])
    cache = config['CACHE']
    if log_data is not None:
        log, log_name, log_date = log_data
        if not is_parsed(log_date, config['REPORT_DIR']):
            logging.info(f'Parsing {log}')
            try:
                parsed_log = parse(log)
            except Exception as e:
                sys.exit(e)
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
        data = sorted(data, key=lambda x: x['count'], reverse=True)[0:int(config['REPORT_SIZE'])]  # In case size in config as str
        try:
            create_report(data, config['REPORT_DIR'], log_date)
        except Exception as e:
            logging.error(f'Failed to create report for {log}: {e}')


if __name__ == "__main__":
    try:
        main(args=parse_args())
    except Exception as e:
        logging.exception('Unknown error')
