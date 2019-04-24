# Downloading contracts

To download contracts from https://consultacontratos.ocpr.gov.pr. This will download contracts as JSON files for every entity.

Note: This is really slow on purpose to be as kind as possible to third party systems.

```
$ docker-compose exec web python manage.py download_contracts
```

You can also specify a list of specific entities by providing a file similar to [this](https://consultacontratos.ocpr.gov.pr/entity/findby?name=&pageIndex=1&pageSize=20000).

```
$ docker-compose exec web python manage.py download_contracts --file entities.json
```

# Merging contracts

To merge all download contracts into a file that can be imported:

```
$ docker-compose exec web python manage.py merge_contracts
```

# Importing contracts

```
$ docker-compose exec web python manage.py import_contracts
```
