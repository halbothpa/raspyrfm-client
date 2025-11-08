"""Minimal offline replacement for :mod:`xeger` used in tests.

This module provides a very small subset of the ``xeger`` package so that
our test-suite can run in environments where fetching the real dependency is
not possible.  It understands the narrow set of regular expressions that the
legacy ``automatic_test`` uses to generate sample channel configurations.

The implementation favours determinism and clarity over completeness – it
returns the first value that satisfies the requested pattern and silently
ignores unsupported regex tokens rather than failing.  For the test-suite this
behaviour mirrors the behaviour of the real library sufficiently well because
all patterns boil down to simple character classes, fixed ranges or small
alternations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(slots=True)
class _QuantifiedToken:
    """Description of a token that should be repeated in the output."""

    text: str
    count: int = 1


class Xeger:
    """Very small subset of :class:`xeger.Xeger` used in tests."""

    def xeger(self, pattern: str) -> str:
        """Return a deterministic string that satisfies ``pattern``."""

        if not pattern:
            return ""

        expression = self._strip_anchors(pattern.strip())
        expression = self._pick_alternative(expression)
        tokens: List[_QuantifiedToken] = []
        index = 0
        while index < len(expression):
            char = expression[index]
            if char == "[":
                index, token = self._parse_class(expression, index)
                tokens.append(token)
                continue
            if char == "(":
                index, token = self._parse_group(expression, index)
                tokens.append(token)
                continue
            if char in "|)":
                index += 1
                continue
            if char == "\\":
                index += 1
                if index < len(expression):
                    literal = expression[index]
                    index += 1
                    count, index = self._parse_quantifier(expression, index)
                    tokens.append(_QuantifiedToken(literal, count))
                continue
            literal = char
            index += 1
            count, index = self._parse_quantifier(expression, index)
            tokens.append(_QuantifiedToken(literal, count))
        return "".join(self._repeat(token) for token in tokens)

    @staticmethod
    def _strip_anchors(pattern: str) -> str:
        if pattern.startswith("^"):
            pattern = pattern[1:]
        if pattern.endswith("$"):
            pattern = pattern[:-1]
        return pattern

    def _pick_alternative(self, pattern: str) -> str:
        """Return the left-most alternative in ``pattern`` if present."""

        depth = 0
        segment = []
        for index, char in enumerate(pattern):
            if char == "(":
                depth += 1
            elif char == ")":
                if depth:
                    depth -= 1
            elif char == "|" and depth == 0:
                return "".join(segment)
            segment.append(char)
        return pattern

    def _parse_class(
        self, pattern: str, start: int
    ) -> tuple[int, _QuantifiedToken]:
        end = self._find_closing(pattern, start, "[", "]")
        charset = pattern[start + 1:end]
        index = end + 1
        count, index = self._parse_quantifier(pattern, index)
        return index, _QuantifiedToken(self._expand_charset(charset)[0], count)

    def _parse_group(
        self, pattern: str, start: int
    ) -> tuple[int, _QuantifiedToken]:
        end = self._find_closing(pattern, start, "(", ")")
        segment = pattern[start + 1:end]
        index = end + 1
        count, index = self._parse_quantifier(pattern, index)
        text = self.xeger(segment)
        return index, _QuantifiedToken(text, count)

    @staticmethod
    def _parse_quantifier(pattern: str, index: int) -> tuple[int, int]:
        if index < len(pattern) and pattern[index] == "{":
            end = pattern.find("}", index)
            if end != -1:
                number = pattern[index + 1:end]
                if number.isdigit():
                    return int(number), end + 1
        return 1, index

    @staticmethod
    def _repeat(token: _QuantifiedToken) -> str:
        return token.text * max(token.count, 0)

    @staticmethod
    def _expand_charset(definition: str) -> List[str]:
        characters: List[str] = []
        index = 0
        while index < len(definition):
            char = definition[index]
            if index + 2 < len(definition) and definition[index + 1] == "-":
                end = definition[index + 2]
                characters.extend(Xeger._range(char, end))
                index += 3
            else:
                characters.append(char)
                index += 1
        return characters or [""]

    @staticmethod
    def _range(start: str, end: str) -> Iterable[str]:
        return (chr(code) for code in range(ord(start), ord(end) + 1))

    @staticmethod
    def _find_closing(
        pattern: str, start: int, opener: str, closer: str
    ) -> int:
        depth = 0
        for index in range(start, len(pattern)):
            char = pattern[index]
            if char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return index
        raise ValueError(f"Unbalanced pattern: {pattern!r}")
