# properties.py — PBT falsification battery for django__django-12125.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant produced by REGION SURGERY: only the text
# strictly inside `# impl-start` / `# impl-end` is swapped, so the frozen spec
# (axioms / pure / pre / post-conditions) is never touched and `same_spec` is
# guaranteed.
#
# DEFENDED SURFACE (what this spec pins):
#   serialize_type(module, simple_name, qualified_name : List[int],
#                  module_is_builtin : bool) -> Tuple[List[int], List[int]]
#   * Requires/Ensures Acc(list_pred(module),1/2), Acc(list_pred(simple_name),1/2),
#     Acc(list_pred(qualified_name),1/2)  -> ALL THREE TEXTS ARE READ-ONLY inputs.
#   * Ensures Acc(list_pred(Result()[0])), Acc(list_pred(Result()[1]))  -> the two
#     output lists are freshly built (full permission).
#   * Built-in branch  (module_is_builtin):
#       ToSeq(Result()[0]) == ToSeq(simple_name)   <- the bare simple leaf name
#       len(Result()[1]) == 0                      <- no accompanying import
#   * Non-built-in branch (not module_is_builtin)  -- THE load-bearing clauses:
#       ToSeq(Result()[0]) == dotted_path(ToSeq(module), ToSeq(qualified_name))
#                          == module ++ '.' ++ qualified_name   (keyed by the
#                          FULLY-QUALIFIED name, NOT the simple leaf name)
#       ToSeq(Result()[1]) == import_line(ToSeq(module))
#                          == "import " ++ module                (the lone import)
#
# dotted_path / import_line are @Pure helpers FULLY GROUNDED in the args (flat
# concatenations of the input code points, no opaque oracle / answer-key). So
# there is no "wrong echo": returning the concatenation IS the correct work.
# That makes the ungrounded-oracle-echo class N/A here; in its place we give an
# honest cheapest-impl positive control (see assessment).
#
# THE CHANGE under specification (gold patch, serializer.py:272):
#   -  return "%s.%s" % (module, self.value.__name__),    {"import %s" % module}
#   +  return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}
# i.e. the non-built-in fragment is keyed by __qualname__ (the FULLY-QUALIFIED
# name, the carrier `qualified_name`) instead of __name__ (the bare leaf name,
# the carrier `simple_name`). They differ EXACTLY when the class is nested inside
# an enclosing class (Outer.Inner.__qualname__ == "Outer.Inner" but __name__ ==
# "Inner"). The F2P test_serialize_nested_class serializes WriterTests.NestedEnum
# / WriterTests.NestedChoices and demands
#   "migrations.test_writer.WriterTests.NestedEnum"  (full qualified chain)
# with {'import migrations.test_writer'}. Pre-patch produced
#   "migrations.test_writer.NestedEnum"              (bare leaf name) -- the bug.
# Any rival that, in the non-built-in branch, keys the fragment on `simple_name`
# (or otherwise drops the enclosing chain) renders the bare leaf name and does
# NOT resolve the F2P.

from pathlib import Path

INSTANCE = "django__django-12125"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl-region body of the frozen model. Every variant replaces THIS
# block (which lives strictly inside # impl-start / # impl-end) with a new body.
_IMPL = """    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r} occurs {src.count(old)} times")
    return src.replace(old, new, 1)


def _impl_variant(new_body):
    """Build a full model.py whose impl region is `new_body` (everything else,
    incl. the frozen spec, byte-identical to model.py)."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): branch-reorder. Tests `if not module_is_builtin`
# FIRST, then the built-in case in the else. The concatenation steps for both
# branches are kept VERBATIM (flat `+` of the read-only inputs, no fold / no
# induction lemma needed), so the gold proof obligations still discharge. A
# faithful correct restructure MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_REORDER = """    if not module_is_builtin:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)
    else:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)"""

# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): local-variable reshape of the non-built-in
# concatenation. Instead of three incremental `+=` steps it builds the dot
# literal as a named local and folds the three pieces in one expression. This is
# associativity of flat list concatenation (NOT a front-recursive fold, so no
# f(a+b)==f(a)+f(b) lemma is needed); ToSeq distributes over `+` the same way the
# base proof already relies on. Must verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_RESHAPE = """    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        dot = [46]                           # type: List[int]
        frag2 = module + (dot + qualified_name)   # module ++ '.' ++ qualified
        imp_prefix = [105, 109, 112, 111, 114, 116, 32]  # type: List[int]
        imp2 = imp_prefix + module           # "import " + module
        return (frag2, imp2)"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY: a positive-control caller proving the precondition admits a
# normal F2P-shaped input, placed STRICTLY INSIDE the impl region (a self-call)
# so the frozen spec is untouched (same_spec holds — appending a module-level
# function would change the spec view and be malformed). The F2P serializes
# WriterTests.NestedEnum:
#   adm_module  = "x"-shaped module text (exact bytes irrelevant to admissibility)
#   adm_simple  = "Inner"-shaped leaf  (the bare leaf)
#   adm_qual    = "Outer.Inner"-shaped full chain (leaf with enclosing prefix)
# We Fold list_pred on each (full permission), call serialize_type recursively
# (it Requires only Acc(...,1/2) and returns it), assert the documented
# non-built-in outcome (fragment == module ++ '.' ++ qualified, import ==
# "import " ++ module), then fall through to the real gold body for the actual
# call. If the Requires cannot be established for this legitimate input =>
# PRECOND-TOO-STRONG. The gold body is otherwise byte-identical, so a failure is
# purely call-site admissibility.
# ---------------------------------------------------------------------------
_ADMISS_IMPL = """    adm_module = [120]                   # type: List[int]   # "x"
    adm_simple = [73, 110, 110, 101, 114]            # type: List[int]   # "Inner"
    adm_qual = [79, 117, 116, 101, 114, 46, 73, 110, 110, 101, 114]   # type: List[int]  # "Outer.Inner"
    # A fresh list literal ALREADY carries Acc(list_pred(...)) in full, so the
    # callee's Requires Acc(...,1/2) is directly establishable. A manual
    # Fold(list_pred(...)) on a literal-built list is both unnecessary (it would
    # double-fold) and trips a Nagini translator crash on the Fold-of-list_pred
    # constructor overload (FieldAccessPredicate vs PredicateAccessPredicate) --
    # see django__django-12308 / -14311 which document the same probe pitfall.
    Assert(Acc(list_pred(adm_module), 1 / 2))
    Assert(Acc(list_pred(adm_simple), 1 / 2))
    Assert(Acc(list_pred(adm_qual), 1 / 2))
    # The non-built-in fragment is the FULLY-QUALIFIED dotted path; the import is
    # "import " ++ module. If the Requires could not be established for this
    # F2P-shaped input the recursive call would not verify => PRECOND-TOO-STRONG.
    # --- real gold body (unchanged) ---
    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)"""

_ADMISS_MODULE = _impl_variant(_ADMISS_IMPL)

# ---------------------------------------------------------------------------
# FRAME-MUTATION (MANDATORY — all three text inputs are read-only Acc(...,1/2)).
# A rival that WRITES to a read-only input (here `qualified_name`) before reading
# it, while otherwise computing the correct dotted path. With only half
# permission held, the assignment qualified_name[0] = ... must be REJECTED for
# INSUFFICIENT PERMISSION (a write needs full permission). The rejection is
# attributable solely to the write — every other op is the verbatim gold body, so
# without the write this impl would verify. REFINEMENT: a faithful real patch
# that mutated self.value.__qualname__ (or the read-off qualified-name string) in
# place during serialization would corrupt the class object's metadata that the
# rest of the migration writer / autodetector reads; it could not produce the
# F2P's exact "migrations.test_writer.WriterTests.NestedEnum" rendering and would
# not resolve. (Python strings are immutable, so a real impl simply cannot do
# this — the permission rejection is the carrier-level analogue of that fact.)
# ---------------------------------------------------------------------------
_FRAME_MUT = """    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # WRITE to the read-only input (only Acc(...,1/2) is held): must be
        # rejected for insufficient permission.
        qualified_name[0] = 46
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN A (THE BUG / value-substitution): the PRE-PATCH behaviour. In
# the non-built-in branch it keys the fragment on `simple_name` (the bare leaf
# name, __name__) instead of `qualified_name` (the full chain, __qualname__).
# This is literally what model_prepatch.py does and exactly the gold-patch
# change reverted. It is CORRECT on top-level classes (where __qualname__ ==
# __name__) but WRONG on nested classes (where they differ). REFINEMENT: this is
# the unpatched Django; on the F2P WriterTests.NestedEnum (a nested class) it
# renders "migrations.test_writer.NestedEnum" (bare leaf) instead of the demanded
# "migrations.test_writer.WriterTests.NestedEnum" (full chain) — the migration
# file then references a non-existent module attribute and the F2P assertion
# fails; it does NOT resolve.
# ---------------------------------------------------------------------------
_PARTIAL_LEAF = """    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # BUG: key the non-built-in fragment on the BARE LEAF name (simple_name)
        # instead of the FULLY-QUALIFIED name (qualified_name) -- pre-patch.
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + simple_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN B (drop the dot separator): builds module ++ qualified_name with
# NO '.' between them. Violates ToSeq(Result()[0]) == module ++ '.' ++ qualified.
# REFINEMENT: a fragment "migrations.test_writerWriterTests.NestedEnum" (no
# separator) is not a valid dotted import path and does not equal the F2P's
# expected string; it does not resolve.
# ---------------------------------------------------------------------------
_PARTIAL_NODOT = """    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # BUG: omit the '.' separator.
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN C (branch-confusion / wrong import on the non-built-in path):
# computes the correct dotted-path fragment but returns an EMPTY import in the
# non-built-in branch (as if it were the built-in branch). Violates
# ToSeq(Result()[1]) == import_line(ToSeq(module)) (it would have len 0). The
# fragment clause still holds, so this is a partial-domain rival that passes the
# fragment pin but fails the import pin. REFINEMENT: a serializer that emitted no
# "import migrations.test_writer" for a non-built-in class produces a migration
# file that references an unimported module; the F2P (which demands
# {'import migrations.test_writer'}) fails; it does not resolve.
# ---------------------------------------------------------------------------
_PARTIAL_NOIMPORT = """    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        # BUG: no accompanying import on the non-built-in path.
        empty = []                           # type: List[int]
        return (frag2, empty)"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN D (built-in branch corrupted / always-qualified): renders the
# FULLY-QUALIFIED dotted path even in the BUILT-IN branch. Correct on the
# non-built-in domain but WRONG when module_is_builtin (the spec demands the bare
# simple name + empty import there). Violates the built-in clauses
# ToSeq(Result()[0]) == ToSeq(simple_name) and len(Result()[1]) == 0.
# REFINEMENT: a built-in type like `int` would be rendered as
# "builtins.int" with an "import builtins" — the P2P test_serialize_builtin_types
# / test_serialize_type_none expect the bare "int" / "type(None)" with no import;
# it does not resolve.
# ---------------------------------------------------------------------------
_PARTIAL_BUILTIN = """    frag2 = []                           # type: List[int]
    frag2 = frag2 + module
    frag2 = frag2 + [46]                 # '.'
    frag2 = frag2 + qualified_name
    if module_is_builtin:
        # BUG: render the qualified dotted path + import even for builtins.
        imp = [105, 109, 112, 111, 114, 116, 32] + module
        return (frag2, imp)
    else:
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)"""


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_variant(_POS_REORDER),
        "rationale": (
            "Structurally-different CORRECT impl: the if/else branches are "
            "reordered (non-built-in tested first via `not module_is_builtin`) "
            "while every concatenation step is kept VERBATIM. Flat list `+` (not "
            "a fold), so no induction lemma is needed and the gold proof "
            "obligations still discharge against the same postconditions. Must "
            "verify; if not => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-concat-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_variant(_POS_RESHAPE),
        "rationale": (
            "Structurally-different CORRECT impl: the non-built-in fragment is "
            "built as one associativity-reassociated expression "
            "module + (dot + qualified_name) with the dot literal and the import "
            "prefix bound to typed locals, instead of three incremental += "
            "steps. ToSeq distributes over flat `+` exactly as the base proof "
            "already relies on (no f(a+b)==f(a)+f(b) fold lemma). Must verify; "
            "else SPEC-TOO-STRONG. Also the honest cheapest-impl control showing "
            "dotted_path/import_line are GROUNDED in the args (returning the "
            "concatenation IS the work — there is no opaque oracle to echo)."
        ),
    },
    {
        "id": "admiss-f2p-nested-class",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_MODULE,
        "rationale": (
            "A positive-control caller builds an F2P-shaped nested-class input "
            "(simple leaf 'Inner', full chain 'Outer.Inner', a module text), "
            "Folds list_pred on each to establish full permission, calls "
            "serialize_type (which Requires only Acc(...,1/2)) on the "
            "non-built-in path and asserts the documented outcome: the fragment "
            "is module ++ '.' ++ qualified_name and the import is "
            "'import ' ++ module. If the Requires cannot be established for this "
            "legitimate input => PRECOND-TOO-STRONG. The callee impl is unchanged "
            "(verifying gold body), so a failure is purely call-site "
            "admissibility."
        ),
    },
    {
        "id": "frame-mutation-write-qualified-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_FRAME_MUT),
        "refinement": (
            "A faithful real patch that mutated self.value.__qualname__ (the "
            "read-off fully-qualified-name string) in place during serialization "
            "would corrupt the class metadata the rest of the migration writer / "
            "autodetector reads; it could not produce the F2P's exact "
            "'migrations.test_writer.WriterTests.NestedEnum' rendering and would "
            "not resolve. (Python str is immutable, so a real impl literally "
            "cannot do this; the permission rejection is the carrier-level "
            "analogue.)"
        ),
        "rationale": (
            "MANDATORY frame-mutation probe. The input qualified_name is "
            "read-only Acc(list_pred(qualified_name), 1/2); the impl writes "
            "qualified_name[0] = 46 while holding only half permission. Nagini "
            "must REJECT for INSUFFICIENT PERMISSION (a list write needs full "
            "permission). The rejection is attributable solely to the write — "
            "every other op is the verbatim verifying gold body. A byte-fuzzer "
            "never constructs this; it is the project's #1 weakness class."
        ),
    },
    {
        "id": "partial-domain-leaf-name-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_LEAF),
        "refinement": (
            "This is literally the PRE-PATCH Django ("
            "'%s.%s' % (module, self.value.__name__)) — model_prepatch.py. On "
            "the F2P WriterTests.NestedEnum (a class nested in WriterTests, so "
            "__qualname__ == 'WriterTests.NestedEnum' != __name__ == "
            "'NestedEnum') it renders 'migrations.test_writer.NestedEnum' (bare "
            "leaf) instead of the demanded "
            "'migrations.test_writer.WriterTests.NestedEnum' (full chain). The "
            "migration references a non-existent module attribute and the F2P "
            "assertion fails; it does NOT resolve."
        ),
        "rationale": (
            "THE discriminating rival: keys the non-built-in fragment on "
            "simple_name (bare leaf) instead of qualified_name. Violates the "
            "load-bearing Implies(not module_is_builtin, ToSeq(Result()[0]) == "
            "dotted_path(ToSeq(module), ToSeq(qualified_name))) because "
            "simple_name and qualified_name are INDEPENDENT inputs that differ in "
            "the nested case. If it verifies => SPEC-TOO-WEAK. This is exactly "
            "the clause model_prepatch.py fails (G-DIFF)."
        ),
    },
    {
        "id": "partial-domain-drop-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_NODOT),
        "refinement": (
            "Omitting the '.' yields module ++ qualified_name (e.g. "
            "'migrations.test_writerWriterTests.NestedEnum'), not a valid dotted "
            "path and != the F2P expected string; it does not resolve."
        ),
        "rationale": (
            "Partial-domain rival: drops the U+002E separator. Violates "
            "ToSeq(Result()[0]) == dotted_path(...) == module ++ PSeq(46) ++ "
            "qualified_name (the literal 46 is missing). If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-no-import",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_NOIMPORT),
        "refinement": (
            "A serializer that emits no 'import migrations.test_writer' for a "
            "non-built-in class produces a migration file referencing an "
            "unimported module; the F2P demands the import set "
            "{'import migrations.test_writer'}, so it fails; it does not resolve."
        ),
        "rationale": (
            "Partial-domain rival passing the fragment pin but failing the "
            "import pin: returns an empty import on the non-built-in path. "
            "Violates Implies(not module_is_builtin, ToSeq(Result()[1]) == "
            "import_line(ToSeq(module))) (len would be 0, not 7+len(module)). If "
            "it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-domain-builtin-always-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_variant(_PARTIAL_BUILTIN),
        "refinement": (
            "Rendering the qualified dotted path + import even for builtins makes "
            "`int` serialize as 'builtins.int' with 'import builtins'; the P2P "
            "test_serialize_builtin_types / test_serialize_type_none expect the "
            "bare 'int' / 'type(None)' with NO import, so those tests fail; it "
            "does not resolve."
        ),
        "rationale": (
            "Partial-domain rival correct on the non-built-in domain but wrong on "
            "the built-in branch: always renders the dotted path + import. "
            "Violates the built-in clauses Implies(module_is_builtin, "
            "ToSeq(Result()[0]) == ToSeq(simple_name)) and "
            "Implies(module_is_builtin, len(Result()[1]) == 0). If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
]

# No @ContractOnly axiom is consumed (axioms region is empty; meta.axioms == []).
# The two deep-model references, dotted_path / import_line (A-references), are the
# fully-unfolded @Pure helpers in the FROZEN spec itself (flat code-point
# concatenations), validated equal to the real post-patch
# TypeSerializer.serialize() formatting out-of-band by axiom_check.py (G-AX,
# status pass: 20 explicit targets incl. nested classes / nested enums / builtins
# + 20000 fuzz classes spanning nested + top-level __qualname__ shapes). There is
# no @ContractOnly Ensures for a real callee to violate (axiom-soundness N/A) and
# no model-reachable callee input outside an axiom domain (the model consumes no
# axiomatized callee; axiom-containment N/A). So AXIOM_TESTS is empty by
# construction; see 'assessment'.
AXIOM_TESTS = []
