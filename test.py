# -*- coding: utf-8 -*-
import sys
import unittest
import time
import json
from pprint import pprint
import hose as h

class TestHose(unittest.TestCase):

    def setUp(self):
        pass
    #
    # todo: cover all fittings.
    #
    def test_fmt(self):
        """test formatter"""

        # format python tuple as tsv
        self.assertEqual(
            (h.vals([('foo', 'bar')]) >> h.fmt("{1}\t{0}") >> h.out() >> h.catch()).run(),
            ['bar\tfoo'])

        # dictionary-based formatting
        self.assertEqual(
            (h.vals([dict(foo=42, bar=66)]) >> h.fmt("meaning={foo}. route={bar}") >> h.out() >> h.catch()).run(),
            ['meaning=42. route=66'])

        # singleton case
        self.assertEqual(
            (h.vals(["HAI"]) >> h.fmt("OH {0}") >> h.out() >> h.catch()).run(),
            ['OH HAI'])

    def test_fetch(self):
        """test url fetch"""
        # todo: repeat this with cache.
        import threading
        import BaseHTTPServer
        from SimpleHTTPServer import SimpleHTTPRequestHandler

        try:
            server=BaseHTTPServer.HTTPServer(('127.0.0.1', 18888), SimpleHTTPRequestHandler)

            httpd=threading.Thread(target=server.serve_forever)
            httpd.start()
            time.sleep(1)

            search_url='http://localhost:18888/data/search-result.json'
            outputs=(h.vals([search_url]) >> h.fetch() >> h.catch()).run()

            self.assertTrue(len(outputs)==1)
            result_json,=outputs
            result=json.loads(result_json)
            self.assertEqual(result,
                             {'repositories': [{'name': 'yoyodyne', 'owner': 'taro'},
                                               {'name': 'projectA', 'owner': 'jiro'}]})

        finally:
            server.shutdown()

def example():

    p=h.vals(['https://api.github.com/legacy/repos/search/nodejs']) \
        >> h.fetch() \
        >> h.jq('-M', '-r', '.repositories[] | "https://api.github.com/repos/\(.owner)/\(.name)/subscribers"') \
        >> h.head(50) \
        >> h.fetch() \
        >> h.jq('-M', '-r', '.[].login') \
        >> h.hist() \
        >> h.fmt("{1}\t{0}")\
        >> h.out()
    p.run()

if __name__ == '__main__':

    if 'example' in sys.argv:
        example()
    else:
        unittest.main()
