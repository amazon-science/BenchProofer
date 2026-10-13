#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12663.

The bundle models ONE function: the `Query.output_field` property
(`django/db/models/sql/query.py:233-238`). Its Lean implementation
(`implementation_outputType`) reports the type descriptor of a query's output:

    if len(selections) == 1:
        select = selections[0]
        return base_or_declared(select)       # target if present, else field
    elif len(annotations) == 1:
        return annotations[0].output_field
    else:
        return None

This script transliterates that R/I impl into Python (`shadow_output`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `Query.output_field`:

    if len(self.select) == 1:
        select = self.select[0]
        return getattr(select, 'target', None) or select.field    # <-- the fix
    elif len(self.annotation_select) == 1:
        return next(iter(self.annotation_select.values())).output_field
    # implicit None

We do NOT stand up Django/ORM (heavy, and the modeled value is a pure decision
over which of a selection's two candidate field descriptors is reported).
Instead we reproduce the patched choice with light stand-ins: each `select` is a
small object exposing `.target` (possibly absent / None) and `.field`; each
annotation exposes `.output_field`. Field descriptors are represented by
integers (their identity); the oracle applies the GENUINE Python expression
`getattr(select, 'target', None) or select.field`, while the shadow applies the
Lean `base.getD declared`. Field ids are drawn >= 1 (always truthy, like real
model-field objects) so the `or` semantics coincide with `Option.getD` — see the
truthiness note in mapping.md.

The differential genuinely tests the Lean modeling: the discriminating case is a
single selection whose underlying referenced attribute (`target`) is present and
DIFFERENT from its declared output type (`field`) — the divergence the patch
turns on (pre-fix the declared type was returned, breaking the downstream
related-field value coercion).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 12663 (also recorded in
mapping.md).
"""
import sys

SEED = 12663
N = 120_000

_MISSING = object()


class Sel:
    """A selected expression with an optional `.target` and a `.field`.

    `target` may be: a field id (present + truthy), None (present but falsy),
    or _MISSING (attribute absent -> getattr returns the default None)."""
    __slots__ = ("target", "field")

    def __init__(self, target, field):
        if target is not _MISSING:
            self.target = target
        self.field = field


class Ann:
    __slots__ = ("output_field",)

    def __init__(self, output_field):
        self.output_field = output_field


# --- ORACLE: the post-patch output_field, faithful in-process replica --------
def oracle_output(selections, annotations):
    if len(selections) == 1:
        select = selections[0]
        return getattr(select, "target", None) or select.field
    elif len(annotations) == 1:
        return annotations[0].output_field
    return None


# --- shadow of implementation_outputType (the R/I leg) -----------------------
# Mirrors Solution.lean: base_or_declared = base if not None else declared;
# the impl carries `base` as Option (None <-> absent OR Python-None target).
def base_or_declared(base, declared):
    return base if base is not None else declared


def shadow_output(selections, annotations):
    if len(selections) == 1:
        base, declared = selections[0]
        return base_or_declared(base, declared)
    elif len(annotations) == 1:
        return annotations[0]
    return None


# The Lean `Selection.base : Option FieldId` collapses Python's "attribute
# absent" and "attribute is a falsy value" into a single `none`. For real
# model-field objects `target` is either absent or a truthy object, so the only
# faithful falsy case is absence. We feed the shadow the Option directly and let
# the oracle exercise the genuine getattr/or.
def to_shadow_sel(sel: "Sel"):
    base = getattr(sel, "target", None)
    if not base:           # mirrors Python `or` falling through on falsy/absent
        base = None
    return (base, sel.field)


def disagree(selections, annotations):
    got = oracle_output(selections, annotations)
    shadow_sels = [to_shadow_sel(s) for s in selections]
    shadow_anns = [a.output_field for a in annotations]
    want = shadow_output(shadow_sels, shadow_anns)
    if got != want:
        return ((selections, annotations), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning the discriminating choice clause."""
    cases = [
        # THE fix: single selection, target present and DIFFERENT from field.
        ([Sel(7, 3)], []),
        # target present and EQUAL to field (ordinary column -> unchanged).
        ([Sel(5, 5)], []),
        # target attribute absent -> fall back to field.
        ([Sel(_MISSING, 9)], []),
        # target attribute present but None -> fall back to field.
        ([Sel(None, 9)], []),
        # zero selections, single annotation -> annotation branch.
        ([], [Ann(11)]),
        # zero selections, zero annotations -> None.
        ([], []),
        # two selections -> not the single-column branch; single annotation used.
        ([Sel(7, 3), Sel(8, 4)], [Ann(11)]),
        # two selections, two annotations -> None.
        ([Sel(7, 3), Sel(8, 4)], [Ann(11), Ann(12)]),
        # single selection AND single annotation -> selection branch wins.
        ([Sel(7, 3)], [Ann(11)]),
        # single annotation among many selections absent -> None when both !=1.
        ([Sel(7, 3), Sel(8, 4)], []),
    ]
    return cases


def _rand_sel(rnd):
    kind = next(rnd) % 4
    field = 1 + (next(rnd) % 6)        # >= 1 (always truthy)
    if kind == 0:
        target = _MISSING              # attribute absent
    elif kind == 1:
        target = None                  # present but falsy
    else:
        target = 1 + (next(rnd) % 6)   # present + truthy; may == field
    return Sel(target, field)


def _rand_list(rnd, maker):
    length = next(rnd) % 4             # 0..3 elements
    return [maker(rnd) for _ in range(length)]


def main() -> int:
    checked = 0

    for selections, annotations in _enumerate_edge():
        d = disagree(selections, annotations)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        selections = _rand_list(rnd, _rand_sel)
        annotations = _rand_list(rnd, lambda r: Ann(1 + (next(r) % 6)))
        d = disagree(selections, annotations)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
