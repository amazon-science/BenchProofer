# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a `conformance.py` has to carry of the code the checker read.

`impl.conformance` holds a `conformance.py` to carrying the implementation, and
`spec.axioms_grounded` to carrying the axioms region as code or quoted. A copy may leave
out comments and docstrings; everything that runs, including a string that is part of an
expression, has to be carried.
"""

from __future__ import annotations

from benchproofer.core.runnable import (
    contains_lines,
    executable_view,
    quotes_lines,
    uncarried,
    unquoted,
)

COMMENT = "#"

#: An axioms region as a Nagini model writes one: an assumption whose body is its
#: docstring, and one whose docstring precedes its contract.
AXIOMS = '''\
@Pure
@ContractOnly
# benchproofer:axiom pathlib.Path.resolve
def canonical(loc: PSeq[int]) -> PSeq[int]:
    """The resolved location: a function of the location alone.

    Deterministic, and never the operation under change.
    """


@ContractOnly
# benchproofer:axiom importlib.import_module
def version_of(name: int) -> int:
    """The version a module reports, or the absent marker."""
    Ensures(True)'''


def quoted(lines: list[str]) -> str:
    """A program quoting ``lines`` behind the comment token, as `axioms.py` does."""
    quotation = "\n".join(f"# {line}" for line in lines)
    return f"import pathlib\n{quotation}\nraise SystemExit(0)\n"


def test_a_quotation_that_leaves_out_the_docstrings_carries_the_declarations() -> None:
    """A docstring, often all a `@ContractOnly` body has, is not part of what it declares."""
    declarations = [
        "@Pure",
        "@ContractOnly",
        "def canonical(loc: PSeq[int]) -> PSeq[int]:",
        "@ContractOnly",
        "def version_of(name: int) -> int:",
        "    Ensures(True)",
    ]

    assert quotes_lines(quoted(declarations), AXIOMS, COMMENT)
    assert unquoted(quoted(declarations), AXIOMS, COMMENT) == ""


def test_leaving_out_the_docstrings_does_not_excuse_a_missing_declaration_line() -> None:
    """Prose is what is exempt, not the contract a docstring happens to sit above."""
    declarations = [
        "@Pure",
        "@ContractOnly",
        "def canonical(loc: PSeq[int]) -> PSeq[int]:",
        "@ContractOnly",
        "def version_of(name: int) -> int:",
    ]

    assert not quotes_lines(quoted(declarations), AXIOMS, COMMENT)
    assert unquoted(quoted(declarations), AXIOMS, COMMENT) == "Ensures(True)"


def test_a_quotation_carrying_the_docstrings_as_well_still_carries_the_declarations() -> None:
    """What the tool quotes itself is the region whole, prose included."""
    assert quotes_lines(quoted(AXIOMS.splitlines()), AXIOMS, COMMENT)


def test_a_string_that_is_part_of_an_expression_is_code_and_has_to_be_carried() -> None:
    """Only a string standing as a statement of its own is prose; an f-string is code."""
    block = (
        "def label(x: int) -> str:\n"
        '    prefix = (\n        "item"\n    )\n'
        '    f"{record(x)}"\n'
        '    return prefix + "s"\n'
        'def other() -> str: """Documented on its own line."""'
    )
    lines = block.splitlines()

    assert contains_lines(block, block)
    for line in (line for line in lines if '"' in line):
        lacking = "\n".join(other for other in lines if other != line)
        assert not contains_lines(lacking, block), line


def test_a_docstring_is_prose_in_a_region_indented_under_a_def_it_does_not_hold() -> None:
    """A method body's region ends at a shallower margin than it starts at."""
    block = (
        "        total = 0\n"
        "        return total\n"
        "    def helper(self) -> int:\n"
        '        """What the helper is for."""\n'
        "        return 1"
    )
    transcribed = "total = 0\nreturn total\ndef helper(self) -> int:\n    return 1\n"

    assert contains_lines(transcribed, block)


def test_a_block_the_tokenizer_refuses_is_held_to_every_line_but_its_comments() -> None:
    """Where the prose cannot be told from the code, a copy is held to more, not less."""
    block = 'def f(x):\n    """Unterminated.\n    return x'

    assert not contains_lines("def f(x):\n    return x\n", block)
    assert contains_lines(block + "\n# a note\n", block)


def test_a_block_that_is_nothing_but_prose_is_never_carried() -> None:
    """An empty block would let a program with no implementation pass for one with it."""
    block = '    """Only a docstring."""\n    # and a note'

    assert not contains_lines("anything at all\n", block)


# ---- trailing comments ------------------------------------------------------


#: An implementation region as Nagini reads one: each assignment typed by a comment the
#: interpreter never reads, and a `#` inside a literal that is part of the value.
TYPED = (
    "        self.width = width    # type: int\n"
    "        self.height = height  # type: int\n"
    '        self.separator = "#"  # what joins the two'
)


def test_the_runnable_form_leaves_out_a_trailing_comment_and_keeps_a_hash_in_a_string() -> None:
    """What runs is the code before the comment; a `#` inside a literal is that code."""
    view = executable_view(TYPED, (), COMMENT)

    assert view.splitlines() == [
        "        self.width = width",
        "        self.height = height",
        '        self.separator = "#"',
    ]


def test_a_copy_that_drops_keeps_or_rewrites_the_trailing_comments_carries_the_lines() -> None:
    """A trailing comment, a type comment included, is set aside on both sides."""
    transcribed = 'self.width = width\nself.height = height\nself.separator = "#"\n'
    own = (
        "self.width = width  # copied from the region\n"
        "self.height = height  # copied from the region\n"
        'self.separator = "#"  # copied from the region\n'
    )

    assert contains_lines(transcribed, executable_view(TYPED, (), COMMENT))
    for copy in (transcribed, TYPED, own):
        assert contains_lines(copy, TYPED), copy


def test_a_hash_inside_a_string_is_code_and_its_value_has_to_be_carried() -> None:
    """Cutting a line at the first `#` would let a copy change the literal and pass."""
    changed = 'self.width = width\nself.height = height\nself.separator = ""\n'

    assert not contains_lines(changed, TYPED)


def test_a_quoted_declaration_is_carried_with_or_without_a_trailing_comment() -> None:
    """A quotation is read as the line it quotes, and that line's comment is prose too."""
    block = (
        "@ContractOnly\ndef width(x: int) -> int:\n    Ensures(Result() >= 0)  # never negative"
    )

    for trailer in ("", "  # never negative", "  # a note of the program's own"):
        harness = quoted(
            [
                "@ContractOnly",
                "def width(x: int) -> int:",
                f"    Ensures(Result() >= 0){trailer}",
            ]
        )
        assert quotes_lines(harness, block, COMMENT), trailer
    assert unquoted(quoted(["@ContractOnly"]), block, COMMENT) == "def width(x: int) -> int:"
    assert unquoted(quoted(["@ContractOnly", "def width(x: int) -> int:"]), block, COMMENT) == (
        "Ensures(Result() >= 0)"
    )


def test_a_trailing_comment_stays_where_the_language_is_not_python() -> None:
    """Without Python's tokenizer a comment token inside a literal cannot be told apart."""
    block = 'def greeting : String := "-- not a comment" -- a comment'

    assert executable_view(block, (), "--") == block


def test_the_line_a_copy_lacks_is_the_one_its_in_order_scan_stopped_at() -> None:
    """Told only that a copy is not verbatim, a reader has to diff two files to find why."""
    block = "    total = 0  # type: int\n    total = helper(x)\n    return total"
    copy = "def shadow(x):\n    total = 0\n    total = shadow_helper(x)\n    return total\n"

    assert not contains_lines(copy, block)
    assert uncarried(copy, block) == "total = helper(x)"
    assert uncarried(copy.replace("shadow_helper", "helper"), block) == ""
