from django.core.cache import cache
from django.core.management.base import BaseCommand

from ...models import Contract
from ...tasks import scrape_contracts


class Command(BaseCommand):
    help = "Update local contracts with data from remote source"

    def add_arguments(self, parser):
        parser.add_argument("--limit", nargs="?", type=int, default=1000)

    def handle(self, *args, **options):
        limit = options.get("limit")

        contracts = (
            Contract.objects.select_related("entity")
            .all()
            .order_by("pk")
            .only("pk", "number", "entity")
        )

        cur_offset = 0
        cur_limit = 1

        cache_key = "cmd:update_contracts:last_preview_id:limit={}".format(limit)
        last_contract_id = cache.get(cache_key)

        if last_contract_id:
            self.stdout.write("=> Starting after {}".format(last_contract_id))
            contracts = contracts.filter(pk__gt=last_contract_id)

        while cur_limit <= limit:
            cur_c = list(contracts[cur_offset:cur_limit].iterator())

            if len(cur_c) > 0:
                c = cur_c[0]
                last_contract_id = c.pk

                self.stdout.write(f"=> Scraping contract {c.pk} / {c.number}")
                scrape_contracts(
                    skip_doc_tasks=True,
                    contract_number=c.number,
                    entity_id=c.entity.source_id,
                )

                self.stdout.write("=> Last contract {}".format(last_contract_id))
                cache.set(cache_key, last_contract_id)
            else:
                self.stdout.write(
                    "=> Nothing found offset={} / limit={} / last_contract_id={}".format(
                        cur_offset, cur_limit, last_contract_id
                    )
                )
                break

            cur_offset += 1
            cur_limit += 1
