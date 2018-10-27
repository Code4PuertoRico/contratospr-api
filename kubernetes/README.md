# Notes

## Setup GKE

```
$ kubectl apply -f rbac-config.yaml
$ helm init --service-account tiller
$ helm install --name tracking-contratospr-postgresql \
  --set postgresqlDatabase=tracking-contratospr stable/postgresql
$ helm install --name tracking-contratospr-redis \
  --set cluster.enabled=false stable/redis
```

## Initial deploy

```
$ kubectl apply -f kubernetes/secrets.yaml
$ kubectl apply -f kubernetes/tracking-contratospr.yaml
$ kubectl apply -f kubernetes/ingress.yaml
```

## Deploy changes

```
$ ./kubernetes/deploy.sh
```
