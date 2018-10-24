# Notes

```
$ docker build -t gcr.io/tracking-contratos-pr/tracking-contratos-pr:latest .
$ docker push gcr.io/tracking-contratos-pr/tracking-contratos-pr:latest
```

```
$ helm install \
  --name tracking-contratospr-postgresql \
  --set postgresqlUser=tracking-contratospr,postgresqlDatabase=tracking-contratospr \
  stable/postgresql
```

```
$ helm install --name tracking-contratospr-redis \
  --set cluster.enabled=false \
  stable/redis
```

```
$ helm install --name tracking-contratospr-elasticsearch stable/elasticsearch
```

```
$ kubectl apply -f kubernetes/secrets.yaml
$ kubectl apply -f kubernetes/tracking-contratospr.yaml
$ kubectl apply -f kubernetes/ingress.yaml
```
