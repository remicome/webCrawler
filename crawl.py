from MyCrawler import MyCrawler

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

#crawler = MyCrawler('https://rewildingeurope.com/', 'RewildingEurope')
crawler = MyCrawler('http://www.iecl.univ-lorraine.fr/~Remi.Come/fr/', 'Test')
crawler.crawl()
crawler.take_screenshots()
#crawler.save_text()
#crawler.save_csv()
#crawler.download_images()
