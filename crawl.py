# coding: utf-8
from Crawler import Crawler

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import pickle

#Blacklist de texte spécifique à Rewilding Europe
def my_text_blacklist(tag):
    # Filter all children of 'give-form' (Donation forms)
    if tag.find_parents(class_='give-form'):
        logging.debug('Texte filtré (formulaire de don)')
        return True
    # Content tabs (cf. https://rewildingeurope.com/rew-project/restoring-the-natural-river-valley-of-dviete/)
    class_blacklist = [
            'contentTabs_link',
            'contentTabs_contentTitle',
            'altList_title',
            ]
    for c in class_blacklist:
        if tag.parent.has_attr('class') and c in tag.parent['class']:
            return True

    return False

#crawler = Crawler('https://rewildingeurope.com/rew-project/restoring-the-natural-river-valley-of-dviete/', project_name = 'filter', text_blacklist = my_text_blacklist)
#crawler = Crawler('https://rewildingeurope.com/donations/children-hope-for-nature/', 'formTest', text_blacklist = my_text_blacklist)
#crawler = Crawler('https://rewildingeurope.com/areas/velebit-mountains/', 'NewTest')
#crawler = Crawler('http://www.iecl.univ-lorraine.fr/~Remi.Come/fr/', 'Test', text_blacklist = my_text_blacklist)

crawler = Crawler('https://rewildingeurope.com/', project_name = 'RewildingEurope', text_blacklist = my_text_blacklist)

crawler.crawl()
crawler.dump()

crawler.save_text()
crawler.save_csv()
crawler.download_images()
crawler.take_screenshots()
