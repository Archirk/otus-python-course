import functools
import unittest


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


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
