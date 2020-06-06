import unittest
import os
from collections import namedtuple
import log_analyzer as la
import shutil


configs = './test_sources/configs'


class TestApp(unittest.TestCase):

    def setUp(self):
        args = namedtuple('namespace_test', 'config')
        self.test_args = args(f'{configs}/config.json')
        self.config = la.read_config(self.test_args)

    def tearDown(self):
        if os.path.isdir(self.config['REPORT_DIR']):
            shutil.rmtree(self.config['REPORT_DIR'])
        if self.config['APP_LOG'] is not None and os.path.isfile(self.config['APP_LOG']):
            os.remove(self.config['APP_LOG'])

    def check_files(self, config):
        self.assertIs(os.path.isdir(config['REPORT_DIR']), True)  # Folder for reports exists/created
        if config['APP_LOG'] is not None:
            self.assertIs(os.path.isfile(config['APP_LOG']), True)  # Logger initialized
        report_date = la.get_last_log(config['LOG_DIR']).date
        report_name = f'report-{report_date}.html'
        self.assertIs(os.path.isfile(os.path.join(config['REPORT_DIR'], report_name)), True)  # report created

    def test_run(self):
        la.main(self.test_args)
        self.check_files(self.config)


if __name__ == '__main__':
    unittest.main()
