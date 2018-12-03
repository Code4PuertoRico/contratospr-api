from rest_framework.schemas import AutoSchema


class ContractSchema(AutoSchema):
    def get_filter_fields(self, path, method):
        if self.view.action != "list":
            return []

        return super().get_filter_fields(path, method)
