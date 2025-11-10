from drf_spectacular.openapi import AutoSchema


class TaggedAutoSchema(AutoSchema):
    """Prefer explicit schema_tags on a view before falling back to defaults."""

    def get_tags(self):
        if hasattr(self.view, "schema_tags") and self.view.schema_tags:
            return list(self.view.schema_tags)
        return super().get_tags()
