#============================================================
#
# MyCrawler.py : définit les classes MyCrawler et MyPage
#
#
#============================================================

import os, re, csv, time, json

import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit

import logging


class MyCrawler:
    def __init__(self, root_url):
        self.root_url = urlunsplit(urlsplit(root_url)) #Sanitize the root url
        self.root_url_netloc = urlparse(self.root_url).netloc
        self.pages = []
        self.urls = [root_url]  #Urls collectées

    # crawl(): remplis self.pages avec des uris plus basses que root_url
    def crawl(self):
        logging.info("Commence à arpenter les pages")
        url_index = 0
        while url_index < len(self.urls):
            url_index = self._append_next_page(url_index)


    # append_next_page(self, i):
    #   Ajoute la page self.urls[i]. Si l'url est invalide (e.g. erreur 404) ou nous redirige vers une url déjà dans notre liste, on enlève self.urls[i].
    #
    #   Arguments: 'i' est l'indice de l'url à traiter dans self.urls
    #   Retourne: l'indice de la prochaine url à traiter dans self.urls ('i' ou 'i+1', selon qu'on est tombé sur une url valide ou pas)
    def _append_next_page(self, i):
        logging.info('Page %d/%d trouvées : %s' % (i, len(self.urls), self.urls[i]))
        try:
            page = MyPage( self.urls[i] )
        except RequestException as err: #TODO: MyPage doit lancer une RequestException en cas d'erreur ou de redirection
            if (not err.response) or (err.response.url in self.urls):
                logging.debug('La page est non-disponible ou nous redirige vers une url déjà dans la liste')
                del self.urls[i]
                return i
            else:
                logging.debug('Redirection: on remplace l\'url trouvée par son arrivée')
                page = MyPage(err.response.url)
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
    #   Retourne True si l'url doit être ajoutée à self.urls (i.e. elle n'y est pas déjà et elle n'est pas dans la blacklist)
    #   Arguments: url est une url absolue
    def _include_url(self,url):
        return not ((url in self.urls) or self._blacklist_url(url))


class MyPage:
    def __init__(self, url):
        self.url = url

        r = requests.get(url)
        if (r.status_code != 200 or len(r.history) > 0):
            logging.debug('Page non disponible ou redirection')
            raise RequestException(r)
        else:
            self.html = r.content
            self.soup = BeautifulSoup(self.html, 'html.parser')
            if not (self.soup.title is None):
                self.title = self.soup.title.get_text()
            else:
                self.title = ''
            self.access_date = time.strftime("%d/%m/%Y")
            
            self.links = []
            self._find_links()

            self.images = []
            self._find_images()

            self.text = ''
            self._find_text()


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
    def _find_text(self):
        texts = []
        for tag in self.soup.main.find_all(["h1","h2","h3","h4","h5","h6","p"]):
           texts.append(tag.get_text())
        self.text = '\n'.join(texts)



