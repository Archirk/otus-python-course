import unittest
import os
from collections import namedtuple
import log_analyzer

base_dir = os.path.dirname(os.path.abspath(__file__))
configs = os.path.join(base_dir, 'test_sources', 'configs')


class TestApp(unittest.TestCase):

    def check_files(self, config):
        self.assertIs(os.path.isdir(config['REPORT_DIR']), True)  # Folder for reports exists/created
        if config['APP_LOG'] is not None:
            self.assertIs(os.path.isfile(config['APP_LOG']), True)  # Logger initialized
        self.assertIs(os.path.isfile(config['CACHE']), True)  # Analyzed data cached
        report_date = log_analyzer.get_last_log(config['LOG_DIR']).date
        report_name = f'report-{report_date}.html'
        self.assertIs(os.path.isfile(os.path.join(config['REPORT_DIR'], report_name)), True)  # report created

    def test_run(self):
        args = namedtuple('namespace_test', 'config')
        test_args = args(os.path.join(configs, 'config.json'))
        config = log_analyzer.read_config(test_args)
        log_analyzer.main(test_args)
        self.check_files(config)


if __name__ == '__main__':
    unittest.main()