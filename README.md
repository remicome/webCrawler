# webCrawler:

Téléchargement d'un site complet pour générer un corpus mobilisable pour des analyses de texte et d'image.

## Usage
La classe Crawler parcourt un site à partir d'une url racine et télécharge:
* tous les textes présents sur la page,
* toutes les images,
* enregistre une capture d'écran de la page
* crée un corpus (fichier .csv exploitable avec IraMuTeQ)

cf `crawl.py` pour l'usage.

## Dépendance:
* geckodriver (pour faire des captures d'écran en utilisant firefox)
