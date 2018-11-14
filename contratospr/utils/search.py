from django.contrib.postgres.search import SearchVectorCombinable, SearchVectorField
from django.db.models.expressions import Func, Value


# Patch SearchVector with https://github.com/django/django/pull/10209
class SearchVector(SearchVectorCombinable, Func):
    function = "to_tsvector"
    arg_joiner = ", ' ',"
    template = "%(function)s(concat(%(expressions)s))"
    output_field = SearchVectorField()
    config = None

    def __init__(self, *expressions, **extra):
        super().__init__(*expressions, **extra)
        self.config = self.extra.get("config", self.config)
        weight = self.extra.get("weight")
        if weight is not None and not hasattr(weight, "resolve_expression"):
            weight = Value(weight)
        self.weight = weight

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        resolved = super().resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        if self.config:
            if not hasattr(self.config, "resolve_expression"):
                resolved.config = Value(self.config).resolve_expression(
                    query, allow_joins, reuse, summarize, for_save
                )
            else:
                resolved.config = self.config.resolve_expression(
                    query, allow_joins, reuse, summarize, for_save
                )
        return resolved

    def as_sql(self, compiler, connection, function=None, template=None):
        config_params = []
        if template is None:
            if self.config:
                config_sql, config_params = compiler.compile(self.config)
                template = "%(function)s({}::regconfig, concat(%(expressions)s))".format(
                    config_sql.replace("%", "%%")
                )
            else:
                template = self.template
        sql, params = super().as_sql(
            compiler, connection, function=function, template=template
        )
        extra_params = []
        if self.weight:
            weight_sql, extra_params = compiler.compile(self.weight)
            sql = "setweight({}, {})".format(sql, weight_sql)
        return sql, config_params + params + extra_params
