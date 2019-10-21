import scrapy
import time
from bs4 import BeautifulSoup
from ptt.items import PttContent, PttItem  # 從ptt.Items 繼承PttItem、PttContent

id_count = 1
main_content = ''

class PttSpider(scrapy.Spider):
    name = "ptt"
    allowed_domains = ['ptt.cc']
    start_urls = ['https://www.ptt.cc/bbs/Hip-Hop/index.html']

    #建立一個 Class 繼承 scrapy.Spider（Scrapy 裡一個基本的 spider class），裡面包含三個屬性：
    #name (爬蟲命名)
    #allowed_domains (允許的網域)：如果網址不屬於此域名將丟棄，可允許多個網域
    #start_urls (起始網址) ：將從這裡定義的網址抓取，允許多個

    def parse(self, response):
        web_count = response.css("a.btn.wide::attr(href)")[1].extract()
        web_count = 1+int(''.join(list(filter(str.isdigit,web_count)))) #取出url中的數字連結 此為倒數第二頁連結 需要將數字加1才是最後一頁連結
        #print(int(web_count))

        for i in range(10):
            time.sleep(1)
            url='https://www.ptt.cc/bbs/Hip-Hop/index' + str(web_count-i) +'.html'
            yield scrapy.Request(url,callback=self.parse_article)

    def parse_article(self,response):
        global id_count
        
        item = PttItem()
        target = response.css("div.r-ent")
        #print('count is '+str(len(target)))

        for tag in target:
            try:
                item['id'] = id_count
                id_count += 1
                item['title'] = tag.css("div.title a::text")[0].extract() #extract() 為提取真實原文數據
                item['authour'] = tag.css("div.author::text")[0].extract()
                item['date'] = tag.css("div.date::text")[0].extract()
                item['push'] = tag.css("span::text")[0].extract()
                item['url'] = 'https://www.ptt.cc'+tag.css("div.title a::attr(href)")[0].extract()
                item['category'] = 0
                

                yield scrapy.Request(item['url'],callback=self.get_content,meta = {'content_id' : item['id']})
                yield item #yield將函數定義為generator的函數 可使用迭代的方式取出結果的值  詳細見https://liam.page/2017/06/30/understanding-yield-in-python/
            except IndexError:
                pass
            continue

    def get_content(self,response):
        item = PttContent()
        target = response.css("body")
        item['content'] = target.css("div#main-content::text").extract()

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
            push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            messages.append({
                'push_tag': push_tag,
                'push_userid': push_userid,
                'push_content': push_content,
                'push_ipdatetime': push_ipdatetime
            })
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        push_count = {
            'all': p + b + n,
            'count': p - b,
            'push': p,
            'boo': b,
            "neutral": n
        }  
        item['push_message'] = messages
        item['push_count'] = push_count
        item['content_id'] = response.meta['content_id']
        return item
