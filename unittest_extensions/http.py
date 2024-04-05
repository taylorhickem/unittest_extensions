import re
import requests
from unittest_extensions.cases import StandardTestCase


HTTP_VERBS = [
    'get',
    'post',
    'put',
    'patch',
    'delete'
]
RESPONSE_TYPES = [
    'text',
    'json'
]
EVALUATE_ATTRIBUTES = [
    'status_code',
    'text',
    'regex'
]


class HTTPTestCase(StandardTestCase):
    http_code = 500
    http_verb = 'get'
    evaluate = {'include': {'status_code': [200]}}
    query_parameters = {}
    headers = {}
    body = {}
    verify_ssl = False
    response = None
    text = ''
    json = {}
    errors = ''

    def __init__(self, methodName, endpoint, request_params={}, **kwargs):
        self.endpoint = endpoint
        if request_params:
            self._set_request_parameters(request_params)
        setattr(self, methodName, self.test_endpoint)
        super(HTTPTestCase, self).__init__(methodName, **kwargs)

    def _set_request_parameters(self, params):
        for k in params:
            setattr(self, k, params[k])        

    def test_endpoint(self):
        self.fetch()
        try:
            self.evaluate_response()
            errors = self.errors
            if errors:
                success = False
            else:
                success = True
        except Exception as e:
            success = False
            errors = str(e)
        if errors:
            self.save_test_result(success, errors=errors)
        else:
            self.save_test_result(success)
        self.assertTrue(success)
        
    def has_allowed_verb(self):
        return self.http_verb in HTTP_VERBS

    def evaluate_response(self):
        if self.evaluate:
            include = self.evaluate.get('include', {})
            exclude = self.evaluate.get('exclude', {})
            if include:
                for k in include:
                    self.evaluate_attribute(k, include[k])
            if exclude:
                for k in exclude:
                    self.evaluate_attribute(k, exclude[k], include=False)
    
    def evaluate_attribute(self, attribute, value, include=True):
        success = False
        json_contents = self.response_json()
        text_contents = self.response.text if self.response.ok else ''
        if attribute == 'regex':
            test_value = text_contents
            if include:
                if isinstance(value, list):
                    for r in value:
                        self.assertRegexMatches(test_value, r)
                else:
                    self.assertRegexMatches(test_value, value)
            else:
                if isinstance(value, list):
                    for r in value:
                        self.assertNotRegexMatches(test_value, r)
                else:
                    self.assertNotRegexMatches(test_value, value)
        elif hasattr(self.response, attribute):            
            test_value = getattr(self.response, attribute) if hasattr(self.response, attribute) else None
            self.compare_values(test_value, value, include)
        elif hasattr(self, attribute):
            test_value = getattr(self, attribute) if hasattr(self, attribute) else None
            self.compare_values(test_value, value, include)
        elif json_contents:
            test_value = json_contents.get(attribute, None)
            self.compare_values(test_value, value, include)
        else:
            eval_error = f'ERROR. unrecognized evaluate attribute: {attribute}'
            self.errors = self.errors + '\n' + eval_error if self.errors else eval_error                       
            raise ValueError(self.errors)

    def response_json(self):
        contents = {}
        if 'application/json' in self.response.headers.get('Content-Type', ''):
            try:
                contents = self.response.json()
            except:
                pass
        return contents

    def compare_values(self, test_value, value, include):
        if include:
            if isinstance(value, list):
                self.assertIn(test_value, value)
            elif value == '*':
                self.assertIsNotNone(test_value)
            elif value == '':
                self.assertIsNone(test_value)
            else:
                self.assertEqual(test_value, value)
        else:
            if isinstance(value, list):
                self.assertNotIn(test_value, value)
            else:
                self.assertNotEqual(test_value, value)

    def fetch(self):
        errors = ''
        if self.has_allowed_verb():
            request_args = self._get_request_args()                                     
            try:
                self.response = getattr(requests, self.http_verb)(self.endpoint, **request_args)
            except Exception as e:
                self.errors = f'ERROR. Failed to fetch {self.http_verb} response from endpoint {self.endpoint} with request arguments {request_args}. {str(e)}'
            else:
                self.http_code = self.response.status_code
        else:
            self.errors = f'ERROR. {self.http_verb} not a recognized HTTP verb. allowed values {HTTP_VERBS}'                    
                
    def _get_request_args(self):
        request_args = {
            'headers': self.headers,
            'params': self.query_parameters,
            'verify': self.verify_ssl,
            'json': self.body
        }
        args = list(request_args.keys())
        for k in args:
            arg_value = request_args[k]
            if isinstance(arg_value, dict):
                if not arg_value:
                    del request_args[k]
            elif arg_value is None:
                    del request_args[k]
        return request_args
