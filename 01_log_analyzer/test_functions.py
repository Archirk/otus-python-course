import unittest
import os
import log_analyzer as la
from collections import namedtuple

configs = './test_sources/configs'
log_folders = './test_sources/log_folders'
test_logs = './test_sources/log_folders/test_logs'

class TestFunctions(unittest.TestCase):

    def setUp(self):
        self.err_level = 0.2
        args = namedtuple('namespace_test', 'config')
        self.test_args = args(f'{configs}/config.json')
        self.log_folder_1 = f'{log_folders}/log_folder_1'  # Choosing between diff. extensions and formatting
        self.log_folder_2 = f'{log_folders}/log_folder_2'  # Choosing the latest log
        self.log_folder_3 = f'{log_folders}/log_folder_3'  # Check folder without required logs
        self.test_log_1 = f'{test_logs}/nginx-access-ui.log-00000001'  # Normal rows
        self.test_log_2 = f'{test_logs}/nginx-access-ui.log-00000002'  # 2/10 rows with unparsed request
        self.test_log_3 = f'{test_logs}/nginx-access-ui.log-00000003'  # 3/10 rows with unparsed time
        self.test_log_4 = f'{test_logs}/nginx-access-ui.log-00000004'  # Empty log
        self.test_log_5 = f'{test_logs}/nginx-access-ui.log-00000005'  # Normal log

    def test_get_last_log(self):
        self.assertEqual(la.get_last_log(self.log_folder_1)[1], 'nginx-access-ui.log-20170610.gz')
        self.assertEqual(la.get_last_log(self.log_folder_2)[1], 'nginx-access-ui.log-20170611')
        self.assertRaises(Exception, la.get_last_log, self.log_folder_3)

    def test_parse(self):
        self.assertEqual(len(list(la.parse(self.test_log_1, self.err_level))), 10)
        self.assertRaises(Exception, la.parse, (self.test_log_2, self.err_level))
        self.assertRaises(Exception, la.parse, (self.test_log_3, self.err_level))
        self.assertRaises(Exception, la.parse, (self.test_log_4, self.err_level))

    def test_analyze(self):
        data_1 = la.analyze(la.parse(self.test_log_5, self.err_level))
        self.assertEqual(data_1[0]['time_max'], 0.5)
        self.assertEqual(data_1[0]['count'], 5)
        self.assertEqual(data_1[0]['count_perc'], '50.0%')
        self.assertEqual(data_1[0]['time_med'], 0.3)
        self.assertEqual(data_1[0]['time_perc'], '50.0%')

    def test_read_configs(self):
        config_default = la.read_config(self.test_args)
        config_default_expected = {
            'REPORT_SIZE': 100,
            'REPORT_DIR': './reports',
            'LOG_DIR': '/var/log/nginx',
            'APP_LOG': './app.log',
            'ERROR_LEVEL': 0.2}
        self.assertEqual(config_default, config_default_expected)


if __name__ == '__main__':
    unittest.main()
