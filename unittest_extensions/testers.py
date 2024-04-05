import os
import json
from unittest import TextTestRunner, TestSuite


DEFAULT_LOGS_FILE = 'test_logs.out'
DEFAULT_RESULTS_FILE = 'test_results.json'
DEFAULT_JSON_INDENT = 3


class StandardTester(object):
    tag = ''
    logs_file = DEFAULT_LOGS_FILE
    results_file = DEFAULT_RESULTS_FILE
    json_indent = DEFAULT_JSON_INDENT
    include_success = False
    suite = None
    test_result_files = {}
    test_results = {}
    logs = ''
    summary_results = {}
    file_prefix = ''

    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])    
        if self.file_prefix:
            self._add_prefix()

    def add_test(self, test):
        if self.suite is None:
            self.suite = TestSuite()
        self.suite.addTest(test)
        self.test_result_files.update({test.getMethodName(): test.result_file})

    def _add_prefix(self):
        for f in [
            'logs_file',
            'results_file'
        ]:
            setattr(self, f, f'{self.file_prefix}{getattr(self, f)}')            

    def run(self):
        if self.suite is not None:
            with open(self.logs_file, 'w') as f:
                runner = TextTestRunner(stream=f)
                runner.run(self.suite)
                f.close()

    def update(self):
        results = self.get_test_results()
        self.update_test_results(results)

    def get_logs(self):
        logs = ''
        if os.path.exists(self.logs_file):
            with open(self.logs_file, 'r') as f:
                logs = f.read()
                f.close()
        return logs
        
    def insert_logs(self, inserted_logs):
        if inserted_logs:
            test_logs = self.get_logs()
            logs = inserted_logs + '\n' + test_logs
            with open(self.logs_file, 'w') as f:
                f.write(logs)
                f.close()

    def has_result_files(self):
        return len(self.test_result_files) > 0

    def get_test_results(self):
        test_results = {}
        if self.has_result_files():
            for test_id in self.test_result_files:
                filename = self.test_result_files[test_id]
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        test_results[test_id] = json.load(f)       
                        f.close()
        return test_results

    def update_test_results(self, test_results):
        self.test_results.update(test_results)

    def get_summary_results(self):
        flat_results = self.test_results
        test_ids = list(flat_results.keys())
        statistics = results_statistics(flat_results)
        failed = {k: flat_results[k] for k in flat_results if not flat_results[k]['success']}
        results = {
            'test_ids': test_ids,
            'statistics': statistics,
            'failed': failed
        }
        if self.include_success:
            success = {k: flat_results[k] for k in flat_results if flat_results[k]['success']}
            results['success'] = success
        if self.tag:
            results['tag'] = self.tag
        return results    

    def save_summary_results(self):
        summary_results = self.get_summary_results()
        filename = self.results_file
        with open(filename, 'w') as f:
            json.dump(summary_results, f, indent=self.json_indent)
            f.close()        


def results_statistics(test_results):
    statistics = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    if test_results:
        statistics['total'] = len(test_results)
        statistics['passed'] = sum([1 for t in test_results if test_results[t]['success']])
        statistics['failed'] = statistics['total'] - statistics['passed'] 
    return statistics