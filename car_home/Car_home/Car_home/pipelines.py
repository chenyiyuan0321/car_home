# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
import pymongo
from .settings import *

class CarHomePipeline(object):
    def process_item(self, item, spider):
        return item

class CarHomeConfigMongoPipeline(object):
    def open_spider(self,spider):
        self.conn=pymongo.MongoClient(MONGO_HOST,MONGO_PORT)
        self.db=self.conn[MONGO_DB]
        self.myset=self.db['car_config_all']

    def process_item(self,item,spider):
        for i in item['info']:
            self.myset.insert_one(i)
        return item

    def close_spider(self, spider):
        self.conn.close()

