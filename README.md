# brief17-appli_chat

## Description

Application de chat en temps réel développée avec Django et WebSockets. Cette application permet aux utilisateurs authentifiés de communiquer instantanément dans des salles de chat dédiées.

## Technologies utilisées

**Backend :** Django 5.2 avec Channels pour les WebSockets, un service d'API dédié à la reconnaissance faciale avec FastAPI, Redis pour la couche de communication, et Daphne comme serveur ASGI.

**Frontend :** Tailwind CSS 4.1 avec Flowbite pour l'interface utilisateur moderne et responsive.

**Architecture :** Communication bidirectionnelle via WebSockets pour les messages en temps réel, authentification Django intégrée, et stockage des données en SQLite.

## En local :

### Run Django app : 
```bash
python manage.py runserver
```

### Redis used for channel layer as its backing store :
```bash
docker run --rm -p 6379:6379 redis:7
```

### Run Tailwind : 
```bash
npx @tailwindcss/cli -i ./web/static/src/input.css -o ./web/static/src/output.css --watch
```

## Docker
```bash
docker-compose up --build
```

## V2 : modification de l'architecture

**Architecture :** L'architecture est désormais basée sur des microservices conteneurisés avec Docker. La reconnaissance faciale est gérée par un service séparé (ml_service) qui communique avec Django via une API. Les données d'authentification faciale sont stockées dans une base de données PostgreSQL dédiée, garantissant l'isolation et la performance.

### Démarrage du projet avec Docker

Le projet est entièrement géré par Docker Compose. Aucune configuration locale n'est requise.

**1. Lancement de l'application**
Pour construire les images Docker et lancer tous les services (web, ml_service, PostgreSQL, Redis, Nginx, Tailwind) en arrière-plan, utilisez la commande suivante :
```bash
docker-compose up --build -d
```

**2. Accès à l'application**
Une fois les services démarrés, vous pouvez accéder à l'application via Nginx à l'adresse suivante :
```bash
http://localhost:80
```

**3. Commandes de gestion**
Voici les commandes essentielles pour gérer les services dans vos conteneurs :

- Exécuter les migrations Django
Les migrations doivent être appliquées à l'intérieur du conteneur web.
```bash
docker exec mychat_web python manage.py makemigrations
docker exec mychat_web python manage.py migrate
```

- Créer un super-utilisateur Django
```bash
docker exec -it mychat_web python manage.py createsuperuser
```

- Afficher les logs de tous les services
```bash
docker-compose logs -f
```

- Arrêter les services
Pour arrêter et supprimer les conteneurs, les réseaux et les volumes créés par docker-compose up :
```bash
docker-compose down
```