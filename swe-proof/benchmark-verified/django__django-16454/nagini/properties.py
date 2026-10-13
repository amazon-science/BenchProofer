# properties.py — PBT manifest for django__django-16454. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are full model.py variants that
# share the FROZEN spec verbatim (region-surgery edits ONLY text inside the two
# # impl-start/# impl-end regions) and differ only in the implementation; they
# are checked by Nagini verify + markers.same_spec. There are no @ContractOnly
# axioms requiring an in-Docker soundness probe beyond the existing G-AX witness
# (the one axiom is grounded in the input token and asserts no Ensures), so
# AXIOM_TESTS is intentionally empty (see 'assessment').
from pathlib import Path

INSTANCE = "django__django-16454"
FLOAT_ENCODING = None  # meta.json float_encoding is null (pure object/flag logic)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- the two impl regions, verbatim, used as anchors for region-surgery -------

# open_subcommand_group impl (the CHANGED function: records the injection policy)
_OPEN_IMPL = """    if is_error_aware_kind(parser_class_token):
        builder.injects_flag = True
        builder.inherited_style = parent.error_style
    else:
        builder.injects_flag = False"""

# build_subcommand_parser impl (the UNCHANGED constructor that consumes the policy)
_BUILD_IMPL = """    if builder.injects_flag:
        child.carries_flag = True
        child.error_style = builder.inherited_style
    else:
        child.carries_flag = False"""


SPEC_TESTS = [

    # ========================================================================
    # POSITIVE CONTROLS (soundness) — a structurally-DIFFERENT but CORRECT impl
    # MUST verify, else SPEC-TOO-STRONG. Branch-reorder / boolean-restructure
    # only; the spec relies on no loop invariant or fold lemma, so no proof gap
    # risk (cf. AVOID #2/#3).
    # ========================================================================
    {
        "id": "pos-open-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reorder so the plain (else) path is written first via an early
        # unconditional default, then overwritten on the error-aware branch.
        # Behaviourally identical: injects_flag == is_error_aware_kind, and when
        # injecting, inherited_style is parent.error_style. The constructor
        # default of injects_flag is False, so the unconditional pre-set is a
        # no-op-equivalent restatement that keeps the gold obligations.
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    builder.injects_flag = False\n"
            "    if is_error_aware_kind(parser_class_token):\n"
            "        builder.injects_flag = True\n"
            "        builder.inherited_style = parent.error_style",
        ),
        "rationale": "a correct impl with reordered/unconditional-default branch "
                     "structure must still verify; postconditions are pinned by "
                     "value, not by branch order, so this is sound (else "
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-build-boolean-direct",
        "kind": "soundness",
        "expect": "verify",
        # Different shape for build_subcommand_parser: set carries_flag directly
        # from the boolean injects_flag (no explicit True/False literals on the
        # control path), then guard the error_style write. Same observable.
        "module": _swap(
            _BASE, _BUILD_IMPL,
            "    child.carries_flag = builder.injects_flag\n"
            "    if builder.injects_flag:\n"
            "        child.error_style = builder.inherited_style",
        ),
        "rationale": "carries_flag assigned directly from the boolean instead of "
                     "via literal True/False branches is a correct structural "
                     "variant; both postconditions still hold (else SPEC-TOO-STRONG).",
    },

    # ========================================================================
    # ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input.
    # A self-call caller constructs in-domain objects (constructors establish
    # the Requires fields) and calls the modeled function; if the Requires
    # cannot be established for a legitimate input => PRECOND-TOO-STRONG.
    # ========================================================================
    {
        "id": "admiss-open-self-call",
        "kind": "admissibility",
        "expect": "verify",
        # A driver in build_subcommand_parser's impl region: constructs a fresh
        # parent+builder and calls open_subcommand_group on a token, then keeps
        # the original build behaviour. The call must establish the Requires
        # (Acc(parent.error_style,1/2) + full Acc on builder fields) from the
        # constructors. Editing happens ONLY inside the build impl region.
        "module": _swap(
            _BASE, _BUILD_IMPL,
            "    p = OpeningParser()\n"
            "    b = SubCommandBuilder()\n"
            "    open_subcommand_group(p, b, 0)\n"
            "    if builder.injects_flag:\n"
            "        child.carries_flag = True\n"
            "        child.error_style = builder.inherited_style\n"
            "    else:\n"
            "        child.carries_flag = False",
        ),
        "rationale": "a representative caller can establish open_subcommand_group's "
                     "Requires from fresh constructors and invoke it on an "
                     "F2P-shaped input; if it can't, PRECOND-TOO-STRONG.",
    },

    # ========================================================================
    # FRAME-MUTATION (MANDATORY) — parent.error_style is Acc(...,1/2) READ-ONLY.
    # A rival that WRITES to it (e.g. to coerce it into the value it then
    # propagates) must be REJECTED for INSUFFICIENT PERMISSION. The gold
    # postconditions are kept verbatim so the rejection is attributable purely
    # to the half-permission write, not a value mismatch.
    # ========================================================================
    {
        "id": "frame-mut-open-parent",
        "kind": "uniqueness",
        "expect": "reject",
        # Writes parent.error_style (held at only 1/2 permission). Even though it
        # then sets inherited_style to match, the write itself is illegal.
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    if is_error_aware_kind(parser_class_token):\n"
            "        parent.error_style = True\n"
            "        builder.injects_flag = True\n"
            "        builder.inherited_style = parent.error_style\n"
            "    else:\n"
            "        builder.injects_flag = False",
        ),
        "refinement": "the real CommandParser.add_subparsers must NOT mutate the "
                      "parent's called_from_command_line (it only READS it to bind "
                      "into the partial); a patch that overwrote self."
                      "called_from_command_line=True would corrupt the parent's own "
                      "error formatting and fail other P2P/runtime behaviour. So a "
                      "faithful patch of this rival would not resolve.",
        "rationale": "REJECT comes from the permission system: parent.error_style "
                     "is Acc(...,1/2) (read-only), so any write is insufficient "
                     "permission. A verifying write => the spec lets a mutating "
                     "impl through => SPEC-TOO-WEAK (frame defect).",
    },
    {
        "id": "frame-mut-build-builder",
        "kind": "uniqueness",
        "expect": "reject",
        # build_subcommand_parser holds builder.inherited_style at 1/2. A rival
        # that writes it (e.g. normalising None to False before propagating) must
        # reject for insufficient permission. Gold postconditions kept verbatim.
        "module": _swap(
            _BASE, _BUILD_IMPL,
            "    if builder.injects_flag:\n"
            "        builder.inherited_style = builder.inherited_style\n"
            "        child.carries_flag = True\n"
            "        child.error_style = builder.inherited_style\n"
            "    else:\n"
            "        child.carries_flag = False",
        ),
        "refinement": "the unchanged argparse construction step only READS the "
                      "recorded policy (the partial's bound value); a patch that "
                      "rewrote the builder/_SubParsersAction's recorded flag would "
                      "be a spurious side-effect not in the gold patch and would "
                      "not faithfully resolve.",
        "rationale": "REJECT from the permission system: builder.inherited_style is "
                     "Acc(...,1/2) in build_subcommand_parser, so the assignment is "
                     "insufficient permission. A verifying write => frame defect / "
                     "SPEC-TOO-WEAK.",
    },

    # ========================================================================
    # PARTIAL-DOMAIN — a rival correct on a SUB-DOMAIN of the flag values but
    # diverging elsewhere. The propagation postcondition uses `is` identity
    # (Implies(injects_flag, inherited_style is parent.error_style)); a rival
    # that hard-codes a particular flag value is correct only when the parent's
    # flag equals that constant. Must REJECT because the spec demands the
    # verbatim propagation for EVERY parent.error_style (None/True/False).
    # ========================================================================
    {
        "id": "partial-open-hardcode-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Injects the constant True instead of the parent's actual flag. Correct
        # only on the sub-domain parent.error_style is True; wrong for None/False.
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    if is_error_aware_kind(parser_class_token):\n"
            "        builder.injects_flag = True\n"
            "        builder.inherited_style = True\n"
            "    else:\n"
            "        builder.injects_flag = False",
        ),
        "refinement": "binding called_from_command_line=True (the command-line "
                      "style) unconditionally, instead of self.called_from_command_"
                      "line, would force human-facing formatting even for the "
                      "programmatic (None/False) parent; the F2P harness runs "
                      "manage.py with the parent's actual flag, so this divergent "
                      "binding would not faithfully match gold across the runtime "
                      "settings the tests exercise.",
        "rationale": "REJECT from postcondition Implies(injects_flag, "
                     "inherited_style is parent.error_style): when parent."
                     "error_style is None/False, `True is None/False` is false, so "
                     "the Ensures cannot be discharged. A verify here => the spec "
                     "fails to pin verbatim propagation => SPEC-TOO-WEAK.",
    },
    {
        "id": "partial-open-hardcode-none",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch-flavoured bug: inject the constructor default None rather
        # than the parent's flag. Correct ONLY when parent.error_style is None
        # (the very default that motivated the gold patch).
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    if is_error_aware_kind(parser_class_token):\n"
            "        builder.injects_flag = True\n"
            "        builder.inherited_style = None\n"
            "    else:\n"
            "        builder.injects_flag = False",
        ),
        "refinement": "this is exactly the pre-patch defect (subparsers built with "
                      "the constructor default called_from_command_line=None) that "
                      "the gold patch fixes; the F2P test_subparser_error_formatting "
                      "fails under it because the sub-command parser then raises a "
                      "stack trace instead of the usage message. A faithful patch "
                      "of this rival does NOT resolve.",
        "rationale": "REJECT from Implies(injects_flag, inherited_style is parent."
                     "error_style): when the parent's flag is True/False, `None is "
                     "True/False` is false. A verify here => SPEC-TOO-WEAK (admits "
                     "the pre-patch behaviour).",
    },

    # ========================================================================
    # PARTIAL-DOMAIN / DECISION-INVERSION — pin the injects_flag decision. A
    # rival that sets injects_flag to a constant (True) regardless of
    # is_error_aware_kind is correct only on the error-aware sub-domain and
    # wrong on the plain path; the spec must reject it.
    # ========================================================================
    {
        "id": "partial-open-always-inject",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the guard: always injects. Correct only when the requested kind
        # IS error-aware; wrong for the plain argparse.ArgumentParser path
        # (regression-guarded by test_subparser_non_django_error_formatting).
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    builder.injects_flag = True\n"
            "    builder.inherited_style = parent.error_style",
        ),
        "refinement": "the gold patch only wraps parser_class in the flag-binding "
                      "partial WHEN issubclass(parser_class, CommandParser); always "
                      "injecting would attempt to pass called_from_command_line to a "
                      "vanilla argparse.ArgumentParser subparser, which does not "
                      "accept it -- breaking the plain path that "
                      "test_subparser_non_django_error_formatting guards. A faithful "
                      "patch does NOT resolve.",
        "rationale": "REJECT from postcondition injects_flag == is_error_aware_kind"
                     "(parser_class_token): forcing injects_flag=True makes the "
                     "equality false whenever the axiom predicate is False (a kind "
                     "the verifier cannot prove is always error-aware, since "
                     "is_error_aware_kind is an arbitrary deterministic predicate). "
                     "A verify here => SPEC-TOO-WEAK.",
    },
    {
        "id": "partial-build-always-carry",
        "kind": "uniqueness",
        "expect": "reject",
        # Symmetric attack on build_subcommand_parser: always carry the flag,
        # ignoring builder.injects_flag. Wrong on the plain path.
        "module": _swap(
            _BASE, _BUILD_IMPL,
            "    child.carries_flag = True\n"
            "    child.error_style = builder.inherited_style",
        ),
        "refinement": "a plain (non-CommandParser) sub-command parser carries no "
                      "called_from_command_line at all; forcing carries_flag=True "
                      "for it would misrepresent the untouched plain path that "
                      "test_subparser_non_django_error_formatting checks. A faithful "
                      "patch does NOT resolve.",
        "rationale": "REJECT from postcondition child.carries_flag == builder."
                     "injects_flag: forcing carries_flag=True makes the equality "
                     "false when injects_flag is False. A verify here => SPEC-TOO-"
                     "WEAK.",
    },

    # ========================================================================
    # FRAME / GARBAGE-WRITE on the PLAIN path — the G-PANEL-1 weakness class
    # this spec was strengthened against: the original postconditions said
    # nothing about inherited_style / error_style when the flag is NOT
    # injected/carried, so a rival could scribble a garbage style value on the
    # plain path and still verify. The added frame clauses
    # (Implies(not injects_flag, inherited_style is Old(inherited_style)) and
    # Implies(not carries_flag, error_style is Old(error_style))) must REJECT
    # these rivals.
    # ========================================================================
    {
        "id": "frame-open-plain-garbage-style",
        "kind": "uniqueness",
        "expect": "reject",
        # Plain (else) path additionally records a bogus style binding.
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    if is_error_aware_kind(parser_class_token):\n"
            "        builder.injects_flag = True\n"
            "        builder.inherited_style = parent.error_style\n"
            "    else:\n"
            "        builder.injects_flag = False\n"
            "        builder.inherited_style = True",
        ),
        "refinement": "the gold add_subparsers, on the non-CommandParser path, "
                      "falls through WITHOUT touching kwargs['parser_class'] -- no "
                      "called_from_command_line binding of any kind is recorded. A "
                      "patch that additionally stashed a bogus binding for the "
                      "plain path would be a spurious side-effect absent from the "
                      "gold patch and would not faithfully resolve.",
        "rationale": "REJECT from the frame clause Implies(not injects_flag, "
                     "inherited_style is Old(inherited_style)): the else-branch "
                     "write flips inherited_style from None to True while "
                     "injects_flag is False. A verify here => the spec again "
                     "admits plain-path garbage writes => SPEC-TOO-WEAK.",
    },
    {
        "id": "frame-build-plain-garbage-style",
        "kind": "uniqueness",
        "expect": "reject",
        # Symmetric attack on the constructor: plain path writes a bogus
        # error_style onto the child while carries_flag stays False.
        "module": _swap(
            _BASE, _BUILD_IMPL,
            "    if builder.injects_flag:\n"
            "        child.carries_flag = True\n"
            "        child.error_style = builder.inherited_style\n"
            "    else:\n"
            "        child.carries_flag = False\n"
            "        child.error_style = True",
        ),
        "refinement": "a plain (non-CommandParser) sub-command parser is built "
                      "with NO called_from_command_line attribute at all; a patch "
                      "that set one anyway would diverge from the unchanged "
                      "argparse construction and misbehave on the plain path "
                      "guarded by test_subparser_non_django_error_formatting.",
        "rationale": "REJECT from the frame clause Implies(not carries_flag, "
                     "error_style is Old(error_style)): the else-branch write "
                     "flips child.error_style from None to True while "
                     "carries_flag is False. A verify here => SPEC-TOO-WEAK.",
    },

    # ========================================================================
    # SUPPORTING near-miss (cheap) — drop the inherited_style propagation write
    # on the error-aware branch in open_subcommand_group. inherited_style keeps
    # its constructor default None; correct only when parent.error_style is None.
    # Carries a real refinement (same as hardcode-none). Supporting, not a
    # substitute for the reasoned attacks above.
    # ========================================================================
    {
        "id": "supp-open-drop-propagation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _OPEN_IMPL,
            "    if is_error_aware_kind(parser_class_token):\n"
            "        builder.injects_flag = True\n"
            "    else:\n"
            "        builder.injects_flag = False",
        ),
        "refinement": "omitting the called_from_command_line binding leaves the "
                      "subparser at the constructor default None -- the pre-patch "
                      "defect that fails F2P test_subparser_error_formatting. "
                      "Faithful patch does NOT resolve.",
        "rationale": "REJECT from Implies(injects_flag, inherited_style is parent."
                     "error_style): with inherited_style left at None it cannot be "
                     "shown `is` the parent's (possibly True/False) flag. Supporting "
                     "near-miss with a real refinement.",
    },
]


# No @ContractOnly axioms require an in-Docker soundness/containment probe in
# this manifest: the single axiom is_error_aware_kind asserts NO Ensures (purely
# determinism/purity, the weakest contract) and is GROUNDED as a function of the
# input token, so there is no exact-value obligation a real callee could violate
# and no answer-key to echo. Its real-callee soundness + caller-domain coverage
# is already exercised by the bundle's axiom_check.py / G-AX (real issubclass on
# 9 boundary classes + an end-to-end propagation witness). See 'assessment'.
AXIOM_TESTS = []
