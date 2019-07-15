#!/usr/bin/python3

# Variables spécifiques au projet
root_url="https://rewildingeurope.com"
project_name='RewildingEurope'


import os, re, csv, time, json

import requests
from bs4 import BeautifulSoup

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
print('Extraction des urls à télécharger')

html = requests.get(root_url).content
soup = BeautifulSoup(html, 'html.parser')

uris=[root_url]
for tag in soup.ul.find_all('a'):
    href = tag['href']
    if not (re.match('.*/blog/', href) or re.match('.*/news/', href) or re.match('.*europeansafaricompany.*', href)):
        uris.append(href)

#============================================================
# Début de la boucle
#============================================================

if not os.path.isdir(project_name):
    os.mkdir(project_name)


page_counter = 1
n_pages = len(uris)

pages = [] # Un tableau de hash qui contient toutes les informations sur les pages


# Début de la grosse boucle

for url in uris:
    print('Téléchargement des informations: page %d/%d' % (page_counter, n_pages))

    this_page_id = '{:0>3}'.format(page_counter)

    #==================================================
    # Préparation de l'arbre à partir du code HTML

    html = requests.get(url).content
    soup = BeautifulSoup(html, 'html.parser')

    # On n'a besoin que du tag <main>
    main = soup.main

    # on enlève de l'arbre les <div> qui correspond à l'image de fond devant s'afficher sur la version mobile (cette partie est spécifique au site de RE

    for tag in main.find_all(is_for_mobile):
        tag.decompose()

    # Fin de la préparation de l'arbre
    #==================================================
    
    #==================================================
    # Titre de la page (ici un titre réduit est dans main.h1 ; à défaut dans la balise title)
    if not (soup.title is None):
        this_page_title = soup.title.get_text()
    else:
        this_page_title = ''
    #
    #==================================================


    #==================================================
    # Récupération du texte
    #==================================================
    texts=[]

    #TODO: ajouter les liens <a> ?
    for tag in main.find_all(["h1","h2","h3","h4","h5","h6","p"]):
       texts.append(tag.get_text())

    this_page_text = '\n'.join(texts)

    #==================================================
    # Récupération des uris des images
    #==================================================
    this_page_images = []

    # On collectionne les uris des images
    for tag in main.find_all(True):
        # 1ere possibilité: l'image est définie par CSS comme image de fond
        if tag.has_attr('style'):
            s = re.search('background-image:url\(\'(.*\.jpg)\'', tag['style'])
            if s:
                this_page_images.append( insert_root_url(s.group(1)) )
        # 2e possibilité: balise <img>
        if (tag.name == 'img') and tag.has_attr('src'):
            this_page_images.append( insert_root_url(tag['src']) )


    pages.append({'id' : this_page_id, \
            'title' : this_page_title, \
            'url' : url, \
            'basepath': project_name + '/page' + this_page_id, \
            'date' : time.strftime("%d/%m/%Y"), \
            'text' : this_page_text, \
            'images' : this_page_images})

    page_counter += 1

#============================================================
# Dump du dictionnaire 'pages' comme fichier json (pour pouvoir
#  le charger facilement plus tard)
print('Écriture du fichier json')
with open(project_name + '.json', 'w') as f:
    json.dump(pages, f)

# fin de l'écriture du fichier json
#============================================================



#============================================================
# Génération du fichier csv

print('Écriture du fichier CSV')

rows = [['Id', 'Titre', 'url', 'Date de téléchargement', 'Nombre d\'images', 'Nombre de signes du texte']]
for p in pages:
    rows.append([ p['id'], p['title'], p['url'], p['date'], len(p['images']), len(p['text']) ])

#TODO: pour compter la longueur du texte, faut-il enlever les espaces et \n ?
with open(project_name + '.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# fin de l'écriture du fichier csv
#============================================================


#============================================================
# Écriture des fichiers textes

print('Écriture des fichiers texte')

gather_texts = ''

for p in pages:
    gather_texts += ('**** *id_%s\n%s\n\n' % (p['id'], p['text']))

    with open(p['basepath'] + '.txt','w') as f:
        f.write(p['text'])

# On écrit un gros fichier qui rassemble tout:
with open(project_name + '.txt','w') as f:
    f.write(gather_texts)

# fin de l'écriture des fichiers texte
#============================================================


#==================================================
# Téléchargement des images
#
page_counter = 1

for p in pages:
    img_counter=1
    n_img = len(p['images'])

    for img_url in p['images']:
        print('Téléchargement des images : page %d/%d : image %d/%d' % (page_counter, n_pages, img_counter, n_img))
        
        with open('%s_img%02d.jpg' % (p['basepath'], img_counter), 'wb') as f:
            f.write(requests.get(img_url).content)

        img_counter += 1

    page_counter += 1
#
# fin du téléchargement des images
#==================================================


#==================================================
# Conversion de la page en pdf
#
page_counter = 1
for p in pages:
    print('Génération du fichier pdf : page %d/%d' % (page_counter, n_pages))
    pdfkit.from_url(p['url'], p['basepath'] + '.pdf', {'quiet': '', 'disable-javascript': ''})

    page_counter += 1
#
# fin de la conversion des pdf
#==================================================

print('C\'est terminé !')
