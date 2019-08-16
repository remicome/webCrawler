#============================================================
#
# MyCrawler.py : définit les classes MyCrawler et Page
#
#
#============================================================

import os, re, csv, time, json

import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit

import logging

# Captures d'écran : pris depuis
# https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
from selenium import webdriver
from save_screenshot import save_screenshot


class Crawler:
    def __init__(self, root_url, project_name = None):
        self.root_url = root_url
        self.root_url_netloc = urlparse(self.root_url).netloc
        self.pages = []                             # Pages parsées
        self.urls = [root_url]                      # Urls collectées
        if project_name:                                # Nom du répertoire du projet
            self.project_name = project_name
        else:
            self.project_name = self.root_url_netloc   
        self.data_dir = '%s/data' % self.project_name                 # Nom du répertoire des données

    def __iter__(self):
        return self.pages.__iter__()

    # crawl(): remplis self.pages avec des uris plus basses que root_url
    def crawl(self):
        logging.info("Commence à arpenter les pages")
        url_index = 0
        while url_index < len(self.urls):
            url_index = self._append_next_page(url_index)


    def save_text(self):
        logging.info('Écriture des fichiers textes')
        self._ensure_project_dir()
        gather_texts = ''

        for page_id, page in enumerate(self):
            gather_texts += ('**** *id_%03d\n%s\n\n' % (page_id, page.text))
            with open('%s/page%03d.txt' % (self.data_dir, page_id), 'w') as f:
                f.write(page.text)
        
        with open('%s/%s.txt' % (self.project_name, self.project_name), 'w') as f:
            f.write(gather_texts)


    def save_csv(self):
        logging.info('Écriture du fichier csv')
        self._ensure_project_dir()
        rows = [['Id', 'Titre', 'url', 'Date de téléchargement', 'Nombre d\'images', 'Nombre de signes du texte', 'Nombre de mots', 'Type']]
        for page_id, page in enumerate(self):
            rows.append([ '%s/page%03d.txt' % (self.data_dir, page_id), page.title, page.url, page.access_date, len(page.images), page.text.count_char(), page.text.count_words(), 'site' ])

        #TODO: pour compter la longueur du texte, faut-il enlever les espaces et \n ?
        with open('%s/%s.csv' % (self.project_name, self.project_name), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def download_images(self):
        self._ensure_project_dir()
        for page_id, page in enumerate(self):
            for img_id, img_url in enumerate(page.images):
                logging.info('Téléchargement des images : page %d/%d : image %d/%d' % (page_id + 1, len(self.pages), img_id + 1, len(page.images)))
                
                s = re.search('.*\.([a-zA-Z0-9]+)$', img_url)
                if s:
                    img_extension = s.group(1)
                else:
                    img_extension = ''

                with open('%s/page%03d_img%03d.%s' % (self.data_dir, page_id, img_id, img_extension), 'wb') as f:
                    f.write(requests.get(img_url).content)

    def take_screenshots(self):
        self._ensure_project_dir()
        with webdriver.Firefox() as driver:
            for page_id, page in enumerate(self):
                logging.info('Capture d\'écran de la page %d/%d' % (page_id + 1, len(self.pages)))
                page.screenshot(driver, '%s/page%03d_screenshot.png' % (self.data_dir, page_id))

    def _ensure_project_dir(self):
        if not os.path.isdir(self.project_name):
            logging.debug('Le répertoire %s n\'existe pas: création' % self.project_name)
            os.mkdir(self.project_name)

        data_path = '%s/%s' % (self.project_name, self.data_dir)
        if not os.path.isdir(self.data_dir):
            logging.debug('Le répertoire %s n\'existe pas: création' % self.data_dir)
            os.mkdir(self.data_dir)


    # append_next_page(self, i):
    #   Ajoute la page self.urls[i]. Si l'url est invalide (e.g. erreur 404) ou nous redirige vers une url déjà dans notre liste, on enlève self.urls[i].
    #
    #   Arguments: 'i' est l'indice de l'url à traiter dans self.urls
    #   Retourne: l'indice de la prochaine url à traiter dans self.urls ('i' ou 'i+1', selon qu'on est tombé sur une url valide ou pas)
    def _append_next_page(self, i):
        logging.info('Page %d/%d trouvées : %s' % (i+1, len(self.urls), self.urls[i]))
        try:
            page = Page( self.urls[i] )
        except RequestException as err: #TODO: Page doit lancer une RequestException en cas d'erreur ou de redirection
            if (not err.response) or (err.response.url in self.urls):
                logging.debug('La page est non-disponible ou nous redirige vers une url déjà dans la liste')
                del self.urls[i]
                return i
            else:
                logging.debug('Redirection: on remplace l\'url trouvée par son arrivée')
                page = Page(err.response.url)
                self.urls[i] = err.response.url

        self.pages.append(page)
        for url in self.pages[i].links:
            if self._include_url(url):
                self.urls.append( urljoin(self.root_url, url) )

        return i+1

    # _blacklist_url
    #   'url' est une url *absolue*
    #   Vérifie si :
    #       - url pointe vers le même site (url relative ou même chemin de base)
    #       - url n'est pas un lien vers le blog ou les actualités (à traiter à part)
    #       - url ne pointe pas vers un fichier des types indiqués ci-dessous
    def _blacklist_url(self, url):
        netloc = urlparse(url).netloc
        scheme = urlparse(url).scheme
        return (not scheme in ['http','https', '']) \
                or ((netloc != '') and (netloc != self.root_url_netloc)) \
                or re.match('.*(/|#)blog.*', url) \
                or re.match('.*(/|#)forum.*', url) \
                or re.match('.*(/|#)tag.*', url) \
                or re.match('.*(/|#)news.*', url) \
                or re.match('.*\.(pdf|jpg|svg|png|gif)$', url) \
                or re.match('.*#[a-zA-Z0-9]*',url)

    # _include_url(self, url):
    #   Retourne True si l'url doit être ajoutée à self.urls (i.e. c'est un enfant de root_url, elle n'y est pas déjà et elle n'est pas dans la blacklist)
    #   Arguments: url est une url absolue
    def _include_url(self,url):
        return (self.root_url in url) and not ((url in self.urls) or self._blacklist_url(url))

class Page:
    def __init__(self, url):
        self.url = url

        r = requests.get(url)
        if (r.status_code != 200 or len(r.history) > 0):
            logging.debug('Page non disponible ou redirection')
            raise RequestException(r)
        else:
            self.html = r.content
            #NB: un choix différent de parser donne un texte différent renvoyé par la fonction self._find_text() (les parser 'html.parser' et 'html5lib' ne trouvent pas tous les textes)
            self.soup = BeautifulSoup(self.html, 'lxml')

            if not (self.soup.title is None):
                self.title = self.soup.title.get_text()
            else:
                self.title = ''
            self.access_date = time.strftime("%d/%m/%Y")
            
            self.links = []
            self._find_links()

            self.images = []
            self._find_images()

            self.text = Text('')
            self._find_text()
	
    def screenshot(self, driver, file):
        driver.get(self.url)
        save_screenshot(driver, file)

    # _find_links(self):
    #   remplis self.images avec tous les liens trouvés dans self.soup. Les liens sont des urls absolues.
    def _find_links(self):
        for tag in self.soup.find_all('a'):
            try:
                href = tag['href']
                self.links.append( urljoin(self.url, href) )
            except KeyError:
                pass
        logging.debug('%d liens trouvés' % len(self.links))


    # _find_images(self):
    #   remplis self.images par une liste d'url vers toutes les images contenues dans soup.main
    def _find_images(self):
        for tag in self.soup.main.find_all(True):
            # 1ere possibilité: l'image est définie par CSS comme image de fond
            if tag.has_attr('style'):
                s = re.search('background-image:url\(\'(.*\.[a-zA-Z0-9]+)\'', tag['style'])
                if s:
                    self.images.append( urljoin(self.url, s.group(1)) )
            # 2e possibilité: balise <img>
            if (tag.name == 'img') and tag.has_attr('src'):
                self.images.append( urljoin(self.url, tag['src']) )
        logging.debug('%d images trouvées' % len(self.images))

    # _find_text(self):
    #   remplis self.text par le texte trouvé dans les balises textes de soup.main
    #
    #   src: https://matix.io/extract-text-from-webpage-using-beautifulsoup-and-python/
    def _find_text(self):
        blacklist = [
            '[document]',
            'noscript',
            'header',
            'html',
            'meta',
            'head', 
            'input',
            'script',
            'style',
            # there may be more elements you don't want, such as "style", etc.
        ]

        self.text = ''
        texts = self.soup.main.find_all(string=True)
        for t in texts:
            if not (t.parent.name in blacklist):
                # Les lignes suivantes enlèvent les espaces en trop et les textes vides
                r = re.search('\s*(.*\S)\s*', str(t))
                if r:
                    self.text += '{}\n'.format(r.group(1))


class Text(str):
    def count_char(self):
        return len(re.findall(r'\w', self))

    def count_words(self):
        return len(re.findall(r'\w+', self))

