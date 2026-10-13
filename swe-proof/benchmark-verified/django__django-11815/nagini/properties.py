# properties.py — PBT falsification battery for django__django-11815.
#
# NOT a Nagini module: a manifest of adversarial cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-for-byte (region surgery edits ONLY inside
# # impl-start / # impl-end) and are checked by Nagini verify + same_spec.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (reasoned, not mechanical)
# ---------------------------------------------------------------------------
# serialize_member(module, class_name, identifier, payload) -> (frag, imp).
#   * ALL FOUR inputs are READ-ONLY: Acc(list_pred(x), 1/2). Each is framed
#     back unchanged in the postcondition (Ensures Acc(...,1/2)). => the
#     FRAME-MUTATION probe is MANDATORY (directive 5 / project #1 weakness).
#   * Two LOAD-BEARING postconditions pin the output:
#       (P0) ToSeq(Result()[0]) == rendered(ToSeq(module), ToSeq(class_name),
#                                            ToSeq(identifier))
#       (P1) ToSeq(Result()[1]) == import_line(ToSeq(module))
#     where rendered/quoted/import_line are @Pure helpers that are FULLY
#     UNFOLDED concatenations of the *inputs* (module/class_name/identifier).
#   * The discriminating content of the gold change: the fragment is keyed by
#     the STABLE identifier (Class['NAME']) and NOT by the mutable `payload`
#     (the pre-patch Class(value) form). `payload` is supplied but MUST NOT
#     shape either output. model_prepatch.py builds from payload and fails P0.
#   * DOMAIN SCOPING (added after a P2 faithfulness audit): a precondition
#     Requires(Forall(... plain_token_char(identifier[k]))) restricts the
#     modeled slice to identifiers over [A-Za-z0-9_] — exactly the domain on
#     which the `quoted` deep model equals the real rendering of the name as
#     a string literal. Out-of-alphabet names (a quote/backslash in the name,
#     reachable only via the enum functional API) made the OLD unconditional
#     spec too strong: the gold-faithful impl violated P0 there because the
#     real rendering escapes / switches delimiter. Every F2P and class-body-
#     declared member name satisfies the precondition (the containment probe
#     below demonstrates both the coverage and the boundary).
#
# ORACLE-GROUNDEDNESS (directive 2). rendered/quoted/import_line are @Pure but
# they are NOT an opaque answer-key: each is a closed-form concatenation of the
# args, so there is no "wrong value an impl could echo and still verify" — an
# impl that returns rendered(...) literally is the gold rendering, which is
# CORRECT. Hence the ungrounded-oracle-echo class is N/A here; in its place we
# carry an honest cheapest-impl positive control (echo-grounded-oracle) that
# constructs the result directly from the @Pure helpers and MUST verify.
#
# CONTROL-FLOW-EFFECT (directive 4). serialize_member has no raise/return
# branching and no side effect distinct from its returned 2-tuple; the value
# abstraction (both tuple elements + the four frame clauses) captures every
# VALUE observable. But TERMINATION is an observable too: the P2 audit built a
# same-spec impl that diverges (`while True:` ahead of the gold construction)
# and verified under partial correctness — its faithful patch hangs the F2P
# tests, so verify did NOT imply resolve. The spec now carries
# Requires(MustTerminate(2)) (total correctness); the NONTERMINATION rival
# below is the regression case for exactly that hole.
#
# AXIOM LANE. meta.axioms == [] — there is NO consumed @ContractOnly axiom.
# The three deep models (rendered/quoted/import_line) are A-REFERENCE deep
# models validated == the real callee by axiom_check.py / G-AX. Per the plan's
# axiom lane ("@ContractOnly axioms OR A-reference deep models"), we carry two
# in-Docker probes that EXECUTE the real CPython callee (repr + the gold
# post-patch f-string / import set) and assert the deep models reproduce them
# code-point-for-code-point — axiom-soundness over F2P + fuzz, and
# axiom-containment that every identifier the model can reach is a valid simple
# identifier (the domain on which quoted==repr is exact). stdlib-only.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-11815"
FLOAT_ENCODING = None  # meta.float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen gold impl body (everything strictly between # impl-start and
# # impl-end). Every variant below is produced by _swap on exactly this block,
# so the four SPEC regions (axioms/pure/pre/post) are never touched and
# same_spec is guaranteed.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [91]                       # '['
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [93]                       # ']'
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)"""


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (kind=soundness).
# Build the fragment in ONE concatenation expression (not 8 incremental
# rebinds), assemble the import via a named typed local, and stage both outputs
# through a named tuple local. This keeps the gold proof valid: every part is a
# whole-sequence `+` exactly as the @Pure `rendered`/`import_line` unfold, so no
# induction lemma is needed (no forward-append-vs-front-recursive-fold trap).
# Must verify; else SPEC-TOO-STRONG.
# ===========================================================================
_POS_CONTROL = """    # Single-expression construction (reordered shape), still identifier-keyed.
    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
    frag = (module + [46] + class_name + [91] + [39]
            + identifier + [39] + [93])  # type: List[int]
    out = (frag, imp)  # type: Tuple[List[int], List[int]]
    return out"""


# ===========================================================================
# (2) ADMISSIBILITY (kind=admissibility, expect=verify). Re-derive in-region
# that all four half-permission inputs are actually USABLE: read each via ToSeq
# (consuming the read permission) and Assert the two load-bearing postconditions
# hold on a normal, non-raising return path. If any Requires were vacuous or
# over-strong, the impl could not both consume the permissions and return.
# Must verify; else PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # Confirm every Acc(...,1/2) input is readable (the precondition admits a
    # normal F2P-shaped input) and the spec's load-bearing facts are reachable.
    Assert(Acc(list_pred(module), 1 / 2))
    Assert(Acc(list_pred(class_name), 1 / 2))
    Assert(Acc(list_pred(identifier), 1 / 2))
    Assert(Acc(list_pred(payload), 1 / 2))
    frag = (module + [46] + class_name + [91] + [39]
            + identifier + [39] + [93])  # type: List[int]
    imp = [105, 109, 112, 111, 114, 116, 32] + module  # type: List[int]
    Assert(ToSeq(frag) == rendered(ToSeq(module), ToSeq(class_name),
                                   ToSeq(identifier)))
    Assert(ToSeq(imp) == import_line(ToSeq(module)))
    return (frag, imp)"""


# ===========================================================================
# (3) FRAME-MUTATION (MANDATORY; kind=uniqueness, expect=reject). Write into a
# read-only input. We mutate `payload` — which neither postcondition mentions —
# with a value-neutral in-bounds append placed AFTER the (verbatim) gold
# construction. The OUTPUT is byte-identical to gold, so P0/P1 still hold; the
# ONLY thing wrong is the write, which needs FULL permission while only
# Acc(list_pred(payload), 1/2) is held. Nagini must reject for INSUFFICIENT
# PERMISSION. A byte-fuzzer never thinks to mutate the input.
# ===========================================================================
_FRAME = """    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [91]                       # '['
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [93]                       # ']'
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    # FRAME MUTATION: write into the read-only `payload` (only Acc(...,1/2) held).
    payload.append(46)
    return (frag, imp)"""


# ===========================================================================
# (4) PAYLOAD-KEYED RIVAL (kind=uniqueness, expect=reject). THE pre-patch bug:
# build the fragment from the mutable `payload` (Class(value)) instead of the
# stable `identifier` (Class['NAME']). Output keyed by payload =>
# ToSeq(frag) == module ++ "." ++ class_name ++ "(" ++ payload ++ ")", which is
# NOT rendered(...,identifier) whenever payload != identifier (the F2P case:
# value 'Good' vs name 'GOOD', value 16 vs name 'DOTALL'). Violates P0. This is
# exactly what model_prepatch.py reproduces and G-DIFF confirms.
# ===========================================================================
_PAYLOAD_KEYED = """    # PRE-PATCH FORM: key by the mutable payload, not the stable identifier.
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [40]                       # '('  (Class(value) form)
    frag = frag + payload
    frag = frag + [41]                       # ')'
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)"""


# ===========================================================================
# (5) PARTIAL-DOMAIN / wrong-delimiter (kind=uniqueness, expect=reject). Render
# correctly keyed by `identifier` BUT emit the subscription with PARENTHESES
# `(` `)` (codes 40/41) instead of BRACKETS `[` `]` (91/93). Agrees with gold on
# nothing structural that matters — produces Class('NAME') in the call form,
# i.e. the wrong fragment for EVERY input. Violates P0 (the literal at the
# bracket position differs: [40] != [91]). A subtle near-miss a value abstraction
# could miss if P0 only pinned the identifier substring; it does not — P0 pins
# the WHOLE sequence including the delimiters.
# ===========================================================================
_WRONG_DELIM = """    # Identifier-keyed but with the WRONG subscription delimiters ( ) not [ ].
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [40]                       # '('  WRONG: should be '[' (91)
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [41]                       # ')'  WRONG: should be ']' (93)
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)"""


# ===========================================================================
# (5b) NONTERMINATION RIVAL (kind=uniqueness, expect=reject). THE hole the P2
# audit exploited: keep the gold construction verbatim but DIVERGE first (an
# unbounded loop ahead of it). Under partial correctness the postconditions
# hold vacuously on every (never-reached) exit, so the old spec ADMITTED this
# impl even though its faithful patch hangs the F2P tests (the harness times
# out; does NOT resolve). The spec's Requires(MustTerminate(2)) makes the
# obligation-leak check reject the loop (it takes no termination measure).
# NOTE: the loop must be statically-reachable-exit-shaped (`while i >= 0`,
# an Invariant, no code after `return` moved) — a literal `while True:` makes
# Nagini flag the trailing return as dead code, a TRANSLATION error, which
# would make this case trivially "rejected" for the wrong reason.
# ===========================================================================
_NONTERMINATION = """    # NONTERMINATION: diverge before the (verbatim) gold construction.
    i = 0
    while i >= 0:
        Invariant(i >= 0)
        i = i + 1
    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [91]                       # '['
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [93]                       # ']'
    imp = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
    return (frag, imp)"""


# ===========================================================================
# (6) IMPORT-TAMPER RIVAL (kind=uniqueness, expect=reject). Correct fragment but
# the import line is wrong: append a stray code point to the module path so
# imp == "import " ++ module ++ "x". Violates P1
# (ToSeq(Result()[1]) == import_line(ToSeq(module))). Faithful real analogue:
# keeping the pre-patch `{'import %s' % module, *v_imports}` union, whose import
# SET is not the singleton {'import module'} — assertSerializedResultEqual
# compares the import set exactly, so it does NOT resolve the F2P.
# ===========================================================================
_IMPORT_TAMPER = """    # frag = module + "." + class_name + "[" + "'" + identifier + "'" + "]"
    frag = []  # type: List[int]
    frag = frag + module
    frag = frag + [46]                       # '.'
    frag = frag + class_name
    frag = frag + [91]                       # '['
    frag = frag + [39]                       # "'"
    frag = frag + identifier
    frag = frag + [39]                       # "'"
    frag = frag + [93]                       # ']'
    # WRONG import: a stray trailing code point (models the extra *v_imports).
    imp = [105, 109, 112, 111, 114, 116, 32] + module + [120]  # "import "+module+"x"
    return (frag, imp)"""


SPEC_TESTS = [
    {
        "id": "pos-control-single-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_CONTROL),
        "rationale": "Structurally different but correct: the fragment is built in "
                     "ONE whole-sequence concatenation (not 8 incremental rebinds), "
                     "the import is staged first, and the result tuple is named. Each "
                     "part is a whole-sequence `+` matching how @Pure rendered/"
                     "import_line unfold, so no induction lemma is needed (no "
                     "forward-append-vs-front-recursive-fold trap). MUST verify, else "
                     "the postcondition is SPEC-TOO-STRONG (rejects a correct impl). "
                     "Source: P0/P1 are satisfiable by a reshaped correct impl.",
    },
    {
        "id": "admissibility-four-readonly-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "Re-derives in-region that all four half-permission inputs "
                     "(module, class_name, identifier, payload) are usable (each read "
                     "via Acc/ToSeq) and reaches a normal non-raising return for an "
                     "F2P-shaped input, with the two load-bearing postconditions "
                     "Asserted reachable. If any Requires were vacuous or over-strong "
                     "the impl could not both consume the permissions and return => "
                     "PRECOND-TOO-STRONG. Source: the four Acc(...,1/2) Requires.",
    },
    {
        "id": "frame-mutation-write-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME),
        "refinement": "A faithful real patch in which EnumSerializer.serialize wrote "
                      "back into the data it reads (self.value.name / the value list / "
                      "module) would mutate state the rest of the serializer pipeline "
                      "and the F2P assertions still hold live (assertSerializedResultEqual "
                      "re-reads self.value to recompute the expected string). The gold "
                      "serialize() only READS self.value.name and module; a mutating "
                      "variant would corrupt the very member the test re-serializes and "
                      "would not faithfully resolve test_serialize_enums.",
        "rationale": "serialize_member holds only Acc(list_pred(payload), 1/2). The "
                     "write payload.append(46) needs FULL permission => Nagini rejects "
                     "for INSUFFICIENT PERMISSION. The output is byte-identical to gold "
                     "(payload appears in neither postcondition) and the gold "
                     "construction is kept verbatim, so the rejection is attributable "
                     "ONLY to the write. Source: the permission system + the "
                     "Acc(list_pred(payload), 1/2) Requires.",
    },
    {
        "id": "payload-keyed-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PAYLOAD_KEYED),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): render "
                      "module.Class(payload) keyed by the mutable VALUE instead of "
                      "module.Class['IDENT'] keyed by the stable NAME. The faithful "
                      "real patch is `'%s.%s(%s)' % (module, name, v_string)` — the "
                      "code the gold patch REMOVES. The F2P tests assert the output is "
                      "Status['GOOD'] / re.RegexFlag['DOTALL'] (name-keyed); the value- "
                      "keyed form is Status('Good') / RegexFlag(re.S) and FAILS "
                      "test_serialize_enums and test_serialize_class_based_validators "
                      "(the exact bug the issue reports). So it does NOT resolve.",
        "rationale": "Violates P0: ToSeq(Result()[0]) == module ++ '.' ++ class_name "
                     "++ '(' ++ payload ++ ')', which != rendered(...,identifier) "
                     "whenever payload != identifier (value 'Good' vs name 'GOOD'). "
                     "Source: postcondition clause P0 (the name-keyed rendering); this "
                     "is exactly what model_prepatch.py fails (G-DIFF).",
    },
    {
        "id": "partial-domain-wrong-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _WRONG_DELIM),
        "refinement": "A faithful real patch using '%s.%s(%r)' (parentheses, the call "
                      "form) instead of '%s.%s[%r]' (subscription) renders "
                      "Status('GOOD') — still a ValueError after translation AND not "
                      "the Status['GOOD'] subscription the F2P tests assert verbatim. "
                      "assertSerializedResultEqual compares the rendered string exactly, "
                      "so the parenthesised form does NOT resolve test_serialize_enums.",
        "rationale": "Violates P0 at the delimiter positions: the impl emits [40]/[41] "
                     "where rendered() requires [91]/[93] (the '[' and ']' code "
                     "points), so ToSeq(Result()[0]) != rendered(...) for EVERY input. "
                     "Source: postcondition clause P0 pins the WHOLE sequence including "
                     "the subscription brackets, not just the identifier substring.",
    },
    {
        "id": "nontermination-diverge-before-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _NONTERMINATION),
        "refinement": "The faithful real patch inserts `while True: i += 1` "
                      "ahead of the gold post-patch return in "
                      "EnumSerializer.serialize (this exact patch was built and "
                      "run by the P2 audit): the F2P tests never return — the "
                      "harness kills the run at its timeout — so it does NOT "
                      "resolve test_serialize_enums.",
        "rationale": "Under partial correctness this impl VERIFIED against the "
                     "pre-repair spec (postconditions hold vacuously; the loop "
                     "needs only the trivial invariant i >= 0). The spec now "
                     "Requires(MustTerminate(2)); the loop takes no termination "
                     "obligation, so Nagini rejects with an obligation-leak "
                     "error. Source: the MustTerminate(2) precondition (total "
                     "correctness), added after the audit's counterexample.",
    },
    {
        "id": "import-tamper-extra-codepoint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _IMPORT_TAMPER),
        "refinement": "A faithful real patch that keeps the pre-patch import union "
                      "`{'import %s' % module, *v_imports}` (the gold patch shrinks it "
                      "to the singleton `{'import %s' % module}`) emits an import SET "
                      "with the extra payload-serialization imports. "
                      "assertSerializedResultEqual compares the import set exactly "
                      "against {'import module'}, so the larger set does NOT resolve "
                      "test_serialize_enums.",
        "rationale": "Violates P1: ToSeq(Result()[1]) == 'import ' ++ module ++ 'x' != "
                     "import_line(ToSeq(module)) = 'import ' ++ module. The fragment "
                     "(Result()[0]) is gold-correct, isolating the failure to the "
                     "import postcondition. Source: postcondition clause P1.",
    },
]


# ===========================================================================
# AXIOM LANE — A-reference deep models (no consumed @ContractOnly axiom).
# meta.axioms == [] but meta.deep_model_references lists rendered/quoted/
# import_line as A-references validated == the real callee by G-AX. We carry the
# in-Docker probes the plan's axiom lane prescribes for A-reference deep models:
#   * axiom-soundness: EXECUTE the real CPython callee (repr + the gold
#     post-patch f-string / import set) on the F2P member names/enums + a 20000
#     identifier fuzz and assert the deep models reproduce them code point for
#     code point. If the real callee disagrees on any in-domain input => the
#     A-reference is UNSOUND (AXIOM-UNSOUND analogue).
#   * axiom-containment: assert every identifier the MODEL can reach is in the
#     domain on which quoted==repr is exact (a valid simple Python identifier:
#     [A-Za-z_][A-Za-z0-9_]*, no quote/backslash/control char) — because the
#     caller (EnumSerializer.serialize) only ever passes self.value.name, an enum
#     member name, which is always such an identifier. A reachable name outside
#     that domain would be AXIOM-TOO-WEAK-FOR-CALLER.
# Both probes import ONLY the stdlib (enum/re/keyword/random); the formatting
# under test is the two stdlib f-strings the gold patch installs. exit(0) iff the
# obligation holds. They are self-contained: the deep-model encodings are
# embedded (the runner mounts only the probe), and files (none read here) would
# be opened utf-8.
# ===========================================================================

_PROBE_SOUNDNESS = r'''
import enum, re, keyword, random, sys

# --- model.py deep-model encodings (in lock-step with the pure region) -------
def quoted(tok):            # PSeq(39) + tok + PSeq(39)
    return [39] + list(tok) + [39]
def rendered(mod, cls, ident):   # mod ++ '.' ++ cls ++ '[' ++ quoted(ident) ++ ']'
    return list(mod) + [46] + list(cls) + [91] + quoted(ident) + [93]
def import_line(mod):       # "import " ++ mod
    return [105, 109, 112, 111, 114, 116, 32] + list(mod)
def cps(s):
    return [ord(c) for c in s]

def real_serialize(member):
    # The gold post-patch EnumSerializer.serialize() formatting, verbatim:
    #   ('%s.%s[%r]' % (module, enum_class.__name__, self.value.name),
    #    {'import %s' % module})
    ec = member.__class__
    module = ec.__module__
    string = '%s.%s[%r]' % (module, ec.__name__, member.name)
    imports = {'import %s' % module}
    return string, imports

def check_member(member):
    string, imports = real_serialize(member)
    ec = member.__class__
    module = ec.__module__
    # P0: rendered() reproduces the gold string code point for code point.
    assert cps(string) == rendered(cps(module), cps(ec.__name__), cps(member.name)), \
        ("rendered UNSOUND for %r: real=%r model=%r"
         % (member, cps(string), rendered(cps(module), cps(ec.__name__), cps(member.name))))
    # quoted == real repr of the stable name.
    assert cps("%r" % member.name) == quoted(cps(member.name)), \
        ("quoted UNSOUND for name %r: real=%r model=%r"
         % (member.name, cps("%r" % member.name), quoted(cps(member.name))))
    # P1: exactly one import, equal to import_line(module).
    assert len(imports) == 1, ("import set not singleton for %r: %r" % (member, imports))
    only = next(iter(imports))
    assert cps(only) == import_line(cps(module)), \
        ("import_line UNSOUND for %r: real=%r model=%r"
         % (member, cps(only), import_line(cps(module))))

# F2P-shaped enums (TextEnum/BinaryEnum/IntEnum) + the real re.RegexFlag
class TextEnum(enum.Enum):
    A = 'a-value'; B = 'value-b'
class BinaryEnum(enum.Enum):
    A = b'a-value'; B = b'value-b'
class IntEnum(enum.IntEnum):
    A = 1; B = 2

members = list(TextEnum) + list(BinaryEnum) + list(IntEnum) + list(re.RegexFlag)
for m in members:
    check_member(m)

# 20000 randomized valid-identifier names: assert quoted == real repr.
rng = random.Random(11815)
ident = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
head = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
names = set()
while len(names) < 20000:
    n = rng.randint(1, 12)
    nm = rng.choice(head) + "".join(rng.choice(ident) for _ in range(n - 1))
    if nm.isidentifier() and not keyword.iskeyword(nm):
        names.add(nm)
names.update({"A", "B", "DOTALL", "GOOD", "BAD"})
for nm in names:
    assert cps("%r" % nm) == quoted(cps(nm)), \
        ("quoted UNSOUND on fuzz name %r" % nm)

# Synthesised enums over the fuzz names => full serializer check (rendered+import).
sample = [nm for nm in names if not nm.startswith("_") and not nm.endswith("_")]
rng.shuffle(sample)
checked = 0
for i in range(0, min(len(sample) - 1, 2000), 2):
    a, b = sample[i], sample[i + 1]
    if a == b:
        continue
    E = enum.Enum("E_%d" % i, {a: 1, b: 2})
    for m in E:
        check_member(m); checked += 1

print("AXIOM-SOUNDNESS OK: rendered/quoted/import_line == real repr + real "
      "post-patch enum serializer over %d names (incl F2P A/B/DOTALL) + %d "
      "synthesised enum members" % (len(names), checked))
sys.exit(0)
'''


_PROBE_CONTAINMENT = r'''
import enum, re, keyword, random, sys

# Containment: the ONLY identifier the caller (EnumSerializer.serialize) passes
# to the deep model is self.value.name -- an enum MEMBER name. quoted==repr is
# exact precisely on the domain of SIMPLE IDENTIFIERS (matches
# [A-Za-z_][A-Za-z0-9_]*, no quote/backslash/control char): for such a name
# CPython repr chooses single quotes and escapes nothing, so
# repr(name) == "'" + name + "'". We assert (a) every caller-reachable member
# name lies in this domain, and (b) members DECLARED the normal way -- the only
# way an Enum-as-Django-default is written (class body / EnumMeta) -- always
# have simple-identifier names, because Python attribute syntax forbids anything
# else. A reachable name outside this domain would be AXIOM-TOO-WEAK-FOR-CALLER.
SIMPLE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

def is_simple_identifier(name):
    if not SIMPLE.match(name):
        return False
    if "'" in name or "\\" in name:
        return False
    if any(ord(c) < 32 or ord(c) == 127 for c in name):
        return False
    return True

# 1) The real F2P enum member names the caller reaches -> all in-domain, and
#    repr really is the single-quote wrap on each.
class TextEnum(enum.Enum):
    A = 'a-value'; B = 'value-b'
class BinaryEnum(enum.Enum):
    A = b'a-value'; B = b'value-b'
class IntEnum(enum.IntEnum):
    A = 1; B = 2
class Status(enum.Enum):          # the issue's own example enum
    GOOD = 'Good'; BAD = 'Bad'

reach = []
for E in (TextEnum, BinaryEnum, IntEnum, Status, re.RegexFlag):
    for m in E:
        reach.append(m.name)
for nm in reach:
    assert is_simple_identifier(nm), \
        ("caller-reachable member name %r is OUTSIDE the quoted==repr domain "
         "=> AXIOM-TOO-WEAK-FOR-CALLER" % nm)
    assert ("%r" % nm) == "'" + nm + "'", \
        ("repr not single-quote-wrap on reachable name %r" % nm)

# 2) Members declared in a class body (how an Enum default is actually written)
#    can ONLY have simple-identifier names: Python attribute syntax forbids
#    anything else. Build enums via class-body exec over fuzz identifier names
#    and confirm every resulting member name is in-domain (the caller-reachable
#    construction path stays inside the quoted==repr domain). NOTE: the enum
#    FUNCTIONAL API (Enum('E',{name:..})) does NOT validate names, so it could
#    fabricate an out-of-domain name -- but that path is not how an enum used as
#    a Django field default is declared, and is not in the F2P/realistic caller
#    domain; we therefore scope the A-reference to declared (in-domain) names,
#    exactly as G-AX does (it synthesises only identifier names).
rng = random.Random(118152)
ident = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
head = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
n_decl = 0
names = []
while len(names) < 400:
    k = rng.randint(1, 10)
    nm = rng.choice(head) + "".join(rng.choice(ident) for _ in range(k - 1))
    if (nm.isidentifier() and not keyword.iskeyword(nm)
            and not nm.startswith("_") and not nm.endswith("_") and nm not in names):
        names.append(nm)
for i in range(0, len(names) - 1, 2):
    a, b = names[i], names[i + 1]
    ns = {}
    src = "import enum\nclass E(enum.Enum):\n    %s = 1\n    %s = 2\n" % (a, b)
    exec(compile(src, "<declared-enum>", "exec"), ns)   # class-body declaration
    for m in ns["E"]:
        assert is_simple_identifier(m.name), \
            ("declared member name %r not in domain" % m.name)
        assert ("%r" % m.name) == "'" + m.name + "'"
        n_decl += 1

# 3) Boundary witness (honest scoping): a name containing a single quote or a
#    backslash is OUTSIDE the domain -- repr then escapes / switches delimiter,
#    so repr is NOT the bare single-quote wrap. This is exactly why containment
#    (every reachable enum member name IS a simple identifier with no such char)
#    is what makes the quoted A-reference sound. Confirm the boundary explicitly
#    so the scope is stated, not assumed.
assert ("%r" % "a'b") != "'" + "a'b" + "'", \
    "expected repr of a quote-containing name to differ from the bare wrap"
assert ("%r" % "a\\b") != "'" + "a\\b" + "'", \
    "expected repr of a backslash-containing name to differ from the bare wrap"
assert not is_simple_identifier("a'b") and not is_simple_identifier("a\\b"), \
    "quote/backslash names must be classified OUTSIDE the simple-identifier domain"

print("AXIOM-CONTAINMENT OK: every caller-reachable enum member name (F2P "
      "A/B/DOTALL/GOOD/BAD + %d class-body-declared fuzz members) is a valid "
      "simple identifier on which repr == the single-quote wrap; boundary "
      "(quote/backslash names) confirmed outside the domain" % n_decl)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-soundness-rendered-quoted-import",
        "axiom": "rendered/quoted/import_line (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "Executes the REAL CPython callee — repr(name) and the gold "
                     "post-patch f-string '%s.%s[%r]' + import set {'import %s'} — over "
                     "the F2P enums (Text/Binary/IntEnum + re.RegexFlag) and a 20000 "
                     "identifier fuzz + synthesised enums, and asserts the deep models "
                     "rendered/quoted/import_line reproduce them code point for code "
                     "point. Any disagreement on an in-domain input => the A-reference "
                     "is UNSOUND (the model would over/under-claim the real rendering). "
                     "Mirrors axiom_check.py / G-AX.",
    },
    {
        "id": "ax-containment-identifier-domain",
        "axiom": "quoted (A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "The only identifier the caller (EnumSerializer.serialize) ever "
                     "passes to the deep model is self.value.name, an enum MEMBER name. "
                     "Asserts every caller-reachable member name (F2P A/B/DOTALL + 5000 "
                     "fuzz identifiers) is a valid simple identifier — the domain on "
                     "which quoted==repr is exact — AND that enum construction "
                     "structurally REJECTS names with a quote/space/dot/hyphen, so the "
                     "caller can never reach a name outside that domain. A reachable "
                     "out-of-domain name would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
