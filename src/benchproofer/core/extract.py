# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Pulling artifacts out of a model's reply.

A reply is prose plus fenced code blocks. These helpers take the block that was asked
for and nothing else, and fail rather than guess, so a round that produced no artifact
is recorded as such instead of yielding a file assembled from whatever the reply held.
"""

from __future__ import annotations

import re

from ..errors import BenchproofError
from .markers import REGIONS

__all__ = ["blocks", "code", "field", "harness", "regions", "witness"]

_FENCE = re.compile(r"^[ \t]*```[^\n]*\n(?P<body>.*?)(?:^[ \t]*```)", re.DOTALL | re.MULTILINE)
_MARKER = "benchproofer:begin"
_IMPL = f"{_MARKER} impl"
_BEGIN = re.compile(rf"{_MARKER}\s+(\S+)")
#: A sentinel for a region a solution file has, which is what makes a block part of the
#: file. A block sentinelled with another name, such as `witness`, is not.
_REGION = re.compile(
    rf"^\s*\S{{1,4}}\s*benchproofer:(?:begin|end)\s+(?:{'|'.join(REGIONS)})(?:\.[0-9]+)?\s*$",
    re.MULTILINE,
)
#: Any sentinel line, whatever it names, for taking one out of a block that is not a file.
_SENTINEL = re.compile(r"^\s*\S{1,4}\s*benchproofer:(?:begin|end)\s+\S+\s*$")
#: Regions only a solution file has; a `conformance.py` carrying one is the solution file again.
_NOT_A_HARNESS = ("spec", "proof", "axioms", "helpers")


def blocks(reply: str) -> list[str]:
    """Every fenced code block in a reply, in order."""
    return [match.group("body") for match in _FENCE.finditer(reply)]


def witness(reply: str) -> str:
    """The refutation witness a reply offers, or an empty string.

    The last block that is not part of the file: a reject case writes the rival's regions,
    then the claim refuting it. Sentinels a reply wrapped the witness in are taken out.
    A missing witness is `spec.strength.battery`'s to report, so this does not raise.
    """
    plain = [block for block in blocks(reply) if not _REGION.search(block)]
    return _unsentinelled(plain[-1]) if plain else ""


def field(reply: str, name: str) -> str:
    """Read a ``NAME: value`` line, or return an empty string.

    Only the prose before the first fenced block is searched, so a value inside code is
    not taken for the answer; a reply that is one fenced block and nothing else copied
    the prompt's fenced reply format, and its body is searched.
    """
    prose = _unwrapped(reply).split("```", 1)[0]
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*:\s*(?P<value>.+)$", re.MULTILINE)
    found = pattern.search(prose)
    return found.group("value").strip() if found else ""


def _unwrapped(reply: str) -> str:
    """The body of a reply that is one fenced block and nothing else; the reply otherwise."""
    found = blocks(reply)
    if len(found) == 1 and reply.count("```") == 2:
        stripped = reply.strip()
        if stripped.startswith("```") and stripped.endswith("```"):
            return found[0]
    return reply


def regions(reply: str) -> str:
    """Extract the marked regions a reply carries, sentinels included.

    A whole solution file or some of one: every block carrying region sentinels is part
    of the answer (`_merged`), since a reply asked for several regions often writes one
    block for each.

    Raises:
        BenchproofError: The reply contains no block with region sentinels.
    """
    candidates = [block for block in blocks(reply) if _REGION.search(block)]
    if candidates:
        return _normalize(_merged(candidates))
    if _REGION.search(reply):
        # A reply that forgot the fence but did write the file.
        return _normalize(reply)
    raise BenchproofError("the reply contains no file with benchproofer region sentinels in it")


def harness(reply: str) -> str:
    """Extract a `conformance.py`, which marks the implementation it carries.

    A `conformance.py` is a plain program whose one region is the Python copy of the
    implementation, in `impl` sentinels so the comparison can be rerun against another
    implementation.

    Raises:
        BenchproofError: The reply has no code block, the block marks no `impl` region,
            or it marks a region only a solution file has.
    """
    found = blocks(reply)
    if not found:
        raise BenchproofError("the reply contains no fenced code block")
    body = found[-1]
    if _IMPL not in body:
        raise BenchproofError(
            "conformance.py does not mark the implementation it contains; wrap the "
            f"Python copy of the implementation in '{_IMPL}' and its closing sentinel"
        )
    intruder = next((name for name in _NOT_A_HARNESS if f"{_MARKER} {name}" in body), "")
    if intruder:
        raise BenchproofError(
            f"conformance.py contains a {intruder!r} region, so it is a solution file "
            "rather than a program that runs against the repository"
        )
    return _normalize(body)


def code(reply: str, *, witnessed: bool = False) -> str:
    """Extract one code block that is not a solution file: a region body, or a program.

    Args:
        witnessed: The reply was asked for a refutation witness too, which it writes
            after the fragment, so the fragment is the second-to-last block where there
            are two.

    Raises:
        BenchproofError: The reply has no code block, or the block carries sentinels.
    """
    found = blocks(reply)
    if not found:
        raise BenchproofError("the reply contains no fenced code block")
    body = found[-2] if witnessed and len(found) > 1 else found[-1]
    if _MARKER in body:
        raise BenchproofError(
            "the reply holds a whole solution file where a fragment was asked for"
        )
    return _normalize(body)


def _merged(candidates: list[str]) -> str:
    """The blocks a reply wrote its regions in, as one fragment, in the order written.

    A block writing a region an earlier block wrote replaces that block whole, so a reply
    that corrects itself, or quotes the file and then changes it, is read by what it
    wrote last.
    """
    kept: list[tuple[set[str], str]] = []
    for block in candidates:
        names = set(_BEGIN.findall(block))
        kept = [(written, earlier) for written, earlier in kept if not written & names]
        kept.append((names, block))
    return "\n\n".join(block.strip("\n") for _, block in kept)


def _unsentinelled(text: str) -> str:
    """``text`` with every sentinel line dropped, under any comment token."""
    kept = [line for line in text.splitlines() if not _SENTINEL.match(line)]
    return _normalize("\n".join(kept))


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip("\n") + "\n"
