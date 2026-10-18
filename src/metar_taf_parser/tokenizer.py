"""Tokenizer that splits a raw METAR/TAF report into individual groups."""


class Tokenizer:
    """Splits a raw report into its whitespace-separated groups, dropping remarks."""

    _END_MARKER = "="
    _REMARKS_MARKER = "RMK"

    def tokenize(self, raw: str) -> list[str]:
        """Return the report's groups in order, excluding the `RMK` section.

        A trailing `=` end-of-report marker is stripped before splitting.

        Args:
            raw: The raw report text.

        Returns:
            The whitespace-separated groups that precede `RMK`, if present.
        """
        body, _remarks = self._split_remarks(raw.rstrip().removesuffix(self._END_MARKER))
        return body.split()

    def _split_remarks(self, raw: str) -> tuple[str, str | None]:
        """Split `raw` into (body, remarks) at the `RMK` group."""
        groups = raw.split()
        if self._REMARKS_MARKER not in groups:
            return " ".join(groups), None

        index = groups.index(self._REMARKS_MARKER)
        return " ".join(groups[:index]), " ".join(groups[index + 1 :])
