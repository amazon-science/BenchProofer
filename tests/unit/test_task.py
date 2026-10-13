# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The normalized task model that every adapter produces."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from benchproofer.core.task import OracleSpec, Reference, SourceFile, Task


def make(**overrides: object) -> Task:
    fields: dict[str, object] = {
        "benchmark": "demo",
        "task_id": "add-two",
        "statement": "Add two numbers.",
    }
    fields.update(overrides)
    return Task(**fields)  # type: ignore[arg-type]


def test_the_key_identifies_a_task_across_benchmarks() -> None:
    assert make().key == "demo/add-two"


@pytest.mark.parametrize(
    ("task_id", "slug"),
    [
        ("astropy__astropy-12907", "astropy__astropy-12907"),
        ("HumanEval/32", "HumanEval_32"),
        ("../escape", ".._escape"),
        ("///", "task"),
    ],
)
def test_the_slug_is_a_filesystem_safe_form_of_the_id(task_id: str, slug: str) -> None:
    """Task ids come from upstream data and are used as directory names."""
    assert make(task_id=task_id).slug == slug


def test_annotating_a_task_does_not_invalidate_the_bundles_built_from_it() -> None:
    plain = make()
    annotated = make(metadata={"noted": "by hand, after the fact"})

    assert annotated.digest() == plain.digest()
    assert make(statement="Add three numbers.").digest() != plain.digest()


def test_a_field_no_adapter_declares_is_refused() -> None:
    """A typo in an adapter must not become a silently ignored field."""
    with pytest.raises(ValidationError):
        make(orcale="pytest")


def test_a_task_is_immutable_once_normalized() -> None:
    with pytest.raises(ValidationError):
        make().statement = "edited"  # type: ignore[misc]


def test_a_task_with_no_reference_solution_is_detectable() -> None:
    assert Reference().is_empty
    assert not Reference(answer="42").is_empty
    assert not Reference(files=(SourceFile(path="a.py", content="pass\n"),)).is_empty


def test_the_default_oracle_decides_nothing() -> None:
    """A benchmark that ships no mechanical check must not appear to have one."""
    assert OracleSpec().kind == "none"
    assert OracleSpec().tests == ()
    assert not OracleSpec().network


def test_the_reference_code_of_a_patch_is_the_added_lines() -> None:
    task = make(
        reference={"patch": "--- a/x.py\n+++ b/x.py\n@@\n-was_wrong()\n+is_right()\n context\n"}
    )

    assert task.reference_code() == "is_right()"


def test_the_reference_code_excludes_what_the_task_already_ships() -> None:
    """A stub belongs in a specification, so it must not count as reference code."""
    task = make(
        context={"files": [{"path": "x.py", "content": "def f(n):\n    ...\n"}]},
        reference={"files": [{"path": "x.py", "content": "def f(n):\n    return n + 1\n"}]},
    )

    assert task.reference_code() == "    return n + 1"
