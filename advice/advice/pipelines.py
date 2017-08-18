# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from pprint import pprint
import pymongo

class AdvicePipeline(object):
    collection_name = 'dear_prudence'

    def __init__(self, mongo_db):
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        print("FROM CRAWLER",crawler.settings.get('MONGO_DATABASE'))
        return cls(
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        print("OPENING")
        self.client = pymongo.MongoClient()
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        print("processing")
        pprint(item)
        self.db[self.collection_name].find_one_and_update(
            {"_id" : item['id']},
            {"$set" :
                { "questions" : item["questions"] }
            }
        )
        return item
