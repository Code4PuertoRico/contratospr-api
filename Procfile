web: gunicorn -b "0.0.0.0:$PORT" -w 3 contratospr.wsgi
worker: ./docker-entrypoint.sh start-worker
