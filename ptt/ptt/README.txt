scrapy.cfg：基礎設置
items.py：抓取條目的結構定義
middlewares.py：中間件定義
pipelines.py：管道定義，用於抓取數據後的處理
settings.py：全局設置
spiders\ptt.py：爬蟲主體，定義如何抓取需要的數據

啟動
scrapy crawl ptt -a board=[board名稱] -a pages=[起始頁數,結束頁數]