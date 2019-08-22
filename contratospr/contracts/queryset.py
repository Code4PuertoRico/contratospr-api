from django.db import models


class ContractQuerySet(models.QuerySet):
    def amendments(self):
        # Amended contracts
        return self.filter(parent__isnull=False)

    def without_amendments(self):
        # Contracts excluding amendments
        return self.filter(parent=None)
