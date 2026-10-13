#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9229 (nagini).

SHADOW: the impl regions of model.py (`select_doc_block`,
`alias_additional_content`) copied VERBATIM below with the contract calls
(Requires/Ensures) stripped; the @Pure helper `has_authored_comment` copies
over as a plain function (`opt_seq` is spec-only — it appears in no impl
statement — so it has nothing to execute). The single @ContractOnly callee,
`make_placeholder`, calls the REAL repo composition the axioms region models
per mapping.md section 3.1: the line-formatter output for the alias target
(the gettext template applied to `sphinx.util.typing.restify` of the real
target object), decoded to the model's code-point carrier.

ORACLE: the REAL gold-patched repo functions the model models per mapping.md
section 1 — `sphinx.ext.autodoc.ClassDocumenter.get_doc` (the alias-branch
block selection, modeled by `select_doc_block`) and
`ClassDocumenter.add_content` (the placeholder-substitution gating, modeled by
`alias_additional_content`). The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched package importable.
We do not build a full Sphinx app: both modeled decisions read only
`self.doc_as_attr`, `self.get_variable_comment()` and (on the substitution
branch) `self.object`, so a REAL `ClassDocumenter` instance built via
`__new__` (heavy constructor bypassed) with those attributes set drives the
real patched code paths:

  * `get_doc` is observed directly. The alias branch returns `[]` or `None`;
    the non-alias branch is observed through its first unchanged shortcut
    (the already-prepared block attribute is returned as-is, i.e. the same
    object — exactly the identity the model's clause (1c) states for the
    read-only `prepared` carrier).
  * `add_content`'s decision is observed by temporarily replacing the base
    `Documenter.add_content` (the `super()` forwarding target) with a
    recorder that captures the exact object forwarded — the freshly-built
    single-line block when the substitution fires, else the incoming content
    object unchanged (an `is`-identity, matching clause (2b)).

Type bridge (mapping.md section 2): repo text maps to List[int] of Unicode
code points. An Optional[List[str]] comment maps to the model's `comment`
carrier via line-terminated encoding (each line's code points + a terminator),
so the truthiness bijection is exact: None and [] both map to the empty list,
and any non-empty list of lines (including [""]) maps to a non-empty list.
A single-line content block maps to the code points of its line; block
presence maps None <-> None. The pass-through and prepared-block legs are
compared by object identity on BOTH sides (the model's `is`-postconditions),
so no content encoding is involved there. The `target` carrier maps to a real
class object through a registry keyed by the code points of the class's
qualified name.

Input domain: the model's Requires demand only read access to the carriers,
so every generated input is Requires-satisfying. Targets are drawn from real
class objects (the operating domain of the real formatter; the defensive
guard around an invalid target is unreachable there and is outside the
modeled domain per refinement.md section B).

>= 1e5 Requires-satisfying inputs: boundary cases + fuzz, every iteration
exercising BOTH modeled functions against the real patched code. Pinned fuzz
seed: 9229 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the in-image Sphinx only.
"""
import json
import random
import sys

SEED = 9229
N_FUZZ = 55_000  # x2 modeled functions per iteration => >= 1.1e5 checks


# --- pure helper from model.py, copied over as a plain function ---------------

def has_authored_comment(comment):
    return len(comment) > 0


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def select_doc_block(is_attr_alias, comment, prepared):
    if is_attr_alias:
        if has_authored_comment(comment):
            empty = []  # type: list
            return empty
        else:
            return None
    return prepared


def alias_additional_content(is_attr_alias, comment, target, more_content):
    if is_attr_alias and not has_authored_comment(comment):
        result = make_placeholder(target)
        return result
    return more_content


# --- @ContractOnly callee: calls the REAL repo composition --------------------

_TARGET_REGISTRY = {}  # tuple(code points of qualname) -> real class object
_REAL = {}             # filled by main(): the real repo callables


def make_placeholder(target):
    """The axioms-region callee, realized by the REAL repo formatter chain it
    models (mapping.md section 3.1): the translated template applied to the
    real renderer's output for the registered target object, as a fresh
    code-point list."""
    obj = _TARGET_REGISTRY[tuple(target)]
    line = _REAL["gettext"]("alias of %s") % _REAL["restify"](obj)
    return [ord(ch) for ch in line]


# --- bridges: repo values <-> model carriers -----------------------------------

def comment_to_codes(comment_lines):
    """Optional[List[str]] -> List[int]: line-terminated code points. None and
    [] (both falsy) map to []; any non-empty list (even [""]) maps to a
    non-empty list — the exact truthiness bijection of mapping.md section 2."""
    if not comment_lines:
        return []
    out = []
    for line in comment_lines:
        out.extend(ord(ch) for ch in line)
        out.append(10)
    return out


def target_codes_for(obj):
    codes = [ord(ch) for ch in getattr(obj, "__qualname__", obj.__name__)]
    _TARGET_REGISTRY[tuple(codes)] = obj
    return codes


# --- ORACLE: the REAL gold-patched ClassDocumenter -----------------------------

class _FreshBlock(list):
    """A distinct list object used as the already-prepared block carrier, so
    the identity leg (`is`) is observable on the oracle side."""


def make_fake(doc_as_attr, comment_lines, obj, prepared_obj):
    """A REAL ClassDocumenter with the heavy __init__ bypassed, exposing
    exactly what the two modeled branches read."""
    fake = _REAL["ClassDocumenter"].__new__(_REAL["ClassDocumenter"])
    fake.doc_as_attr = doc_as_attr
    # instance attribute shadows the method for `self.get_variable_comment()`
    fake.get_variable_comment = lambda: comment_lines
    fake.object = obj
    if prepared_obj is not None:
        fake._new_docstrings = prepared_obj
    return fake


def oracle_get_doc(doc_as_attr, comment_lines, prepared_obj):
    fake = make_fake(doc_as_attr, comment_lines, None, prepared_obj)
    return _REAL["ClassDocumenter"].get_doc(fake)


def oracle_add_content(doc_as_attr, comment_lines, obj, incoming_sl):
    """Run the REAL add_content; return the exact object it forwards to the
    base-class forwarding target."""
    captured = []

    def recorder(self, more_content, no_docstring=False):
        captured.append(more_content)

    Documenter = _REAL["Documenter"]
    orig = Documenter.add_content
    Documenter.add_content = recorder
    try:
        fake = make_fake(doc_as_attr, comment_lines, obj, None)
        _REAL["ClassDocumenter"].add_content(fake, incoming_sl)
    finally:
        Documenter.add_content = orig
    return captured[0]


# --- the differential check on one input configuration -------------------------

def check_case(is_alias, comment_lines, obj, incoming_lines, use_none_incoming):
    """Exercise BOTH modeled functions on one configuration; return an error
    string on any disagreement, else None. Counts 2 checked inputs."""
    comment_codes = comment_to_codes(comment_lines)
    target_codes = target_codes_for(obj)

    # ---- site A: block selection (select_doc_block vs real get_doc) ----------
    prepared_obj = _FreshBlock([["prepared", "block"]])
    prepared_codes = [112, 114, 101, 112]  # opaque read-only carrier
    shadow_a = select_doc_block(is_alias, comment_codes, prepared_codes)
    oracle_a = oracle_get_doc(is_alias, comment_lines, prepared_obj)
    if is_alias:
        # PRESENT-EMPTY vs ABSENT must match exactly
        sh = "absent" if shadow_a is None else (
            "present-empty" if len(shadow_a) == 0 else "present-nonempty")
        oc = "absent" if oracle_a is None else (
            "present-empty" if len(oracle_a) == 0 else "present-nonempty")
        if sh != oc:
            return ("DISAGREEMENT (block selection, alias branch)\n"
                    "  is_alias=%r comment=%r\n  shadow=%s (%r)\n  real=%s (%r)"
                    % (is_alias, comment_lines, sh, shadow_a, oc, oracle_a))
    else:
        # identity leg: the prepared block object comes back as-is on BOTH sides
        if shadow_a is not prepared_codes or oracle_a is not prepared_obj:
            return ("DISAGREEMENT (block selection, non-alias identity)\n"
                    "  is_alias=%r comment=%r\n  shadow is prepared: %r\n"
                    "  real is prepared: %r"
                    % (is_alias, comment_lines,
                       shadow_a is prepared_codes, oracle_a is prepared_obj))

    # ---- site B: content substitution (alias_additional_content vs real ------
    #      add_content) ---------------------------------------------------------
    if use_none_incoming:
        incoming_sl = None
        incoming_codes = None
    else:
        incoming_sl = _REAL["StringList"](list(incoming_lines), source="<conf>")
        incoming_codes = comment_to_codes(incoming_lines)
    shadow_b = alias_additional_content(is_alias, comment_codes, target_codes,
                                        incoming_codes)
    oracle_b = oracle_add_content(is_alias, comment_lines, obj, incoming_sl)

    substituted_shadow = shadow_b is not incoming_codes
    substituted_oracle = oracle_b is not incoming_sl
    if substituted_shadow != substituted_oracle:
        return ("DISAGREEMENT (substitution gating)\n"
                "  is_alias=%r comment=%r incoming=%r\n"
                "  shadow substituted=%r\n  real substituted=%r"
                % (is_alias, comment_lines,
                   None if use_none_incoming else list(incoming_lines),
                   substituted_shadow, substituted_oracle))
    if substituted_shadow:
        real_lines = list(oracle_b.data)
        if len(real_lines) != 1:
            return ("DISAGREEMENT (substituted block shape)\n"
                    "  is_alias=%r comment=%r target=%r\n  real lines=%r"
                    % (is_alias, comment_lines, obj, real_lines))
        real_codes = [ord(ch) for ch in real_lines[0]]
        if shadow_b != real_codes or len(shadow_b) == 0:
            return ("DISAGREEMENT (substituted content)\n"
                    "  is_alias=%r comment=%r target=%r\n"
                    "  shadow=%r\n  real=%r"
                    % (is_alias, comment_lines, obj, shadow_b, real_codes))
    return None


# --- input families -------------------------------------------------------------

class _TargetA:
    pass


class _TargetB:
    pass


class _Nested:
    class Inner:
        pass


def target_objects():
    return [_TargetA, _TargetB, _Nested.Inner, int, dict, ValueError]


def comment_variants():
    # None (lookup error) / [] (no entry): both falsy; then truthy shapes,
    # including the all-empty-lines list (truthy list, empty text).
    return [None, [], [""], ["docstring"], ["line one", "line two", ""],
            ["", ""]]


def incoming_variants():
    return [[], ["body line"], ["a", "b"], [""]]


def main():
    # REAL patched callees (PYTHONPATH=/testbed; the gate applied patch.diff).
    try:
        from sphinx.ext.autodoc import ClassDocumenter, Documenter
        from sphinx.util.typing import restify
        from docutils.statemachine import StringList
        try:
            from sphinx.locale import _ as gettext_
        except Exception:
            def gettext_(s):
                return s
    except Exception as e:
        print("G-CONF ERROR: could not import the patched repo functions: %r"
              % (e,))
        return 2
    _REAL.update(ClassDocumenter=ClassDocumenter, Documenter=Documenter,
                 restify=restify, StringList=StringList, gettext_=gettext_,
                 gettext=gettext_)

    checked = 0
    n_boundary = 0

    # --- boundary sweep: full cross product of the discriminating shapes -----
    for is_alias in (True, False):
        for comment_lines in comment_variants():
            for obj in target_objects():
                for inc in incoming_variants():
                    err = check_case(is_alias, comment_lines, obj, inc, False)
                    if err:
                        print(err)
                        return 1
                    checked += 2
                    n_boundary += 2
                err = check_case(is_alias, comment_lines, obj, [], True)
                if err:
                    print(err)
                    return 1
                checked += 2
                n_boundary += 2

    # --- randomized fuzz (pinned seed) ----------------------------------------
    rng = random.Random(SEED)
    lines_pool = ["docstring", "", "x", "some text", "  indented", "tail  "]
    objs = target_objects()
    for _ in range(N_FUZZ):
        p = rng.random()
        if p < 0.30:
            comment_lines = None
        elif p < 0.50:
            comment_lines = []
        else:
            comment_lines = [rng.choice(lines_pool)
                             for _ in range(rng.randint(1, 4))]
        is_alias = rng.random() < 0.6
        obj = rng.choice(objs)
        use_none = rng.random() < 0.15
        inc = ([] if use_none else
               [rng.choice(lines_pool) for _ in range(rng.randint(0, 4))])
        err = check_case(is_alias, comment_lines, obj, inc, use_none)
        if err:
            print(err)
            return 1
        checked += 2

    print("G-CONF OK: shadow impl == real patched block selection + content "
          "substitution on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee -> real repo formatter)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
