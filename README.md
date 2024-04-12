# unittests_extensions

An extension to the python library unittest which organizes individual unit tests in a standard format and interface and 
produces a standard unit test result artifact as a JSON file.  

Python unittest documentation [unittest](https://docs.python.org/3/library/unittest.html)

Includes support for HTTP API and SQL query tests

## Example: General Function
test a simple addition function

* create a unit test cases JSON file
* create a unit test function
* run the unit tests from the config file

_directory_

```
- root
  | - arithmatic.py
  | - cases_config.json
  | - test.py
  | - unit_tests.py
```

### Develop

Write a module that you want to test `arithmatic` that performs simple addition and subtraction.

This example contains a bug in the subtract_integers function that we will try to catch using a unit test.

_arithmatic.py_
```

def add_integers(a, b):
    return a + b


def subtract_integers(a, b):
    return a * b

```

### Create unit test cases
Write two unit tests in a config JSON file for the two arithmatic functions.

_cases_config.json_
```
{
	"01_addition": {
		"test_type": "function",
		"module_name": "arithmatic",
		"function_name": "add_integers",
		"inputs": {"a": 1, "b": 2},
		"expected": 3
	},
	"02_subtraction": {
		"test_type": "function",
		"module_name": "arithmatic",
		"function_name": "subtract_integers",
		"inputs": {"a": 1, "b": 2},
		"expected": -1
	}
}
```

### Create unit test function
create a unit tests using unittests_extensions.cases.FunctionTestCase

create a function `create_test` to read the case from file to create a test instance.
To use multiple types of unit tests, use the test case parameter `test_type` and create separate functions
customized for each unit test type.

unit_tests.py
```
from unittest_extensions.cases import FunctionTestCase
import arithmatic

def create_test(test_id, case_config, **kwargs): 
    function_handle = getattr(arithmatic, case_config['function_name'])
    test = FunctionTestCase(
        test_id,
        function_handle,
        case_config['inputs'],
        case_config['expected'],
        **kwargs
    )
    return test

```

### Run unit tests

use the tester unittests_extensions.testers.StandardTester
to run the unit test using the function `create_test` and generate the output results JSON file

test.py
```
import os
import json
from unittest_extensions.testers import StandardTester
from unit_tests import create_test


CASES_CONFIG_FILE = 'cases_config.json'
RESULTS_INCLUDE_SUCCESS = False
CASES_CONFIG = {}
SUMMARY_RESULTS = {} 
LOGS = ''
TEST_COUNT = 0


def run_tests():
    global SUMMARY_RESULTS, LOGS
    results = {}
    for test_id in CASES_CONFIG:
        case_config = CASES_CONFIG[test_id]
        test = create_test(test_id, case_config, save_to_file=True)
        tester = StandardTester(include_success=RESULTS_INCLUDE_SUCCESS)
        tester.add_test(test)
        if results:
            tester.update_test_results(results)        
        tester.run()
        tester.update()
        if LOGS:
            tester.insert_logs(LOGS)
        LOGS = tester.get_logs()
        results = tester.get_test_results()
    SUMMARY_RESULTS = tester.get_summary_results()
            

def load_cases_config():
    global CASES_CONFIG, TEST_COUNT
    if os.path.exists(CASES_CONFIG_FILE):
        with open(CASES_CONFIG_FILE, 'r') as f:
            CASES_CONFIG = json.load(f)
            f.close()           
    if CASES_CONFIG:
        TEST_COUNT = len(CASES_CONFIG)


if __name__ == '__main__':
    load_cases_config()
    run_tests()
    print('summary results \n')
    print(SUMMARY_RESULTS)
    print(\n'logs \n')
    print(LOGS)

```

### Test results

```
{
   "statistics": {
      "total": 2,
      "passed": 1,
      "failed": 1
   },
   "test_ids": [
      "01_addition", 
      "02_subtraction"
   ]
   "failed": {
      "02_subtraction": {
         "success": false,
         "errors": "2 != -1"
      }
   },
   "success": {
      "01_addition": {
         "success": true
      }
   }
}

```


## Test results
the StandardTester.get_summary_results() output includes summary statistics and lists of the test ids as well as their error output for failed test cases. 

summary results
```
{
  "test_date": "",      # string timestamp
  "statistics": {
      "total": 0,       # integer number of tests run
	  "passed": 0,      # integer number of tests passed
	  "failed": 0       # integer number of tests failed
  },
  "test_ids": [],       # list of test ids
  "failed": {},         # test results for failed tests key=test_id with errors
  "success": {},        # (optional) test results for success tests key=test_id. Use optional flag include_success. Default=False
  "tag": ""             # (optional) string label to associate the collection of tests to an app or release
}
```

## HTTP unit test

use the `unittest_extensions.http.HTTPTestCase` class to test endpoint with python requests
[python request documentation](https://requests.readthedocs.io/en/latest/)

### HTTP test case request
The test case request parameters includes configuration for the request including the domain, route headers and query parameters
You can pass optional arguments to the `requests.<verb>` method such as `headers` using the optional `request_params` in the case config.

```
{
	'endpoint':'',         #required                     full url endpoint including https:// and ending with /
	'verb': '',            #(optional) default = GET.    HTTP verb [GET, POST, PUT, UPDATE, DELETE]
	'evaluate': {},        #(optional) default = {'include': {'status_code': [200]}}.    
	'verify_ssl':          #(optional) default = False   verify https ssl certificate True/False
	'request_params':{},   #(optional) default = {}.     arguments to pass to the requests.<verb> method such as headers
}
```

_requests_params_

```
'request_params': {

	'query_parameters':,   #(optional) default = {}.     {key: value} url parameters to be substituted into the generic endpoint
	'headers':{},          #(optional)                    HTTP headers to inclue in the request
	'body':{},             #(optional)                    JSON body as dictionary to include for POST requests
    }
}
```

### HTTP test case evaluate
the test case evaluate parameters specify how to evaluate the HTTP response.
They are grouped into include and exclude. The include group are parameters that are expected in the response and the exclude are those not expected.
Both are optional with the default value set at include status_code = 200.

The status_code is a special case of the general method to evaluate any attribute from the requests.Response object
Another option is to include attribute from the response.json() contents excluding those reserved keywords from the requests.Response object such as "status_code" "json" "text" etc..
Another option is to evaluate a general regex pattern from the response.text contents

evaluate
```
{
    'include': {}          #(optional)          conditions expected in the response
    'exclude': {}          #(optional)          conditions not expected in the response
}
```

```
{
    'include': {
		'status_code':[],          #(optional) default = []    list of HTTP status codes 200, 401 etc..
		<response attribute>:{},   #(optional) default = None  {attribute: value} attribute in the requests.Response object
		<contents attribute>:{},   #(optional) default = None  {attribute: value} attribute in response.json() contents
		'regex':''                 #(optional) default = ''    regex pattern to evaluate on response.text
	}

}
```

## Example: HTTP API endpoint
test an HTTP API endpoint

### test cases

unit test cases
```
{
	"01_http_stock_price_NVDA_available": {
		"test_type": "http",
		"endpoint": "https://financialmodelingprep.com/api/v3/historical-price-full/NVDA/",
		"verb": "get",
		"request_params": {
			"query_parameters": {				
				"apikey": "t7UXHCxTJuwdeZmGxK1h6gbdfigYxMbS"
			}
		},
		"evaluate": {
			"include": {
				"status_code": [200]
			}
		}		
	},
	"02_http_stock_price_NVDA_has_prices": {
		"test_type": "http",
		"endpoint": "https://financialmodelingprep.com/api/v3/historical-price-full/NVDA/",
		"verb": "get",
		"request_params": {
			"query_parameters": {				
				"apikey": "t7UXHCxTJuwdeZmGxK1h6gbdfigYxMbS",
				"from": "2024-01-01",
				"to": "2024-04-02"
			}
		},
		"evaluate": {
			"include": {
				"historical": "*"
			}			
		}		
	}
}

```

### unit test function

unit_tests.py
```
...
from unittest_extensions.http import HTTPTestCase
...
      
def create_test(test_id, case_config, **kwargs):    
    test_type = case_config['test_type']
    if test_type == 'function':

        ...

    elif test_type == 'http':
        required_args = [
            'endpoint'
        ]
        optional_args = {k: case_config[k] for k in case_config if not k in required_args}
        test = _http_test(
            test_id,
            case_config['endpoint'],
            **optional_args,
            **kwargs
        )
     
    return test


def _http_test(test_id, endpoint, **kwargs):    
    test = HTTPTestCase(
        test_id,
        endpoint,
        **kwargs
    )
    return test

```

### test results

```
{
   "statistics": {
      "total": 2,
      "passed": 2,
      "failed": 0
   },
   "test_ids": [
      "01_http_stock_price_NVDA_available", 
      "02_http_stock_price_NVDA_has_prices"
   ]
   "failed": {},
   "success": {
      "01_http_stock_price_NVDA_available": {
         "success": true
      },
      "02_http_stock_price_NVDA_has_prices": {
         "success": true
      }
   }
} 
```

## SQL query test 

uses pandas [read_sql_query](https://pandas.pydata.org/docs/reference/api/pandas.read_sql_query.html) to execute SQL on a 
client supplied connection object.


### SQL query test case
the test case is a JSON file that contains arguments to specify how to execute the SQL test case.

test case
```
{
  'test_type': str,                              required = sql
  'query': str,                                  required                          either string query statement or file reference ex: '01_row_count.sql'
  'connection': *,                               required                          either dictionary or file reference ex: 'redshift_connection.json'
  'expected': dict,                              required                           see below
  'params': dict,                                optional {}                       dictionary of parameters to substitute in the sql query 
  'column_encoding': str,                        optional                          encoding if column names are bytes ex 'utf-8'
  'param_sub_method': str,                       optional default = 'before_query' defines when parameter substitution occurs 'before_query' done by SQLTestCase and 'connection' parameters passed to the connection instance  
  'connection_type': str,                        optional default = 'redshift'
}
```

### SQL test case expected
The expected argument defines how to evaluate the query results. It is organized into
  expected criteria:   column, standard, operator  

expected
```
{
 <column>: {                                 required                            the column in the query results table to be evaluated ex: "row_count"
				'standard': *                required                            reference value to compare against using the operator. data type must match value in the column ex: 0
				'operator': str              required                            comparison operator such as = < != 
			},
}
```

## Example: SQL query row count on AWS Redshift database
test whether the row count in two tables match. Uses AWS python library [redshift-connector](https://pypi.org/project/redshift-connector/) 
to create a connection to a Redshift database.

### SQL query
In this example parameter substitution uses the python string substitution delimiters "{" and "}" for variable names "{SOURCE_SCHEMA}"

01_row_count.sql
```
select
  source_count as row_count,
  target_count - source_count as failed
from
(select
  (select
    count(*)
  from {SOURCE_SCHEMA}.{SOURCE_TABLE_NAME}) as source_count,
  (select
    count(*)
  from {TARGET_SCHEMA}.{TARGET_TABLE_NAME}) as target_count
) as t1
;
```

### test cases

unit test cases
```
{
	"01_bsvisits_row_count": {
		"test_type": "sql",
		"connection_type": "redshift",
		"connection": "redshift_connection.json",
		"column_encoding": "utf-8",
		"param_sub_method": "before_query",
		"query": "01_row_count.sql",
		"params": {
			"SOURCE_SCHEMA": "cl_ci",
			"SOURCE_TABLE_NAME":"bsvisits",
			"TARGET_SCHEMA": "cl_ci_dev",
			"TARGET_TABLE_NAME":"cl_rcode_bsvisits"
			},
		"expected": {
			"row_count": {
				"standard": 0,
				"operator": ">"
			},
			"failed": {
				"standard": 0,
				"operator": "="
			}
		}
	},
	"02_calltxns_row_count": {
		"test_type": "sql",
		"connection_type": "redshift",
		"connection": "redshift_connection.json",
		"column_encoding": "utf-8",
		"param_sub_method": "before_query",
		"query": "01_row_count.sql",
		"params": {
			"SOURCE_SCHEMA": "cl_ci",
			"SOURCE_TABLE_NAME":"cc_calltrans",
			"TARGET_SCHEMA": "cl_ci_dev",
			"TARGET_TABLE_NAME":"cl_rcode_calltransaction"
			},
		"expected": {
			"row_count": {
				"standard": 0,
				"operator": ">"
			},
			"failed": {
				"standard": 0,
				"operator": "="
			}
		}
	}
}
```


### unit test function
create a python file `unit_tests.py` with a function `create_test` that reads from config and uses the class `unittest_extensions.sql.SQLTestCase`
The connection type used is the AWS Redshift python package `redshift_connector`. The custom method `get_connection` created the 
database connection and passes it at construction to SQLTestCase

unit_tests.py
```
import os
import json
import redshift_connector
from unittest_extensions.sql import SQLTestCase


CONNECTION_DEFAULT = 'redshift'
CONNECTIONS = {
    'redshift': {
        'url': 'jdbc:redshift://{host}:{port}/{database}',
        'url_params': ['host', 'port', 'database'],
        'connect_params': ['host', 'port', 'database', 'user', 'password']
    }
}

      
def create_test(test_id, case_config, **kwargs):    
    test_type = case_config['test_type']
    if test_type == 'sql':
        required_args = [
            'query',
            'expected',
            'connection',
        ]        
        optional_args = {k: case_config[k] for k in case_config if not k in required_args}
        test = _sql_test(
            test_id,
            case_config['query'],
            case_config['expected'],
            case_config['connection'],
            **optional_args,
            **kwargs
        )
     
    return test


def _sql_test(test_id, query, expected, connect_spec, 
                connection_type=CONNECTION_DEFAULT, params={}, **kwargs):    
    connect_config = read_path_or_dict(connect_spec)
    conn = get_connection(connect_config, connection_type=connection_type)
    test = SQLTestCase(
        test_id,
        query,
        conn,
        expected,
        params=params,
        **kwargs
    )
    return test
    

def get_connection(connect_params, connection_type=CONNECTION_DEFAULT):
    conn = None
    conn_args = {k: connect_params[k] for k in CONNECTIONS[connection_type]['connect_params']}
    if connection_type == 'redshift':
        conn = redshift_connector.connect(**conn_args)
    return conn
    

def read_path_or_dict(reference) -> dict:
    dict_value = reference
    errors = ''
    if not isinstance(dict_value, dict):
        if isinstance(reference, str):
            if os.path.exists(reference):
                try:
                    with open(reference, 'r') as f:
                        dict_value = json.load(f)
                        f.close()
                except Exception as e:
                    errors = f'ERROR. Error reading JSON file into dictionary. {str(e)}'
    if not isinstance(dict_value, dict):
        errors = f'ERROR. value: {dict_value} is not a python dictionary. {errors}'
        dict_value = {}
    
    if errors:
        raise ValueError(errors)

    return dict_value

```


### test results

```
{
   "test_ids": [
      "01_bsvisits_row_count",
      "02_calltxns_row_count"
   ],
   "statistics": {
      "total": 2,
      "passed": 0,
      "failed": 2
   },
   "failed": {
      "01_bsvisits_row_count": {
         "success": false,
         "errors": "-1144 != 0 : failed -1144 is not = 0"
      },
      "02_calltxns_row_count": {
         "success": false,
         "errors": "137 != 0 : failed 137 is not = 0"
      }
   },
   "success": {}
}
```

