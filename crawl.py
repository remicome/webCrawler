# coding: utf-8
from Crawler import Crawler

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


#Blacklist de texte spécifique à Rewilding Europe
def my_text_blacklist(tag):
    # Filter all children of 'give-form' (Donation forms)
    if tag.find_parents(class_='give-form'):
        logging.debug('Texte filtré (formulaire de don)')
        return True

crawler = Crawler('https://rewildingeurope.com/donations/children-hope-for-nature/', 'formTest', text_blacklist = my_text_blacklist)
#crawler = Crawler('https://rewildingeurope.com/areas/velebit-mountains/', 'NewTest')
#crawler = Crawler('http://www.iecl.univ-lorraine.fr/~Remi.Come/fr/', 'Test', text_blacklist = my_text_blacklist)

crawler.crawl()

crawler.save_text()
#crawler.save_csv()
#crawler.download_images()
#crawler.take_screenshots()
