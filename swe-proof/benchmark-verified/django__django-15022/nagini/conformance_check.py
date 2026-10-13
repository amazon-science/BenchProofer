#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15022 (nagini).

SHADOW: the impl region of model.py's ``search_retains_object``, copied
VERBATIM below with only the contract calls (Invariant / Assert; there are no
Requires / Ensures statements inside the impl region) stripped. The @Pure
helpers ``row_matches_all`` / ``some_row_matches_all`` copy over as plain
functions on top of a small immutable tuple-backed PSeq shim and serve as an
internal cross-check of the executable shadow. The single @ContractOnly
symbol, ``matches(row, term)``, is an UNINTERPRETED relation (mapping.md
section 1 / refinement.md step A3): it stands for the per-(related-row,
search-term) truth of one per-term OR-query, an operation the change leaves
untouched. Its "real" counterpart is therefore the per-pair truth that the
oracle's database rows materialize: each probe constructs the related rows so
that the REAL ORM lookup (token containment on a searched text field) holds
for exactly the (row, term) pairs the abstract matrix says, and the shadow's
``matches`` reads that same matrix. The materialization itself is validated
against the real lookup semantics on the first batch (see
``_validate_materialization``).

ORACLE: the REAL patched repo method the model models per mapping.md
section 1 — ``django.contrib.admin.options.ModelAdmin.get_search_results``.
The gate applies patch.diff to /testbed and sets PYTHONPATH=/testbed before
this script runs, so the import resolves to the patched module. Each probe:
one candidate (Parent) object, one related row (Child) per abstract row, the
Child's searched text field holding one opaque token per term that row
matches; ``search_fields = ["children__tag"]`` names the multi-valued
relation; the search term is the space-joined token list, so smart_split
yields exactly one bit per abstract term and each bit's OR-query truth
against one Child row is exactly the matrix entry. The candidate's retention
is observed as membership of its pk in the returned queryset. Probes sharing
a term sequence are batched (many independent candidates per
``get_search_results`` call): retention is per-candidate — each candidate's
join rows are its own children — so batching is sound and keeps >=1e5 probes
fast.

TYPE BRIDGE (mapping.md section 2): ``terms`` / ``rows`` are ``PSeq[int]`` of
opaque identifiers; only their cardinality and the per-pair ``matches`` truth
are observable. Term id t <-> the search bit carrying token "q<t>q"; row id r
<-> one Child row. The tokens are pairwise substring-free and contain no
whitespace, quotes, or LIKE wildcards, so tokenization and containment are
exact. The model's boolean result <-> the candidate's membership in the
returned queryset (refinement.md step A5).

INPUT DOMAIN: the precondition is empty, but the mapping binds ``terms`` to
the bits of an actually-performed search (mapping.md section 1: the modelled
body only runs for a non-empty term list; axiom_check.py fixes the same
n_terms >= 1 domain), so probes use len(terms) >= 1 and any number of related
rows including zero. Duplicate term ids in the sequence (a repeated search
bit) and rows carrying extra non-searched noise tokens are probed explicitly.

>= 1e5 Requires-satisfying inputs: exhaustive match matrices up to 3 rows x
4 terms (5054), boundary cases (repeated bits, noise tokens, all-True /
all-False / diagonal shapes), plus 95000 random matrices over rows 0..6 x
terms 1..6 at mixed densities. Pinned fuzz seed: 15022 (recorded in
mapping.md). Exit 0 iff zero disagreements; on disagreement prints the match
matrix, the term sequence, and both outputs, then exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15022
N_FUZZ = 95000
BATCH = 500
TOK = "q%dq"          # opaque per-term token; qNq is never a substring of qMq


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- the @ContractOnly relation, realized by the probe's materialized data ---
# CURRENT_MATRIX[r][t] is the per-(row, term-id) truth the database rows of
# the probe under test materialize (token t present in row r's searched
# field); the shadow reads the relation from here, the oracle reads it
# through the real ORM lookup over the same data.

CURRENT_MATRIX = []


def matches(row, term):
    return CURRENT_MATRIX[row][term]


# --- pure region of model.py, copied as plain functions (cross-check) --------

def row_matches_all(row, terms):
    if len(terms) == 0:
        return True
    return matches(row, terms[0]) and row_matches_all(row, terms.drop(1))


def some_row_matches_all(rows, terms):
    if len(rows) == 0:
        return False
    return row_matches_all(rows[0], terms) or \
        some_row_matches_all(rows.drop(1), terms)


# --- impl region of model.py, verbatim with contract calls stripped ----------

def search_retains_object(rows, terms):
    retained = False
    i = len(rows)
    while i > 0:
        row = rows[i - 1]
        all_clear = True
        j = len(terms)
        while j > 0:
            term = terms[j - 1]
            if not matches(row, term):
                all_clear = False
            j = j - 1
        if all_clear:
            retained = True
        i = i - 1
    return retained


# --- oracle: the real patched ModelAdmin.get_search_results ------------------

class Oracle(object):
    """Runs the REAL (patched) get_search_results against an in-memory
    sqlite database; one Parent per probe, one Child per abstract row."""

    def __init__(self):
        import types

        import django
        from django.conf import settings

        # Stub app module so the probe models' app is INSTALLED: without an
        # installed app, apps.get_models() never yields Child, so Parent's
        # reverse relation tree would miss the multi-valued relation.
        mod = types.ModuleType("confcheck")
        mod.__path__ = ["/tmp/sbu_confcheck_app"]  # no models submodule
        sys.modules.setdefault("confcheck", mod)

        if not settings.configured:
            settings.configure(
                DEBUG=True,
                DATABASES={"default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }},
                INSTALLED_APPS=[
                    "django.contrib.contenttypes",
                    "django.contrib.auth",
                    # Simple config: no admin autodiscovery at setup
                    "django.contrib.admin.apps.SimpleAdminConfig",
                    "confcheck",
                ],
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
                USE_TZ=True,
            )
        django.setup()

        from django.contrib.admin import AdminSite, ModelAdmin
        from django.db import connection, models

        class Parent(models.Model):
            name = models.CharField(max_length=64)

            class Meta(object):
                app_label = "confcheck"

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.CASCADE,
                                       related_name="children")
            tag = models.CharField(max_length=512)

            class Meta(object):
                app_label = "confcheck"

        with connection.schema_editor() as editor:
            editor.create_model(Parent)
            editor.create_model(Child)

        class ParentAdmin(ModelAdmin):
            # the multi-valued relation the search spans (mapping.md sec. 1)
            search_fields = ["children__tag"]

        self.Parent = Parent
        self.Child = Child
        self.admin = ParentAdmin(Parent, AdminSite())
        self._next_pk = 1

    def _tag(self, rowbits, noise):
        toks = [TOK % t for t, hit in enumerate(rowbits) if hit]
        if noise:
            # non-searched noise: a near-collision token (never searched
            # while term ids stay small) plus plain filler words
            toks += [TOK % 997, "zz", "plain filler"]
        return " ".join(toks)

    def run_batch(self, term_seq, cases, noise=False):
        """cases: list of match matrices (rows x distinct-term-ids booleans)
        all sharing the search-bit sequence `term_seq` (ids, may repeat).
        Returns the list of per-candidate real retention booleans."""
        Parent, Child = self.Parent, self.Child
        Child.objects.all().delete()
        Parent.objects.all().delete()
        parents = []
        for matrix in cases:
            parents.append(Parent(pk=self._next_pk, name="c%d" % self._next_pk))
            self._next_pk += 1
        Parent.objects.bulk_create(parents)
        children = []
        for parent, matrix in zip(parents, cases):
            for rowbits in matrix:
                children.append(Child(parent_id=parent.pk,
                                      tag=self._tag(rowbits, noise)))
        Child.objects.bulk_create(children)
        search_term = " ".join(TOK % t for t in term_seq)
        qs, _dups = self.admin.get_search_results(
            None, Parent.objects.all(), search_term)
        retained = set(qs.values_list("pk", flat=True))
        return [p.pk in retained for p in parents]


def _validate_materialization(oracle):
    """One-time check that the token encoding realizes the abstract matrix
    exactly under the REAL per-row lookup: for every (row, term) pair of a
    probe matrix, containment of the term's token in the row's searched field
    equals the matrix entry (including with noise tokens present)."""
    matrix = [[True, False, True], [False, True, False], [False, False, False]]
    for noise in (False, True):
        oracle.Child.objects.all().delete()
        oracle.Parent.objects.all().delete()
        p = oracle.Parent.objects.create(pk=oracle._next_pk, name="v")
        oracle._next_pk += 1
        kids = [oracle.Child.objects.create(parent_id=p.pk,
                                            tag=oracle._tag(rb, noise))
                for rb in matrix]
        for r, kid in enumerate(kids):
            for t in range(3):
                real = oracle.Child.objects.filter(
                    pk=kid.pk, tag__icontains=TOK % t).exists()
                if real != matrix[r][t]:
                    print("MATERIALIZATION DEFECT: row %d term %d noise=%r: "
                          "lookup=%r matrix=%r (tag=%r)"
                          % (r, t, noise, real, matrix[r][t], kid.tag))
                    return False
    return True


# --- input generation ---------------------------------------------------------

def exhaustive_cases():
    """Every match matrix with 0..3 rows and 1..4 term ids (5054 matrices),
    term sequence = the identity over the ids."""
    out = []
    for n_rows in range(0, 4):
        for n_terms in range(1, 5):
            for code in range(2 ** (n_rows * n_terms)):
                matrix = []
                for r in range(n_rows):
                    matrix.append(tuple(
                        bool((code >> (r * n_terms + t)) & 1)
                        for t in range(n_terms)))
                out.append((tuple(range(n_terms)), tuple(matrix), False))
    return out


def boundary_cases():
    """Shapes worth pinning: repeated search bits, noise-token rows, and the
    quantifier-swap witnesses (every term covered but by different rows)."""
    T = tuple
    cases = [
        # repeated bits: same term id appearing several times in the sequence
        (T([0, 0]), T([T([True]), T([False])]), False),
        (T([0, 0, 1]), T([T([True, False]), T([False, True])]), False),
        (T([1, 0, 1]), T([T([True, True])]), False),
        (T([0, 0, 0]), T([]), False),
        # swap witnesses: each column covered, no row clears all columns
        (T([0, 1]), T([T([True, False]), T([False, True])]), False),
        (T([0, 1, 2]),
         T([T([True, False, True]), T([False, True, True])]), False),
        # one row clears everything among distractors
        (T([0, 1]), T([T([True, False]), T([True, True])]), False),
        # all-True / all-False blocks, single cells, zero rows
        (T([0, 1, 2, 3]), T([T([True] * 4), T([True] * 4)]), False),
        (T([0, 1, 2, 3]), T([T([False] * 4)]), False),
        (T([0]), T([T([True])]), False),
        (T([0]), T([T([False])]), False),
        (T([0, 1, 2]), T([]), False),
        # diagonal / anti-diagonal over 4x4
        (T(range(4)),
         T([T([r == t for t in range(4)]) for r in range(4)]), False),
        (T(range(4)),
         T([T([r != t for t in range(4)]) for r in range(4)]), False),
    ]
    # every shape again with non-searched noise tokens in every row's field
    cases += [(seq, matrix, True) for (seq, matrix, _n) in cases]
    return cases


def fuzz_cases(rng, n):
    out = []
    densities = (0.2, 0.5, 0.8)
    for _ in range(n):
        n_terms = rng.randint(1, 6)
        n_rows = rng.randint(0, 6)
        p = rng.choice(densities)
        matrix = tuple(tuple(rng.random() < p for _ in range(n_terms))
                       for _ in range(n_rows))
        noise = rng.random() < 0.1
        out.append((tuple(range(n_terms)), matrix, noise))
    return out


# --- differential driver --------------------------------------------------------

def shadow_result(term_seq, matrix):
    global CURRENT_MATRIX
    CURRENT_MATRIX = [list(rb) for rb in matrix]
    rows = ToSeq(range(len(matrix)))
    terms = ToSeq(term_seq)
    got = search_retains_object(rows, terms)
    # internal cross-check: the impl region agrees with the pure predicate
    assert got == some_row_matches_all(rows, terms), (
        "internal shadow inconsistency at %r / %r" % (term_seq, matrix))
    return got


def main():
    oracle = Oracle()
    if not _validate_materialization(oracle):
        return 1

    cases = exhaustive_cases() + boundary_cases()
    rng = random.Random(SEED)
    cases += fuzz_cases(rng, N_FUZZ)

    # bucket by (term sequence, noise) so each bucket is one real search call
    buckets = {}
    order = []
    for seq, matrix, noise in cases:
        key = (seq, noise)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(matrix)

    checked = 0
    disagreements = 0
    for key in order:
        seq, noise = key
        pending = buckets[key]
        for i in range(0, len(pending), BATCH):
            chunk = pending[i:i + BATCH]
            real = oracle.run_batch(list(seq), chunk, noise=noise)
            for matrix, real_kept in zip(chunk, real):
                shadow_kept = shadow_result(seq, matrix)
                checked += 1
                if shadow_kept != real_kept:
                    disagreements += 1
                    print("DISAGREEMENT at terms=%r matrix=%r noise=%r:\n"
                          "  shadow (impl region)              = %r\n"
                          "  real (patched get_search_results) = %r"
                          % (seq, matrix, noise, shadow_kept, real_kept))
                    if disagreements >= 10:
                        print("FAIL: stopping after 10 disagreements")
                        print(json.dumps({"checked": checked,
                                          "disagreements": disagreements,
                                          "seed": SEED}))
                        return 1

    if disagreements:
        print("FAIL: %d disagreement(s) over %d inputs"
              % (disagreements, checked))
        print(json.dumps({"checked": checked,
                          "disagreements": disagreements, "seed": SEED}))
        return 1
    print("PASS: shadow impl == real patched get_search_results retention on "
          "%d probes (5054 exhaustive + boundary + %d fuzz; seed %d); "
          "0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({
        "checked": checked, "disagreements": 0, "seed": SEED,
        "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
