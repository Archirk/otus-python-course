import unittest
import os
import log_analyzer

base_dir = os.path.dirname(os.path.abspath(__file__))
configs = os.path.join(base_dir, 'test_sources', 'configs')


class TestApp(unittest.TestCase):

    def check_files(self, config):
        with open('last_update','r') as d:
            report_name = f'report-{d.read()}.html'
        self.assertIs(os.path.isfile('last_update'), True, 'update date cached')  # Parsed log date saved to file
        self.assertIs(os.path.isdir(config[1]), True, 'report folder created')  # Folder for reports exists/created
        if config[3] is not None:
            self.assertIs(os.path.isfile(config[3]), True, 'app_log created')  # Logger initialized
        self.assertIs(os.path.isfile(config[4]), True, 'analyzed data cached')  # Analyzed data cached
        self.assertIs(os.path.isfile(os.path.join(config[1], report_name)), True, 'analyzed data cached')  # report created

    def test_run(self):
        args = ['path', '--config', os.path.join(configs, 'config.json')]
        config = log_analyzer.read_config(args)
        log_analyzer.main(args)
        self.check_files(config)


if __name__ == '__main__':
    unittest.main()