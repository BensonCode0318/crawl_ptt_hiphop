# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from ptt.items import PttItem,PttContent #從ptt.Items 繼承PttItem、PttContent
import re,string,jieba,numpy,pymysql,json
from ptt import settings
sort = ['公告','分享','知識','音樂','活動','討論','問題','創作','新聞','趣味','Re']
authour_name = []
authour_contain = []

class PttPipeline(object):
    def __init__(self):
        self.connect = pymysql.connect(
            host=settings.MYSQL_HOST,
            db=settings.MYSQL_DB,
            user=settings.MYSQL_USER,
            passwd=settings.MYSQL_PASS,
            charset='utf8',
            use_unicode=True)
        self.sort_count = numpy.zeros(12)
        self.cursor = self.connect.cursor()


    def process_item(self, item, spider):
        global authour_name
        global authour_contain
        #item['push'] = int(item['push'])
        #item['title'] = re.sub("[\u0060|\u0021-\u002c|\u002e-\u002f|\u003a-\u003f|\u2200-\u22ff|\uFB00-\uFFFD|\u2E80-\u33FF]", ' ', item['title']) 
        #table = str.maketrans({key: None for key in string.punctuation})
        #item['title'] = item['title'].translate(table, string.punctuation)

        add_punc='，。、【】“”：；（）﹙﹚［］《》〈〉‘’{}？！⑦()、%^>℃：.”“^-——=&#@￥「」※◆*●～–｜▶‧／◎\n－♥\u3000'
        punctuation = string.punctuation+add_punc

        if isinstance(item,PttItem):
            item_title = item['title'].translate(str.maketrans('','',punctuation))
            #item['content'] = item['content'].translate(str.maketrans('','',punctuation))

            #item['title'] = item['title'].translate(str.maketrans('','',punctuation))
            #item['title'] = jieba.cut(item['title'], cut_all=False)
            #item['title'] = " ".join(item['title'])
            
            try:
                self.sort_count[sort.index(item_title[0:2])] += 1
                item['category'] = sort.index(item_title[0:2])+1
            except ValueError:
                self.sort_count[11] += 1
                item['category'] = 11

            insert_sql = "INSERT INTO data(id, authour, category, date, push, title, url) VALUES ('%d','%s', '%d', '%s', '%s', '%s', '%s')" % (item['id'], item['authour'], item['category'], item['date'], item['push'], item['title'], item['url'])
            self.cursor.execute(insert_sql)
            self.connect.commit()

            if item['authour'] not in authour_name:
                authour_name.append(item['authour']) #新增authour名字到list
                authour_contain.append([]) #新增authour_contain中的空list
                authour_contain[authour_name.index(item['authour'])].append(str(item['id'])) #搜尋authour_name中 authour的所在的索引值 對應到authour_contain中的索引值位置
            else:
                authour_contain[authour_name.index(item['authour'])].append(str(item['id']))

            
            return item

        if isinstance(item,PttContent):
            while '\n' in item['content']:
                item['content'].remove('\n')
            item['content'] = "".join(item['content'])
            item['content'] = item['content'].translate(str.maketrans('','','\n')) #去除標點與特殊字符

            insert_sql = "INSERT INTO content(content_id, full_content, push_count, push_message) VALUES ('%d', '%s', '%s', '%s')" % (item['content_id'], item['content'], json.dumps(item['push_count'], ensure_ascii=False), json.dumps(item['push_message'], ensure_ascii=False))
            self.cursor.execute(insert_sql)
            self.connect.commit()
            return item

    def close_spider(self, spider):
        for count in range(11):
            update_sql = "UPDATE category set count = '%d' WHERE id = '%d'" % (self.sort_count[count], count+1)
            self.cursor.execute(update_sql)
            self.connect.commit()

        for index in range(len(authour_name)):
            contain = ','.join(authour_contain[index])
            sql = "INSERT INTO authour(authour_name, authour_contain) VALUES ('%s', '%s')" % (authour_name[index], contain)
            self.cursor.execute(sql)
            self.connect.commit()

        self.cursor.close()
        self.connect.close()
