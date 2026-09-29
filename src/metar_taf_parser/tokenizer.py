"""Tokenizer that splits a raw METAR/TAF report into individual groups."""


class Tokenizer:
    """Splits a raw report into its whitespace-separated groups, dropping remarks."""

    def tokenize(self, raw: str) -> list[str]:
        """Return the report's groups in order, excluding the `RMK` section. Logic pending."""
        raise NotImplementedError

    def _split_remarks(self, raw: str) -> tuple[str, str | None]:
        """Split `raw` into (body, remarks) at the `RMK` group. Logic pending."""
        raise NotImplementedError
