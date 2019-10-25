# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from ptt.items import PttItem #從ptt.Items 繼承PttItem、PttContent
import re,string,jieba,numpy,pymysql,json
from ptt import settings
#sort = ['公告','分享','知識','音樂','活動','討論','問題','創作','新聞','趣味','Re']

class PttPipeline(object):
    def __init__(self):
        self.connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            db=settings.MYSQL_DB,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASS,
            charset='utf8',
            use_unicode=True)
        self.sort = []
        self.sort_count = []
        self.authour_name = []
        self.authour_contain = []
        self.board = ''
        #self.sort_count = numpy.zeros(12)
        self.cursor = self.connect.cursor()


    def process_item(self, item, spider):
        add_punc='，。、【】“”：；（）﹙﹚［］《》〈〉‘’{}？！⑦()、%^>℃：.”“^-——=&#@￥「」※◆*●～–｜▶‧／◎\n－♥\u3000'
        punctuation = string.punctuation+add_punc
        self.board = item['board']
        #判斷item是不是已經存在資料庫中
        select_sql = "SELECT * FROM data WHERE url = '%s'" % (item['url'])
        self.cursor.execute(select_sql)
        results = self.cursor.fetchall()  

        if len(results) is 0:
            item_title = item['title'].translate(str.maketrans('','',punctuation))
            try:
                self.sort_count[self.sort.index(item_title[0:2])] += 1
                item['category'] = self.sort.index(item_title[0:2])+1
            except ValueError:
                self.sort.append(item_title[0:2])
                self.sort_count.append(1)
                #self.sort_count[11] += 1
                item['category'] = self.sort.index(item_title[0:2])+1
            #insert data
            insert_sql = "INSERT INTO data(authour, category, date, push, title, url, board) VALUES ('%s', '%d', '%s', '%s', '%s', '%s', '%s')" % (item['authour'], item['category'], item['date'], item['push'], item['title'], item['url'], item['board'])
            self.cursor.execute(insert_sql)
            insert_id = self.connect.insert_id()
            self.connect.commit()

            #新增新的帳號名稱
            if item['authour'] not in self.authour_name:
                self.authour_name.append(item['authour']) #新增authour名字到list
                self.authour_contain.append([]) #新增authour_contain中的空list
                self.authour_contain[self.authour_name.index(item['authour'])].append(str(insert_id)) #搜尋authour_name中 authour的所在的索引值 對應到authour_contain中的索引值位置
            else:
                self.authour_contain[self.authour_name.index(item['authour'])].append(str(insert_id))

            #insert content
            while '\n' in item['content']:
                item['content'].remove('\n')
            item['content'] = "".join(item['content'])
            item['content'] = item['content'].translate(str.maketrans('','',punctuation)) #去除標點與特殊字符

            insert_sql = "INSERT INTO content(content_id, full_content, push_count, push_message) VALUES ('%d', '%s', '%s', '%s')" % (insert_id, item['content'], json.dumps(item['push_count'], ensure_ascii=False), json.dumps(item['push_message'], ensure_ascii=False))
            self.cursor.execute(insert_sql)
            self.connect.commit()
        else:
            pass

        return item


    def close_spider(self, spider):
        for count in range(len(self.sort)):
            update_sql = "INSERT INTO category(name, count, board) VALUES ('%s', '%d', '%s')" % (self.sort[count], self.sort_count[count], self.board)
            self.cursor.execute(update_sql)
            self.connect.commit()

        for index in range(len(self.authour_name)):
            contain = ','.join(self.authour_contain[index])
            sql = "INSERT INTO authour(authour_name, authour_contain) VALUES ('%s', '%s')" % (self.authour_name[index], contain)
            self.cursor.execute(sql)
            self.connect.commit()

        self.cursor.close()
        self.connect.close()
