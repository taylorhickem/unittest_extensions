import os
import json
import pandas as pd
from unittest_extensions.cases import StandardTestCase


ENCODING_DEFAULT = 'utf-8'
conn = None


class SQLTestCase(StandardTestCase):
    column_encoding = ''    
    param_sub_method = 'connection'
    query = ''
    expected = {}
    params = {}
    response = []
    errors = ''

    def __init__(self, methodName, query, connection, expected, params={}, **kwargs):
        self.query, input_e = read_path_or_string(query)        
        self.expected, expected_e = read_path_or_dict(expected)
        connection_e = self._set_connection(connection)
        self.params = params
        for errors in [input_e, connection_e, expected_e]:
            self._error_handle(errors, suppress=True)
        self._error_handle()        
        setattr(self, methodName, self.test_sql)
        super(SQLTestCase, self).__init__(methodName, **kwargs)

    def _error_handle(self, errors='', suppress=False):
        if errors:
            self.errors = self.errors + '\n' + errors if self.errors else errors
        if not suppress and self.errors:
            raise ValueError(self.errors)

    def test_sql(self):
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
        self.evaluate_response()

    def evaluate_response(self):
        if self.response:
            for row in self.response:
                self.evaluate_row(row)
        else:
            errors = 'query results empty'
            self._error_handle(errors)

    def evaluate_row(self, row):
        for c, criteria in self.expected.items():
            if c in row:
                test_value = row[c]
                standard = criteria['standard']
                operator = criteria['operator']
                self.compare_values(row[c], criteria['standard'], criteria['operator'], label=c)
            else: 
                errors = f'expected column: {c} not found in results: {row}'
                self._error_handle(errors)
                       
    def compare_values(self, test_value, standard, operator, label=''):
        fail_msg = f'{label} {test_value} is not {operator} {standard}'
        if operator == '=':                    
            self.assertEqual(test_value, standard, msg=fail_msg)
        elif operator == '!=':
            self.assertNotEqual(test_value, standard, msg=fail_msg)
        elif operator == '>=':
            self.assertGreaterEqual(test_value, standard, msg=fail_msg)
        elif operator == '<=':
            self.assertLessEqual(test_value, standard, msg=fail_msg)
        elif operator == '<':
            self.assertLess(test_value, standard, msg=fail_msg)
        elif operator == '>':
            self.assertGreater(test_value, standard, msg=fail_msg)

    def conn(self):
        return conn

    def connected(self):
        return self.conn() is not None

    def _set_connection(self, connection):
        is_live, errors = is_live_connection(connection)
        if is_live:
            _conn_load(connection)
        return errors

    def disconnect(self):
        _conn_unload()

    def fetch(self):
        errors = ''
        if self.connected():
            if self.param_sub_method == 'before_query':
                self._format_query()
            try:
                qry_results = []
                if self.param_sub_method == 'connection':
                    qry_results = pd.read_sql_query(self.query, con=self.conn(), params=self.params) 
                else:
                    qry_results = pd.read_sql_query(self.query, con=self.conn()) 
                if self.column_encoding and len(qry_results) > 0:
                    columns_decode(qry_results, encoding=self.column_encoding)
                self.response = qry_results.to_dict(orient='records') if len(qry_results) > 0 else []                    
            except Exception as e:
                errors = f'ERROR. Failed to fetch query {self.query} with arguments {self.params}. {str(e)}'
        else:
            errors = f'ERROR. failed to connect to database'
        if errors:
            self._error_handle(errors)
        self.disconnect()

    def _format_query(self):
        if self.params:
            self.query = self.query.format(**self.params)
                

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
    
    return dict_value, errors


def read_path_or_string(reference: str) -> str:
    str_value = reference
    errors = ''
    if os.path.exists(reference):
        with open(reference, 'r') as f:
            str_value = f.read()
            f.close()
    if not isinstance(str_value, str):
        errors = f'ERROR. value: {str_value} is not a string literal'
        str_value = ''
    
    return str_value, errors


def is_live_connection(connection):
    success = False
    errors = ''
    sql_stm = 'SELECT 1'
    try:
        connection.cursor().execute(sql_stm)
        success = True
    except Exception as e:
        errors = f'ERROR. execute SQL SELECT 1 failed. {str(e)}'
    return success, errors


def _conn_load(connection):
    global conn
    conn = connection    


def _conn_unload():
    global conn
    errors = ''
    if conn:
        try:
            conn.close()
        except Exception as e:
            errors = f'ERROR. error encountered when attempting to close connection. {str(e)}'
        conn = None
    return errors


def columns_encode(df, encoding=ENCODING_DEFAULT):
    columns_bytes = [c.encode(encoding) for c in list(df.columns)]
    df.rename(columns=dict(zip(list(df.columns), columns_bytes)), inplace=True)
    
    
def columns_decode(df, encoding=ENCODING_DEFAULT):
    columns_str = [c.decode(encoding) for c in list(df.columns)]
    df.rename(columns=dict(zip(list(df.columns), columns_str)), inplace=True)
