# coding: utf-8
#============================================================
#
# MyCrawler.py : définit les classes MyCrawler et Page
#
#
#============================================================

import os, re, csv, time, json

import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit

import logging

import pickle

# Captures d'écran : pris depuis
# https://gist.github.com/fabtho/13e4a2e7cfbfde671b8fa81bbe9359fb
from selenium import webdriver
from save_screenshot import save_screenshot


class Crawler:
    def __init__(self, root_url, project_name = None, text_blacklist= None):
        self.root_url = root_url
        self.root_url_netloc = urlparse(self.root_url).netloc
        self.pages = []                             # Pages parsées
        self.urls = [root_url]                      # Urls collectées
        if project_name:                                # Nom du répertoire du projet
            self.project_name = project_name
        else:
            self.project_name = self.root_url_netloc   
        self.data_dir = '%s/data' % self.project_name                 # Nom du répertoire des données
        self.add_text_blacklist = text_blacklist
        

    def __iter__(self):
        return self.pages.__iter__()

    # __getstate__():
    #   Pour pickle: retourne tous les attributs de l'instance *excepté* self.add_text_blacklist (c'est une référence à une fonction qui est définie à l'extérieur de la classe. La sauvegarder conduit à une erreur quand on appelle pickle.load, il faut donc la spécifier manuellement -> cf. self.load(path, text_blacklist)
    def __getstate__(self):
        state = {
                'root_url' : self.root_url,
                'root_url_netloc' : self.root_url_netloc,
                'pages' : self.pages,
                'urls' : self.urls,
                'project_name' : self.project_name,
                'data_dir' : self.data_dir,
                }
        return state

    # __setstate()__
    #   Pour pickle.
    def __setstate__(self, state):
        self.root_url = state['root_url']
        self.root_url_netloc = state['root_url_netloc']
        self.pages = state['pages']
        self.urls = state['urls']
        self.project_name = state['project_name']
        self.data_dir = state['data_dir']
        self.add_text_blacklist = None

    # dump():
    # Utilise pickle pour sauver l'objet de type crawler
    def dump(self, path = None):
        if not path:
            path = '%s/%s.dat' % (self.project_name, self.project_name)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    # load():
    #   Utilise pickle pour charger un objet Crawler. Il faut ajouter manuellement la fonction add_text_blacklist (pickkle stocke seulement la référence à cette fonction ; si on fait pickle.load sans précaution depuis un environnement différent, cette référence ne pointe vers rien et provoque une erreur. Voir __getargs__.
    @staticmethod
    def load(path = None, text_blacklist=None):
        with open(path, 'rb') as f:
            crawler = pickle.load(f)
            crawler.add_text_blacklist = text_blacklist
            return crawler
        return None

    # crawl(): remplis self.pages avec des uris plus basses que root_url
    def crawl(self):
        logging.info("Commence à arpenter les pages")
        url_index = 0
        while url_index < len(self.urls):
            url_index = self._append_next_page(url_index)


    # text_blacklist():
    #   Teste 'tag' (objet bs4.NavigableString) pour savoir si le texte contenu doit être inclus
    #   Retourne: True si tag est blacklisté, False sinon.
    def text_blacklist(self, tag):
        # Blacklist comments
        if isinstance(tag, Comment):
            logging.debug('Texte filtré (commentaire) : %s' % tag)
            return True
        # Blacklist style, scripts, etc
        blacklist_parent_name = [
            #'[document]',          # Inutile (on regarde seulement le texte dans <main>
            #'header',
            #'html',
            #'meta',
            #'head', 
            'noscript',
            'input',
            'script',
            'style',
        ]
        if (tag.parent.name in blacklist_parent_name):
            logging.debug('Texte filtré (parent %s) :\n%s' %(tag.parent.name, str(tag)))
            return True
        # Teste la blacklist optionnelle fournie à la construction de l'objet
        if self.add_text_blacklist:
            return self.add_text_blacklist(tag)
            
        return False
    #
    # fin de text_blacklist()

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

    # save_csv():
    #   Enregistre un fichier csv compatible avec TXM
    def save_csv(self):
        logging.info('Écriture du fichier csv')
        self._ensure_project_dir()
        rows = [['id', 'titre', 'url', 'date_telechargement', 'nb_images', 'nb_signes', 'nb_mots', 'type']]
        for page_id, page in enumerate(self):
            rows.append([ page_id, page.title, page.url, page.access_date, len(page.images), page.text.count_char(), page.text.count_words(), 'site' ])

        #TODO: pour compter la longueur du texte, faut-il enlever les espaces et \n ?
        with open('%s/metadata.csv' % self.data_dir, 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=',', quotechar='"')
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
            page = Page( self.urls[i], text_blacklist=self.text_blacklist )
        except RequestException as err:
            if (not err.response) or (err.response.url in self.urls):
                logging.debug('La page est non-disponible ou nous redirige vers une url déjà dans la liste')
                del self.urls[i]
                return i
            else:
                logging.debug('Redirection: on remplace l\'url trouvée par son arrivée')
                page = Page(err.response.url, text_blacklist = self.text_blacklist)
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
    def __init__(self, url, text_blacklist = None):
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
            self._find_text(text_blacklist)

    # __getstate__():
    #   Appelée par pickle pour sauvegarder l'objet
    #   Returns: a pickable object
    def __getstate__(self):
        state = {
            'url' : self.url,
            'html' : self.html,
            'access_date' : self.access_date,
            'links' : self.links,
            'images' : self.images,
            'text' : self.text,
            'title' : self.title,
        }
        return state

    def __setstate__(self, state):
        self.url = state['url']
        self.html = state['html']
        self.access_date = state['access_date']
        self.links = state['links']
        self.images = state['images']
        self.text = state['text']
        self.title = state['title']

        self.soup = BeautifulSoup(self.html, 'lxml')

	
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
    def _find_text(self, text_blacklist = None):
        text = ''
        texts = self.soup.main.find_all(string=True)
        for t in texts:
            if text_blacklist and (not text_blacklist(t)):
                # Les lignes suivantes enlèvent les espaces en trop et les textes vides
                r = re.search('\s*(.*\S)\s*', str(t))
                if r:
                    text += '{}\n'.format(r.group(1))
        self.text = Text(text)


class Text(str):
    def count_char(self):
        return len(re.findall(r'\S', self))

    def count_words(self):
        return len(re.findall(r'\S+', self))

