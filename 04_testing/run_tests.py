import unittest
from tests.functional import test_fields, test_storage
from tests.integration import test_api

def run_test(test_cases):
    class NewResult(unittest.TextTestResult):
        def getDescription(self, test):
            doc_first_line = test.shortDescription()
            return doc_first_line or ""

    class NewRunner(unittest.TextTestRunner):
        resultclass = NewResult

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for t in test_cases:
        case = loader.loadTestsFromTestCase(t)
        suite.addTest(case)
    runner = NewRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_test(test_fields.TEST_CASES)
    run_test(test_storage.TEST_CASES)
    run_test(test_api.TEST_CASES)
