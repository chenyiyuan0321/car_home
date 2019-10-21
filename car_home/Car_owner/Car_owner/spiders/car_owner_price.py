# -*- coding: utf-8 -*-
import scrapy
import uuid
import time
import json
import re
from lxml import etree
from selenium import webdriver
from ..items import CarOwnerItem


class CarOwnerPriceSpider(scrapy.Spider):
    name = 'car_owner_price'
    allowed_domains = ['autohome.com.cn']
    owner_url = 'https://jiage.autohome.com.cn/price/carlist/p-{}-2-0-0-0-0-{}-0'
    one_url = 'https://www.autohome.com.cn/grade/carhtml/{}.html'
    two_url = 'https://jiage.autohome.com.cn/getSpec?seriesId={}'
    letter_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                   'O', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z']
    DOM = ("var rules = '2';"
           "var document = {};"
           "function getRules(){return rules}"
           "document.createElement = function() {"
           "      return {"
           "              sheet: {"
           "                      insertRule: function(rule, i) {"
           "                              if (rules.length == 0) {"
           "                                      rules = rule;"
           "                              } else {"
           "                                      rules = rules + '#' + rule;"
           "                              }"
           "                      }"
           "              }"
           "      }"
           "};"
           "document.querySelectorAll = function() {"
           "      return {};"
           "};"
           "document.head = {};"
           "document.head.appendChild = function() {};"

           "var window = {};"
           "window.decodeURIComponent = decodeURIComponent;")

    def start_requests(self):
        for letter in self.letter_list:
            one_url = self.one_url.format(letter)
            yield scrapy.Request(url=one_url, callback=self.parse)

    def parse(self, response):
        html = response.text
        # print(html)
        model_list = re.findall('<li id="s(.*?)">', html, re.S)
        for model_id in model_list:
            two_url = self.two_url.format(model_id)
            response.meta['model_id'] = model_id
            yield scrapy.Request(url=two_url, callback=self.parse_two, meta=response.meta)

    def parse_two(self, response):
        info_list = json.loads(response.text)
        # print(info_list)
        if info_list:
            for info in info_list:
                trim_list = info['specitems']
                for trim in trim_list:
                    trim_id = trim['id']
                    trim_name = trim['name']
                    response.meta['trim_id'] = trim_id
                    response.meta['trim_name'] = trim_name
                    response.meta['page'] = 1
                    url = self.owner_url.format(trim_id, '1')
                    print(url)
                    yield scrapy.Request(url=url, callback=self.parse_page, meta=response.meta)

    def parse_page(self, response):
        html = self.change_html(response.text)
        item = CarOwnerItem()
        car_owner_list = []
        car_table_list = re.findall('<ul class="car-lists" >(.*?)</ul>', html, re.S)
        print(len(car_table_list))
        if car_table_list:
            for car_table in car_table_list:
                # print(car_table)
                items = {}
                items['id'] = uuid.uuid1().hex
                items['trim_id'] = response.meta['trim_id']
                items['userName'] = re.findall('class="car-lists-item-use-name-detail ">(.*?)</a>', car_table)[0]
                items['userId'] = re.findall('//.*?cn/(.*?)#pvareaid', car_table)[0]
                items['publishTime'] = re.findall('<span class="time">(.*?)</span>发表', car_table)[0]
                items['buyTime'] = re.findall('购车时间：<time>(.*?)</time></p>', car_table)[0]
                items['buyCity'] = re.findall('<span class="bought-location">(.*?)</span>', car_table)[0]
                items['nakedPriceHide'] = re.findall('<span class="luochejia red"><span class="luochejia-num"><!--hs-->(.*?)<!--@HS_ZY@-->',car_table)[0]
                items['fullPrice'] = re.findall('<span class="quankuan red"><span class="quankuan-num"><!--hs-->(.*?)<!--@HS_ZY@-->',car_table)[0]
                items['msrp'] = re.findall('<span class="luochejia"><span class="luochejia-num"><!--hs-->(.*?)<!--@HS_ZY@-->',car_table)[0]
                items['useTax'] = re.findall('''<span class="list-name">车船使用税</span>
                  <span class="list-details">(.*?)</span>''', car_table,re.S)[0]
                items['purchaseTax'] = re.findall('''<span class="list-name">购置税</span>
                  <span class="list-details">(.*?)</span>''', car_table,re.S)[0]
                items['insurer'] = re.findall('''<span class="list-name">交强险</span>
                  <span class="list-details">(.*?)</span>''', car_table,re.S)[0]
                items['trafficInsurance'] = re.findall('''<span class="list-name" >商业险</span>
                  <span class="list-details">(.*?)</span>''', car_table,re.S)[0]
                items['licenseFee'] = re.findall('''<span class="list-name">上牌费</span>
                  <span class="list-details">(.*?)</span>''', car_table,re.S)[0]
                print(items)
                car_owner_list.append(items)
            item['car_owners'] = car_owner_list
            yield item
            if len(car_owner_list) == 10:
                response.meta['page'] += 1
                url = self.owner_url.format(response.meta['trim_id'], str(response.meta['page']))
                yield scrapy.Request(url=url, callback=self.parse_page, meta=response.meta)
        else:
            print('页面无内容')
            pass

    def change_html(self, html):
        price_list = re.findall('''<ul class="car-lists" >
          <li class="car-lists-item">
            <div class="car-lists-item-top">
              <div class="car-lists-item-top-left">(.*?)</ul>''',
                                html, re.S)
        # print(len(price_list))
        js_list=[]
        for price_str in price_list:
            js_code = re.findall('\(function.*?\)\(document\);', price_str, re.S)
            js_str = ''
            for js_ in js_code:
                js_str += js_
            js_list.append(js_str)
        # print(js_list)
        DOM = self.DOM
        for js in js_list:
            DOM = DOM + js
        ne_html = "<html><meta http-equiv='Content-Type' content='text/html; charset=utf-8' /><head></head><body>    <script type='text/javascript'>"
        # 拼接成一个可以运行的网页
        new_html = ne_html + DOM + " document.write(rules)</script></body></html>"
        # 再次运行的时候，请把文件删除，否则无法创建同名文件，或者自行加验证即可
        with open("./demo.html", "w") as f:
            f.write(new_html)
        # 通过selenium将数据读取出来，进行替换
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        # 上面三行代码就是为了将Chrome不弹出界面，实现无界面爬取
        browser.get("file:///home/tarena/PycharmProjects/code/spider/car_home/Car_owner/Car_owner/demo.html")
        # 读取body部分
        text = browser.find_element_by_tag_name('body').text

        span_list = re.findall("<!--hs--><span class='hs_kw0(.*?)></span><!--@HS_ZY@-->", html, re.S)
        for span in span_list:
            span = "'hs_kw0" + span
            key = re.findall("'(.*?)'", span)[0]
            if key:
                key_str = key + "::before { content:(.*?)}"
                content = re.findall(key_str, text)
                if content:
                    content = content[0]
                    # print(content)
                    content_str = str(re.findall("\"(.*?)\"", content)[0])
                    html = html.replace(str("<span class='" + key + "'></span>"),
                                        content_str)
        return html
