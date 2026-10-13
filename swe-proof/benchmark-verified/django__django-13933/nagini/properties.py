"""PBT manifest for django__django-13933 — an INSTANCE-SPECIFIC adversarial
falsification battery, authored by reasoning about this spec's defended surface.

THE DEFENDED SURFACE
--------------------
`render_invalid_choice(template, value)` models the rendered text of the
invalid-choice error a single-object ModelChoiceField raises. Both inputs are
READ-ONLY: `Requires(Acc(list_pred(template), 1/2))` and
`Requires(Acc(list_pred(value), 1/2))`. The load-bearing postcondition is

    Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))

where `interpolated` is a @Pure front-recursive fold that substitutes EVERY
`%(value)s` token by `value` and passes every other code point through. The
proof carrier `_render(ts, value, i)` mirrors this fold (read-only value at
1/4; postcondition `ToSeq(Result()) == interpolated(ts.drop(i), ToSeq(value))`).

GROUNDED ORACLE (no ungrounded-oracle echo possible)
----------------------------------------------------
`interpolated` is NOT an opaque answer-key: it is a total @Pure function of the
two actual inputs, fully unfolded. There is no "marker" an impl could echo to
satisfy the postcondition without computing the substitution — the postcondition
*is* the substitution. So the ungrounded-oracle-echo class does not apply; we
instead supply honest positive controls (the cheapest correct impl must verify)
and attack the input-mutation / value-divergence surface where this spec could
actually be hollow.

ATTACK CLASSES EXERCISED
------------------------
- FRAME-MUTATION (MANDATORY; both inputs read-only): a rival that WRITES to the
  half-permission `template` / `value` to satisfy the postcondition must be
  rejected for INSUFFICIENT PERMISSION (kept gold-correct return so the rejection
  is attributable solely to the write).
- PARTIAL-DOMAIN: (a) the prepatch verbatim-copy (correct only on placeholder-free
  templates); (b) a value-truncation rival correct only on the empty value.
- POSITIVE CONTROLS: structurally-different but correct impls (local-variable
  reshape in render_invalid_choice; tail-reshape in _render) that MUST verify.
- ADMISSIBILITY: a witness that the helper's precondition admits a fresh,
  F2P-shaped concrete input.
- CONTROL-FLOW-EFFECT: N/A — the modeled function is a pure value function; the
  invalid-choice raise/render path carries no side-effect or raise distinction
  visible to the List[int] abstraction (the change is purely *which string is
  rendered*). Justified, omitted.

AXIOM LANE: empty. This bundle consumes NO @ContractOnly axiom; the one
deep-model reference (`interpolated` == real str %-mapping) is validated
out-of-band by axiom_check.py / G-AX, not as a probe here.
"""
from pathlib import Path

INSTANCE = "django__django-13933"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _region(src, first, last):
    """The inclusive span from `first` to the first `last` at or after it.

    A guard whose body must go with it cannot be anchored by its header alone:
    deleting the header orphans the block, and rewriting the header to `if False:`
    makes the body unreachable, which Nagini's front end rejects (`dead.code`)
    before Viper sees anything -- and a rival that fails to translate proves
    nothing about the spec (43c6680f6). So the whole statement is the anchor.
    """
    if src.count(first) != 1:
        raise AssertionError(f"not unique: {first!r}")
    i = src.index(first)
    j = src.index(last, i) + len(last)
    return src[i:j]


# The WHOLE substitution branch as one anchor, plus the assert immediately after
# it. The branch has no else -- the statements below it are the verbatim-copy
# fallback -- so deleting the branch is exactly "never substitute" and needs no
# guard to disable. The following `Assert(not starts_with_placeholder(...))` has to
# go with it: it is justified only by having FALLEN THROUGH the guard, and left
# behind it is false on any template that does start with the token, which would
# move the rejection off the postcondition and onto a stale proof hint.
_PLACEHOLDER_BLOCK_END = "    Assert(not starts_with_placeholder(ts.drop(i)))\n"


# ---------------------------------------------------------------------------
# Anchors (all inside impl regions; verified unique against _BASE)
# ---------------------------------------------------------------------------
_RIC_RET = "    return _render(ToSeq(template), value, 0)\n"

_VALUE_LOOP = (
    "        j = len(value)\n"
    "        while j > 0:\n"
)

_TAIL_RESHAPE = (
    "    result = _render(ts, value, i + 1)\n"
    "    result = [head] + result\n"
    "    return result"
)

_PLACEHOLDER_BRANCH = (
    "    if i + 9 <= n and ts.drop(i).take(9) == placeholder():"
)


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = []

# --- POSITIVE CONTROL 1: local-variable reshape in render_invalid_choice ----
# Bind the result to a typed local before returning. Structurally different,
# behaviourally identical; keeps the gold proof obligations untouched.
SPEC_TESTS.append({
    "id": "pos-local-bind",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _RIC_RET,
        "    rendered = _render(ToSeq(template), value, 0)  # type: List[int]\n"
        "    return rendered\n",
    ),
    "rationale": "A correct impl that only reshapes the return into a typed "
                 "local must verify; else SPEC-TOO-STRONG. Keeps every gold "
                 "proof obligation; only the executable shape changes.",
})

# --- POSITIVE CONTROL 2: tail-reshape in _render's non-placeholder branch ----
# Compute the recursive tail into a fresh local, then prepend `head`. Same
# behaviour, same proof; only a local-variable reshape (NOT a loop-direction
# flip, so no fold lemma is needed).
SPEC_TESTS.append({
    "id": "pos-render-tail-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _TAIL_RESHAPE,
        "    tail = _render(ts, value, i + 1)  # type: List[int]\n"
        "    result = [head] + tail\n"
        "    return result",
    ),
    "rationale": "A structurally-different but correct impl (tail computed into "
                 "a local then prepended) must verify; else SPEC-TOO-STRONG. "
                 "All framing asserts on the non-placeholder branch are kept.",
})

# --- ADMISSIBILITY: helper precondition admits a fresh F2P-shaped input -----
# Construct a concrete '%(value)s'/'X' input (a fully-permissioned fresh list),
# call _render on it at i=0 (establishing Acc(value,1/4) and 0<=0<=len(ts)),
# then fall through to the gold return. If the call site fails to establish the
# precondition for this legitimate input => PRECOND-TOO-STRONG.
SPEC_TESTS.append({
    "id": "admiss-helper-fresh-input",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _RIC_RET,
        "    demo_t = [37, 40, 118, 97, 108, 117, 101, 41, 115]  # type: List[int]\n"
        "    demo_v = [88]  # type: List[int]\n"
        "    _demo = _render(ToSeq(demo_t), demo_v, 0)  # type: List[int]\n"
        "    return _render(ToSeq(template), value, 0)\n",
    ),
    "rationale": "The helper's precondition (Acc(value,1/4), 0<=i<=len(ts)) must "
                 "be establishable for a fresh F2P-shaped '%(value)s'/'X' input; "
                 "else PRECOND-TOO-STRONG.",
})

# --- FRAME-MUTATION 1: write to read-only `template` (Acc 1/2) ---------------
# Append to `template` before the gold return. The spec grants only half
# permission on `template`, so list_pred mutation is unavailable -> must be
# rejected for INSUFFICIENT PERMISSION. The gold return is unchanged, so the
# rejection is attributable purely to the illegal write, not to a value defect.
SPEC_TESTS.append({
    "id": "frame-mut-template",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _RIC_RET,
        "    template.append(0)\n"
        "    return _render(ToSeq(template), value, 0)\n",
    ),
    "refinement": "A faithful real patch that mutates the message template "
                  "before rendering (e.g. appends a code point) would change the "
                  "rendered text away from the configured template, so the F2P "
                  "expected message '\"invalid\" is not one of the available "
                  "choices.' would not be produced => would NOT resolve.",
    "rationale": "Rejection comes from the PERMISSION system: `template` is held "
                 "at Acc(list_pred,1/2), so `template.append(...)` cannot be "
                 "framed. A byte-fuzzer never mutates a read-only input.",
})

# --- FRAME-MUTATION 2: write to read-only `value` (Acc 1/2) ------------------
SPEC_TESTS.append({
    "id": "frame-mut-value",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _RIC_RET,
        "    value.append(0)\n"
        "    return _render(ToSeq(template), value, 0)\n",
    ),
    "refinement": "A faithful real patch that mutates the rejected `value` "
                  "before interpolation would interpolate a corrupted value, so "
                  "the F2P expected '\"invalid\" is not one of the available "
                  "choices.' would not be produced => would NOT resolve.",
    "rationale": "Rejection comes from the PERMISSION system: `value` is held at "
                 "Acc(list_pred,1/2), so `value.append(...)` cannot be framed.",
})

# --- PARTIAL-DOMAIN 1: prepatch verbatim copy (the actual bug) --------------
# Make _render NEVER recognise the placeholder by forcing the placeholder branch
# unreachable: replace its guard with a constant-false test, so every position
# takes the passthrough branch -> the template is emitted verbatim, %(value)s
# survives. Correct ONLY on placeholder-free templates; wrong (and == prepatch)
# whenever the template contains %(value)s. Must be rejected by the postcondition
# ToSeq(Result()) == interpolated(...).
SPEC_TESTS.append({
    "id": "partial-domain-verbatim",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _region(_BASE, _PLACEHOLDER_BRANCH, _PLACEHOLDER_BLOCK_END),
        "    # PRE-PATCH: there is no substitution branch at all, so every\n"
        "    # template character (the %(value)s token included) falls through to\n"
        "    # the verbatim copy below.\n",
    ),
    "refinement": "This is exactly the PREPATCH behaviour: no %(value)s "
                  "substitution, the template (placeholder intact) is rendered "
                  "verbatim. The F2P template '\"%(value)s\" is not one of the "
                  "available choices.' would render with the literal %(value)s "
                  "surviving, not '\"invalid\"' => would NOT resolve (this is the "
                  "G-DIFF / model_prepatch failure mode).",
    "rationale": "Rejection comes from the load-bearing postcondition "
                 "ToSeq(Result()) == interpolated(...): a verbatim copy differs "
                 "from the interpolation on every template containing the token.",
})

# --- PARTIAL-DOMAIN 2: value-truncation (drop first code point of value) ----
# In the value-prepend loop, stop at `j > 1` instead of `j > 0`: the first code
# point of `value` is never prepended. Correct ONLY when value is empty
# (loop never runs); on every nonempty value the substituted text loses its
# first character. Must be rejected by the value-exact postcondition.
SPEC_TESTS.append({
    "id": "partial-domain-value-trunc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _VALUE_LOOP,
        "        j = len(value)\n"
        "        while j > 1:\n",
    ),
    "refinement": "A faithful real patch interpolating str(value)[1:] (dropping "
                  "the first character of the rejected value) renders the F2P "
                  "value 'invalid' as 'nvalid', so '\"nvalid\" is not one of the "
                  "available choices.' != the expected '\"invalid\" ...' => would "
                  "NOT resolve. Correct only on the empty-value sub-domain.",
    "rationale": "Rejection comes from the value-exact postcondition: the "
                 "interpolation must reproduce the WHOLE value; dropping value[0] "
                 "breaks ToSeq(Result()) == interpolated(...) for any nonempty "
                 "value (the loop invariant ToSeq(result) == value.drop(j)+... "
                 "leaves value.drop(1) when j stops at 1).",
})


# ===========================================================================
# AXIOM LANE — empty: no @ContractOnly axiom; the lone A-reference
# (`interpolated` == real str %-mapping) is validated by axiom_check.py / G-AX.
# ===========================================================================
AXIOM_TESTS = []
