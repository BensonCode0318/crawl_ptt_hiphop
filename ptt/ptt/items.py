# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PttItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field() #文章id
    title = scrapy.Field() #文章標題
    authour = scrapy.Field() #作者
    #item_date = scrapy.Field() #日期
    push = scrapy.Field() #推虛文數
    url = scrapy.Field() #URL網址
    category = scrapy.Field() #文章分類
    board = scrapy.Field() #看板名稱

    content_id = scrapy.Field() #文章id
    content = scrapy.Field() #文章內容
    push_count = scrapy.Field() #推文數量
    push_message = scrapy.Field() #詳細推文
    date = scrapy.Field() #推文日期

'''
class PttContent(scrapy.Item):
    content_id = scrapy.Field() #文章id
    content = scrapy.Field() #文章內容
    push_count = scrapy.Field() #推文數量
    push_message = scrapy.Field() #詳細推文
    date = scrapy.Field() #推文日期
    #neutral_count = scrapy.Field() #平推數量
    #final_count = scrapy.Field() #總推文數 = 推文數量 - 虛文數量

'''