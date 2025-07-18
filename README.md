# brief17-appli_chat

## Description

Application de chat en temps réel développée avec Django et WebSockets. Cette application permet aux utilisateurs authentifiés de communiquer instantanément dans des salles de chat dédiées.

## Technologies utilisées

**Backend :** Django 5.2 avec Channels pour la gestion des WebSockets, Redis comme couche de communication entre les instances, et Daphne comme serveur ASGI.

**Frontend :** Tailwind CSS 4.1 avec Flowbite pour l'interface utilisateur moderne et responsive.

**Architecture :** Communication bidirectionnelle via WebSockets pour les messages en temps réel, authentification Django intégrée, et stockage des données en SQLite.

## En local :

### Run Django app : 
```
python manage.py runserver
```

### Redis used for channel layer as its backing store :
```
docker run --rm -p 6379:6379 redis:7
```

### Run Tailwind : 
```
npx @tailwindcss/cli -i ./static/src/input.css -o ./static/src/output.css --watch
```

## Docker
```
docker-compose up --build
```
