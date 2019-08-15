from Crawler import Crawler

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

#crawler = Crawler('https://rewildingeurope.com/', 'RewildingEurope')
crawler = Crawler('http://www.iecl.univ-lorraine.fr/~Remi.Come/fr/', 'Test')
crawler.crawl()

crawler.save_text()
crawler.save_csv()

#crawler.download_images()
#crawler.take_screenshots()
