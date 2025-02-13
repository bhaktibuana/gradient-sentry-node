docker build -t bhaktibuana/gradient-bot:latest -f docker/dockerfile .
docker push bhaktibuana/gradient-bot:latest
docker-compose -f docker/docker-compose.yml up -d --force-recreate
docker system prune -a -f