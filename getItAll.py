#/usr/bin/python

# Variables de test
test_url="https://rewildingeurope.com/what-is-rewilding/"
root_url="https://rewildingeurope.com/"
dest_dir='RewildingEurope'
uris=[]


import requests
from bs4 import BeautifulSoup

import re
import os
import pdfkit


#============================================================
# Quelques méthodes utiles
#============================================================

# is_for_mobile(): retourne True si la classe du tag passé en argument contient 'mobile'
def is_for_mobile(tag):
    if tag.has_attr('class'):
        for c in tag['class']:
            if 'mobile' in c:
                return True
    return False

# Ajoute l'URL de base pour obtenir une adresse complète
#TODO: ça ne marche pas si des chemins relatifs sont donnés
def insert_root_url(url):
    if re.match('^/', url):
        return root_url + url
    else:
        return url


#============================================================
# On cherche toutes les uris à télécharger
#============================================================

html = requests.get(root_url).content
soup = BeautifulSoup(html, 'html.parser')

for tag in soup.ul.find_all('a'):
    href = tag['href']
    if not (re.match('.*/blog/', href) or re.match('.*/news/', href)):
        uris.append(href)

#============================================================
# Début de la boucle
#============================================================

if not os.path.isdir(dest_dir):
    os.mkdir(dest_dir)


page_counter = 1
n_pages = len(uris)

# Début de la grosse boucle

for url in uris:
    basename = dest_dir + '/page' + '{:0>3}'.format(page_counter)

    #==================================================
    # Préparation de l'arbre à partir du code HTML
    #==================================================
    html = requests.get(url).content
    soup = BeautifulSoup(html, 'html.parser')

    # On n'a besoin que du tag <main>
    main = soup.main

    # on enlève de l'arbre les <div> qui correspond à l'image de fond devant s'afficher sur la version mobile (cette partie est spécifique au site de RE

    for tag in main.find_all(is_for_mobile):
        tag.decompose()

    
    #==================================================
    # Récupération du texte
    #==================================================
    print('Page %d/%d : téléchargement du texte' % (page_counter, n_pages))
    texts=[]

    #TODO: ajouter les liens <a> ?
    for tag in main.find_all(["h1","h2","h3","h4","h5","h6","p"]):
       texts.append(tag.get_text())

    with open(basename + '.txt','w') as f:
        f.write('\n'.join(texts))


    #==================================================
    # Récupération des images
    #==================================================
    images=[]

    # On collectionne les uris des images
    for tag in main.find_all(True):
        # 1ere possibilité: l'image est définie par CSS comme image de fond
        if tag.has_attr('style'):
            s = re.search('background-image:url\(\'(.*\.jpg)\'', tag['style'])
            if s:
                images.append( insert_root_url(s.group(1)) )
        # 2e possibilité: balise <img>
        if (tag.name == 'img') and tag.has_attr('src'):
            images.append( insert_root_url(tag['src']) )

    # On télécharge les images
    img_counter=1
    n_img = len(images)

    for img_url in images:
        print('Page %d/%d : image %d/%d' % (page_counter, n_pages, img_counter, n_img))
        
        with open('%s_img%02d.jpg' % (basename, img_counter), 'wb') as f:
            f.write(requests.get(img_url).content)

        img_counter += 1
    # fin de la récupération des images


    #==================================================
    # Conversion de la page en pdf
    #==================================================
    print('Page %d/%d : génération du fichier pdf' % (page_counter, n_pages))
    #pdfkit.from_url(url, basename + '.pdf' , {'quiet': ''})
    pdfkit.from_url(url, basename + '.pdf')


    page_counter += 1


