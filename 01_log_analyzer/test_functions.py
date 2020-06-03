import unittest
import os
import log_analyzer

base_dir = os.path.dirname(os.path.abspath(__file__))
log_folders = os.path.join(base_dir,'test_sources', 'log_folders')
test_logs = os.path.join(log_folders, 'test_logs')
configs = os.path.join(base_dir,'test_sources', 'configs')


class TestFunctions(unittest.TestCase):

    def test_get_last_log(self):
        print('Testing log acquiring from folder')
        log_folder_1 = os.path.join(log_folders, 'log_folder_1')  # Choosing between diff. extensions and formatting
        log_folder_2 = os.path.join(log_folders, 'log_folder_2')  # Choosing the latest log
        log_folder_3 = os.path.join(log_folders, 'log_folder_3')  # Check folder without required logs
        self.assertEqual(log_analyzer.get_last_log(log_folder_1)[1], 'nginx-access-ui.log-20170610.gz')
        self.assertEqual(log_analyzer.get_last_log(log_folder_2)[1], 'nginx-access-ui.log-20170611')
        self.assertIs(log_analyzer.get_last_log(log_folder_3), None)

    def test_parse(self):
        test_log_1 = os.path.join(test_logs, 'nginx-access-ui.log-00000001')  # Normal rows
        test_log_2 = os.path.join(test_logs, 'nginx-access-ui.log-00000002')  # 2/10 rows with unparsed request
        test_log_3 = os.path.join(test_logs, 'nginx-access-ui.log-00000003')  # 3/10 rows with unparsed time
        test_log_4 = os.path.join(test_logs, 'nginx-access-ui.log-00000004')  # Empty log

        self.assertEqual(len(list(log_analyzer.parse(test_log_1))), 10)
        self.assertRaises(Exception, log_analyzer.parse(test_log_2))
        self.assertRaises(Exception, log_analyzer.parse(test_log_3))
        self.assertRaises(Exception, log_analyzer.parse(test_log_4))


    def test_analyze(self):
        test_log_1 = os.path.join(test_logs, 'nginx-access-ui.log-00000005')  # Normal log
        parsed_log_1 = log_analyzer.parse(test_log_1)
        data_1 = log_analyzer.analyze(*parsed_log_1)

        test_log_2 = os.path.join(test_logs, 'nginx-access-ui.log-00000004')  # Empty log
        self.assertRaises(Exception, log_analyzer.parse(test_log_2))

        self.assertEqual(data_1[0]['time_max'], 0.5)
        self.assertEqual(data_1[0]['count'], 5)
        self.assertEqual(data_1[0]['count_perc'], '50.0%')
        self.assertEqual(data_1[0]['time_med'], 0.3)
        self.assertEqual(data_1[0]['time_perc'], '50.0%')



    def test_read_configs(self):
        # Get configs if external are not provided
        args = log_analyzer.parse_args()
        config_default = log_analyzer.read_config(args)
        config_default_expected = {
            'REPORT_SIZE': 1000,
            'REPORT_DIR': os.path.join(base_dir, 'reports'),
            'LOG_DIR': os.path.join(base_dir, 'log_dir'),
            'APP_LOG': None,
            'CACHE': os.path.join(base_dir, 'output.json')}
        self.assertEqual(config_default, config_default_expected)



if __name__ == '__main__':
    unittest.main()