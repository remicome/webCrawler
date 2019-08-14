from MyCrawler import MyCrawler

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

crawler = MyCrawler('https://rewildingeurope.com')
crawler.crawl()

print(crawler.urls)
