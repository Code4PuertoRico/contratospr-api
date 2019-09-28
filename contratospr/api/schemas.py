from rest_framework.schemas.openapi import AutoSchema


class CustomAutoSchema(AutoSchema):
    def __init__(self, *args, **kwargs):
        self.tags = kwargs.pop("tags")
        return super().__init__(*args, **kwargs)

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)

        if self.tags:
            operation["tags"] = self.tags

        return operation
