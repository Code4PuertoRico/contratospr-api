# Tracking Contratos PR

Gather data from the ["Consulta del Registro de Contratos"](https://consultacontratos.ocpr.gov.pr/) to enable independent research and analysis.

## Development

### Docker

```
$ docker-compose up -d
$ docker-compose exec web python manage.py createsuperuser
$ docker-compose exec web python manage.py scrape --limit 1000
$ open http://localhost:8000/admin
```

