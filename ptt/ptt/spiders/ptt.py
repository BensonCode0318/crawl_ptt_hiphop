import scrapy
import time
import datetime
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from scrapy.http import FormRequest
from ptt.items import  PttItem  # 從ptt.Items 繼承PttItem、PttContent

id_count = 1
main_content = ''

class PttSpider(scrapy.Spider):
    name = "ptt"
    allowed_domains = ['ptt.cc']

    def __init__(self,
                 board=None,
                 pages=None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

            # const
        self.start_url = ''
        self._domain = 'https://www.ptt.cc'
        self._cookies = {'over18': '1'}
        self.board = board
        self.pages = None

        self.start_url = '{}/bbs/{}/index.html'.format(self._domain, self.board)
        self.start_urls = [self.start_url]

        if pages:
            page_index = pages.split(',')
            page_index = list(map(str.strip, page_index))
            if len(page_index) == 2 and all([i.isdigit() or i == '-1' for i in page_index]):
                self.pages = (int(page_index[0]), int(page_index[1]))



    #建立一個 Class 繼承 scrapy.Spider（Scrapy 裡一個基本的 spider class），裡面包含三個屬性：
    #name (爬蟲命名)
    #allowed_domains (允許的網域)：如果網址不屬於此域名將丟棄，可允許多個網域
    #start_urls (起始網址) ：將從這裡定義的網址抓取，允許多個


    def start_requests(self):
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse,
            cookies=self._cookies)

    def parse(self, response):

        if len(response.xpath('//div[@class="over18-notice"]')) > 0:
            requests_retries = 0
            if requests_retries < self.settings.attributes['REQUEST_RETRY_MAX'].value:
                requests_retries += 1
                self.logger.warning('Retry {} times'.format(requests_retries))
                yield FormRequest.from_response(
                    response,
                    formdata={'yes': 'yes'},
                    callback=self.parse,
                    dont_filter=True)
            else:
                self.logger.error('You cannot pass')
                raise CloseSpider('You cannot pass over18-form')
        

        if self.pages:
            begin_index, end_index = self.pages
            for i in range(begin_index, end_index + 1):
                time.sleep(1)
                url = '{}/bbs/{}/index{}.html'.format(self._domain, self.board, i)
                yield scrapy.Request(url,callback=self.parse_article)
        else:
            web_count = response.css("a.btn.wide::attr(href)")[1].extract()
            web_count = 1+int(''.join(list(filter(str.isdigit,web_count)))) #取出url中的數字連結 此為倒數第二頁連結 需要將數字加1才是最後一頁連結
            for i in range(1 , web_count):
                time.sleep(1)
                url = '{}/bbs/{}/index{}.html'.format(self._domain, self.board, i)
                yield scrapy.Request(url,callback=self.parse_article)


    def parse_article(self,response):
        global id_count
        
        item = PttItem()
        target = response.css("div.r-ent")
        #print('count is '+str(len(target)))

        for tag in target:
            try:
                item['title'] = tag.css("div.title a::text")[0].extract() #extract() 為提取真實原文數據
                item['title'] = item['title'].replace("'","''")
                #因為push再版面上的數據如果是0或者負數 將不顯示數字 所以將push而外用try的形式 讓如果是空值的話賦予其值為0
                try:
                    item['push'] = tag.css("span::text")[0].extract()
                except IndexError:
                    item['push'] = '0'

                item['url'] = "https://www.ptt.cc"+tag.css("div.title a::attr(href)")[0].extract()
                item['authour'] = tag.css("div.author::text")[0].extract()
                #item['item_date'] = tag.css("div.date::text")[0].extract()
                item['board'] = self.board

                meta = {
                    'title':item['title'],
                    'authour':item['authour'],
                    #'item_date':item['item_date'],
                    'push':item['push'],
                    'url':item['url'] ,
                    'category':0,
                    'board':item['board']
                }
                yield scrapy.Request(item['url'],callback=self.get_content,meta=meta)
                #yield item #yield將函數定義為generator的函數 可使用迭代的方式取出結果的值  詳細見https://liam.page/2017/06/30/understanding-yield-in-python/
            except IndexError:
                pass
            continue

    def get_content(self,response):
        meta = response.meta
        item = PttItem()
        target = response.css("body")
        item['content'] = target.css("div#main-content::text").extract()
        item['date'] = target.css("div.article-metaline span.article-meta-value::text")[2].extract()
        item['date'] = str(datetime.datetime.strptime(item['date'],'%a %b %d %H:%M:%S %Y'))

        soup = BeautifulSoup(response.body, 'lxml')
        main_content = soup.find(id="main-content")
        pushes = main_content.find_all('div', class_='push')
        for push in pushes:
            push.extract()


        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            push_tag = push.find('span', 'push-tag')
            if not push_tag: continue
            push_tag = push_tag.string.strip(' \t\n\r')
            push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')

            # if find is None: find().strings -> list -> ' '.join; else the current way
            push_content = push.find('span', 'push-content').strings

            # remove ':'
            push_content = ' '.join(push_content)[1:].strip(' \t\n\r')
            push_content = push_content.replace("'","''").replace("\\"," ")
            push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            messages.append({
                "push_tag": push_tag,
                "push_userid": push_userid,
                "push_content": push_content,
                "push_ipdatetime": push_ipdatetime
            })
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        push_count = {
            "all": p + b + n,
            "count": p - b,
            "push": p,
            "boo": b,
            "neutral": n
        }  

        item['push_message'] = messages
        item['push_count'] = push_count


        final_item = {
            'title':meta['title'],
            'authour':meta['authour'],
            #'item_date':meta['item_date'],
            'push':meta['push'],
            'url':meta['url'] ,
            'category':0,
            'board':meta['board'],
            'push_message':item['push_message'],
            'push_count':item['push_count'],
            'content':item['content'],
            'date':item['date']
        }

        return final_item
