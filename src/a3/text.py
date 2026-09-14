"""Small deterministic text utilities used by the bounded V1 evaluator."""

from __future__ import annotations

import re

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "in", "is", "it", "of", "on", "or", "that", "the", "their", "this", "to",
    "use", "with", "not", "no", "does", "do", "every", "all", "material",
}

NORMALISE = {
    "mandatory": "require", "mandates": "require", "mandate": "require",
    "required": "require", "requires": "require", "voluntarily": "voluntary",
    "organisations": "organization", "organizations": "organization",
    "certification": "certify", "certified": "certify",
    "guarantees": "guarantee", "guaranteed": "guarantee", "prohibited": "prohibit",
    "prohibits": "prohibit", "approved": "approve", "approves": "approve",
}


def tokens(text: str) -> set[str]:
    values = re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())
    return {NORMALISE.get(value, value) for value in values if value not in STOPWORDS}


def claims(answer: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", answer.strip())
    return [part.strip() for part in parts if len(tokens(part)) >= 2]


def citations(text: str) -> list[str]:
    return re.findall(r"\[([A-Za-z0-9_.:-]+)\]", text)


def numbers(text: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?%?", text))


def overlap_score(claim: str, passage: str) -> float:
    left, right = tokens(claim), tokens(passage)
    if not left:
        return 0.0
    return len(left & right) / len(left)
