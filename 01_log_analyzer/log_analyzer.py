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

Logdata = namedtuple('Log', 'path name date')


def create_app_logger(logpath):
    fmt, dfmt = '[%(asctime)s] %(levelname).1s %(message)s', '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(filename=logpath, format=fmt, datefmt=dfmt, level=logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Path to config')
    return parser.parse_args()


def read_config(args):
    config = {'REPORT_SIZE': 1000,
              'ERROR_LEVEL': 0.2,
              'APP_LOG': None,
              'REPORT_DIR': './reports',
              'LOG_DIR': '/var/log/nginx'}

    if args.config is not None:
        with open(args.config, 'r') as c:
            for k, v in json.load(c).items():
                if k in config and v != '':
                    config[k] = v
    return config


def check_config(config):
    if not os.path.isdir(config['REPORT_DIR']):
        os.mkdir(config['REPORT_DIR'])

    if not os.path.isdir(config['LOG_DIR']):
        f = config['LOG_DIR']
        raise Exception(f'Log folder not found: \"{f}\"')


def get_last_log(dir_path):
    files, pat = os.listdir(dir_path), re.compile(r'^nginx-access-ui\.log-\d{8}(\.gz$|$)')
    logs = [f for f in files if pat.search(f)]
    if len(logs) == 0:
        msg = f'Logs not found in {dir_path}'
        logging.error(msg)
        raise Exception(msg)
    log = max(logs)  # If exist .gz and plain text log with same date - gz log is returned
    log = (log, log.split('.')[1].split('-')[1])
    logging.info(f'Got log: {log[0]} from {dir_path}')
    return Logdata(f'{dir_path}/{log[0]}', log[0], log[1])


def is_parsed(log_date, report_dir):
    return os.path.isfile(f'{report_dir}/report-{log_date}.html')


def parse(log, err_level):
    total_rows, unparsed_rows = 0, 0
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


def analyze(gen):
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

    rows = []
    for k, v in data['report'].items():
        v['time_perc'] = v['time_sum'] / data['total_time']
        v['count_perc'] = v['count'] / data['count_total']
        v['time_med'] = median(v['durations'])
        del v['durations']

        for metric in v:
            if metric in ['count_perc', 'time_perc']:
                v[metric] = '{:.1%}'.format(v[metric])
            elif metric in ['time_avg', 'time_sum', 'time_med']:
                v[metric] = round(v[metric], 3)

        rows.append(v)
    return rows


def create_report(data, report_dir, date):
    template, report = './report.html', f'{report_dir}/report-{date}.html'
    if not os.path.isfile(template):
        msg = 'report.html TEMPLATE not found. Report was not created'
        logging.error(msg)
        raise Exception(msg)

    with open(template, 'r') as tmp, open(report, 'w') as report:
        report.write(Template(tmp.read()).safe_substitute(table_json=json.dumps(data)))


def main(args):
    config = read_config(args)
    try:
        check_config(config)
    except Exception as e:
        sys.exit(f'Unable to get config. {e}')

    create_app_logger(config['APP_LOG'])
    log, log_name, log_date = get_last_log(config['LOG_DIR'])

    if is_parsed(log_date, config['REPORT_DIR']):
        logging.info(f'Log was already parsed and analyzed.')
    else:
        logging.info(f'Parsing {log}')
        try:
            parsed_log = parse(log, config['ERROR_LEVEL'])
        except Exception as e:
            sys.exit(e)
        logging.info(f'Analysis is launched')
        data = analyze(parsed_log)
        logging.info(f'Analysis is finished')

        data = sorted(data, key=lambda x: x['count'], reverse=True)[0:int(config['REPORT_SIZE'])]  # If SIZE is str
        create_report(data, config['REPORT_DIR'], log_date)


if __name__ == "__main__":
    try:
        main(args=parse_args())
    except Exception as e:
        logging.exception('Unknown error')
