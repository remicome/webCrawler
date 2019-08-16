# coding: utf-8
from Crawler import Crawler

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

crawler = Crawler('https://rewildingeurope.com/', 'RewildingEurope')
#crawler = Crawler('https://rewildingeurope.com/areas/velebit-mountains/', 'NewTest')
#crawler = Crawler('http://www.iecl.univ-lorraine.fr/~Remi.Come/fr/', 'Test')

crawler.crawl()

crawler.save_text()
crawler.save_csv()
crawler.download_images()
crawler.take_screenshots()
