# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Marker regions: the projection everything downstream is defined against."""

from __future__ import annotations

import pytest

from benchproofer.core import markers
from benchproofer.errors import MarkerError

COMMENT = "#"

MINIMAL = """\
# benchproofer:begin spec
assert True
# benchproofer:end spec
# benchproofer:begin impl
def impl(x):
    return x
# benchproofer:end impl
"""

#: The same file, with an assumption in the axioms region, where one is allowed.
ASSUMING = (
    "# benchproofer:begin axioms\nassume(loads_is_total)\n# benchproofer:end axioms\n" + MINIMAL
)


def test_parse_reports_every_region_with_its_body(solution: str) -> None:
    regions = markers.parse(solution, COMMENT)

    assert set(regions) == {"helpers", "impl", "spec"}
    assert "def impl(cents):" in regions["impl"].text
    assert regions["spec"].text
    assert regions["impl"].start < regions["impl"].end


def test_a_fragment_of_a_file_is_read_when_that_is_what_was_asked_for() -> None:
    """A variant writes the regions it owns, so its reply is not a whole file."""
    fragment = "# benchproofer:begin impl\ndef impl(x):\n    return x\n# benchproofer:end impl"

    regions = markers.parse(fragment, COMMENT, required=())

    assert set(regions) == {"impl"}
    with pytest.raises(MarkerError, match="missing required region"):
        markers.parse(fragment, COMMENT)


def test_a_marker_in_another_language_is_not_read(solution: str) -> None:
    """The comment token is the backend's, so `//` markers are text to Python."""
    with pytest.raises(MarkerError):
        markers.parse(solution, "//")


@pytest.mark.parametrize(
    "line",
    [
        "# benchproofer:begin proof.det",
        "# benchproofer:begin proof pinned",
        "# benchproofer:end  proof.pin",
        "# benchproofer:begin",
    ],
    ids=["suffix", "trailing-word", "closing", "nameless"],
)
def test_a_line_that_opens_a_region_and_is_not_a_sentinel_is_refused(line: str) -> None:
    """Read as a comment, what it wraps would sit outside every region and be shown."""
    with pytest.raises(MarkerError, match="not in the form a sentinel has"):
        markers.parse(f"{MINIMAL}{line}\nx = 1\n", COMMENT)


def test_a_sentinel_written_in_another_languages_comment_is_still_text() -> None:
    """The refusal is about this backend's own markers: `--` is code or prose to Python."""
    assert set(markers.parse(f"{MINIMAL}-- benchproofer:begin proof.det\n", COMMENT)) == {
        "spec",
        "impl",
    }


def test_the_spec_view_elides_the_implementation_and_is_idempotent(solution: str) -> None:
    view = markers.spec_view(solution, COMMENT)

    assert "quarters = cents // 25" not in view
    assert "benchproofer:elided impl" in view
    assert "property_change_is_the_fewest_coins" in view
    assert markers.spec_view(view, COMMENT) == view


def test_two_implementations_of_one_spec_share_a_spec_view(solution: str) -> None:
    rival = markers.replace_region(solution, COMMENT, "impl", "def impl(cents):\n    return ()")

    assert markers.same_spec(solution, rival, COMMENT)
    assert not markers.same_spec(
        solution,
        markers.replace_region(solution, COMMENT, "spec", "assert True"),
        COMMENT,
    )


def test_region_digests_change_only_where_the_bytes_changed(solution: str) -> None:
    before = markers.region_digests(solution, COMMENT)
    after = markers.region_digests(
        markers.replace_region(solution, COMMENT, "impl", "def impl(cents):\n    return ()"),
        COMMENT,
    )

    assert before["impl"] != after["impl"]
    assert before["spec"] == after["spec"]
    assert before["spec_view"] == after["spec_view"]


def test_blanking_a_region_scopes_a_scan_to_everything_outside_it() -> None:
    """An assumption is allowed in one region, so a scan skips it, keeping line numbers."""
    scoped = markers.without_region(ASSUMING, COMMENT, "axioms")

    assert markers.occurrences(ASSUMING, COMMENT, ("assume(",)) == {"assume(": 2}
    assert markers.occurrences(scoped, COMMENT, ("assume(",)) == {}
    assert scoped.splitlines()[2:] == ASSUMING.splitlines()[2:]


def test_blanking_a_region_the_file_does_not_have_changes_nothing() -> None:
    assert markers.without_region(MINIMAL, COMMENT, "axioms") == MINIMAL


def test_replacing_an_absent_region_is_refused() -> None:
    with pytest.raises(MarkerError, match="absent"):
        markers.replace_region(MINIMAL, COMMENT, "proof", "trivial")


def test_a_token_named_only_in_prose_is_not_an_occurrence() -> None:
    """What matters is what the checker reads, so a comment cannot be an offence."""
    text = "# this file never calls assume(False), honestly\nx = 1\n"

    assert markers.occurrences(text, COMMENT, ("assume(False",)) == {}


def test_a_directive_comment_is_matched_against_the_file_as_written() -> None:
    """Masking comments would hide exactly the token that turns the checker off."""
    text = "def impl(x):\n    # crosshair: off\n    return x\n"

    found = markers.occurrences(text, COMMENT, ("# crosshair: off", "NoReturn"))

    assert found == {"# crosshair: off": 2}


def test_a_token_named_only_in_a_docstring_is_not_an_occurrence_where_strings_are_inert() -> (
    None
):
    """Without ``strings``, as for a checker whose contracts are docstrings, it is found."""
    text = (
        '"""A model of the parser.\n\n'
        "There are NO consumed `@ContractOnly` axioms here.\n"
        '"""\n'
        "def f(x: int) -> int:\n"
        '    note = "calls Assume( nowhere"\n'
        "    return x\n"
    )
    tokens = ("ContractOnly", "Assume(")

    assert markers.occurrences(text, COMMENT, tokens, strings=True) == {}
    assert markers.occurrences(text, COMMENT, tokens) == {"ContractOnly": 3, "Assume(": 6}


def test_a_directive_inside_a_string_is_not_one_and_a_directive_comment_still_is() -> None:
    """Masking strings must not hide the comment that turns the checker off."""
    text = 'banner = "# type: ignore"\nvalue = compute()  # type: ignore\n'

    found = markers.occurrences(text, COMMENT, ("# type: ignore",), strings=True)

    assert found == {"# type: ignore": 2}


def test_masking_strings_keeps_every_line_and_column() -> None:
    """A `#` inside a string is part of it, and an f-string is code."""
    text = 'x = "a # b"  # note\n"""one\ntwo"""\ny = f"{Assume(x)}"\n'

    masked = markers.mask_strings(text)

    assert masked.splitlines() == [
        "x = " + " " * len('"a # b"') + "  # note",
        " " * len('"""one'),
        " " * len('two"""'),
        'y = f"{Assume(x)}"',
    ]
    assert len(masked) == len(text)
    assert markers.mask_comments(masked, COMMENT).splitlines()[0].strip() == "x ="


def test_a_string_in_a_region_indented_under_a_def_it_does_not_hold_is_still_masked() -> None:
    """A region is a fragment of a file, and its first line need not be at its margin."""
    text = '        return x\n    def g(self) -> int:\n        """No Assume( here."""\n'

    assert markers.occurrences(text, COMMENT, ("Assume(",), strings=True) == {}


def test_text_the_tokenizer_refuses_has_none_of_its_strings_masked() -> None:
    """Where a string cannot be told from code, a token is read as code and reported."""
    text = 'x = """never closed\nAssume(False)\n'

    assert markers.mask_strings(text) == text
    assert markers.occurrences(text, COMMENT, ("Assume(",), strings=True) == {"Assume(": 2}


def test_occurrences_reports_the_first_line_of_each_token_in_the_order_asked() -> None:
    text = "a = 1\nsys.exit(0)\nassume(False)\nsys.exit(1)\n"

    found = markers.occurrences(text, COMMENT, ("assume(False", "sys.exit", "missing"))

    assert list(found) == ["assume(False", "sys.exit"]
    assert found == {"assume(False": 3, "sys.exit": 2}


def test_masking_a_comment_keeps_every_line_and_column() -> None:
    """Line numbers a check reports have to be the file's own."""
    text = "value = 1  # assume(False)\nother = 2\n"

    masked = markers.mask_comments(text, COMMENT)

    assert masked.splitlines() == ["value = 1" + " " * 17, "other = 2"]
    assert len(masked) == len(text)


def test_a_lean_block_comment_is_masked_however_deeply_it_nests() -> None:
    """A docstring is a comment: a word in one is not a token a check should fire on."""
    text = (
        "/-- admitted while it lasts -/\n"
        "def f (x : Nat) : Nat := x -- while\n"
        "/- a /- nested -/ one -/ def g := \"a -- b\" ++ '-'.toString ++ x'\n"
    )

    masked = markers.mask_comments(text, "--")

    assert len(masked) == len(text)
    assert "while" not in masked and "admitted" not in masked and "nested" not in masked
    assert 'def g := "a -- b"' in masked
    assert "def f (x : Nat) : Nat := x" in masked


@pytest.mark.parametrize(
    ("proof", "tokens", "stated"),
    [
        pytest.param(
            "theorem impl_meets_spec (n : Nat) : Spec n (impl n) := by\n  unfold Spec impl\n",
            ("theorem", "lemma"),
            ["impl_meets_spec (n : Nat) : Spec n (impl n)"],
            id="stops-where-the-proof-begins",
        ),
        pytest.param(
            "theorem long\n    (n : Nat)\n    : Spec n (impl n) := by\n  simp\n",
            ("theorem",),
            ["long (n : Nat) : Spec n (impl n)"],
            id="broken-over-lines-is-one-claim",
        ),
        pytest.param(
            "theorem nothing : True",
            ("theorem",),
            ["nothing : True"],
            id="no-proof-runs-to-end",
        ),
        pytest.param(
            "theorem meets : let s := summary xs; Spec xs s.average := by\n  simp\n",
            ("theorem",),
            ["meets : let s := summary xs; Spec xs s.average"],
            id="a-let-in-the-statement-is-part-of-it",
        ),
        pytest.param(
            "theorem t : f (x := 1) { a := 2 } = g ⟨3⟩ := rfl\nlemma u : P := by trivial\n",
            ("theorem", "lemma"),
            ["t : f (x := 1) { a := 2 } = g ⟨3⟩", "u : P"],
            id="a-named-argument-or-a-field-is-part-of-it",
        ),
        pytest.param(
            'theorem q : name "(" = 1 := by rfl',
            ("theorem",),
            ['q : name "(" = 1'],
            id="a-bracket-in-a-string-is-not-one",
        ),
        pytest.param("-- theorem impl_meets_spec : X", ("theorem",), [], id="in-a-comment"),
        pytest.param("theorem impl_meets_spec : X := by rfl", (), [], id="no-claim-word"),
    ],
)
def test_a_claim_is_what_a_declaration_states_before_its_proof(
    proof: str, tokens: tuple[str, ...], stated: list[str]
) -> None:
    """What the declaration asserts is what a variant of the file has to restate."""
    assert markers.claims(proof, "--", tokens) == stated


def test_wrap_produces_something_parse_reads_back() -> None:
    source = markers.wrap(COMMENT, "spec", "assert True") + "\n"
    source += markers.wrap(COMMENT, "impl", "def impl(x):\n    return x") + "\n"

    regions = markers.parse(source, COMMENT)

    assert regions["spec"].text == "assert True"
    assert regions["impl"].text.startswith("def impl")


#: A file modelling two functions: the regions of the second are numbered.
TWO = """\
# benchproofer:begin spec
def first(x: int) -> int:
    Ensures(Result() == x)
# benchproofer:end spec
# benchproofer:begin impl
    return x
# benchproofer:end impl

# benchproofer:begin spec.2
def second(x: int) -> int:
    Ensures(Result() == x + 1)
# benchproofer:end spec.2
# benchproofer:begin impl.2
    return x + 1
# benchproofer:end impl.2
"""


def test_a_file_that_models_two_functions_numbers_the_second_ones_regions() -> None:
    regions = markers.parse(TWO, COMMENT)

    assert markers.named(regions, "impl") == ("impl", "impl.2")
    assert markers.named(regions, "spec") == ("spec", "spec.2")
    assert markers.joined(regions, "impl") == "    return x\n    return x + 1"
    assert markers.kind("impl.2") == "impl"


def test_the_spec_view_elides_the_body_of_every_function() -> None:
    view = markers.spec_view(TWO, COMMENT)

    assert "return x" not in view
    assert "# benchproofer:elided impl.2" in view
    assert "def second(x: int) -> int:" in view


@pytest.mark.parametrize(
    ("source", "complaint"),
    [
        ("# benchproofer:begin spec\n", "never closed"),
        ("# benchproofer:end spec\n", "without opening"),
        (MINIMAL + "# benchproofer:begin spec\n# benchproofer:end spec\n", "opened twice"),
        ("# benchproofer:begin nonsense\n", "unknown region"),
        ("# benchproofer:begin spec\n# benchproofer:end spec\n", "missing required region"),
        (TWO.replace("impl.2", "impl.1"), "numbered from 2"),
        (TWO.replace("impl.2", "impl.02"), "numbered from 2"),
        (TWO + "# benchproofer:begin helpers.2\n# benchproofer:end helpers.2\n", "only"),
        (
            TWO + "# benchproofer:begin spec.3\nx\n# benchproofer:end spec.3\n",
            "function 3 has no impl.3",
        ),
    ],
)
def test_a_malformed_file_is_refused_rather_than_half_read(source: str, complaint: str) -> None:
    with pytest.raises(MarkerError, match=complaint):
        markers.parse(source, COMMENT)


def test_an_implementation_is_transplanted_function_by_function() -> None:
    donor = TWO.replace("return x + 1", "return x + 2").replace(
        "    return x\n", "    return 0\n"
    )

    moved = markers.transplant(TWO, donor, COMMENT)

    regions = markers.parse(moved, COMMENT)
    assert (regions["impl"].text, regions["impl.2"].text) == (
        "    return 0",
        "    return x + 2",
    )
    assert markers.same_spec(moved, TWO, COMMENT)


def test_a_function_only_the_target_models_keeps_its_own_body_in_a_transplant() -> None:
    one = TWO.split("\n\n", 1)[0].replace("return x", "return 0") + "\n"

    moved = markers.parse(markers.transplant(TWO, one, COMMENT), COMMENT)

    assert (moved["impl"].text, moved["impl.2"].text) == ("    return 0", "    return x + 1")
