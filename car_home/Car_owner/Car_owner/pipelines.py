# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from .settings import *

class CarOwnerPipeline(object):
    def process_item(self, item, spider):
        return item

class CarOwnerPriceMongoPipeline(object):
    def open_spider(self,spider):
        self.conn=pymongo.MongoClient(MONGO_HOST,MONGO_PORT)
        self.db=self.conn[MONGO_DB]
        self.myset=self.db['car_owner_price']

    def process_item(self,item,spider):
        # dic={}
        # dic['_id']=item["_id"]
        # dic['model_id']=item["model_id"]
        # dic['trim_id']=item["trim_id"]
        # dic['trim_name']=item["trim_name"]
        # dic['userName']=item["userName"]
        # dic['userId']=item['userId']
        # dic['publishTime']=item["publishTime"]
        # dic['buyTime']=item["buyTime"]
        # dic['buyCity']=item["buyCity"]
        # dic['nakedPriceHide']=item["nakedPriceHide"]
        # dic['fullPrice']=item["fullPrice"]
        # dic['msrp']=item["msrp"]
        # dic['useTax']=item["useTax"]
        # dic['purchaseTax']=item["purchaseTax"]
        # dic['insurer']=item["insurer"]
        # dic['trafficInsurance']=item["trafficInsurance"]
        # dic['licenseFee']=item["licenseFee"]
        count=0
        for car_owner in item['car_owners']:
            count+=1
            print(count)
            self.myset.insert_one(car_owner)

        return item

    def close_spider(self,spider):
        self.conn.close()