"""properties.py — PBT falsification manifest for astropy__astropy-13453.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template.

The function under spec
-----------------------
    resolve_column_formats(names: List[int], prior_formats: List[int],
                           formats: Dict[int, int]) -> List[int]

models the column-format-resolution step the gold patch wires into the HTML
writer (`self.data.cols = cols; self.data._set_col_formats()`). Per output
column i it returns the *resolved* format token:

    Result()[i] == formats[names[i]]   if names[i] in formats   (override)
    Result()[i] == prior_formats[i]    otherwise                (untouched)

ALL THREE inputs are READ-ONLY: Requires(Acc(list_pred(names), 1/2)),
Acc(list_pred(prior_formats), 1/2), Acc(dict_pred(formats), 1/2) — and the
postcondition GIVES BACK exactly those half-permissions
(Ensures(Acc(..., 1/2))). So the frame-mutation attack (directive 5) APPLIES and
is MANDATORY: an impl that writes to any of the three inputs to satisfy a
postcondition vacuously must be REJECTED for insufficient permission.

The load-bearing postcondition clauses (model.py:82-93)
-------------------------------------------------------
  (P1) len(Result()) == len(names)
  (P2) Forall i in [0,len): Result()[i] == resolved_format(names[i],
                                            prior_formats[i], formats)
  (P3) Forall i: names[i] in formats  =>  Result()[i] == formats[names[i]]
       — the DISCRIMINATING clause (present name -> SUPPLIED spec); this is what
         senses the gold change (model_prepatch keeps prior and FAILS it).
  (P4) Forall i: names[i] not in formats  =>  Result()[i] == prior_formats[i]
       — absent name -> PRIOR spec (untouched column).

The @Pure oracle `resolved_format` is GROUNDED, not an answer-key
----------------------------------------------------------------
`resolved_format(name, prior, formats)` is a TOTAL function of the args, fully
unfolded in the contract (`if name in formats: return formats[name]; return
prior`). The postcondition pins Result()[i] to it AND to the two concrete
re-pins P3/P4. There is therefore NO opaque oracle an impl could echo WITHOUT
doing the work — echoing `resolved_format(names[i], prior_formats[i], formats)`
IS the correct answer, and any echo that disagrees with P3/P4 is rejected. Hence
ungrounded-oracle ECHO does not apply (directive 2): instead we supply an honest
cheapest-correct positive control (the per-element echo via a local) which MUST
verify. This is stated in the StructuredOutput assessment.

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
`resolve_column_formats` is total over its precondition domain (it never raises
and has no side effect other than building the fresh result list). The real
callee's only extra effect — the validating `Column.format` setter raising
`ValueError` on a dtype-incompatible selected spec — is OUTSIDE the modeled
resolution decision and is documented as the GUARDED A-reference boundary
(mapping.md §3.1, axiom_check.py raise-boundary probe). It is exercised in the
AXIOM lane below, not as a spec capability-token rival. The control-flow-effect
class therefore does not apply to the SPEC lane; stated in 'assessment'.

Axiom lane
----------
meta.axioms == [] (NO @ContractOnly axiom). The single soundness obligation is
the A-reference: the deep model (`resolved_format` / the loop) == the real
`BaseData._set_col_formats` selection on format/dtype-compatible inputs (the
F2P/P2P domain), with the dtype-incompatible raise boundary positively asserted.
The AXIOM_TESTS reuse + strengthen axiom_check.py: (1) axiom-soundness drives the
GENUINE astropy `_set_col_formats` on real int+float Columns and asserts the
resolved `info.format` matches the model on the compatible domain AND that the
documented raise boundary fires on a dtype-incompatible selected spec; (2)
axiom-containment confirms every callee-input the MODEL can reach (a name in/out
of the mapping over dtype-compatible specs) lies in the callee's no-raise domain.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY text inside `resolve_column_formats`'s `# impl-start` /
`# impl-end` body (the loop body or the result-construction shape), so
`markers.same_spec` is GUARANTEED and a rejection is attributable to the
POSTCONDITION / the permission system catching wrong behaviour, never to a
tampered spec. The gold invariants are kept VERBATIM in every variant so a reject
is never a mislabeled proof gap. Each `expect:"reject"` rival carries the
refinement argument that its faithful real patch would NOT resolve the F2P/P2P.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13453"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors inside resolve_column_formats's impl region (each unique in model.py).
# The loop body (after the invariants block) is the resolution step:
# ---------------------------------------------------------------------------

# The gold loop body (text strictly after `# invariants-end`, before `i = i + 1`).
_GOLD_BODY = """        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Branch-REORDER positive control. Test the absent-name case first and the
# present-name case second — a structurally different control shape that is
# semantically identical to gold. The gold invariants are kept VERBATIM, so the
# loop-invariant proof obligation
# (result[k] == resolved_format(names[k], prior_formats[k], formats)) is
# discharged exactly as before; only the executable branch ORDER changes. If this
# CORRECT impl fails to verify, the postcondition is over-fit to the gold branch
# order => SPEC-TOO-STRONG.
_POS_REORDER_BODY = """        name = names[i]
        if not (name in formats):
            result.append(prior_formats[i])
        else:
            result.append(formats[name])
        i = i + 1"""
_POS_REORDER = _swap(_BASE, _GOLD_BODY, _POS_REORDER_BODY)

# (5b) LOCAL-RESHAPE positive control. Compute the resolved token into a typed
# local `chosen` first, then append it once (a single append site instead of two
# branch-local appends). Same behaviour, different data shape. Invariants kept
# verbatim. If it fails => SPEC-TOO-STRONG (over-fit to the two-append form).
_POS_LOCAL_BODY = """        name = names[i]
        chosen = prior_formats[i]  # type: int
        if name in formats:
            chosen = formats[name]
        result.append(chosen)
        i = i + 1"""
_POS_LOCAL = _swap(_BASE, _GOLD_BODY, _POS_LOCAL_BODY)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped in-domain input must establish
# the precondition (two index-aligned lists of equal length + a Dict, all under
# half-permission) and return a contract-satisfying result. We replace the impl
# body with a single self-call on the SAME in-scope inputs (names, prior_formats,
# formats) and return its result. The caller holds Acc(...,1/2) of each and
# `len(names) == len(prior_formats)` (its own precondition, in scope), which is
# EXACTLY the callee's Requires; the self-call consumes those half-permissions and
# the callee's Ensures GIVES THEM BACK. We Assert the probe's length to pin that
# the call site succeeded, then return the probe — its Ensures transitively
# re-establishes this function's own postcondition. If the call site cannot
# establish the Requires for a legitimate input => PRECOND-TOO-STRONG.
#
# NOTE (why the self-call must REPLACE the loop, not PRECEDE it): the frozen
# postcondition correctly does NOT restate input-length preservation
# (`len(names) == len(prior_formats)` is the caller's precondition, not an output
# guarantee — the function reads inputs under half-permission and returns a FRESH
# list). When the half-permissions are handed to the callee and returned, Nagini
# havocs `len(names)` (no Ensures pins it). A self-call PREPENDED before the gold
# loop would therefore poison the loop-entry invariant
# `Invariant(len(names) == len(prior_formats))` — a PROOF artifact of the
# permission round-trip, NOT a precondition defect. Delegating the whole body to
# the self-call exercises the precondition AND the postcondition faithfully
# without that spurious interaction, while keeping `markers.same_spec` (only the
# impl region changes).
_IMPL_BODY_ANCHOR = """    result = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(prior_formats), 1 / 2))
        Invariant(Acc(dict_pred(formats), 1 / 2))
        Invariant(len(names) == len(prior_formats))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i
            and k < len(prior_formats),
            result[k] == resolved_format(names[k], prior_formats[k], formats)))))
        # invariants-end
        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1
    return result"""
_ADMISS_BODY = (
    "    _probe = resolve_column_formats(names, prior_formats, formats)\n"
    "    Assert(len(_probe) == len(names))\n"
    "    return _probe"
)
_ADMISS = _swap(_BASE, _IMPL_BODY_ANCHOR, _ADMISS_BODY)


# ===========================================================================
# UNIQUENESS / FRAME-MUTATION RIVALS (must be REJECTED)
# ===========================================================================

# (FRAME-MUTATION — MANDATORY, directive 5) Instead of building a fresh result
# list, the rival WRITES the selected spec back onto the read-only input
# `prior_formats[i]` (mutating the caller's column-format array in place) and then
# appends from it. To assign `prior_formats[i] = ...` Nagini needs FULL permission
# on `prior_formats`, but the precondition grants only Acc(list_pred(prior_formats),
# 1/2). The write is therefore REJECTED for INSUFFICIENT PERMISSION — before any
# postcondition is even considered. The gold invariants/structure are kept
# VERBATIM so the rejection is attributable solely to the write.
#
# Refinement (why its faithful real patch would NOT resolve): the read-only
# half-permission abstracts the gold patch's contract that the resolution step
# READS each column's prior `info.format` and the supplied `self.formats` and
# leaves the input column array's identity/length untouched (it sets each
# selected column's `info.format`, but the model carries the per-column resolved
# token in a fresh aligned list — mapping.md §2/§A4). A real "patch" that, to
# resolve a column, overwrote the *prior_formats* carrier (e.g. clobbered another
# column's pre-existing format, or mutated the shared input array aliased
# elsewhere) would corrupt columns whose names are ABSENT from the mapping —
# breaking P2P `test_write_table_html_fill_values` (absent-name columns must keep
# their prior format) — so it would NOT resolve. The half-permission is exactly
# the spec defending that read-only contract.
_RIVAL_FRAME_MUTATE_BODY = """        name = names[i]
        if name in formats:
            prior_formats[i] = formats[name]
        result.append(prior_formats[i])
        i = i + 1"""
_RIVAL_FRAME_MUTATE = _swap(_BASE, _GOLD_BODY, _RIVAL_FRAME_MUTATE_BODY)

# (uniqueness — PRE-PATCH bug) The rival ALWAYS appends the prior format and never
# consults the mapping — exactly model_prepatch.py (the pre-patch HTML writer that
# never calls _set_col_formats, so every column keeps its prior format). It
# satisfies P1, P4 and the loop length invariant, but VIOLATES P3 (and P2) on any
# column whose name is in the mapping.
#
# Refinement: this IS the pre-patch behaviour; its faithful real patch is the
# unmodified HTML.write (no `self.data.cols = cols` / no `_set_col_formats()`
# call), under which the F2P `test_write_table_formatted_columns` renders C1 as
# `1` / `2` instead of `0001` / `0002` and C2 unformatted instead of `1.23e-11` —
# the test FAILS. It would NOT resolve (this is precisely the bug the patch fixes,
# G-DIFF).
_RIVAL_PREPATCH_BODY = """        name = names[i]
        result.append(prior_formats[i])
        i = i + 1"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_BODY, _RIVAL_PREPATCH_BODY)

# (uniqueness — VALUE double-mask / proxy) On a present name the rival appends the
# prior format's value only when it happens to EQUAL the supplied spec, else it
# appends the supplied spec — but it reads the wrong source on the present branch
# by appending `formats[name]` UNLESS prior already differs. Concretely: it pins
# the override only via the proxy `prior_formats[i]` when name present and the two
# coincide, dropping the genuine override when they differ. We realise this as the
# subtle bug "present -> use prior when prior == supplied, else supplied" which is
# equivalent to gold; the WRONG variant that the spec must reject is the one that
# on a present name appends the prior ONLY (covered by rival-prepatch). To keep a
# DISTINCT well-defined rival we use: absent-name correctly keeps prior, but a
# present name appends `formats[name]` for i even, and `prior_formats[i]` for i
# odd — a value-proxy that masks the override on odd-indexed present columns.
_RIVAL_PROXY_MASK_BODY = """        name = names[i]
        if (name in formats) and (i % 2 == 0):
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1"""
_RIVAL_PROXY_MASK = _swap(_BASE, _GOLD_BODY, _RIVAL_PROXY_MASK_BODY)

# (uniqueness — PARTIAL-DOMAIN, first element) The rival is CORRECT on every
# column except column 0: for i == 0 it always appends the prior format (ignoring
# the mapping), for i > 0 it resolves correctly. It diverges ONLY on the first
# column sub-domain.
#
# Refinement: its faithful real patch is a _set_col_formats that skips the first
# column of `self.cols` (e.g. `for col in self.cols[1:]`). Under it the F2P
# `test_write_table_formatted_columns` — whose FIRST column C1 carries the
# supplied `"04d"` and must render `0001`/`0002` — renders C1 as `1`/`2`, so the
# exact-HTML assertion FAILS. It would NOT resolve. Rejection source: P3/P2 at
# i == 0 (when names[0] in formats).
_RIVAL_SKIP_FIRST_BODY = """        name = names[i]
        if i > 0 and (name in formats):
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1"""
_RIVAL_SKIP_FIRST = _swap(_BASE, _GOLD_BODY, _RIVAL_SKIP_FIRST_BODY)

# (uniqueness — PARTIAL-DOMAIN, last element / length-off-by-one) The rival
# resolves correctly but DROPS the last column (loop runs to len-1), producing a
# result one element short. It satisfies P2/P3/P4 element-wise on the indices it
# DOES emit, but violates P1 (len(Result()) == len(names)). This targets the
# length clause specifically.
#
# Refinement: its faithful real patch is a writer that resolves all but the final
# output column (e.g. an off-by-one over `self.cols`); the rendered HTML would be
# missing the last column's formatted cell — the F2P/P2P exact-output assertions
# FAIL. It would NOT resolve. Rejection source: P1, len(Result()) == len(names)
# (model.py:80), and the loop-exit invariant len(result) == i with i == len(names).
_RIVAL_DROP_LAST_BODY = """        name = names[i]
        if i + 1 < len(names):
            if name in formats:
                result.append(formats[name])
            else:
                result.append(prior_formats[i])
        i = i + 1"""
_RIVAL_DROP_LAST = _swap(_BASE, _GOLD_BODY, _RIVAL_DROP_LAST_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl (absent-name branch tested "
                  "first, present-name second) with the gold loop invariants kept verbatim "
                  "must verify; if not, the postcondition is over-fit to the gold branch "
                  "order => SPEC-TOO-STRONG."},
    {"id": "pos-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_LOCAL,
     "rationale": "structurally-different but CORRECT impl (resolved token computed into a "
                  "typed local `chosen` then appended once, instead of two branch-local "
                  "appends); invariants verbatim. Must verify, else the spec is over-fit to "
                  "the two-append code form => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call resolve_column_formats(names, prior_formats, formats) on the "
                  "in-scope F2P-shaped input (two index-aligned lists, a Dict, all under the "
                  "half-permissions the caller holds and the callee Ensures back) must "
                  "establish the precondition and return a len(names)-long list; if the call "
                  "site cannot establish the Requires for a legitimate input => "
                  "PRECOND-TOO-STRONG."},

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {"id": "rival-frame-mutate-prior", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_MUTATE,
     "refinement": "WRITES the selected spec back onto the read-only input "
                   "prior_formats[i] (mutating the caller's column-format carrier in place) "
                   "then appends from it. The half-permission Acc(list_pred(prior_formats), "
                   "1/2) abstracts the gold contract that resolution READS each column's "
                   "prior info.format and the supplied self.formats and does not clobber the "
                   "input array (the resolved tokens live in a fresh aligned carrier, "
                   "mapping.md §A4). A real patch that overwrote the prior-format carrier in a "
                   "way visible to aliases / other columns would corrupt absent-name columns "
                   "and break P2P test_write_table_html_fill_values (untouched columns must "
                   "keep their prior format) — so it would NOT resolve.",
     "rationale": "FRAME-MUTATION (directive 5). Rejection source: the PERMISSION SYSTEM — "
                  "assigning prior_formats[i] needs full Acc(list_pred(prior_formats)) but the "
                  "precondition grants only 1/2, so the write fails for INSUFFICIENT "
                  "PERMISSION before any postcondition is considered. If it verified, a "
                  "mutating impl could satisfy the postcondition vacuously => SPEC-TOO-WEAK."},
    {"id": "rival-prepatch-keep-prior", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "ALWAYS keeps the prior format and never consults the mapping — exactly "
                   "model_prepatch.py (the pre-patch HTML writer that never sets "
                   "self.data.cols nor calls _set_col_formats). Its faithful real patch is the "
                   "unmodified HTML.write, under which the F2P test_write_table_formatted_columns "
                   "renders C1 as 1/2 (not 0001/0002) and C2 unformatted (not 1.23e-11): the "
                   "exact-HTML assertion FAILS. It would NOT resolve (this is the bug the patch "
                   "fixes, G-DIFF).",
     "rationale": "Rejection source: the DISCRIMINATING clause P3 "
                  "Implies(names[i] in formats, Result()[i] == formats[names[i]]) "
                  "(model.py:87-89) and P2; violated on any column whose name is in the "
                  "mapping. If it verified => SPEC-TOO-WEAK (admits the pre-patch keep-prior "
                  "bug)."},
    {"id": "rival-proxy-mask-odd-present", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PROXY_MASK,
     "refinement": "VALUE-double-mask / partial-domain: a present name is overridden to the "
                   "supplied spec only on EVEN indices; on an ODD-indexed present column it "
                   "keeps the prior format (the override is masked). Its faithful real patch "
                   "is a _set_col_formats that conditions the assignment on a column-position "
                   "proxy (e.g. only overrides every other column), so a present-name column "
                   "at an odd position is NOT overridden — the F2P/P2P exact-HTML output "
                   "differs and the test FAILS. It would NOT resolve.",
     "rationale": "Rejection source: P3 Implies(names[i] in formats, "
                  "Result()[i] == formats[names[i]]) (model.py:87-89), violated on the "
                  "odd-indexed present sub-domain (there Result()[i] == prior_formats[i] != "
                  "formats[names[i]] whenever they differ). If it verified => SPEC-TOO-WEAK "
                  "(the override is masked on a sub-domain)."},
    {"id": "rival-skip-first-column", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SKIP_FIRST,
     "refinement": "PARTIAL-DOMAIN (first element): correct on every column except column 0, "
                   "for which it always keeps the prior format (ignores the mapping). Its "
                   "faithful real patch is a _set_col_formats that skips the first output "
                   "column (`for col in self.cols[1:]`). Under it the F2P "
                   "test_write_table_formatted_columns — whose FIRST column C1 carries the "
                   "supplied 04d and must render 0001/0002 — renders C1 as 1/2, so the "
                   "exact-HTML assertion FAILS. It would NOT resolve.",
     "rationale": "partial-domain on the i==0 sub-domain. Rejection source: P2/P3 at i==0 "
                  "(when names[0] in formats), Result()[0] == formats[names[0]] "
                  "(model.py:82-89). If it verified => SPEC-TOO-WEAK (drops the first "
                  "column's override)."},
    {"id": "rival-drop-last-column", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_LAST,
     "refinement": "PARTIAL-DOMAIN (length): resolves all emitted columns correctly but DROPS "
                   "the final column, returning a list one element short. Its faithful real "
                   "patch is a writer that resolves all but the last output column (off-by-one "
                   "over self.cols); the rendered HTML is missing the last column's formatted "
                   "cell and the F2P/P2P exact-output assertions FAIL. It would NOT resolve.",
     "rationale": "Rejection source: P1 len(Result()) == len(names) (model.py:80) — the "
                  "loop-exit invariant len(result) == i with i == len(names) cannot hold when "
                  "the last index is skipped. If it verified => SPEC-TOO-WEAK (length not "
                  "pinned)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real astropy callee) — the A-reference soundness +
# containment obligation. meta.axioms == [] (NO @ContractOnly axiom); the single
# soundness obligation is the deep model == real BaseData._set_col_formats on the
# format/dtype-compatible domain, with the documented raise boundary positively
# asserted. These reuse + strengthen axiom_check.py (which the runner does NOT
# mount in-container, so the probes are SELF-CONTAINED).
# ===========================================================================

# (axiom-soundness) Drive the GENUINE astropy BaseData._set_col_formats on real
# int AND float Column objects and assert, on the format/dtype-COMPATIBLE domain
# (exactly what F2P/P2P exercise), that each column's resolved info.format equals
# the model's resolution (formats[name] if name present else prior). Then
# positively assert the documented RAISE BOUNDARY: a float column with an
# int-only selected spec drives the validating Column.format setter to raise
# ValueError AT ASSIGNMENT inside _set_col_formats. Exit 0 iff the model matches
# on the compatible domain AND the raise boundary fires.  No patch needed: the
# A-reference callee (_set_col_formats, core.py:934-938) is UNCHANGED by the gold
# patch — it exists identically at base_commit.  Self-contained (stdlib + astropy
# only); file reads use encoding="utf-8" (container locale is ASCII).
_AX_SOUNDNESS = r'''
import random
import sys


def model_resolve(names, prior_formats, formats):
    """Reference of model.py's resolve_column_formats loop (token-level)."""
    out = []
    for i in range(len(names)):
        nm = names[i]
        out.append(formats[nm] if nm in formats else prior_formats[i])
    return out


def main():
    try:
        from astropy.io.ascii.core import BaseData
        from astropy.table import Column
    except ImportError as exc:
        print("AXIOM probe: astropy not importable (%r) — cannot run the REAL "
              "callee; this lane MUST run in the instance image" % (exc,))
        return 1

    def norm(x):
        return None if x in ("", None) else x

    # specs that render cleanly on each dtype ('i' = int col, 'f' = float col)
    compat_specs = {
        "i": ["", "04d", "%d", "6d", "+05d"],
        "f": ["", ".2e", ".3f", "10.4g", "+.1f"],
    }

    def make_col(kind, nm, spec):
        data = [1, 2] if kind == "i" else [1.234567e-11, -9.876543e11]
        c = Column(data=data, name=nm)
        c.info.format = spec if spec else None
        return c

    def renders_ok(col):
        try:
            list(col.info.iter_str_vals())
            return True
        except Exception:
            return False

    rng = random.Random(2013453)
    kinds = ["i", "f"]
    compat_checks = 0
    for _ in range(2000):
        n = rng.randint(0, 6)
        col_names, col_kinds, prior_specs = [], [], []
        seen = set()
        for _c in range(n):
            nm = "C%d" % rng.randint(0, 5)
            if nm in seen:          # real Tables have unique column names
                continue
            seen.add(nm)
            k = rng.choice(kinds)
            col_names.append(nm)
            col_kinds.append(k)
            prior_specs.append(rng.choice(compat_specs[k]))

        name_kind = dict(zip(col_names, col_kinds))
        formats_str = {}
        for _k in range(rng.randint(0, 4)):
            nm = "C%d" % rng.randint(0, 5)
            k = name_kind.get(nm, rng.choice(kinds))
            formats_str[nm] = rng.choice(compat_specs[k])

        cols = [make_col(k, nm, ps)
                for nm, k, ps in zip(col_names, col_kinds, prior_specs)]

        data = BaseData()
        data.cols = cols
        data.formats = dict(formats_str)
        data._set_col_formats()                         # the REAL callee

        # Model resolution per column (token-level: the normalised spec string IS
        # the token; norm() makes ""/None coincide). model_resolve gives the same
        # value as `formats_str[nm] if nm present else prior` — asserted directly:
        names_tok = [norm(nm) for nm in col_names]
        prior_tok = [norm(ps) for ps in prior_specs]
        fmt_tok = {norm(nm): norm(v) for nm, v in formats_str.items()}
        model_out = model_resolve(names_tok, prior_tok, fmt_tok)
        for nm, ps, col, m in zip(col_names, prior_specs, cols, model_out):
            expected = norm(formats_str[nm] if nm in formats_str else ps)
            assert m == expected, "self-consistency: model_resolve != hand expectation"
            got = norm(col.info.format)
            if got != expected:
                print("AXIOM-UNSOUND: real _set_col_formats mismatch for col %r: "
                      "prior=%r formats=%r -> real=%r model=%r"
                      % (nm, ps, formats_str, got, expected))
                return 1
            if not renders_ok(col):
                print("AXIOM-UNSOUND: compatible-domain render failed for col %r "
                      "with resolved format %r" % (nm, norm(col.info.format)))
                return 1
        compat_checks += 1

    # RAISE BOUNDARY: float column, mapping selects an int-only spec. The model is
    # total (returns the selected token); the real validating Column.format setter
    # rejects it and _set_col_formats raises AT ASSIGNMENT.
    raise_checks = 0
    for _ in range(200):
        nm = "C0"
        float_col = make_col("f", nm, "")
        bad_spec = rng.choice(["04d", "6d", "+05d", "d"])    # int-only formats
        data = BaseData()
        data.cols = [float_col]
        data.formats = {nm: bad_spec}
        raised = False
        try:
            data._set_col_formats()
        except (ValueError, TypeError):
            raised = True
        if not raised:
            print("AXIOM boundary WRONG: expected real _set_col_formats to RAISE on "
                  "int-only spec %r on a float column, but it did not" % bad_spec)
            return 1
        raise_checks += 1

    print("AXIOM-SOUND: deep format-resolution model == real BaseData._set_col_formats "
          "selection on %d compatible-domain cases (int+float columns, each resolved "
          "spec also renders) + %d positive raise-boundary probes (float col, int-only "
          "spec, validating Column.format setter raises at assignment => GUARDED equality)"
          % (compat_checks, raise_checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# (axiom-containment) Every callee-input the MODEL can REACH lies in the real
# callee's no-raise domain. The model's reachable callee-inputs are: a column
# whose name is IN the mapping (-> overridden to the supplied spec) and a column
# whose name is ABSENT (-> kept). On the format/dtype-COMPATIBLE domain (the only
# domain the modeled equality claims — mapping.md §3.1) both branches must be
# handled by the real _set_col_formats WITHOUT raising. We enumerate witnesses for
# each reachable branch over BOTH dtypes and confirm no raise. Covering MORE than
# the caller reaches (the dtype-incompatible specs, which raise) is SOUND and is
# the documented boundary, not a containment defect. A reachable compatible-domain
# input the callee could not handle => AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import sys


def main():
    try:
        from astropy.io.ascii.core import BaseData
        from astropy.table import Column
    except ImportError as exc:
        print("CONTAINMENT probe: astropy not importable (%r) — must run in image"
              % (exc,))
        return 1

    def make_col(kind, nm, spec):
        data = [1, 2] if kind == "i" else [1.234567e-11, -9.876543e11]
        c = Column(data=data, name=nm)
        c.info.format = spec if spec else None
        return c

    # The reachable callee-inputs of the model, each a (kind, prior_spec,
    # mapping_for_this_name) witness over the format/dtype-COMPATIBLE domain:
    #   - name PRESENT, compatible selected spec -> override branch
    #   - name ABSENT (empty mapping)            -> keep branch
    #   - prior spec set vs unset
    reachable = [
        # (col_kind, prior_spec, formats_for_name)  formats_for_name None => absent
        ("i", "",    "04d"),     # present override, int col, no prior
        ("i", "%d",  "+05d"),    # present override, int col, prior set
        ("i", "04d", None),      # absent keep, int col
        ("f", "",    ".2e"),     # present override, float col, no prior
        ("f", ".3f", "10.4g"),   # present override, float col, prior set
        ("f", ".2e", None),      # absent keep, float col
    ]
    checked = 0
    for kind, prior, sel in reachable:
        nm = "C0"
        col = make_col(kind, nm, prior)
        data = BaseData()
        data.cols = [col]
        data.formats = {} if sel is None else {nm: sel}
        try:
            data._set_col_formats()                 # must not raise on compat domain
        except Exception as exc:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable compatible-domain input "
                  "(kind=%r prior=%r sel=%r) is OUTSIDE the callee no-raise domain "
                  "(raised %r)" % (kind, prior, sel, exc))
            return 1
        checked += 1

    print("CONTAINMENT OK: every reachable model callee-input over the "
          "format/dtype-compatible domain (present-override + absent-keep, int and "
          "float columns) is handled by the real BaseData._set_col_formats without "
          "raising (%d witnesses). The dtype-incompatible raise boundary is OUTSIDE "
          "the caller-reachable compatible domain by design (guarded equality), not "
          "a containment defect." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-resolution-sound", "axiom": "set_col_formats_deep_model",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": False,
     "probe": _AX_SOUNDNESS,
     "rationale": "the bundle's single soundness obligation: the deep "
                  "format-resolution model (resolved_format / the loop) must equal the REAL "
                  "BaseData._set_col_formats selection on the format/dtype-compatible domain "
                  "(int AND float Columns, each resolved spec also rendering cleanly), with "
                  "the documented dtype-incompatible RAISE boundary positively asserted. The "
                  "callee is UNCHANGED by the patch (apply_gold=False). Any mismatch on the "
                  "compatible domain or a missing raise => the A-reference is UNSOUND."},
    {"id": "ax-resolution-containment", "axiom": "set_col_formats_deep_model",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": False,
     "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach over the compatible domain "
                  "(present-override + absent-keep, int and float columns) lies in the real "
                  "callee's no-raise domain; the dtype-incompatible raise boundary is outside "
                  "the caller-reachable compatible domain (guarded equality, mapping.md §3.1), "
                  "which is SOUND over-coverage, not AXIOM-TOO-WEAK-FOR-CALLER."},
]
