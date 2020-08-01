import unittest
import functools
import api
from validation_error import ValidationError


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestField(unittest.TestCase):
    @cases([{'required': True, 'nullable': False, 'value': 'Artem'},
            {'required': True, 'nullable': True, 'value': ''},
            {'required': False, 'nullable': False, 'value': None},
            {'required': False, 'nullable': True, 'value': None},
            {'required': False, 'nullable': True, 'value': ''}])
    def test_valid_combinations(self, arguments):
        """ Test parent's field required and nullable VALID combinations """
        r, n, v = arguments['required'], arguments['nullable'], arguments['value']
        # Must not rise ValidationError
        api.Field(required=r, nullable=n, value=v).check_requirements()

    @cases([{'required': True, 'nullable': False, 'value': None},
            {'required': True, 'nullable': False, 'value': ''},
            {'required': True, 'nullable': True, 'value': None},
            {'required': False, 'nullable': False, 'value': ''}])
    def test_invalid_combinations(self, arguments):
        """ Test parent's field required and nullable INVALID combinations """
        r, n, v = arguments['required'], arguments['nullable'], arguments['value']
        with self.assertRaises(ValidationError):
            api.Field(required=r, nullable=n, value=v).check_requirements()

class TestCharField(unittest.TestCase):
    @cases(['', 'Text', 1, -2, 0.1, 1/3])
    def test_valid_value(self, val):
        """ Test CharField VALID values """
        api.CharField(required=False, nullable=True, value=val).validate()

    @cases([1, -1, 0.1, 1/3])
    def test_invalid_value(self, v):
        """ Test CharField INVALID values """
        with self.assertRaises(ValidationError):
            api.CharField(required=False, nullable=True, value=v, name='first_name').validate()
            api.CharField(required=False, nullable=True, value=v, name='last_name').validate()

class TestArgumentsField(unittest.TestCase):
    @cases([{}, [], {'key': 'val'}, [1, 2]])
    def test_valid_value(self, val):
        """ Test ArgumentsField VALID values """
        api.ArgumentsField(required=False, nullable=True, value=val).check_type()

    @cases(['', True, 1, 1/3, -1])
    def test_invalid_value(self, val):
        """ Test ArgumentsField INVALID values """
        with self.assertRaises(ValidationError):
            api.ArgumentsField(required=False, nullable=True, value=val).check_type()
class TestEmailField(unittest.TestCase):
    @cases(['otus@yandex.ru'])
    def test_valid_value(self, val):
        """ Test EmailField VALID values """
        api.EmailField(required=False, nullable=True, value=val).validate()

    @cases(['chirkov', 1, 0.1])
    def test_invalid_value(self, val):
        """ Test EmailField INVALID values """
        with self.assertRaises(ValidationError):
            api.EmailField(required=False, nullable=True, value=val).validate()

class TestPhoneField(unittest.TestCase):
    @cases(['79161234567', 79161234567])
    def test_valid_value(self, val):
        """ Test PhoneField VALID values """
        api.PhoneField(required=False, nullable=True, value=val).validate()

    @cases(['89161234567', 89161234567,
            '791612345678', 791612345678,
            '7916123456', 7916123456,
            'abcabcabcab', '7bcabcabcab', '7.161234567', '7*^/1234567'
            ])
    def test_invalid_value(self, val):
        """ Test PhoneField INVALID values """
        with self.assertRaises(ValidationError):
            api.PhoneField(required=False, nullable=True, value=val).validate()

class TestDateField(unittest.TestCase):
    @cases(['15.05.1993'])
    def test_valid_value(self, val):
        """ Test DateField VALID values """
        api.DateField(required=False, nullable=True, value=val).validate()

    @cases(['15-05-1993', '15.05.93', '05.15.1993', '32.05.1993',
            'dd.mm.yyyy', 15051993])
    def test_invalid_value(self, val):
        """ Test DateField INVALID values """
        with self.assertRaises(ValidationError):
            api.DateField(required=False, nullable=True, value=val).validate()

class TestBirthDayField(unittest.TestCase):
    @cases(['15.05.1993'])
    def test_valid_value(self, val):
        """ Test BirthDayField VALID values """
        api.BirthDayField(required=False, nullable=True, value=val).validate()

    @cases(['15.05.1923'])
    def test_invalid_value(self, val):
        """ Test BirthDayField INVALID values """
        with self.assertRaises(ValidationError):
            api.BirthDayField(required=False, nullable=True, value=val).validate()

class TestGenderField(unittest.TestCase):
    @cases([0, 1, 2])
    def test_valid_value(self, val):
        """ Test GenderField VALID values """
        api.GenderField(required=False, nullable=True, value=val).validate()

    @cases(['0', '1', '2', 3])
    def test_invalid_value(self, val):
        """ Test GenderField INVALID values """
        with self.assertRaises(ValidationError):
            api.GenderField(required=False, nullable=True, value=val).validate()

class ClientIDsField(unittest.TestCase):
    @cases([[0, 1], [1]])
    def test_valid_value(self, val):
        """ Test ClientIDsField VALID values """
        api.ClientIDsField(required=False, nullable=True, value=val).validate()

    @cases([[], {'key': 1}, 'text', [1, 'a'], [1.1, 2.2], [[1, 2], [3, 4]]])
    def test_invalid_value(self, val):
        """ Test ClientIDsField INVALID values """
        with self.assertRaises(ValidationError):
            api.ClientIDsField(required=False, nullable=True, value=val).validate()


if __name__ == "__main__":
    class NewResult(unittest.TextTestResult):
        def getDescription(self, test):
            doc_first_line = test.shortDescription()
            return doc_first_line or ""

    class NewRunner(unittest.TextTestRunner):
        resultclass = NewResult
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    field_tests = [TestField, TestCharField, TestArgumentsField, TestEmailField,
                   TestPhoneField, TestDateField, TestBirthDayField, TestGenderField,
                   ClientIDsField]
    for t in field_tests:
        case = loader.loadTestsFromTestCase(t)
        suite.addTest(case)
    runner = NewRunner(verbosity=2)
    runner.run(suite)