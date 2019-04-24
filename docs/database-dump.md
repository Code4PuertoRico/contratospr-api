
# Using latest dump for development

- Download [latest database dump](./data.md#database-dump-for-development)
- Place `backup.dump` in `docker/postgres/backup.dump`.

# Generating database dump

```
$ docker-compose exec -T database \
  pg_dump -Fc --no-acl --no-owner \
    -h localhost -U postgres postgres > docker/postgres/backup.dump
```
