#/usr/bin/python

# Variables de test
test_url="https://rewildingeurope.com/what-is-rewilding/"


import requests
from bs4 import BeautifulSoup

import re


# On ouvre la page et on la charge dans le parser
html = requests.get(test_url).content
soup = BeautifulSoup(html, 'html.parser')

# On n'a besoin que du tag <main>
main = soup.main

#Specifique au site de rewilding Europe: on enlève de l'arbre le <div> qui correspond à l'image de fond devant s'afficher sur la version mobile
def is_for_mobile(tag):
    if tag.has_attr('class'):
        for c in tag['class']:
            if 'mobile' in c:
                return True
    return False

for tag in main.find_all(is_for_mobile):
    tag.decompose()


# Récupère tout le texte: on cherche toutes les balises HTML qui contiennent du texte
#TODO: ajouter les liens <a> ?
for text in main.find_all(["h1","h2","h3","h4","h5","h6","p"]):
   print(text.get_text())


## Récupère toutes les images de la page
images=[]

for tag in main.find_all(True):
    # 1ere possibilité: l'image est définie par CSS comme image de fond
    if tag.has_attr('style'):
        s = re.search('background-image:url\(\'(.*\.jpg)\'', tag['style'])
        if s:
            images.append(s.group(1))

    # 2e possibilité: balise <img>
    if (tag.name == 'img') and tag.has_attr('src'):
        images.append(tag['src'])


print(len(images))
