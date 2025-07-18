# brief17-appli_chat

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
