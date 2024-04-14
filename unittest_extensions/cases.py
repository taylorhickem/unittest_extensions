import json
from unittest import TestCase


DEFAULT_JSON_INDENT = 3


class StandardTestCase(TestCase):
    tag = ''
    test_id = ''
    save_to_file = False
    result_file = ''
    json_indent = DEFAULT_JSON_INDENT
    file_prefix = ''
    
    def __init__(self, methodName, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])
        super(StandardTestCase, self).__init__(methodName)
        self._set_result_filename()
        if self.file_prefix:
            self._add_prefix()

    @classmethod
    def setUpClass(cls, **kwargs):
        cls.test_result = {}
        
    def save_test_result(self, success, **kwargs):
        test_result = {'success': success}
        if kwargs:
            test_result.update(kwargs)
        self.test_result = test_result
        if self.save_to_file:
            with open(self.result_file, 'w') as f:
                json.dump(self.test_result, f, indent=self.json_indent)            
                f.close()

    def getMethodName(self):
        return self._testMethodName
        
    def _set_result_filename(self):
        if self.tag:
            self.result_file = f'{self.tag}_{self._testMethodName}_result.json'
        else:
            self.result_file = f'{self._testMethodName}_result.json'

    def _add_prefix(self):
        self.result_file = f'{self.file_prefix}{self.result_file}'
            

class FunctionTestCase(StandardTestCase):

    def __init__(self, methodName, function_handle, inputs, expected, **kwargs):
        self.function_handle = function_handle
        self.inputs = inputs
        self.expected = expected
        setattr(self, methodName, self.test_function)
        super(FunctionTestCase, self).__init__(methodName, **kwargs)

    def test_function(self):
        actual = self.function_handle(**self.inputs)
        try:
            self.assertEqual(actual, self.expected)
            success = True
            errors = ''
        except Exception as e:
            success = False
            errors = str(e)
        if errors:
            self.save_test_result(success, errors=errors)
        else:
            self.save_test_result(success)
        self.assertEqual(actual, self.expected)
