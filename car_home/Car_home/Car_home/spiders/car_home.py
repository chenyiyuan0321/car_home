# -*- coding: utf-8 -*-
import scrapy
import re
import requests
from ..items import CarHomeItem
from selenium import webdriver
import json
import uuid

class CarHomeSpider(scrapy.Spider):
    name = 'car_home'
    allowed_domains = ['autohome.com.cn']
    # start_urls = ['https://www.autohome.com.cn/car']
    one_url='https://www.autohome.com.cn/grade/carhtml/{}.html'
    two_url='https://car.autohome.com.cn/config/series/{}.html'
    letter_list = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N',
                   'O','P','Q','R','S','T','V','W','X','Y','Z']
    count=0
    # letter_list=['P','T']

    def start_requests(self):
        for letter in self.letter_list:
            one_url=self.one_url.format(letter)
            yield scrapy.Request(url=one_url,callback=self.parse)

    def parse(self, response):
        html=response.text
        model_list=re.findall('<li id="s(.*?)">', html, re.S)
        for id in model_list:
            two_url=self.two_url.format(id)
            # item['scrapedUrl']=two_url
            print(two_url)
            yield scrapy.Request(url=two_url,callback=self.parse_two)

    def parse_two(self,response):
        # item=response.meta['item']
        # item=CarHomeItem()
        if response.url == response.request.url:
            exist_data=response.xpath('/html/body/div[3]/p/text()').extract_first()
            if not exist_data:
                html = response.text
                js_list = re.findall('(\(function\([a-zA-Z]{2}.*?_\).*?\(document\);)', html, re.S)
                # print(js_list)
                car_info = ''
                keyLink = re.search('var keyLink = (.*?)};', html, re.S)
                config = re.search('var config = (.*?)};', html, re.S)  # 车的参数
                option = re.search('var option = (.*?)};', html, re.S)  # 主被动安全装备
                color = re.search('var color = (.*?)};', html, re.S)  # 颜色
                innerColor = re.search('var innerColor =(.*?)};', html, re.S)  # 内置颜色
                bag = re.search('var bag = (.*?)};', html, re.S)  # 选装包
                if keyLink:
                    # print(keyLink.group(0))
                    car_info += keyLink.group(0)  # 匹配整体内容
                if config:
                    # print(config.group(0))
                    car_info += config.group(0)
                if option:
                    car_info += option.group(0)
                if color:
                    # print(color.group(0))
                    car_info += color.group(0)
                if innerColor:
                    # print(innerColor.group(0))
                    car_info += innerColor.group(0)
                if bag:
                    car_info += bag.group(0)
                # print(car_info)
                car_info_right=self.get_car_info(js_list, car_info)
                # 取出各项配置
                # try:
                keyLink = re.search('var keyLink = (\[.*?\]);', car_info_right).group(1)  # 匹配第一个括号的内容
                config = re.search('var config = (.*?);var', car_info_right).group(1)
                option = re.search('var option = (.*?);var', car_info_right).group(1)
                color = re.search('var color = (.*?);var', car_info_right).group(1)
                innerColor = re.search('var innerColor =(.*?);', car_info_right).group(1)
                bag = re.search('var bag = (.*?);', car_info_right).group(1)
                # except Exception as e:
                #     print(e)
                #     pass

                # 转换字典
                keyLink_dic = json.loads(keyLink)
                config_dic = json.loads(config)
                option_dic = json.loads(option)
                color_dic = json.loads(color)
                innerColor_dic = json.loads(innerColor)
                bag_dic = json.loads(bag)
                # print(keyLink_dic)

                all_config_list = []
                car_name_specid_dict = {}
                key_value_dict_list = config_dic['result']["paramtypeitems"][0]['paramitems'][0]['valueitems']
                for key_value_dict in key_value_dict_list:
                    car_name_specid_dict[key_value_dict['specid']] = key_value_dict['value']
                for paramtypeitem in config_dic['result']['paramtypeitems']:
                    config_type = paramtypeitem['name']
                    for paramitem in paramtypeitem['paramitems']:
                        config_name = paramitem['name']
                        config_id = config_type + paramitem['name']
                        for valueitem in paramitem['valueitems']:
                            val = valueitem['value']
                            version_id = valueitem['specid']
                            version_name = car_name_specid_dict[version_id]
                            if val == '-':
                                val = '无'
                            ite = {}
                            ite['_id'] = uuid.uuid1().hex
                            ite['createTime'] = config_dic['time']
                            ite['versionId'] = str(version_id)
                            ite['versionName'] = version_name
                            ite['config_type'] = config_type
                            ite['config_name'] = config_name
                            ite['config_id'] = str(config_id)
                            ite['val'] = val
                            all_config_list.append(ite)
                            self.count+=1
                for configtypeitem in option_dic['result']['configtypeitems']:
                    config_type = configtypeitem['name']
                    for configitem in configtypeitem['configitems']:
                        config_name = configitem['name']
                        config_id = config_type + configitem['name']
                        for valueitem in configitem['valueitems']:
                            version_id = valueitem['specid']
                            version_name = car_name_specid_dict[version_id]
                            val = ''
                            if not valueitem['sublist']:
                                val = valueitem['value']

                                if (val == '-') or (not val):
                                    val = '无'
                            else:
                                for sub in valueitem['sublist']:
                                    subname = sub['subname']
                                    if sub['subvalue'] == 1:
                                        val = '(标配)' + subname
                                    elif sub['subvalue'] == 2:
                                        val = '(选配)' + subname
                                    else:
                                        val = '无' + subname
                            ite = {}
                            ite['_id'] = uuid.uuid1().hex
                            ite['createTime'] = option_dic['time']
                            ite['versionId'] = str(version_id)
                            ite['versionName'] = version_name
                            ite['config_type'] = config_type
                            ite['config_name'] = config_name
                            ite['config_id'] = str(config_id)
                            ite['val'] = val.replace('&nbsp;', '').replace('○', '(选配)') \
                                .replace('●', '(标配)').replace('-', '(无)')
                            # print(item)
                            all_config_list.append(ite)
                            self.count += 1
                for specitem in color_dic['result']['specitems']:
                    version_id = specitem['specid']
                    version_name = car_name_specid_dict[version_id]
                    val = ''
                    for coloritem in specitem['coloritems']:
                        val += coloritem['name'] + '，'
                    val = val[:-1]
                    ite = {}
                    ite['_id'] = uuid.uuid1().hex
                    ite['createTime'] = color_dic['time']
                    ite['versionId'] = str(version_id)
                    ite['versionName'] = version_name
                    ite['config_type'] = '选装包'
                    ite['config_name'] = '外观颜色'
                    ite['config_id'] = 'color'
                    ite['val'] = val
                    all_config_list.append(ite)
                    self.count += 1
                for specitem in innerColor_dic['result']['specitems']:
                    version_id = specitem['specid']
                    version_name = car_name_specid_dict[version_id]
                    val = ''
                    for coloritem in specitem['coloritems']:
                        val += coloritem['name'] + '，'
                    val = val[:-1]
                    ite = {}
                    ite['_id'] = uuid.uuid1().hex
                    ite['createTime'] = innerColor_dic['time']
                    ite['versionId'] = str(version_id)
                    ite['versionName'] = version_name
                    ite['config_type'] = '选装包'
                    ite['config_name'] = '内饰颜色'
                    ite['config_id'] = 'innerColor'
                    ite['val'] = val
                    all_config_list.append(ite)
                    self.count += 1
                for bagtypeitem in bag_dic['result']['bagtypeitems']:
                    config_type = bagtypeitem['name']
                    if bagtypeitem['bagitems']:
                        for bagitem in bagtypeitem['bagitems']:
                            version_id = bagitem['specid']
                            if bagitem['valueitems']:
                                for valueitem in bagitem['valueitems']:
                                    version_name = car_name_specid_dict[version_id]
                                    ite = {}
                                    ite['_id'] = uuid.uuid1().hex
                                    ite['createTime'] = bag_dic['time']
                                    ite['versionId'] = str(version_id)
                                    ite['versionName'] = version_name
                                    ite['config_type'] = config_type
                                    ite['config_name'] = valueitem['name']
                                    ite['config_id'] = str(valueitem['bagid'])
                                    ite['val'] = valueitem['pricedesc'] + '+' + valueitem['description']
                                    # print(item)
                                    all_config_list.append(ite)
                                    self.count += 1
                item=CarHomeItem()
                item['info']=all_config_list
                yield item
            else:
                print(exist_data)
                pass
        else:
            print('页面重定向了')
            pass
        print(self.count)


    def get_car_info(self, js_list, car_info):
        if car_info:
            # 运行JS的DOM --
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

            # 把JS文件写入到文件中去
            for item in js_list:
                DOM = DOM + item
            ne_html = "<html><meta http-equiv='Content-Type' content='text/html; charset=utf-8' /><head></head><body>    <script type='text/javascript'>"
            # 拼接成一个可以运行的网页
            new_html = ne_html + DOM + " document.write(rules)</script></body></html>"
            # 再次运行的时候，请把文件删除，否则无法创建同名文件，或者自行加验证即可
            with open("./demo/demo.html", "w") as f:
                f.write(new_html)
            # 通过selenium将数据读取出来，进行替换
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            browser = webdriver.Chrome(options=options)
            # 上面三行代码就是为了将Chrome不弹出界面，实现无界面爬取
            browser.get("file:///home/tarena/PycharmProjects/code/spider/car_home/Car_home/Car_home/demo/demo.html")
            # 读取body部分
            text = browser.find_element_by_tag_name('body').text
            # print(text)
            # 匹配车辆参数中所有的span标签
            span_list = re.findall('<span(.*?)></span>', car_info)  # car_info 是上面拼接的字符串

            # 按照span标签与text中的关键字进行替换
            for span in span_list:
                # 这个地方匹配的是class的名称  例如 <span class='hs_kw7_optionZl'></span> 匹配   hs_kw7_optionZl 出来
                info = re.search("'(.*?)'", span)
                # print(info.group(1))
                if info:
                    class_info = str(info.group(1)) + "::before { content:(.*?)}"  #
                    content = re.search(class_info, text).group(1)  # 匹配到的字体
                    car_info = car_info.replace(str("<span class='" + info.group(1) + "'></span>"),
                                                re.search("\"(.*?)\"", content).group(1))
            return car_info
        else:
            print('没有匹配到配置数据')
            return ''

    #         exist_data = response.xpath("//div[@class='mainWrap sub_nav']/p/text()").extract_first()  # '抱歉，暂无相关数据。'
    #         if not exist_data:
    #             html=response.text
    #             print(html)






