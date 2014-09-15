#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import datetime
import os, sys
import json
import urllib
import urllib2

from scrapy.http import Request
from scrapy.item import *
from scrapy.selector import *
from scrapy.contrib.spiders import CrawlSpider
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy import log

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tmp_path = os.path.join(root_path, 'tmp')
good_proxy_file = os.path.join(tmp_path, 'goodproxy.list')

class CheckproxySpider(CrawlSpider):
    name = "checkproxy"
    check_proxy_url = 'http://checkerproxy.net/checker2.php'

    def __init__(self):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.current_proxy_list = []
        self.good_proxy_list = []

    def post(self, url, data):
        req = urllib2.Request(url)
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0)\
                      Gecko/20100101 Firefox/12.0'
        req.add_header('User-agent', user_agent)
        data = urllib.urlencode(data, True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        response = opener.open(req, data)
        return response.read()

    def start_requests(self):
        current_date = datetime.date.today().strftime("%d-%m-%Y")
        proxy_url = "http://checkerproxy.net/%s" % current_date
        proxy_req = Request(proxy_url, self.parse_proxy_page,\
                             dont_filter=True)
        yield proxy_req

    def parse_proxy_page(self, response):
        log.msg("parse search page: %s" % response.url, level = log.INFO)
        hxs = Selector(response)
        ip_port_list = hxs.xpath("//tbody/tr/td[@class='proxy-ipport']/text()").extract()
        for index, ipport in enumerate(ip_port_list):
            if 'u' in ipport:
                continue

            self.current_proxy_list.append('%s:%s' % (index, ipport))

    def spider_closed(self, spider):

        proxy_list = []

        for proxy in self.current_proxy_list:
            proxy_list.append(proxy)

            if len(proxy_list) < 100:
                continue
    
            data = {
                'proxy[]':proxy_list,
                'timeout':30,
                'step':20,
                'lang':'en',
                'proxy_type':0,
                'publish_status':False
            }

            json_data = self.post(self.check_proxy_url, data)
            res = json.loads(json_data)

            for proxy in res['proxy']:
                if proxy['result'] == 1:
                    self.good_proxy_list.append(proxy['ipport'])

            uniq_proxy_list = {}.fromkeys(self.good_proxy_list).keys()
            with open(good_proxy_file, 'w') as f:
                for ipport in uniq_proxy_list:
                    ipport = ipport.replace(':',' ')
                    f.write("%s\n" % ipport)
                    proxy_list = []

if __name__  == '__main__':
    pass
