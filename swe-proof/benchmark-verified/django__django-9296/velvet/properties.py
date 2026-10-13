"""properties.py — G-PBT falsification battery for django__django-9296 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct enumeratePages`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates).

DEFENDED SURFACE (one contracted method over an index sequence and an opaque
per-index sub-view selector):

  enumeratePages (pageRange : List PageIdx) return (out : List (List Int))
    ensures out = pageSeq pageRange          -- THE load-bearing (and only) clause

with ``pageSeq`` the front-recursive fold ``pageSeq (p :: ps) = pageOf p ::
pageSeq ps``, and the carrier of indices

  opaque numPages : Nat
  def PageIdx : Type := {n : Nat // 1 ≤ n ∧ n ≤ numPages}
  opaque pageOf : PageIdx → List Int

``pageOf`` is OPAQUE (its concrete result is never pinned; the spec relies only
on the SAME map being applied to every index, in order) and — the point of the
carrier — it is DEFINED ONLY ON INDICES THE OBJECT NAMES. ``pageRange`` is the
sole INPUT binder.

The clause pins, for every input: (count) one sub-view per index; (order) the
k-th result element is the sub-view named by the k-th index; (value) each element
is ``pageOf`` of THAT index; (empty) ``[] -> []``. ``pageSeq`` is GROUNDED in the
input (a fully-unfolded fold over ``pageRange``), not an opaque answer key — the
opaque leaf is ``pageOf``, applied position-by-position, so there is no wrong echo
to build and the ungrounded-oracle probe is replaced by an honest positive
control.

THE DOMAIN IS PART OF THE CARRIER, AND THAT IS WHAT THIS REVISION CHANGES.
The accessor being modeled is a PARTIAL operation: it yields a sub-view at an
index only while ``1 ≤ n ≤ numPages`` and REFUSES every other index. An earlier
revision of this bundle modeled it as ``pageOf : Nat → List Int``, total on all
of ``Nat``. A single value-only postcondition cannot then constrain what an
implementation does with indices it does not return: a variant could apply the
accessor at an index the object does not name, discard the result, and still
satisfy ``out = pageSeq pageRange`` — so it VERIFIED, while its faithful
counterpart hits the accessor's refusal at run time and does not resolve the
failing test. That is a recorded, measured hole (G-EQ / G-PANEL-1, 2026-08-16:
the attack variant verified, its counterpart failed FAIL_TO_PASS 1/1 with
PASS_TO_PASS 20/20 passing), and it is closed here by making the off-domain
application INEXPRESSIBLE rather than merely unadmitted: the index type carries
the object's own bound, so the accessor cannot be written down at an index
outside it.

MEASURED, not argued (real builds, private scratch dir):
  * the attack's own shape — an accessor application at one index past the last
    one named, discarded — no longer states. ``pageOf ⟨pageRange.length + 1, by
    omega, by omega⟩`` fails with ``omega could not prove the goal: a possible
    counterexample may satisfy the constraints ... where a := ↑pageRange.length,
    b := ↑numPages``: the membership the carrier demands is not derivable,
    because the bound belongs to the OBJECT and cannot be read off the
    argument's length.
  * discharging that membership with ``sorry`` is the only route left, and it
    exits 3 (``file elaborates but uses sorry/admit``) — banned by G-HYGIENE and
    by the witness screen.
  * the sibling drift — a TOTAL out-of-range list read yielding a junk index —
    is not expressible either: ``pageRange[pageRange.length]!`` fails with
    ``failed to synthesize Inhabited PageIdx``, and so do ``.head!``,
    ``default``, ``Classical.arbitrary`` and ``#synth Nonempty PageIdx``. The
    ABSENCE of an ``Inhabited PageIdx`` instance is load-bearing: an index cannot
    be conjured, only received or built from the object's own count.
  * the restriction is not over-strong, and that is shipped as a case rather
    than asserted: ``pos-control-in-domain-selection`` consults the accessor at
    an index built from the object's count under a guard, discards the result,
    and VERIFIES.
  * what SURVIVES is the guarded form, and it is shipped as two reject cases
    (``partial-domain-shifted-index``, ``value-indexed-by-position``): a variant
    may still ask for a DIFFERENT index than the one at this position provided it
    proves that index is named, or falls back when it is not. Both are rejected
    by the clause, with witnesses; the first one's counterpart is precisely the
    recorded attack made expressible, and it does NOT resolve.

ARITHMETIC TOTALITY DRIFT — THE ONE CLASS THIS BATTERY CANNOT REJECT, AND WHY
THAT IS THE RIGHT ANSWER. A second recorded finding (G-EQ / G-PANEL-1,
2026-08-16) submitted two implementations that VERIFY and whose Python
counterparts do not resolve:

  * a prologue ``let _z : Nat := pageRange.length / (pageRange.length -
    pageRange.length)`` feeding the counter, whose counterpart wrote
    ``len(page_range) // (len(page_range) - len(page_range))`` and raised
    ``ZeroDivisionError`` (harness: ``resolved=false, completed=true``,
    FAIL_TO_PASS 0/1, PASS_TO_PASS 20/20); and
  * an extra loop ``k := pageRange.length + 1; while k ≠ 0 ... k := k - 2``,
    whose measure provably reaches 0 because ``Nat`` subtraction SATURATES, and
    whose counterpart counted ``1, -1, -3, ...`` forever (harness:
    ``resolved=false, completed=false, "Test timed out after 3600 seconds"``).

Both Lean modules are CORRECT — ``n - n`` is 0, ``n / 0`` is 0, the extra loop
lands exactly on 0 and changes nothing — so they are shipped here as POSITIVE
controls (``pos-control-dead-nat-arith``, ``pos-control-dead-saturating-loop``),
not as rivals. A spec that rejected them would be SPEC-TOO-STRONG.

And no clause of this spec could have rejected them, which is MEASURED rather
than argued: both shapes written with bare ``Nat`` LITERALS verify too — ``let _z
: Nat := 5 / (5 - 5)`` (exit 0) and ``let mut k : Nat := 7`` with the same loop
(exit 0) — and neither mentions one symbol of this spec (not ``pageRange``, not
``numPages``, not ``pageOf``, not ``out``). A postcondition is a predicate on the
inputs and the output, so it cannot distinguish a module containing such a
prologue from one that does not, and it cannot constrain a local whose value is
discarded or provably neutral. The defect was on the OTHER side of the
correspondence: both counterparts translated a Lean ``Nat`` operation into the
same-looking Python ``int`` operator, and those are different algebras — ``Nat``
is total by saturation where ``int`` is signed and ``//`` raises. mapping.md §2.1
now fixes the realization of every ``Nat`` operation, conformance_check.py
executes it (``nat_sub``/``nat_div``/``nat_mod``, with the laws measured
exhaustively), ``admiss-nat-semantics-carried`` below pins the SAME laws on the
Lean side in-region, and refinement.md §B'' records the finding and the measured
resolve outcomes. The battery's contribution to that class is three cases: the
two positives above, and one REJECT rival that routes its bug THROUGH the
saturating arithmetic (``truncated-arith-drop-last``: its bound
``pageRange.length - 1`` is correct on the empty run only because ``Nat``
subtraction truncates), so the algebra is exercised in the reject lane too and
not only in an assert.

THE SAME CLASS, ONE TYPE OVER. A THIRD recorded finding (G-EQ / G-PANEL-1,
2026-08-16) submitted three more VERIFYING implementations whose counterparts do
not resolve, and all three route through Lean ``Int`` rather than ``Nat`` —
because ``Int`` is a THIRD algebra (signed like Python, total at a zero divisor
like ``Nat``, and EUCLIDEAN where Python's ``//``/``%`` are FLOORED) and it is
spec-visible here: ``pageOf : PageIdx → List Int``.

  * ``let _z : Nat := ((pageRange.length : Int) / 0).toNat`` feeding the counter.
    ``Int`` division by zero is 0, so ``_z = 0``: verifies, correctly. The
    counterpart wrote ``// 0`` and raised (F2P 0/1, P2P 20/20). This is the very
    shape the ``Nat`` row above closed — reopened by writing it in another type.
  * ``let d : Nat := ((1 : Int) % (-2)).toNat`` with counter ``length + d - 1``.
    ``Int.emod`` is the non-negative-remainder convention, so ``d = 1`` and the
    bound is ``length``: verifies, correctly. Python's ``%`` is floored, ``d``
    realizes to 0, the bound becomes ``length - 1``, and the LAST sub-view is
    dropped (F2P 0/1, P2P 20/20). NOTHING is partial in this one — no zero
    divisor, both operands total on both sides — so a zero-divisor guard could
    not have caught it. It is purely a disagreement about what ``%`` denotes.
  * the loop body guarded by ``if ((1 : Int) % (-2)) < 0 then (no-op) else
    prepend``. In Lean ``1 < 0`` is false, so it always prepends: verifies,
    correctly. In Python ``-1 < 0`` is true and the iterator yields NOTHING
    (F2P 0/1, P2P 20/20).

The third one matters for the argument above, not just for the count: its value
is NOT discarded — it decides a branch, and the branch decides the output. So
"no clause can constrain a discarded local" was the wrong reason. The reason
that survives is CLOSEDNESS, and it was measured the same way: the prologue
rebuilt with bare ``Int`` literals and nothing else (``((1 : Int) % (-2)).toNat``)
verifies while mentioning no symbol of this spec, and a closed term denotes the
same value in every module, so no postcondition over inputs and output can
separate a module containing it from one that does not — wherever its value flows
afterwards.

Adding ``Int`` rows would only have moved the class again (measured: the same
trick in ``UInt8`` verifies too), so mapping.md §2.1 is now a LAW — R0, a closed
sub-expression realizes as the value Lean evaluates it to; R1, an open one as a
TOTAL Python function extensionally equal to the Lean operation — with tables for
``Nat``, ``Int``, fixed-width and ``Float`` under it and an explicit obligation to
transcribe a row rather than reuse a Python spelling. refinement.md §B''' records
the finding, and the measurement that all three counterparts RESOLVE (1/1, 20/20)
once realized per §2.1. The battery's contribution to this second half of the
class is FIVE more cases: the three attack shapes as positives
(``pos-control-dead-int-arith``, ``pos-control-emod-convention``,
``pos-control-emod-guarded-branch`` — the last one carrying the guard, so the
control-flow route is covered), the not-yet-submitted next type over as a
pre-emptive positive (``pos-control-fixed-width-wraparound``), and one REJECT
rival whose bound is computed by ``Int.emod`` rather than by ``Nat`` subtraction
(``emod-convention-drop-last-two``). The in-region assert
``admiss-int-semantics-carried`` pins the six ``Int`` equations on the Lean side,
and ``check_int_algebra``/``check_uint_algebra``/``check_float_algebra`` pin the
Python side.

THE SAME CLASS AGAIN, WITHOUT A NEW TYPE — AND THE ARGUMENT ABOVE IS WRONG TWICE
OVER. A FOURTH recorded finding (G-EQ / G-PANEL-1, 2026-08-16) reopened the class
without leaving the types already tabled. It attacked COMPOSITION: it assembled a
counterpart out of two rows the map already carried, ``List.range n -> range(n)``
and ``xs.length -> len(xs)``, giving ``len(list(range(n)))`` — which raises
``OverflowError: Python int too large to convert to C ssize_t`` for every
``n >= 2**63``, because CPython bounds every container and every ``len`` by
``ssize_t`` (``sys.maxsize == 2**63 - 1``, measured), while the Lean composite
``(List.range n).length`` answers ``n`` for every ``n : Nat``. Four verifying
shapes, all exit 0:

  * ``let _z : Nat := 0 * (List.range (2 ^ (64 + pageRange.length))).length``
    feeding the counter (``Nat.zero_mul``, so ``_z = 0``);
  * the same with the factors swapped (``... .length * 0``);
  * the same through a DIFFERENT constructor,
    ``(List.replicate (2 ^ (64 + pageRange.length)) (0 : Int)).length * 0``;
  * the value consumed by CONTROL FLOW: ``if (List.range N).length * 0 > 0 then
    result := result else <prepend>``, whose Lean guard is false so the prepend
    always happens, and whose counterpart never even evaluated the guard because
    the ``len(list(...))`` inside it raised first.

Each counterpart failed F2P 0/1 with P2P 20/20 and ``completed=true``, and the
raise is immediate (~1e-5 s), so this is DEFINEDNESS and not the cost caveat
refinement.md §B'' had carved out — which is exactly what §B'' had named as its
open residual, and it was misclassified there.

The bigger correction is to the reason. CLOSEDNESS does not cover this family:
measured, the closed variant ``let _z : Nat := 0 * (List.range (2 ^ 70)).length``
does NOT verify, it TIMES OUT at 900 s, because the elaborator tries to evaluate
the range. So both of this docstring's earlier inexpressibility arguments have now
been refuted by a case in this very battery — "a postcondition cannot constrain a
discarded local" by ``pos-control-emod-guarded-branch``, and CLOSEDNESS by
``pos-control-dead-range-materialization``. The argument that survives all four
findings is neither, and it is now a machine-checked case rather than a paragraph
(``admiss-postcondition-single-valued``, an IN-REGION assert under the frozen proof
body — a same-spec variant may not add top-level theorems, so the claim is
discharged where the method is verified): this spec's only obligation is ``out =
pageSeq pageRange``, which DETERMINES ``out`` from the input, so exactly one ``o``
satisfies ``o = pageSeq pr`` for every input, so any two verifying impls agree
everywhere, so the frozen impl and every one of the nine arithmetic/container
positives compute the SAME FUNCTION. A postcondition is a predicate over the inputs and the output;
this one already pins the output uniquely; therefore it is MAXIMALLY STRONG on its
observable interface and no strengthening can reject any of these shapes without
also rejecting gold. That holds whatever the prologue looks like, wherever its
value flows, and whether it is closed or open — which is why it is the argument
this bundle now rests on, and why every remaining ``verify => resolved`` gap here
is a refinement-map gap by construction rather than by preference.

mapping.md §2.1 therefore gained rule R2: a composite is realized from ITS OWN
defining equation, not by chaining rows, whenever an intermediate leaves what
Python can represent. Its one-line form is REALIZE THE LENGTH, NOT THE LIST, and
Lean supplies the equations (``List.length_range``, ``List.length_replicate``, the
``map``/``take``/``drop``/``++`` lengths — each ``simp``-discharged, measured).
refinement.md §B'''' records the finding and the measurement that all three
distinct counterparts RESOLVE (1/1, 20/20) once realized per R2. The battery's
contribution to this fourth round is SIX cases: three attack shapes as positives
(``pos-control-dead-range-materialization``,
``pos-control-replicate-materialization``, ``pos-control-range-guarded-branch``),
one in-region assert pinning the five length equations on the Lean side
(``admiss-derived-length-carried``), one REJECT rival whose bound is computed by
``List.length_replicate`` rather than by ``Nat.sub`` or ``Int.emod``
(``derived-length-drop-last-three``), and the single-valuedness obligation itself
(``admiss-postcondition-single-valued``). ``check_container_realization`` pins the
Python side, including that both materializing routes really do raise.

THE SAME CLASS, ONE LEVEL UP: A STATEMENT, NOT AN EXPRESSION. A FIFTH recorded
finding (G-EQ / G-PANEL-1, 2026-08-16) left expressions alone and attacked the
LOOP. Five verifying shapes, all exit 0 (re-measured here, one build each):

  * ``k := 2 ^ (64 + pageRange.length)`` then a decorative countdown
    ``while k > 0 invariant True done_with k = 0 decreasing k do k := k - 1``,
    before the frozen traversal (``pos-control-cost-countdown``);
  * the same with an initialiser Python cannot even BUILD,
    ``2 ^ (2 ^ (64 + pageRange.length))`` (``pos-control-cost-countdown-huge``);
  * the countdown plus a body GUARDED on the value it leaves,
    ``if k > 0 then result := result else <prepend>`` — so control flow, not just
    cost, depends on it (``pos-control-cost-guarded-body``);
  * the frozen loop's OWN counter widened to
    ``pageRange.length + 2 ^ (64 + pageRange.length)``, with the
    ``i ≤ pageRange.length`` invariant dropped and the obligation reproved by
    cases (``pos-control-widened-counter``);
  * the loop body guarded by ``if 2 ^ (2 ^ (64 + pageRange.length)) > 0``, whose
    Lean guard is provably the constant ``True`` (``Nat.two_pow_pos``), so it
    always prepends (``pos-control-two-pow-guard``).

The submitted counterparts transliterated the loop statement for statement and
the guard expression for expression, and all five were recorded
``completed=false`` at the harness's 3600s timeout, with the gold control
resolving in 118s in the same run. That is not the cost caveat §B'' carved out
and it is not a slower function: a Python statement that runs ``2 ^ (64 + n)``
times DOES NOT FINISH, and one that evaluates ``2 ** (2 ** (64 + n))`` raises
``MemoryError`` (measured: 15s under a 2GiB cap; ``2 ** 2^31`` needs 13s and
256MiB), so neither transliteration is a realization of anything. Measured the
other way, one resolve each, serialized: the FIVE R3-realized counterparts all
resolve — ``resolved=true, completed=true`` in 97.0s, 99.4s, 80.1s, 85.1s and
83.7s respectively.

Two rules answer it, and one of them was already written. mapping.md §2.1's ``^``
row is now side-conditioned exactly as ``xs.length -> len(xs)`` was: ``a ** b`` is
the realization only where the value is one Python can hold, and above that R2
applies — ``2 ^ m > 0`` realizes as the constant ``True``, never as
``2 ** m > 0``, which is what closes the fifth shape with no new rule at all
(R1's extensionality clause, "where a Lean sub-term is provably a constant, the
realization is that constant", already said so). The other four need the
statement-level analogue, and §2.1 gained it as R3: an annotated
``while g invariant I done_with D decreasing m`` is realized by any total Python
statement that establishes ``I ∧ D`` from the entry state, PROVIDED ``I ∧ D``
determines the final value of every variable the loop modifies — because ``I ∧ D``
is all the verifier ever hands the continuation, so it is what the loop MEANS.
A decorative countdown realizes as ``k = 0``; a widened frozen loop realizes as
the traversal its own ``result = pageSeq (pageRange.drop i)`` with ``i = 0``
determines. Where ``I ∧ D`` does NOT determine the modified variables R3 gives
nothing and the body is transcribed step for step, which is the frozen impl's own
realization. R3 cannot launder a wrong impl: it demands the loop's OWN ``I ∧ D``,
which the verifier proved of that loop, and a loop establishing anything else is
either rejected or — by single-valuedness — computes ``pageSeq pageRange`` anyway.

The battery's contribution to this fifth round is SEVEN cases: the five attack
shapes as positives (named above), one in-region assert pinning the Lean facts
both rules rest on (``admiss-loop-denotation-carried``: ``0 < 2 ^ n``, that
``done_with`` determines the counter, and that the frozen loop's ``I ∧ D``
determines ``result``), and one REJECT rival whose bound is computed by
``Nat.pow`` — the very operation the five shapes abuse — rather than by
``Nat.sub``, ``Int.emod`` or ``List.length_replicate``
(``pow-bound-drop-last-four``). ``check_loop_realization`` in
conformance_check.py pins the Python side: the countdown's denotation against the
real loop exhaustively at small ``k``, the transliteration measured NOT to have
finished after a large step budget from ``k = 2 ^ 64``, the ``^`` row's side
condition measured at the bound, and ``2 ** n > 0`` as the constant it is.

THE CARRIER IS PARTLY OPAQUE. ``pageOf`` never reduces at a concrete index, so a
``decide``-on-a-literal tester gets STUCK on every ``pageOf p``. Two routes
remain, and both are used here:

  * STRUCTURAL clauses of the fold are transparent WITHOUT knowing ``pageOf``:
    length/count and which indices are traversed. A rival that returns the wrong
    NUMBER of sub-views is refutable with no assumption about ``pageOf`` at all —
    its result list has a different length than ``pageSeq``.
  * VALUE / ORDER clauses need CONDITIONING ON THE CARRIER: a rival that reverses
    the order, or feeds the accessor another named index, produces ``pageOf q``
    where the spec demands ``pageOf p``. That is refutable at a symbolic point
    under one weak hypothesis ``pageOf ⟨1,_⟩ ≠ pageOf ⟨2,_⟩`` — exactly the
    sub-domain where the rival diverges. The hypothesis is satisfiable (a
    non-constant selector exists), so the refutation is not from a contradiction;
    the gate's consistency probe leaves ``False`` unsolved, confirmed by a real
    build for each conditioned witness.

WITNESSES NAME INDICES, AND SO CARRY THE OBJECT'S COUNT. An index literal is no
longer a bare ``Nat``: ``⟨1, by omega, by omega⟩`` needs ``1 ≤ numPages``, so
each witness binds ``hn : k ≤ numPages`` for the smallest ``k`` its point needs
and builds its indices from it. That hypothesis is a statement about the OBJECT
(``the collection presents at least k sub-views``), it is satisfiable (nothing
pins the opaque count), and it is exactly the shape the failing test's fixture
has (3 items at 2 per page: two sub-views). The consistency probe is stated over
the module's own vocabulary only — ``numPages`` and ``pageOf`` — so it really
elaborates and really tries to derive ``False``; no witness-local helper is
smuggled into a hypothesis where the probe could not see it.

Every reject witness reaches the impl through Velvet's extractor
(``extract_program_for enumeratePages`` gives ``enumeratePagesExec pageRange =
NonDetT.run (enumeratePages pageRange)``) and states ``enumeratePagesExec xs ≠
DivM.res (pageSeq xs)`` at a named point ``xs``.

THE FROZEN IMPL CANNOT SERVE AS THE WITNESSES' SECOND SUBJECT — measured, not
assumed. Its ``while`` loop under ``loom.semantics.choice "demonic"`` elaborates
through ``Classical.choice``, which the kernel cannot unfold, so the goal keeps an
un-normalised ``forIn Lean.Loop.mk`` term and NOTHING about the frozen impl
decides. A gold-side exit code therefore carries NO information here, and a
forged witness asserting the rival is CORRECT would clear both halves of the
discrimination check.

So every reject case carries ``witness_reference``: ONE shared, VERIFYING,
kernel-reducible implementation of the same frozen spec (the closed form
``pageRange.map pageOf``, whose ``prove_correct`` closes by an explicit induction
on ``pageRange`` — no new lemma, no weakened obligation). It is shipped as the
``pos-control-closed-form`` positive too, so the battery itself records that
loop-freeness is not what any rival is being rejected for. Against that reference
each witness fails SEMANTICALLY (residual ``⊢ False``, or a residual equation
between two ``pageOf`` applications, i.e. the equality genuinely holds there).

THE FORGERY TEST is what establishes that, rather than a reading of the error
text — re-measured for THIS revision, all nine reject cases, both subjects. For
each, a second file differing from the witness ONLY in what it CLAIMS (the
equality instead of its negation: asserting the impl is CORRECT at that point)
was built against both subjects. All nine flipped claims EXIT 0 against the
reference and EXIT 1 against their own rival, the rival-side failure leaving the
concrete disagreement as the residual goal:

    drop-first          ⊢ False
    drop-last           ⊢ False
    order-reversed      ⊢ pageOf ⟨2,_⟩ = pageOf ⟨1,_⟩ ∧ pageOf ⟨1,_⟩ = pageOf ⟨2,_⟩
    shifted-index       ⊢ (if h : 2 ≤ numPages then pageOf ⟨2,_⟩ else []) = pageOf ⟨1,_⟩
    spurious-leading    ⊢ False
    by-position         ⊢ (if h : 1 ≤ numPages then pageOf ⟨1,_⟩ else []) = pageOf ⟨5,_⟩
    emod-drop-last-two  ⊢ False   (context ``hn : 3 ≤ numPages``)
    len-drop-last-three ⊢ False   (context ``hn : 4 ≤ numPages``)
    pow-drop-last-four  ⊢ False   (context ``hn : 5 ≤ numPages``)

Three of those residuals are the ones they are because their witness tails are
now wrapped in ``try (...)``: ``order-reversed``, ``partial-domain-shifted-index``
and ``value-indexed-by-position`` used to open with a bare ``intro``, and against
the REFERENCE — where the claim is false and ``simp`` has already collapsed the
goal to ``False`` — ``intro`` has no binder to take, so the recorded gold-side
signature was ``Tactic `introN` failed: There are no additional binders``. That is
a STRUCTURAL failure (``pbt_signature_tiers``: tier ``shape``, a WEAK tier that
asks an auditor whether the opposite claim fails identically) even though the
underlying build had in fact decided the claim. Wrapping the tail changes nothing
about what the witness must prove — it still has to CLOSE against its own rival,
measured exit 0 for all three — and makes the gold-side residual the reduct
itself: ``unsolved goals ... ⊢ False``, tier ``reduced``. All nine reject cases
now carry a non-weak gold-side signature, so the question those three used to
raise is answered by the bytes rather than by an audit. The forgery direction is
unchanged by the wrap and was re-measured for all four affected cases (the three
retiered plus the new one): reference 0, rival 1, residuals as tabled.

So the reference-side exit code TRACKS the claim in both directions — 0 when the
claim holds there, 1 when it does not — which is exactly what a discriminating
subject must do and exactly what the frozen impl does not. Each witness's own
direction is therefore carrying the information, not the subject's inability to
decide.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY framing rivals (store into / append to the read-only index run)
    because its index run is held at a fractional heap permission an impl can
    illegally WRITE. Lean and Velvet are referentially transparent: ``pageRange``
    is an immutable value, this bundle declares NO ``mut`` binder, there is no
    heap and no aliasing — so there is no read-only input to overwrite and no
    substitute probe to build. Not fabricated (per the porting map: this class is
    vacuous on Lean/Velvet).
  * DIVERGENCE / NON-TERMINATION — the sibling carries NO such case, so there is
    nothing to port, and the class is CLOSED BY THE SPEC rather than left as a
    hole. This bundle sets ``loom.semantics.termination "total"`` AND opens
    ``TotalCorrectness`` (the ``open`` is what selects the semantics: both
    namespaces define ``WPGen.forWithInvariantLoop`` and the later ``open`` wins,
    so a bundle that set the option but opened ``PartialCorrectness`` had a
    DECORATIVE measure that elaborated and was never checked). Under the total
    scope every loop carries the obligation ``measure b' < measure b``, so a
    non-terminating impl no longer satisfies ``out = pageSeq pageRange``
    vacuously: it is REJECTED. Measured on this bundle, one build: the frozen
    impl with its ``i := i - 1`` step deleted and its measure removed fails with
    ``Decreasing annotations are required in total correctness semantics``. No
    reject case is shipped for the class even so: a reject case needs a witness
    that refutes the rival at a concrete input, and a rival rejected for a
    MISSING MEASURE is refuted by the verifier's own obligation, not by an input
    point — there is no value at which its output disagrees, because it has no
    output.
  * PARTIAL-DOMAIN / VALUE / ORDER / COUNT — APPLIES; these are the heart of the
    port and re-express directly onto the single ``out = pageSeq pageRange``
    clause. The partial-domain class is now attacked in the only form the carrier
    still admits (guarded), which is what makes the two guarded rivals below the
    most load-bearing cases in this battery.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total ``def`` over the
    method's own input; ``pageOf`` is the opaque leaf, applied position-by-
    position, so there is no answer-key to echo. Replaced by positive controls.

WITNESS PLACEMENT / BINDER COVERAGE. The sole input binder ``pageRange`` is moved
across the nine reject witnesses: a three-index run (count, leading element), a
two-index run (order), a one-index run (value at a single index), the EMPTY run
(the ``[] -> []`` boundary), a one-index run whose index is NOT its position
(``[⟨5,_⟩]``, the value clause off the ``[1..n]`` sub-domain), a one-index run
at index 2 (count, TRAILING element — the point the saturating-arithmetic rival
is wrong at, and the empty run is exactly where it is right), a two-index run
at ``[⟨2,_⟩, ⟨3,_⟩]`` (count, TWO trailing elements — the ``Int.emod`` rival drops
both, and at every one-index run it and the frozen impl agree on ``[]``, so no
shorter point separates it), and a THREE-index run at
``[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩]`` (count, THREE trailing elements — the derived-length
rival drops all three, and at the two-index run it and the ``Int.emod`` rival
agree on ``[]``, so no shorter point separates THEM), and a FOUR-index run at
``[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩, ⟨5,_⟩]`` (count, FOUR trailing elements — the
``Nat.pow``-bound rival drops all four, and at the three-index run it and the
derived-length rival agree on ``[]``, so again no shorter point separates them:
the same forced-lengthening the drop widths one, two and three already showed,
one step further). Length and contents both
vary — and the variation is MEANINGFUL, not spellings of one point: ``[⟨5,_⟩]`` vs
``[⟨2,_⟩]`` vs ``[⟨1,_⟩]``
are three one-index runs whose differences are respectively index-vs-position,
trailing-vs-leading and the baseline; ``[⟨2,_⟩, ⟨3,_⟩]`` vs the leading
two-index run separates a drop-two from an order swap; and the two three-index
runs differ in where they START (``[⟨1,_⟩, …]`` for the head bug,
``[⟨2,_⟩, …]`` for the width-three trailing bug), and the four-index run extends
that same ladder by one, which is what makes the drop widths one, two, three and
four separable in a single battery. Each is the refutation
point of a rival the others satisfy. No two rivals share a refutation point, and
each independent sub-obligation of the fold is attacked by at least one rival.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; ``pageOf`` is an
``opaque`` A-reference validated == the real accessor, DOMAIN INCLUDED, by
axiom_check.py — that is G-AX's job, and this gate ignores ``AXIOM_TESTS``
regardless).
"""
from pathlib import Path

INSTANCE = "django__django-9296"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the `prove_correct` tactic body, and is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only these
# keeps markers.same_spec True and the prove_correct enumeratePages header
# intact (the spec view elides the impl region and the proof body).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the accumulating backward loop plus
# the return). Reject rivals replace it with a closed form; the loop-shape
# positive control instead edits only the loop body (below).
_IMPL_BODY = (
    "    let mut result : List (List Int) := []\n"
    "    let mut i := pageRange.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ pageRange.length\n"
    "      invariant result = pageSeq (pageRange.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := pageRange[i - 1]?\n"
    "      result := (p.map pageOf).toList ++ result\n"
    "      i := i - 1\n"
    "    return result"
)

# The three-statement loop body only. The loop-shape positive control reshapes
# exactly this (hoist the index into a local, then prepend the per-step image) —
# same backward direction, same front-recursive unfold, so the frozen loop
# invariants and the frozen proof script still close.
#
# Note the shape the carrier forces: the step reads the index with `[i - 1]?`
# and maps the accessor OVER the resulting `Option`. A total read (`[i - 1]!`)
# would need `Inhabited PageIdx`, which does not exist and must not: that is the
# instance whose absence makes an out-of-range index unwritable.
_DO_BODY = (
    "      let p := pageRange[i - 1]?\n"
    "      result := (p.map pageOf).toList ++ result\n"
    "      i := i - 1"
)

# The frozen loop's SCAFFOLD: the counter init, the guard, the two invariants,
# the exit condition and the DECREASING MEASURE. The forward-loop positive
# control replaces this whole block, because a forward walk needs a genuinely
# different invariant (`take i` in place of `drop i`) — that is what makes it a
# real soundness probe rather than a reshuffle of the frozen one.
#
# The measure is part of the anchor, and must be: this bundle opens
# `TotalCorrectness`, under which every loop carries a proof obligation
# `measure b' < measure b` (Loom/MonadAlgebras/NonDetT/Basic.lean:544). The
# frozen loop counts DOWN from `pageRange.length` to 0, so `i` itself decreases;
# a forward walk counts UP, and `i` INCREASES. An anchor stopping at `done_with`
# would leave the frozen `decreasing i` in place below the replacement and hand
# the forward variant a measure that grows — rejected for `decreasing_1: i`,
# i.e. for its measure rather than for its behaviour, which would read as
# SPEC-TOO-STRONG on a faithful forward traversal. Each replacement therefore
# states the measure its own counter admits (`pageRange.length - i` here).
_LOOP_HEAD = (
    "    let mut i := pageRange.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ pageRange.length\n"
    "      invariant result = pageSeq (pageRange.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i"
)

# The first line of the impl region, used as the insertion point for the
# admissibility cases' in-region assertions and for the in-domain probe.
_RESULT_INIT = "    let mut result : List (List Int) := []"

# The counter's initialiser alone. The dead-arithmetic control below routes its
# discarded `Nat` value THROUGH the counter (`+ _z` where `_z` is provably 0), so
# the probe is not merely an unused `let` the elaborator could drop on the floor:
# the value reaches the loop.
_COUNTER_INIT = "    let mut i := pageRange.length"

# The frozen tactic body. The closed-form positive control drops the loop, so the
# backward drop-step rewrite the frozen script applies has no goal to fire on and
# must be replaced by the induction the closed form actually needs. Only the
# tactic body changes; the `prove_correct enumeratePages by` header is untouched,
# and no lemma / axiom / `sorry` is introduced.
_PROOF_BODY = (
    "  loom_solve\n"
    "  rw [pageSeq_drop_step pageRange i (by omega) (by omega)]\n"
    "  simp_all"
)


def _closed(expr: str) -> str:
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`."""
    return _swap(_BASE, _IMPL_BODY, f"    return ({expr})")


# ---------------------------------------------------------------------------
# THE SHARED WITNESS REFERENCE.
#
# A correct, VERIFYING, kernel-reducible implementation of the frozen spec: the
# closed form `pageRange.map pageOf`. It exists because the FROZEN impl decides
# nothing — its `while` loop elaborates through `Classical.choice` and leaves an
# un-normalised `forIn Lean.Loop.mk` term, so a witness build against it fails
# for a TRUE claim exactly as it does for a false one (measured; see the module
# docstring). Refuting each witness against this reference instead is sound for
# the same reason gold was: an impl the verifier ACCEPTS cannot violate its own
# spec, so a genuine "the spec is violated here" claim must fail against it.
#
# The proof is the honest one the new shape needs (induction on the index
# sequence, using the frozen `pageSeq` equations), NOT a weakened obligation: the
# `prove_correct enumeratePages by` header is byte-identical and nothing is
# assumed. It is also shipped as `pos-control-closed-form` below, so the battery
# records that this shape VERIFIES and no rival is being rejected merely for
# being loop-free.
# ---------------------------------------------------------------------------
_REFERENCE = _swap(
    _closed("pageRange.map pageOf"), _PROOF_BODY,
    "  loom_solve\n"
    "  induction pageRange with\n"
    "  | nil => rfl\n"
    "  | cons p ps ih => simp only [List.map_cons, ih, pageSeq_cons]")


# ---- witness preamble. The spec is a `method` CONTRACT over a partly-opaque
# ---- carrier, so a witness reaches the impl through Velvet's extractor:
# ---- `enumeratePagesExec xs` is `NonDetT.run (enumeratePages xs)`, and
# ---- `≠ DivM.res (pageSeq xs)` says the impl's output contradicts the
# ---- postcondition at that point. Checked in a file whose `prove_correct`
# ---- block is stripped, so no tactic script can mask the verdict. `pageOf`
# ---- never reduces, so the value/order witnesses condition on it via a single
# ---- satisfiable inequality.
_EXTRACT = "extract_program_for enumeratePages\n\n"


def _idx(k: int) -> str:
    """The index the object names at 1-based position `k`.

    An index is a member of the accessor's domain, so naming one is a proof
    obligation, not a literal: `⟨k, _, _⟩` needs `1 ≤ k` (immediate) and
    `k ≤ numPages`, which `omega` gets from the witness's own
    `hn : k' ≤ numPages` hypothesis for `k' ≥ k`. This is the whole reason each
    witness binds a count hypothesis: after the carrier change an index cannot
    be conjured from thin air, and a witness that tried would not elaborate.
    """
    return f"⟨{k}, by omega, by omega⟩"


def _lst(ks) -> str:
    return "[" + ", ".join(_idx(k) for k in ks) + "]"


def _witness(binders: str, xs: str, tail: str) -> str:
    return (_EXTRACT
            + f"example {binders}:\n"
            + f"    enumeratePagesExec {xs}\n"
            + f"      ≠ DivM.res (pageSeq {xs}) := by\n"
            + "  unfold enumeratePagesExec enumeratePages\n"
            + "  simp [NonDetT.run, pure, pageSeq]\n"
            + tail)


# The two GUARDED near-misses. Neither can be written unguarded any more: the
# accessor demands a proof that the index it is handed is one the object names,
# and neither `p.val + 1` nor a position `k + 1` comes with one. So each rival
# does the only thing left — prove the membership when it holds, and fall back
# when it does not — and each is still rejected by the clause. The `else` branch
# is not a decoration: it is what the counterpart must do at the last index,
# and it is why the counterpart does not resolve.
_GUARD_SHIFT = ("pageRange.map (fun p =>\n"
                "      if h : p.val + 1 ≤ numPages then pageOf ⟨p.val + 1, by omega, h⟩\n"
                "      else [])")
_GUARD_POSITION = ("(List.range pageRange.length).map (fun k =>\n"
                   "      if h : 1 ≤ k + 1 ∧ k + 1 ≤ numPages then pageOf ⟨k + 1, h.1, h.2⟩\n"
                   "      else [])")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================

    # Ports the nagini pos-control-localvar-reshape: hoist the index into a local
    # `j`, then prepend the per-step image. Same backward direction and same
    # front-recursive unfold, so the frozen loop invariants and the frozen proof
    # script close the obligation with no retune.
    {
        "id": "pos-control-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _DO_BODY,
            "      let j := i - 1\n"
            "      let p := pageRange[j]?\n"
            "      result := (p.map pageOf).toList ++ result\n"
            "      i := i - 1"),
        "rationale": "a CORRECT reshape of the loop body: index via a local "
                     "`j = i-1`, then prepend the per-step image. Same backward "
                     "direction and same front-recursive unfold as the frozen impl, "
                     "so `out = pageSeq pageRange` still discharges under the frozen "
                     "loop invariants and the frozen proof script. NOTE (audit): "
                     "this reshape is DEFINITIONALLY the frozen body — the `let` "
                     "hoist closes by `rfl` — so this case is a MINIMAL control, not "
                     "a strong soundness probe: it shows the obligation is not "
                     "sensitive to surface spelling, and nothing more. The "
                     "load-bearing soundness probes are pos-control-closed-form (no "
                     "loop at all), pos-control-forward-loop (a different invariant) "
                     "and pos-control-in-domain-selection (an extra accessor "
                     "application), none of which is definitionally the frozen impl.",
    },

    # The strongest available soundness probe that is still a LOOP: it walks the
    # index sequence front-to-back and APPENDS, so the frozen backward invariant
    # (`drop i`) does not describe it at all — the invariant becomes `take i` and
    # the frozen `pageSeq_drop_step` rewrite has no goal to fire on. Neither
    # definitionally nor tactically the frozen impl, unlike the reshape above.
    {
        "id": "pos-control-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_swap(_BASE, _LOOP_HEAD,
                        "    let mut i := 0\n"
                        "    while i < pageRange.length\n"
                        "      invariant i ≤ pageRange.length\n"
                        "      invariant result = pageSeq (pageRange.take i)\n"
                        "      done_with i = pageRange.length\n"
                        "      decreasing pageRange.length - i"),
                  _DO_BODY,
                  "      let p := pageRange[i]?\n"
                  "      result := result ++ (p.map pageOf).toList\n"
                  "      i := i + 1"),
            _PROOF_BODY,
            "  loom_solve\n"
            "  have hmap : ∀ l : List PageIdx, pageSeq l = l.map pageOf := by\n"
            "    intro l; induction l with\n"
            "    | nil => rfl\n"
            "    | cons hd tl ih => simp [pageSeq_cons, ih]\n"
            "  have hi : i < pageRange.length := by omega\n"
            "  simp only [invariant_2, hmap, List.take_succ,\n"
            "    List.getElem?_eq_getElem hi, List.map_append]\n"
            "  simp"),
        "rationale": "a CORRECT impl that walks the index sequence FORWARD and "
                     "appends each sub-view, so its loop invariant is "
                     "`result = pageSeq (pageRange.take i)` — the frozen backward "
                     "invariant (`drop i`) is false of it at every step, and the "
                     "frozen `pageSeq_drop_step` rewrite has no goal to fire on. "
                     "The obligation must still discharge: the postcondition "
                     "constrains the RESULT, not the direction of traversal, so "
                     "rejecting a faithful forward walk would be SPEC-TOO-STRONG on "
                     "the traversal ORDER. Its proof is the honest one the new "
                     "invariant needs (a per-position characterisation of the fold, "
                     "then the forward step: `List.take_succ` plus the read at `i`) "
                     "with the obligation header untouched and nothing assumed. It "
                     "carries its OWN measure `decreasing pageRange.length - i`, "
                     "because under this bundle's `TotalCorrectness` every loop must "
                     "be proven to terminate and this counter goes UP where the "
                     "frozen one goes down. That is not a weaker case: the same "
                     "soundness property is probed under the strictly stronger "
                     "obligation that it also terminate, which it does.",
    },

    # The shared witness reference, shipped as a case in its own right. Two jobs:
    # it is the SECOND, far more aggressive soundness positive (the loop is gone
    # entirely, so the postcondition is defended against a completely different
    # control flow rather than a local reshape), and it puts on the record that
    # this loop-free shape VERIFIES — so none of the loop-free rivals below can be
    # read as rejected merely for dropping the loop.
    {
        "id": "pos-control-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": "a CORRECT impl with entirely different control flow: no "
                     "accumulator and no loop, just the direct per-index image of "
                     "the whole index sequence. It must verify — the postcondition "
                     "constrains the RESULT, not the traversal that produced it, so "
                     "rejecting this would be SPEC-TOO-STRONG. Its proof is the "
                     "honest one the new shape needs (induction on the index "
                     "sequence via the frozen fold equations); the obligation "
                     "header is byte-identical and nothing is assumed. This case "
                     "also anchors the reject lane: it is the `witness_reference` "
                     "every rival below is refuted against, so the battery itself "
                     "records that loop-freeness is not the reason for any "
                     "rejection.",
    },

    # THE CONTROL FOR THE DOMAIN-CARRYING CARRIER. The strengthening this revision
    # makes must reject off-domain accessor applications and NOTHING ELSE, so the
    # battery ships the near side of that line: an impl that consults the accessor
    # at an index it PROVES the object names, discards the result, and is
    # otherwise the frozen impl. It VERIFIES (measured), so the carrier restricts
    # the accessor's argument, not the number of times it may be applied.
    {
        "id": "pos-control-in-domain-selection",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    let _probe : List Int :=\n"
            "      if h : 1 ≤ numPages then pageOf ⟨1, by omega, h⟩ else []\n"
            + _RESULT_INIT),
        "rationale": "a CORRECT impl that additionally consults the accessor at an "
                     "index the object NAMES — the first one, guarded by the "
                     "object's own count — and discards the result. It must verify, "
                     "and this is the control that keeps the domain-carrying index "
                     "type honest: the carrier's job is to make an application at an "
                     "index the object does not name INEXPRESSIBLE, not to forbid "
                     "extra applications at named ones. A real counterpart doing "
                     "this asks the object for a sub-view it already presents and "
                     "throws it away: the accessor admits the call, nothing "
                     "observable changes, and the failing test and all 20 passing "
                     "tests are unaffected — so a spec that REJECTED it would be "
                     "SPEC-TOO-STRONG. Measured: it verifies, while the same probe "
                     "at one index PAST the object's count does not even elaborate "
                     "(`omega could not prove the goal`, the membership the carrier "
                     "demands). Together those two builds are the record that the "
                     "restriction is exactly the accessor's real domain.",
    },

    # THE CONTROLS FOR THE `Nat` ALGEBRA (mapping.md §2.1, refinement.md §B'').
    # Both of the next two cases are the attack shapes of the second recorded
    # G-EQ / G-PANEL-1 finding, shipped as POSITIVE controls — because they are
    # correct, and a spec that rejected them would be SPEC-TOO-STRONG. What the
    # finding actually exposed is that their NAIVE Python translation is not their
    # translation at all: it reads Lean's total, saturating `Nat` operations as
    # Python's partial `int` ones. The fix is in the refinement map, and these two
    # cases are what stop that fix from being a paper claim — they put on the
    # record, in the battery, that these impls DO verify, so the reason their naive
    # counterparts fail can only be the mistranslation.
    {
        "id": "pos-control-dead-nat-arith",
        "kind": "soundness",
        "expect": "verify",
        # `_z` is `n / (n - n)`: `Nat` subtraction saturates to 0 and `Nat`
        # division by 0 is 0, so `_z = 0` and the counter is unchanged. The value
        # is not merely bound and dropped — it flows into `i`.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let _z : Nat := pageRange.length "
                  "/ (pageRange.length - pageRange.length)\n"
                  + _RESULT_INIT),
            _COUNTER_INIT,
            "    let mut i := pageRange.length + _z"),
        "rationale": "a CORRECT impl that computes a `Nat` quotient by a "
                     "provably-zero divisor and adds it to the loop counter. It MUST "
                     "verify: in `Nat`, `n - n` is `0` and `n / 0` is `0`, so `_z` is "
                     "`0`, the counter is `pageRange.length`, and the traversal is the "
                     "frozen one — a spec that rejected it would be SPEC-TOO-STRONG "
                     "about arithmetic that cannot change the result. This case "
                     "exists because it is the shape of a recorded G-EQ / "
                     "G-PANEL-1 finding (2026-08-16, second finding): the attack "
                     "verified here and its submitted Python counterpart raised "
                     "`ZeroDivisionError`, failing FAIL_TO_PASS 1/1 with PASS_TO_PASS "
                     "20/20 passing. NO CLAUSE OF THIS SPEC COULD HAVE CLOSED THAT, "
                     "and that is measured rather than argued: the same prologue "
                     "written with bare literals (`let _z : Nat := 5 / (5 - 5)`) also "
                     "verifies, and it mentions no symbol of the spec — not "
                     "`pageRange`, not `numPages`, not `pageOf`, not `out` — so no "
                     "predicate over the inputs and the output can distinguish a "
                     "module containing it from one that does not, and a "
                     "postcondition cannot constrain a local whose value is "
                     "discarded or provably neutral. The defect was in the "
                     "refinement map's arithmetic leg, which read Lean's TOTAL `-` "
                     "and `/` as Python's PARTIAL ones; mapping.md §2.1 now fixes "
                     "the realization (`a - b` -> `max(0, a-b)`, `a / 0` -> `0`), "
                     "conformance_check.py executes it, admiss-nat-semantics-carried "
                     "pins the Lean side of it, and the counterpart under the "
                     "corrected realization was measured to RESOLVE (refinement.md "
                     "§B'').",
    },
    {
        "id": "pos-control-dead-saturating-loop",
        "kind": "soundness",
        "expect": "verify",
        # A second loop, before the frozen one, that counts DOWN BY TWO from an
        # ODD start and so would step past zero — except that `Nat` subtraction
        # saturates, so it lands on 0 and the measure `k` really does fall.
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    let mut k : Nat := pageRange.length + 1\n"
            "    while k ≠ 0\n"
            "      invariant True\n"
            "      done_with k = 0\n"
            "      decreasing k\n"
            "    do\n"
            "      k := k - 2\n"
            + _RESULT_INIT),
        "rationale": "a CORRECT impl carrying an extra loop that touches nothing "
                     "observable and terminates. It MUST verify, and it must verify "
                     "under this bundle's `TotalCorrectness`: the measure `k` falls "
                     "by two per step and CANNOT step past zero, because `Nat` "
                     "subtraction saturates — from an odd start it lands exactly on "
                     "`0`. Rejecting it would be SPEC-TOO-STRONG about a loop that "
                     "provably ends and provably changes nothing. It is the second "
                     "shape of the same recorded finding: the submitted Python "
                     "counterpart of this loop counted `1, -1, -3, ...` forever and "
                     "the harness recorded `completed=false, 'Test timed out after "
                     "3600 seconds'`. The termination the verifier PROVED is real; it "
                     "just does not survive a translation that swaps the algebra "
                     "underneath the measure. So this case is also the battery's "
                     "record of the sharpest statement in mapping.md §2.1: a "
                     "`TotalCorrectness` termination proof transfers to the "
                     "counterpart only because the realized step performs the SAME "
                     "saturating arithmetic (`nat_sub`), and would not transfer under "
                     "Python's signed `-`. Measured the same way as the case above: "
                     "the literal-only form (`let mut k : Nat := 7`, same loop) also "
                     "verifies and mentions no symbol of the spec, so no clause "
                     "could have rejected it.",
    },

    # ---- The THIRD recorded finding: the same class in Lean `Int` ----------
    # The second finding's fix (mapping.md §2.1) fixed the realization of every
    # `Nat` operation — and only of `Nat`. A third G-EQ / G-PANEL-1 pass
    # (2026-08-16) then rebuilt the identical attack ONE TYPE OVER, three times,
    # and all three verified while their submitted counterparts did not resolve.
    # `Int` is a THIRD algebra: total at a zero divisor like `Nat`, but signed
    # like Python — and EUCLIDEAN where Python is FLOORED, which is a divergence
    # with no partiality anywhere in it. Measured in this workspace, one build:
    #   (1 : Int) % (-2) = 1      (Python: -1)
    #   (7 : Int) / (-2) = -3     (Python: -4)
    #   (-7 : Int) / (-2) = 4     (Python:  3)
    #   (-7 : Int) % (-2) = 1     (Python: -1)
    #   (5 : Int) / 0 = 0, (5 : Int) % 0 = 5   (Python: ZeroDivisionError)
    # The three shapes are shipped here as POSITIVES, for the same reason as the
    # two `Nat` ones: they are CORRECT Lean modules, so a spec that rejected them
    # would be SPEC-TOO-STRONG, and putting them in the battery is what makes the
    # failure of their counterparts attributable to the translation.
    {
        "id": "pos-control-dead-int-arith",
        "kind": "soundness",
        "expect": "verify",
        # `((pageRange.length : Int) / 0).toNat`: Int division by zero is 0 and
        # `Int.toNat 0` is 0, so the counter is unchanged. The value reaches `i`.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let _z : Nat := ((pageRange.length : Int) / 0).toNat\n"
                  + _RESULT_INIT),
            _COUNTER_INIT,
            "    let mut i := pageRange.length + _z"),
        "rationale": "a CORRECT impl that divides an `Int` by zero and adds the "
                     "result to the loop counter. It MUST verify: `Int` division is "
                     "TOTAL (`a / 0 = 0`), so `_z` is `0`, the counter is "
                     "`pageRange.length`, and the traversal is the frozen one. This "
                     "is the first shape of the THIRD recorded G-EQ / G-PANEL-1 "
                     "finding (2026-08-16): the attack verified and its submitted "
                     "counterpart wrote `len(self.page_range) // 0`, raising "
                     "`ZeroDivisionError` — FAIL_TO_PASS 0/1, PASS_TO_PASS 20/20, "
                     "`completed=true`. It is the SECOND finding's shape written one "
                     "type over, and it reopened it for exactly one reason: "
                     "mapping.md §2.1's realization table was scoped to `Nat`. §2.1 "
                     "now states the realization LAW for every Lean operation and "
                     "tables `Int` in full; `conformance_check.check_int_algebra` "
                     "measures the Python side, `admiss-int-semantics-carried` pins "
                     "the Lean side in-region, and the counterpart under the "
                     "corrected realization was measured to RESOLVE (refinement.md "
                     "§B''').",
    },
    {
        "id": "pos-control-emod-convention",
        "kind": "soundness",
        "expect": "verify",
        # `((1 : Int) % (-2)).toNat` is 1 in Lean (Euclidean remainder, always
        # non-negative), so the counter is `length + 1 - 1 = length`. NOTHING is
        # partial here: both operands are total in both languages and no zero
        # divisor appears. The divergence is purely the CONVENTION.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let d : Nat := ((1 : Int) % (-2)).toNat\n" + _RESULT_INIT),
            _COUNTER_INIT,
            "    let mut i := pageRange.length + d - 1"),
        "rationale": "a CORRECT impl whose loop bound is computed through an `Int` "
                     "remainder by a NEGATIVE divisor. It MUST verify: Lean's `%` on "
                     "`Int` is `Int.emod`, the EUCLIDEAN remainder, which is always "
                     "non-negative — `(1 : Int) % (-2) = 1` (measured) — so `d = 1`, "
                     "the counter is `pageRange.length + 1 - 1 = pageRange.length`, "
                     "and the traversal is the frozen one. This is the SHARPEST of "
                     "the three third-finding shapes and the reason the fix could not "
                     "be a zero-divisor guard: there is no partiality anywhere in it. "
                     "Python's `%` is FLOOR-mod, so the naive counterpart computed "
                     "`1 % -2 = -1`, the bound became `length - 1`, the last sub-view "
                     "was dropped, and the harness recorded FAIL_TO_PASS 0/1 with "
                     "PASS_TO_PASS 20/20. Realized per the corrected mapping.md §2.1 "
                     "(`a % b` -> `a % abs(b)` for `b ≠ 0`), the same counterpart "
                     "RESOLVES (refinement.md §B''').",
    },
    {
        "id": "pos-control-emod-guarded-branch",
        "kind": "soundness",
        "expect": "verify",
        # The same Euclidean remainder, but CONSUMED BY A BRANCH rather than
        # discarded: `((1 : Int) % (-2)) < 0` is False in Lean, so the else-branch
        # always runs and the fold is the frozen one.
        "module": _swap(
            _BASE, _DO_BODY,
            "      let p := pageRange[i - 1]?\n"
            "      if ((1 : Int) % (-2)) < 0 then\n"
            "        result := result\n"
            "      else\n"
            "        result := (p.map pageOf).toList ++ result\n"
            "      i := i - 1"),
        "rationale": "a CORRECT impl whose loop body is GUARDED by the sign of an "
                     "`Int` remainder. It MUST verify: `(1 : Int) % (-2) = 1`, so "
                     "`1 < 0` is False, the else-branch always runs, and every index "
                     "is prepended exactly as in the frozen body. This is the third "
                     "shape of the third recorded finding, and it is the one that "
                     "answers an objection to the other two: here the arithmetic "
                     "value is NOT discarded, it is consumed by control flow, so "
                     "\"a postcondition cannot constrain a discarded local\" is not "
                     "what makes the class inexpressible. What makes it "
                     "inexpressible is that the guard is a CLOSED term — it mentions "
                     "no input and no output — so no predicate over `pageRange` and "
                     "`out` can see it (mapping.md §2.1 rule R0). Its naive "
                     "counterpart computed `1 % -2 = -1 < 0`, took the no-op branch "
                     "every time and yielded NO sub-views at all: FAIL_TO_PASS 0/1, "
                     "PASS_TO_PASS 20/20. Realized per §2.1 it RESOLVES "
                     "(refinement.md §B''').",
    },
    {
        "id": "pos-control-fixed-width-wraparound",
        "kind": "soundness",
        "expect": "verify",
        # A FOURTH algebra, found by looking for the next type over before an
        # auditor did: `UInt8` arithmetic is MODULAR. `(200 : UInt8) + 100 = 44`
        # (measured), so `d = 44 - 43 = 1` and the counter is unchanged.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let d : Nat := ((200 : UInt8) + 100).toNat - 43\n"
                  + _RESULT_INIT),
            _COUNTER_INIT,
            "    let mut i := pageRange.length + d - 1"),
        "rationale": "a CORRECT impl whose loop bound is computed through "
                     "FIXED-WIDTH arithmetic. It MUST verify: `UInt8` addition is "
                     "modular, so `(200 : UInt8) + 100 = 44` (measured, one build), "
                     "`d = 44 - 43 = 1`, the counter is `pageRange.length`, and the "
                     "traversal is the frozen one. This case was NOT submitted by an "
                     "auditor — it is the next type over from the third recorded "
                     "finding, shipped because the first two rounds of that finding "
                     "were the same defect re-found in a type the map had not "
                     "reached, and the fix is only credible if it is the LAW rather "
                     "than a list of the types already attacked. Its naive "
                     "counterpart would compute `300 - 43 = 257`. mapping.md §2.1 "
                     "covers it twice over: rule R0 (a closed term is realized by "
                     "the value it evaluates to, here `44`) and the fixed-width row "
                     "of the R1 table (`a + b` -> `(a + b) % 2^n`), with "
                     "`conformance_check.check_uint_algebra` measuring the Python "
                     "side.",
    },

    # ---- The FOURTH recorded finding: an unbounded CONTAINER, not a number ----
    # The third finding's fix stated the realization as a LAW over types. A fourth
    # G-EQ / G-PANEL-1 pass (2026-08-16) then broke it WITHOUT leaving the types
    # already tabled, by attacking COMPOSITION instead: it assembled its Python
    # counterpart out of two rows the map already carried — `List.range n` ->
    # `range(n)` and `xs.length` -> `len(xs)` — and got `len(list(range(n)))`,
    # which raises `OverflowError: Python int too large to convert to C ssize_t`
    # for every `n >= 2 ** 63`, while the Lean composite `(List.range n).length`
    # answers `n` for every `n : Nat`. Measured, this workspace:
    #   sys.maxsize             = 2**63 - 1
    #   len(range(2**62))       = 4611686018427387904
    #   len(range(2**63))       -> OverflowError    (also 2**64, 2**66)
    #   len(list(range(2**66))) -> OverflowError
    # So the defect is DEFINEDNESS, not cost: the raise is immediate. The fix is
    # mapping.md §2.1's new rule R2 — a composite is realized from its own
    # defining equation, not by chaining rows, whenever an intermediate leaves
    # what Python can represent; REALIZE THE LENGTH, NOT THE LIST. Lean's own
    # `List.length_range` gives `(List.range n).length = n`, so `n` is the
    # realization. The three shapes below are the auditor's, shipped as POSITIVES
    # for the same reason as the five before them: they are CORRECT Lean modules,
    # a spec that rejected them would be SPEC-TOO-STRONG, and having them in the
    # battery is what makes the failure of the naive counterparts attributable to
    # the translation. All three verify (measured, exit 0), and all three of their
    # counterparts RESOLVE once realized per R2 (refinement.md §B'''').
    #
    # NOTE what is different about this family, because it changes the argument:
    # the CLOSED variant of these prologues does NOT verify — `0 * (List.range
    # (2 ^ 70)).length` with a literal exponent TIMES OUT at 900 s (measured),
    # because the elaborator tries to evaluate it. So unlike the second and third
    # findings, this class is NOT inexpressible by the closedness route of
    # mapping.md §2.1 R0. It is inexpressible for the stronger reason recorded in
    # `admiss-postcondition-single-valued` below: this spec's obligation is
    # SINGLE-VALUED, so every verifying impl computes exactly `pageSeq pageRange`,
    # and no strengthening can reject one of these without rejecting gold too.
    {
        "id": "pos-control-dead-range-materialization",
        "kind": "soundness",
        "expect": "verify",
        # `0 * (List.range N).length` where `N = 2 ^ (64 + pageRange.length)`.
        # `Nat.zero_mul` closes it at 0 without ever building the list, which is
        # exactly why the realization must not build it either.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let _z : Nat := 0 * (List.range "
                  "(2 ^ (64 + pageRange.length))).length\n"
                  + _RESULT_INIT),
            _COUNTER_INIT,
            "    let mut i := pageRange.length + _z"),
        "rationale": "a CORRECT impl that multiplies the length of an astronomically "
                     "long `List.range` by zero and adds the result to the loop "
                     "counter. It MUST verify: `0 * k = 0` for every `k : Nat` "
                     "(`Nat.zero_mul`), so `_z = 0`, the counter is "
                     "`pageRange.length`, and the traversal is the frozen one — and it "
                     "verifies without evaluating the range, because the proof is by "
                     "the multiplication law and not by computation. This is the "
                     "MINIMAL witness of the FOURTH recorded G-EQ / G-PANEL-1 finding "
                     "(2026-08-16), and it is the first of the four that did not need "
                     "a new TYPE: the auditor built its counterpart compositionally "
                     "out of two rows mapping.md §2.1 already carried, `List.range n` "
                     "-> `range(n)` and `xs.length` -> `len(xs)`, giving "
                     "`len(list(range(2 ** (64 + n))))`, which raises `OverflowError: "
                     "Python int too large to convert to C ssize_t` in ~1e-5 s — "
                     "FAIL_TO_PASS 0/1, PASS_TO_PASS 20/20, `completed=true`. So it is "
                     "a DEFINEDNESS divergence, not the cost caveat: CPython bounds "
                     "every container by `ssize_t` (`sys.maxsize = 2^63 - 1`, "
                     "measured) where Lean's `List.length` returns an unbounded "
                     "`Nat`. §2.1 now carries rule R2 — a composite is realized from "
                     "ITS OWN defining equation, never by chaining rows through an "
                     "intermediate Python cannot represent — whose one-line form is "
                     "REALIZE THE LENGTH, NOT THE LIST; "
                     "`conformance_check.check_container_realization` measures the "
                     "Python side, `admiss-derived-length-carried` pins the Lean side "
                     "in-region, and the counterpart realized per R2 was measured to "
                     "RESOLVE (refinement.md §B'''').",
    },
    {
        "id": "pos-control-replicate-materialization",
        "kind": "soundness",
        "expect": "verify",
        # A DIFFERENT constructor, to show the defect was never about `range`:
        # `(List.replicate N 0).length * 0`. Naive Python: `len([0] * N) * 0`.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let _z : Nat := (List.replicate "
                  "(2 ^ (64 + pageRange.length)) (0 : Int)).length * 0\n"
                  + _RESULT_INIT),
            _COUNTER_INIT,
            "    let mut i := pageRange.length + _z"),
        "rationale": "the same CORRECT shape through a DIFFERENT unbounded "
                     "constructor. It MUST verify: `List.length_replicate` gives "
                     "`(List.replicate n a).length = n` and `k * 0 = 0`, so `_z = 0` "
                     "and the traversal is the frozen one. It is shipped because the "
                     "auditor submitted it alongside the `range` shape, and it is the "
                     "case that fixes what the finding was ABOUT: not one library "
                     "function, but the composition rule. Any Lean list constructor "
                     "whose length is a closed form of its arguments — `range`, "
                     "`replicate`, `map`, `take`, `drop`, `++`, `reverse` — gives a "
                     "length Lean computes without building the list, and R2 requires "
                     "the realization to do the same. Its naive counterpart "
                     "`len([0] * (2 ** (64 + n))) * 0` raises before it can allocate. "
                     "Realized per R2 as `(2 ** (64 + n)) * 0` it RESOLVES "
                     "(refinement.md §B'''': `resolved=true`, F2P 1/1, P2P 20/20).",
    },
    {
        "id": "pos-control-range-guarded-branch",
        "kind": "soundness",
        "expect": "verify",
        # The derived length CONSUMED BY CONTROL FLOW rather than discarded, so
        # this family's inexpressibility cannot be blamed on a dropped local.
        "module": _swap(
            _BASE, _DO_BODY,
            "      let p := pageRange[i - 1]?\n"
            "      if (List.range (2 ^ (64 + pageRange.length))).length * 0 > 0 then\n"
            "        result := result\n"
            "      else\n"
            "        result := (p.map pageOf).toList ++ result\n"
            "      i := i - 1"),
        "rationale": "a CORRECT impl whose loop body is GUARDED by a derived length. "
                     "It MUST verify: `k * 0 = 0` and `¬ (0 > 0)`, so the "
                     "else-branch always runs and every index is prepended exactly as "
                     "in the frozen body. It is the third shape of the fourth finding "
                     "and it is here for the same reason "
                     "`pos-control-emod-guarded-branch` is: the value is NOT "
                     "discarded, it decides control flow, so \"a postcondition cannot "
                     "constrain a discarded local\" is not what makes the class "
                     "inexpressible. Nor is CLOSEDNESS (mapping.md §2.1 R0) the reason "
                     "this time — measured, the closed variant of this prologue with a "
                     "literal exponent does not verify at all, it TIMES OUT at 900 s, "
                     "because the elaborator tries to evaluate the range. What makes "
                     "it inexpressible is `admiss-postcondition-single-valued`: the "
                     "obligation pins `out` uniquely, so this impl and the frozen one "
                     "are the same function of the input and no predicate over inputs "
                     "and output can separate them. Its naive counterpart never "
                     "evaluated the guard at all — the `len(list(range(...)))` inside "
                     "it raised first — so the iterator yielded nothing: F2P 0/1, P2P "
                     "20/20. Realized per R2 it RESOLVES (refinement.md §B'''').",
    },

    # =====================================================================
    # THE FIFTH FINDING (2026-08-16): the same class one LEVEL up — a STATEMENT
    # rather than an expression. The four rounds above all attacked a value
    # flowing through a prologue; this one attacked the LOOP, so no row of
    # mapping.md §2.1's tables was in a position to say anything about it. The
    # five shapes below are the auditor's, shipped as POSITIVES for the same
    # reason as the twelve before them: they are CORRECT Lean modules, they MUST
    # verify, and a battery that did not record that fact would let the next
    # revision "close" the class by rejecting a faithful impl. All five verify
    # (measured, exit 0, one build each), all five of their naively transliterated
    # counterparts were recorded `completed=false` at the harness's 3600 s timeout
    # while the gold control resolved in 118 s in the same run, and all five of
    # their R3-realized counterparts RESOLVE (measured, one resolve each,
    # serialized: 97.0 s, 99.4 s, 80.1 s, 85.1 s, 83.7 s, every one
    # `resolved=true completed=true`). mapping.md §2.1 R3 is the fix and
    # refinement.md §B''''' records it.
    # =====================================================================

    # ---- the decorative countdown: cost only ----
    {
        "id": "pos-control-cost-countdown",
        "kind": "soundness",
        "expect": "verify",
        # A whole LOOP inserted before the frozen traversal, whose annotations say
        # it does nothing: `invariant True`, `done_with k = 0`. The frozen impl and
        # the frozen proof body below it are untouched.
        "module": _swap(
            _BASE, _RESULT_INIT,
            _RESULT_INIT + "\n"
            "    let mut k : Nat := 2 ^ (64 + pageRange.length)\n"
            "    while k > 0\n"
            "      invariant True\n"
            "      done_with k = 0\n"
            "      decreasing k\n"
            "    do\n"
            "      k := k - 1"),
        "rationale": "a CORRECT impl with a DECORATIVE loop in front of the frozen "
                     "traversal. It MUST verify: the countdown modifies only `k`, its "
                     "invariant is `True`, its measure descends, and it leaves "
                     "`result` untouched, so the frozen invariants and the frozen "
                     "proof script close the obligation unchanged. Rejecting it would "
                     "be SPEC-TOO-STRONG on the SCHEDULE of a loop that computes "
                     "nothing. The auditor's counterpart transcribed it as "
                     "`k = 2 ** (64 + len(page_range))` plus a Python `while k > 0: "
                     "k -= 1`, which was recorded `completed=false` at the 3600 s "
                     "harness timeout. That is not a slower realization, it is not a "
                     "realization: a statement that does not finish denotes nothing. "
                     "Per mapping.md §2.1 R3 the loop is realized by its DENOTATION — "
                     "`I ∧ D` determines `k = 0`, so the realization is `k = 0` — and "
                     "that counterpart RESOLVES in 97.0 s (measured).",
    },

    # ---- the same, with an initialiser Python cannot even build ----
    {
        "id": "pos-control-cost-countdown-huge",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _RESULT_INIT,
            _RESULT_INIT + "\n"
            "    let mut k : Nat := 2 ^ (2 ^ (64 + pageRange.length))\n"
            "    while k > 0\n"
            "      invariant True\n"
            "      done_with k = 0\n"
            "      decreasing k\n"
            "    do\n"
            "      k := k - 1"),
        "rationale": "the same decorative loop with a DOUBLY exponential initialiser, "
                     "and it separates COST from DEFINEDNESS — the distinction "
                     "refinement.md §B'' got wrong and §B'''' corrected. The shape "
                     "above is merely infeasible to run; this one cannot be "
                     "REPRESENTED: `2 ** (2 ** 64)` raises `MemoryError` after 15 s "
                     "under a 2 GiB cap (measured), so mapping.md §2.1's `Nat` row for "
                     "`a ^ b` is not a realization above what Python can hold and now "
                     "carries that side condition explicitly, exactly as "
                     "`xs.length -> len(xs)` does. It MUST verify: Lean's `2 ^ m` is an "
                     "ordinary closed term the kernel never expands, and the loop still "
                     "modifies only `k`. Realized per R3 (`I ∧ D` gives `k = 0`, so "
                     "the unrepresentable initialiser is never built) its counterpart "
                     "RESOLVES in 99.4 s (measured). Its sibling `atk_8`, which widened "
                     "the frozen counter by the same term, is REJECTED — the elaborator "
                     "aborts with a stack overflow — which is worth recording: the Lean "
                     "side is not indifferent to these terms either, it just draws the "
                     "line somewhere else than CPython does.",
    },

    # ---- the countdown's exit value CONSUMED BY CONTROL FLOW ----
    {
        "id": "pos-control-cost-guarded-body",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _COUNTER_INIT,
                  _COUNTER_INIT + "\n"
                  "    let mut k : Nat := 2 ^ (64 + pageRange.length)\n"
                  "    while k > 0\n"
                  "      invariant True\n"
                  "      done_with k = 0\n"
                  "      decreasing k\n"
                  "    do\n"
                  "      k := k - 1"),
            _DO_BODY,
            "      let p := pageRange[i - 1]?\n"
            "      if k > 0 then\n"
            "        result := result\n"
            "      else\n"
            "        result := (p.map pageOf).toList ++ result\n"
            "      i := i - 1"),
        "rationale": "the countdown's EXIT VALUE decides the loop body's branch, so "
                     "this family cannot be dismissed as a dead statement any more than "
                     "`pos-control-emod-guarded-branch` or "
                     "`pos-control-range-guarded-branch` could be dismissed as dead "
                     "locals. It MUST verify: `done_with k = 0` gives the continuation "
                     "`k = 0`, so `¬ (k > 0)` and the else-branch always runs, which is "
                     "the frozen body. This is the case that fixes R3's SHAPE: the rule "
                     "cannot be \"drop a loop whose result is unused\", because the "
                     "result IS used here; it has to be \"realize the loop by the "
                     "`I ∧ D` the verifier hands the continuation\", which then decides "
                     "the guard as well. Counterpart, realized per R3: `k = 0` then the "
                     "guard's else-branch, RESOLVES in 80.1 s (measured).",
    },

    # ---- the frozen loop's OWN counter widened ----
    {
        "id": "pos-control-widened-counter",
        "kind": "soundness",
        "expect": "verify",
        # No extra loop: the frozen loop itself starts astronomically high. The
        # `i ≤ pageRange.length` invariant is dropped (it is FALSE at entry now)
        # and the obligation is reproved by cases on `i ≤ pageRange.length`.
        "module": _swap(
            _swap(_BASE, _LOOP_HEAD,
                  "    let mut i := pageRange.length + 2 ^ (64 + pageRange.length)\n"
                  "    while i > 0\n"
                  "      invariant result = pageSeq (pageRange.drop i)\n"
                  "      done_with i = 0\n"
                  "      decreasing i"),
            _PROOF_BODY,
            "  loom_solve\n"
            "  · by_cases h : i ≤ pageRange.length\n"
            "    · rw [pageSeq_drop_step pageRange i (by omega) h]\n"
            "      simp_all\n"
            "    · have h1 : pageRange.length ≤ i - 1 := by omega\n"
            "      have h2 : pageRange.length ≤ i := by omega\n"
            "      rw [List.getElem?_eq_none (by omega), List.drop_eq_nil_of_le h1]\n"
            "      rw [List.drop_eq_nil_of_le h2] at invariant_1\n"
            "      simp_all\n"
            "  · rw [List.drop_eq_nil_of_le (Nat.le_add_right _ _)]\n"
            "    rfl"),
        "rationale": "the sharpest shape of the fifth finding: no decorative loop is "
                     "added at all, the FROZEN loop's own counter starts at "
                     "`pageRange.length + 2 ^ (64 + pageRange.length)`. The extra "
                     "iterations read past the end of the index sequence, `[i-1]?` "
                     "answers `none`, and `pageSeq (drop i)` is `pageSeq []`, so they "
                     "prepend nothing — the impl is CORRECT and MUST verify. It carries "
                     "its own proof, because the frozen `i ≤ pageRange.length` "
                     "invariant is FALSE at entry here and is therefore dropped: the "
                     "obligation is reproved by cases (in range, the frozen drop-step; "
                     "out of range, `List.getElem?_eq_none` and "
                     "`List.drop_eq_nil_of_le`), with the `prove_correct "
                     "enumeratePages by` header untouched and nothing assumed. Why it "
                     "matters beyond the countdown: R3's side condition is doing real "
                     "work here rather than trivially — the loop MODIFIES `result`, so "
                     "the realization is licensed only because this loop's OWN "
                     "invariant `result = pageSeq (pageRange.drop i)` together with "
                     "`done_with i = 0` DETERMINES `result = pageSeq pageRange`. "
                     "Counterpart, realized per R3: the frozen traversal, RESOLVES in "
                     "85.1 s (measured). Transcribed step for step it is "
                     "`completed=false` at 3600 s.",
    },

    # ---- a guard that is provably the constant True: closed by R1, not R3 ----
    {
        "id": "pos-control-two-pow-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _DO_BODY,
                  "      let p := pageRange[i - 1]?\n"
                  "      if 2 ^ (2 ^ (64 + pageRange.length)) > 0 then\n"
                  "        result := (p.map pageOf).toList ++ result\n"
                  "      else\n"
                  "        result := result\n"
                  "      i := i - 1"),
            _PROOF_BODY,
            "  loom_solve\n"
            "  all_goals first\n"
            "    | exact absurd (Nat.two_pow_pos (2 ^ (64 + pageRange.length))) "
            "(by assumption)\n"
            "    | (rw [pageSeq_drop_step pageRange i (by omega) (by omega)]; "
            "simp_all)"),
        "rationale": "the fifth shape, and the one that needs NO new rule — which is "
                     "why it is shipped separately from the four above. Its guard "
                     "`2 ^ (2 ^ (64 + pageRange.length)) > 0` is provably the constant "
                     "`True` (`Nat.two_pow_pos`), so the prepend always happens and the "
                     "impl is CORRECT; it MUST verify. mapping.md §2.1 R1 has said "
                     "since the third finding that where a Lean sub-term is provably a "
                     "constant the realization IS that constant, so the realization of "
                     "this guard is `if True`, not `if 2 ** (2 ** (64 + n)) > 0` — the "
                     "counterpart that transliterated the arithmetic was recorded "
                     "`completed=false` at 3600 s, and the R1 realization RESOLVES in "
                     "83.7 s (measured). It is here as a positive because the rule "
                     "being already written is not the same thing as the battery "
                     "recording that the shape verifies: the next revision could "
                     "otherwise \"close\" the fifth finding by rejecting a faithful "
                     "impl whose guard happens to be a large power of two.",
    },

    # The SIXTH recorded finding's shape (refinement.md §B''''''): a DEAD local
    # bound to a `^` value above mapping.md §2.1's side condition. The map had no
    # rule for it — R0 needs a closed term, R1 a total Python operation, R2 a
    # consuming composite and R3 an annotated statement — so §2.1 now carries R4: a
    # binding nothing READS denotes the identity, and its realization is the empty
    # statement. This case is the attack module itself, so the battery records that
    # the SPEC accepts it and the submitted patch failed by translation alone.
    {
        "id": "pos-control-dead-pow-local",
        "kind": "soundness",
        "expect": "verify",
        # `_z` is never read: not by the loop, not by the return, not even by an
        # invariant. The value is astronomical in Lean and costs nothing, because
        # `Nat.pow` at a symbolic exponent never reduces.
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    let _z : Nat := 2 ^ (2 ^ (64 + pageRange.length))\n"
                  + _RESULT_INIT),
            _PROOF_BODY,
            "  loom_solve\n"
            "  all_goals first\n"
            "  | trivial\n"
            "  | (rw [pageSeq_drop_step pageRange i (by omega) (by omega)]; "
            "simp_all)\n"
            "  | simp_all\n"
            "  | omega"),
        "rationale": "a CORRECT impl that binds a local to "
                     "`2 ^ (2 ^ (64 + pageRange.length))` and never reads it. It MUST "
                     "verify: the traversal below is the frozen one, and `_z` is "
                     "invisible to any predicate over `pageRange` and `out`, so a spec "
                     "that rejected it would be SPEC-TOO-STRONG about a statement it "
                     "cannot observe — the argument pos-control-dead-nat-arith has "
                     "carried since the second finding, now at a value Python cannot "
                     "hold rather than at an arithmetic convention. This is the shape "
                     "of the SIXTH recorded G-EQ / G-PANEL-1 finding (2026-08-16): the "
                     "attack verified here and its submitted counterpart transliterated "
                     "`_z = 2 ** (2 ** (64 + len(page_range)))`, which CPython cannot "
                     "build (2 305 843 009 213 693 953 bytes by arithmetic at the "
                     "smallest input; MemoryError in a memory-capped child, measured), "
                     "so `__iter__` raised on every input and the patch did not "
                     "resolve. NO CLAUSE OF THIS SPEC COULD HAVE CLOSED IT: a "
                     "postcondition is a predicate over the inputs and the output, and "
                     "`_z` is in neither. The defect was mapping.md §2.1's, which had a "
                     "side-conditioned `^` row and no rule for a BINDING; it now "
                     "carries R4 (a binding is realized by its denotation, and one "
                     "nothing reads denotes the identity, so its realization is the "
                     "empty statement), with the side condition DECIDED by "
                     "`impl_reads_binding` and both directions measured by "
                     "`check_dead_binding_realization` (refinement.md §B'''''').",
    },

    # =====================================================================
    # ADMISSIBILITY. This bundle declares no `require`, so the nagini "a normal
    # input satisfies the precondition" probe has no precondition to admit. Two
    # analogues are shipped: the obligation must not be unsatisfiable or
    # degenerate at an F2P-shaped input, and the carrier's own domain claim — the
    # thing the strengthening rests on — must be checkable in-region.
    # =====================================================================
    {
        "id": "admiss-postimage-grounded-at-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        # Keeps the frozen impl and the frozen proof body VERBATIM and adds an
        # in-region assertion about the post-image at the failing test's shape.
        # The assert is LIVE, measured with a negative control: the same case
        # claiming the two-index run's post-image has length 3 FAILS, leaving
        # `⊢ ∀ (hn : 2 ≤ numPages), ... (pageSeq [⟨1,⋯⟩, ⟨2,⋯⟩]).length = 3 ...`
        # unsolved — so nothing is closing this regardless of what it claims.
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    assert (with_name_prefix `adm\n"
            "      (∀ hn : 2 ≤ numPages,\n"
            "        pageSeq [⟨1, by omega, by omega⟩, ⟨2, by omega, by omega⟩]\n"
            "            = [pageOf ⟨1, by omega, by omega⟩, pageOf ⟨2, by omega, by omega⟩] ∧\n"
            "        (pageSeq [⟨1, by omega, by omega⟩, ⟨2, by omega, by omega⟩]).length = 2 ∧\n"
            "        pageSeq ([] : List PageIdx) = [] ∧\n"
            "        (pageSeq [⟨1, by omega, by omega⟩, ⟨2, by omega, by omega⟩]\n"
            "            = pageSeq [⟨2, by omega, by omega⟩, ⟨1, by omega, by omega⟩] →\n"
            "          pageOf ⟨1, by omega, by omega⟩ = pageOf ⟨2, by omega, by omega⟩)))\n"
            + _RESULT_INIT),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at the "
                     "F2P-shaped input, discharged in-region while the frozen "
                     "obligation closes verbatim. Four claims about the post-image "
                     "at the two-index run the failing test's fixture produces (3 "
                     "items at 2 per page, so `2 ≤ numPages` — the hypothesis the "
                     "carrier now requires before an index can even be named, and "
                     "satisfiable because nothing pins the opaque count): the "
                     "post-image is exactly the two sub-views in order (so the "
                     "clause names a REACHABLE value, not an unsatisfiable one); it "
                     "has one element per index (count is 2, not 1 or 3); the empty "
                     "run maps to the empty family (the base case is inhabited); and "
                     "the fold is ORDER-SENSITIVE — it can only identify the run "
                     "with its reverse when the two sub-views coincide, so the clause "
                     "is not silently order-blind. If any of these failed, the single "
                     "clause would be degenerate or unsatisfiable at a test-shaped "
                     "input, which is the total-carrier form of PRECOND-TOO-STRONG: "
                     "an obligation no faithful impl can meet would make every "
                     "reject case vacuous. The frozen impl AND the frozen proof body "
                     "are kept byte-for-byte, so a failure here would be "
                     "attributable to the assert alone. (Sibling: "
                     "admissibility-f2p-shaped, re-aimed from the "
                     "fractional-permission protocol — which has no analogue here — "
                     "onto the post-image at the same F2P-shaped input.)",
    },

    # THE STRENGTHENING, AS A POSITIVE OBLIGATION. The reject cases below record
    # that the surviving guarded attacks are refused; this case records the claim
    # that makes the unguarded ones unwritable, machine-checked inside the module
    # rather than asserted in prose: every index the operation can hand the
    # accessor lies in the accessor's domain. LIVE, measured with a negative
    # control: the same assert claiming `2 ≤ p.val` FAILS with
    # `Type mismatch: p.property has type 1 ≤ ↑p ∧ ↑p ≤ numPages but is expected
    # to have type 2 ≤ ↑p ∧ ↑p ≤ numPages` — i.e. the bound being read off the
    # carrier is the real one, not whatever the assert asks for.
    {
        "id": "admiss-accessor-domain-carried",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _RESULT_INIT,
                  "    assert (with_name_prefix `dom\n"
                  "      (∀ p : PageIdx, 1 ≤ p.val ∧ p.val ≤ numPages))\n"
                  + _RESULT_INIT),
            _PROOF_BODY,
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (rw [pageSeq_drop_step pageRange i (by omega) (by omega)]; "
            "simp_all)\n"
            "    | (intro p; exact p.2)"),
        "rationale": "the accessor's DOMAIN is carried by its argument type, and "
                     "this case discharges that in-region: every index of the "
                     "carrier satisfies `1 ≤ p.val ∧ p.val ≤ numPages`, so every "
                     "accessor application any implementation of this method can "
                     "write is one the real accessor admits. That is the admissibility "
                     "half of the partial-domain story — the reject cases show wrong "
                     "index CHOICES are refused, and this shows the ones that remain "
                     "expressible are all legal — and it is the claim the carrier "
                     "change rests on, so it is checked by the verifier rather than "
                     "argued in a comment. It is also what makes the modeled "
                     "operation TOTAL without totalizing the accessor: the method has "
                     "no failure mode because it cannot name an index outside the "
                     "domain, not because the accessor was extended to answer "
                     "everywhere. The frozen impl is kept byte-for-byte; only the "
                     "assert and the one extra tactic branch it needs are added.",
    },

    # THE SECOND CARRIER CLAIM, AS A POSITIVE OBLIGATION: the `Nat` ALGEBRA.
    # `Nat` is not the integers. Its operations are TOTAL, and total by
    # SATURATION: subtraction floors at 0 and division by zero answers 0. A
    # translation that maps them onto Python's `-` and `//` therefore changes
    # algebra silently, and an expression that is defined here becomes one that
    # RAISES there. mapping.md §2.1 fixes the realization instead; this case is
    # the Lean half of that section, discharging in-region exactly the four laws
    # `conformance_check.check_nat_algebra` measures on the Python half, so the
    # two sides are pinned to one shared set of equations rather than to a
    # resemblance between two operator spellings. See refinement.md §B''.
    #
    # LIVE, measured with three negative controls, one build each, each leaving
    # the FALSE claim as the residual goal (so nothing here is closed by the
    # frozen script regardless of what it asks):
    #   `a / 0 = 1`                  -> unsolved `⊢ ... ∧ (∀ a, a / 0 = 1) ∧ ...`
    #   `a ≤ b → a - b = 1`          -> unsolved, same shape
    #   `a - b + b = a` (hyp dropped) -> unsolved, same shape
    # The third is the load-bearing one: it fails precisely BECAUSE `Nat`
    # subtraction truncates, so this case is measuring the saturation itself and
    # not a tautology about ordinary subtraction.
    {
        "id": "admiss-nat-semantics-carried",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl AND frozen proof body byte-for-byte; only the assert added.
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    assert (with_name_prefix `nat\n"
            "      ((∀ a b : Nat, b ≤ a → a - b + b = a) ∧\n"
            "       (∀ a b : Nat, a ≤ b → a - b = 0) ∧\n"
            "       (∀ a : Nat, a / 0 = 0) ∧\n"
            "       (∀ a : Nat, a % 0 = a)))\n"
            + _RESULT_INIT),
        "rationale": "the `Nat` arithmetic this method's impl region may use is "
                     "TOTAL BY SATURATION, and that is discharged in-region rather "
                     "than assumed: subtraction truncates at zero (`a ≤ b → "
                     "a - b = 0`, and the cancellation law holds only under "
                     "`b ≤ a`), division and modulo by zero answer `0` and `a`. "
                     "These are the same four equations `conformance_check.py`'s "
                     "`check_nat_algebra` measures exhaustively of its Python "
                     "realization `nat_sub`/`nat_div`/`nat_mod`, which is what makes "
                     "mapping.md §2.1 a checked correspondence between two algebras "
                     "instead of an unstated assumption that Lean's `-` and `/` are "
                     "Python's. Why it belongs in the ADMISSIBILITY lane rather than "
                     "the reject lane: these operations are perfectly admissible — a "
                     "faithful impl may use them, and the frozen one does (`i - 1`) "
                     "— so the obligation is not that they be refused but that what "
                     "they MEAN be on the record and be the same on both sides of "
                     "the refinement. The recorded G-EQ finding this addresses was "
                     "not a missing clause but a mistranslation, and a clause could "
                     "not have closed it (see the module docstring's ARITHMETIC "
                     "TOTALITY DRIFT block for the measurement).",
    },

    # The `Int` half of the same obligation, added for the THIRD recorded finding.
    # `Int` is not `Nat` and it is not Python's `int`: it is signed (so nothing
    # truncates at zero), it is TOTAL at a zero divisor (so nothing raises), and
    # its `/` and `%` are the EUCLIDEAN pair `Int.ediv`/`Int.emod` — remainder
    # always non-negative — where Python's are FLOORED. The four literal equations
    # below are exactly the four places the two disagree, and they are exactly the
    # fixtures `conformance_check.check_int_algebra` measures its realization
    # against.
    #
    # LIVE, measured with five negative controls, one build each, each leaving the
    # false claim as the residual goal (`⊢ (∀ (a : ℤ), a / 0 = 1) ∧ ...` for the
    # last one), so nothing here is being closed by the frozen script regardless
    # of what it asks:
    #   `(1 : Int) % (-2) = -1`   (Python's answer)  -> unsolved
    #   `(7 : Int) / (-2) = -4`   (Python's answer)  -> unsolved
    #   `(-7 : Int) / (-2) = 3`   (Python's answer)  -> unsolved
    #   `(-7 : Int) % (-2) = -1`  (Python's answer)  -> unsolved
    #   `∀ a : Int, a / 0 = 1`                       -> unsolved
    # The first four are the load-bearing ones: each is FALSE in Lean and TRUE of
    # the naive translation, so this case fails exactly when the algebra is read
    # as Python's.
    {
        "id": "admiss-int-semantics-carried",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl AND frozen proof body byte-for-byte; only the assert added.
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    assert (with_name_prefix `int\n"
            "      ((∀ a : Int, a / 0 = 0) ∧\n"
            "       (∀ a : Int, a % 0 = a) ∧\n"
            "       ((1 : Int) % (-2) = 1) ∧\n"
            "       ((7 : Int) / (-2) = -3) ∧\n"
            "       ((-7 : Int) / (-2) = 4) ∧\n"
            "       ((-7 : Int) % (-2) = 1)))\n"
            + _RESULT_INIT),
        "rationale": "the `Int` arithmetic this method's impl region may use — and "
                     "`Int` is spec-visible, since `pageOf : PageIdx → List Int` — is "
                     "TOTAL AT A ZERO DIVISOR and EUCLIDEAN, and that is discharged "
                     "in-region rather than assumed: `a / 0 = 0`, `a % 0 = a`, and "
                     "the four literal equations where Lean's answer is not Python's "
                     "(`1 % -2 = 1` not `-1`; `7 / -2 = -3` not `-4`; "
                     "`-7 / -2 = 4` not `3`; `-7 % -2 = 1` not `-1`). These are the "
                     "same equations `conformance_check.check_int_algebra` measures "
                     "of its Python realization `int_ediv`/`int_emod`, so mapping.md "
                     "§2.1's `Int` rows are a CHECKED correspondence between two "
                     "algebras on both sides at once rather than a resemblance "
                     "between two operator spellings. Why the ADMISSIBILITY lane and "
                     "not the reject lane: these operations are perfectly admissible "
                     "— a faithful impl may use them — so the obligation is not that "
                     "they be refused but that what they MEAN be on the record. This "
                     "is the sibling of `admiss-nat-semantics-carried`, and the pair "
                     "exists because the SAME defect was recorded twice, once per "
                     "algebra: the second finding was `Nat`, the third was `Int`. "
                     "Neither was closable by a clause (see the module docstring's "
                     "ARITHMETIC TOTALITY DRIFT block for the literal-only "
                     "measurement).",
    },

    # The CONTAINER half of the same obligation, added for the FOURTH recorded
    # finding. The two cases above pin what Lean's NUMBERS mean; this one pins what
    # Lean's derived LENGTHS are, which is the thing the fourth finding showed a
    # realization can get wrong without touching a number at all. Every equation
    # below is a closed form: Lean computes the length from the constructor's
    # arguments and never builds the list, so a realization that builds the list is
    # not merely slower, it is a DIFFERENT (partial) function — CPython bounds
    # `len` by `ssize_t` where `List.length` returns an unbounded `Nat`. These are
    # exactly the equations `conformance_check.check_container_realization` measures
    # of `range_length`/`replicate_length`/`map_length`/`take_length`/
    # `append_length` on the Python side. See mapping.md §2.1 rule R2 and
    # refinement.md §B''''.
    #
    # LIVE, measured with three negative controls, one build each, each leaving the
    # FALSE claim as the residual goal (`⊢ (∀ (n : ℕ), (List.range n).length =
    # n + 1) ∧ ...` for the first):
    #   `(List.range n).length = n + 1`              -> unsolved
    #   `(List.replicate n a).length = 0`            -> unsolved
    #   `(xs.take k).length = k`   (drops the `min`) -> unsolved
    # The third is the load-bearing one: it is TRUE of Python's `xs[:k]` only when
    # `k ≤ len(xs)`, so it is precisely the place where a realization that reasons
    # about slices instead of about `List.take` would go wrong.
    {
        "id": "admiss-derived-length-carried",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl AND frozen proof body byte-for-byte; only the assert added.
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    assert (with_name_prefix `len\n"
            "      ((∀ n : Nat, (List.range n).length = n) ∧\n"
            "       (∀ (n : Nat) (a : Int), (List.replicate n a).length = n) ∧\n"
            "       (∀ (xs : List Int) (f : Int → Int), (xs.map f).length = xs.length) ∧\n"
            "       (∀ (k : Nat) (xs : List Int), (xs.take k).length = min k xs.length) ∧\n"
            "       (∀ (xs ys : List Int), (xs ++ ys).length = xs.length + ys.length)))\n"
            + _RESULT_INIT),
        "rationale": "the LENGTH of a derived list is a closed form of the "
                     "constructor's arguments, and that is discharged in-region "
                     "rather than assumed: `(List.range n).length = n`, "
                     "`(List.replicate n a).length = n`, `(xs.map f).length = "
                     "xs.length`, `(xs.take k).length = min k xs.length`, "
                     "`(xs ++ ys).length = xs.length + ys.length`. Lean proves each "
                     "WITHOUT building the list, and that is the whole content of "
                     "mapping.md §2.1's rule R2: the realization must do the same, "
                     "because a realization that materializes is a different function "
                     "— `len(list(range(n)))` raises `OverflowError` for `n ≥ 2^63` "
                     "(measured) while the Lean side answers `n` for every `n : Nat`. "
                     "Why the ADMISSIBILITY lane and not the reject lane: these "
                     "constructors are perfectly admissible, and one of them is "
                     "already used by a shipped rival (`List.range pageRange.length` "
                     "in `value-indexed-by-position`), so the obligation is not that "
                     "they be refused but that what their LENGTH is be on the record "
                     "and be the same on both sides of the refinement. This is the "
                     "sibling of `admiss-nat-semantics-carried` and "
                     "`admiss-int-semantics-carried`, and the trio exists because the "
                     "SAME defect was recorded three times in three different places: "
                     "`Nat` (second finding), `Int` (third), and COMPOSITION (fourth). "
                     "None was closable by a clause — see "
                     "`admiss-postcondition-single-valued` for the mechanical reason "
                     "why none of them ever could be.",
    },

    # THE REASON NONE OF THE FOUR FINDINGS WAS CLOSABLE BY A CLAUSE, as a machine
    # -checked obligation instead of a paragraph. Three successive G-EQ passes
    # answered "the spec is too weak" for shapes that were, in fact, CORRECT; each
    # time the honest response was to fix the refinement map. That response is only
    # legitimate if "strengthen the spec instead" is genuinely unavailable, and
    # here that is not a judgement call — it is provable, in one line, from the
    # shape of the obligation:
    #
    #   the spec's only `ensures` is `out = pageSeq pageRange`, which DETERMINES
    #   `out` as a function of the input; so for each input there is EXACTLY ONE
    #   admissible output; so any two impls that verify agree everywhere; so the
    #   frozen impl and every one of the nine arithmetic/container positive controls
    #   (indeed all thirteen positive controls) compute the same
    #   function; so no predicate over (inputs, output) can admit gold and reject
    #   any of them.
    #
    # A spec that pins its output uniquely is MAXIMALLY STRONG on its observable
    # interface: there is no admissible strengthening left, because a strictly
    # stronger postcondition would have to reject `pageSeq pageRange` itself, i.e.
    # reject gold, i.e. be SPEC-TOO-STRONG. Therefore every remaining
    # `verify ⇒ resolved` gap in this cell lives in the refinement map by
    # construction, and "fix the map, not the spec" is the only available repair
    # rather than the convenient one.
    #
    # IT IS AN IN-REGION ASSERT, NOT A PAIR OF NEW THEOREMS, and that was forced
    # rather than chosen: the first form of this case stated `spec_single_valued`
    # and `verify_implies_out_equal` as top-level `theorem`s after the frozen file,
    # and G-PBT correctly refused it — `variant_scope.variant_problems` reports
    # "declares new theorem/lemma [...]: a variant reproves the SAME obligations",
    # because a same-spec variant may not add declarations (measured: G-PBT
    # MALFORMED-TESTS, 1 case, outcome `spec-changed`). The obligation is therefore
    # discharged where every other `admiss-*-carried` case discharges its own, in
    # the impl region under the frozen proof body, which is strictly better: the
    # claim is proved IN the context the method is verified in rather than beside
    # it. `∃!` is spelled out (`∃ o, o = pageSeq pr ∧ ∀ o', o' = pageSeq pr →
    # o' = o`) because the `∃!` notation is measured NOT to be discharged by this
    # bundle's tactic (one build, the goal survives verbatim) while the unfolded
    # form is.
    #
    # LIVE, measured with four negative controls, one build each, each leaving the
    # FALSE claim as its residual goal:
    #   the agreement conjunct denied (`… → o1 ≠ o2`)          -> unsolved
    #   existence denied (`∀ pr o, o ≠ pageSeq pr`)            -> unsolved
    #   agreement without its hypotheses (`∀ pr o1 o2, o1 = o2`) -> unsolved
    #   uniqueness overreaching (`∀ o', o' = o`, no premise)   -> unsolved
    # So the case is not a tautology that would pass however the obligation were
    # written: it is false of a spec that admits no output, false of one that
    # admits several, and false of the two ways of overstating it.
    {
        "id": "admiss-postcondition-single-valued",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl AND frozen proof body byte-for-byte; only the assert added.
        # Nothing in the spec region is touched — the point of the case is a
        # property OF the frozen obligation, proved inside it.
        "module": _swap(
            _BASE, _RESULT_INIT,
            "    assert (with_name_prefix `sv\n"
            "      ((∀ pr : List PageIdx, ∃ o : List (List Int),\n"
            "          o = pageSeq pr ∧ ∀ o' : List (List Int), o' = pageSeq pr → o' = o) ∧\n"
            "       (∀ (pr : List PageIdx) (o1 o2 : List (List Int)),\n"
            "          o1 = pageSeq pr → o2 = pageSeq pr → o1 = o2)))\n"
            + _RESULT_INIT),
        "rationale": "the spec's obligation is a FUNCTION, not a constraint, and this "
                     "case proves it IN-REGION: for every input there is exactly one "
                     "`o` with `o = pageSeq pr` (existence and uniqueness, the `∃!` "
                     "spelled out), hence "
                     "any two verifying impls agree everywhere. That single fact is "
                     "what makes this bundle's four recorded G-EQ findings "
                     "refinement-map defects as a matter of proof rather than of "
                     "preference. A postcondition is a predicate over the inputs and "
                     "the output; this one already pins the output uniquely; so it is "
                     "MAXIMALLY STRONG on its observable interface, and any strictly "
                     "stronger postcondition would have to reject `pageSeq pageRange` "
                     "itself — which is what gold computes — and would be "
                     "SPEC-TOO-STRONG. Concretely: each of the nine arithmetic and "
                     "container positive controls in this battery computes exactly "
                     "`pageSeq pageRange`, identically to the frozen impl, so NO "
                     "clause addable to the spec region can admit gold and reject any "
                     "of them, whatever their prologues look like and whether their "
                     "values are discarded, consumed by a branch, closed or open. "
                     "This is the general form of the argument that earlier revisions "
                     "made twice and got wrong twice — first as \"a postcondition "
                     "cannot constrain a discarded local\" (refuted by "
                     "`pos-control-emod-guarded-branch`, whose value decides a "
                     "branch), then as CLOSEDNESS (refuted by "
                     "`pos-control-dead-range-materialization`, whose prologue reads "
                     "`pageRange` and whose closed variant does not even verify). "
                     "Single-valuedness needs neither premise. Why the ADMISSIBILITY "
                     "lane: it is a positive obligation about the spec being "
                     "well-formed and non-degenerate — it says the obligation has "
                     "exactly one solution per input, so it is neither unsatisfiable "
                     "nor loose — and it is the companion of "
                     "`admiss-postimage-grounded-at-f2p-shape`, which shows that "
                     "unique solution is the RIGHT one at the failing test's shape. "
                     "Measured live against four negative controls (existence "
                     "denied, agreement denied, agreement without its hypotheses, "
                     "and uniqueness overstated), each leaving the false claim as "
                     "its residual goal.",
    },

    # The Lean half of mapping.md §2.1 R3 and of the `^` row's new side
    # condition, discharged IN-REGION rather than asserted in prose. Three
    # claims, one per thing the fifth finding's fix rests on:
    #
    #   1. `0 < 2 ^ n` for every `n : Nat`. This is what makes
    #      `pos-control-two-pow-guard`'s guard the constant `True`, i.e. what R1's
    #      extensionality clause needs to realize it as `True` instead of building
    #      the number. Lean proves it without expanding anything.
    #   2. `k = 0 → k' = 0 → k = k'`: the `done_with` of the decorative countdown
    #      DETERMINES its counter. Trivial as arithmetic and that is the point —
    #      R3's side condition is a determinacy claim, and this is that claim for
    #      the shape R3 was written for.
    #   3. the same for the FROZEN loop, where the side condition is not trivial:
    #      `result = pageSeq (pageRange.drop i)` together with `i = 0` determines
    #      `result`. This is the premise that licenses realizing
    #      `pos-control-widened-counter` as the traversal.
    #
    # Unlike the other `admiss-*-carried` cases this one carries its own tactic
    # body, because `loom_solve` does NOT discharge these three (measured: the
    # assert goal survives verbatim and the frozen `rw ... i ...` then fails with
    # `Unknown identifier i`, since the assert's goal is the first one). The proof
    # is the explicit term the claims need, applied with `all_goals first | ... |
    # <the frozen script>` — the same shape the auditor's own atk_9 used. The
    # `prove_correct enumeratePages by` header is byte-identical, no lemma or axiom
    # is introduced, and the impl region is the frozen one plus the assert.
    #
    # LIVE, measured with three negative controls, one build each: positivity
    # denied (`0 = 2 ^ n`) EXIT 1; determinacy overreaching to a DIFFERENT exit
    # (`i' = 1` in place of `i' = 0`) EXIT 1, leaving exactly the false claim
    # `⊢ pageSeq (List.drop 0 pr) = pageSeq (List.drop 1 pr)` as its residual
    # goal; determinacy stated WITHOUT the `done_with` premises EXIT 1. The first
    # and third fail through the fallback branch (`Unknown identifier i`) because
    # the explicit term stops typechecking against the false claim, so it is the
    # second that exhibits the residual — recorded here rather than implied.
    {
        "id": "admiss-loop-denotation-carried",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _RESULT_INIT,
                "    assert (with_name_prefix `r3\n"
                "      ((∀ n : Nat, 0 < 2 ^ n) ∧\n"
                "       (∀ (k k' : Nat), k = 0 → k' = 0 → k = k') ∧\n"
                "       (∀ (pr : List PageIdx) (r r' : List (List Int)) (i i' : Nat),\n"
                "          r = pageSeq (pr.drop i) → i = 0 →\n"
                "          r' = pageSeq (pr.drop i') → i' = 0 → r = r')))\n"
                + _RESULT_INIT),
            _PROOF_BODY,
            "  loom_solve\n"
            "  all_goals first\n"
            "    | exact ⟨fun n => Nat.two_pow_pos n,\n"
            "             fun k k' hk hk' => by omega,\n"
            "             fun pr r r' i i' h1 h2 h3 h4 => by\n"
            "               subst h2; subst h4; rw [h1, h3]⟩\n"
            "    | (rw [pageSeq_drop_step pageRange i (by omega) (by omega)]; "
            "simp_all)"),
        "rationale": "the three Lean facts mapping.md §2.1's fifth-finding fix rests "
                     "on, discharged where the method is verified: `0 < 2 ^ n` for "
                     "every `n` (so a `2 ^ m > 0` guard is the constant `True` and R1 "
                     "realizes it as `True` rather than building the number, which "
                     "CPython cannot do — `2 ** (2 ** 64)` raises `MemoryError`, "
                     "measured), and TWO determinacy claims, which are R3's side "
                     "condition made checkable: `done_with k = 0` determines the "
                     "decorative countdown's counter, and the frozen loop's "
                     "`result = pageSeq (pageRange.drop i)` with `done_with i = 0` "
                     "determines `result`. R3 licenses a closed-form realization of a "
                     "loop only under that premise, so the premise belongs in the "
                     "battery and not only in the map. Why the ADMISSIBILITY lane and "
                     "not the reject lane: none of the three is a rival's bug — they "
                     "are facts the REALIZATION uses, and the question is whether Lean "
                     "agrees with what mapping.md says it proves. The reject-lane "
                     "companion for this round is `pow-bound-drop-last-four`, whose "
                     "bound is computed by the same `Nat.pow` the five shapes abuse.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a distinct point and the refinement argument for why
    # its faithful counterpart would NOT resolve the failing test.
    #
    # The failing test pulls the sub-views ONE AT A TIME and compares each:
    #   paginator = Paginator([1, 2, 3], 2); it = iter(paginator)
    #   for page, expected in enumerate(([1, 2], [3]), start=1):
    #       assertEqual(expected, list(next(it)))
    # so a counterpart is caught by the FIRST pulled sub-view that differs, and a
    # counterpart that emits extra sub-views AFTER the ones the test pulls is NOT
    # caught. That is why the empty-boundary rival below emits its spurious
    # sub-view FIRST rather than last.
    # =====================================================================

    # ---- COUNT clause: drop the first index (structural; no pageOf assumption) ----
    {
        "id": "partial-domain-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit a sub-view for every index EXCEPT the first: the tail of the run,
        # each mapped through the selector. Correct on the empty/one-index
        # sub-domain; for any run of >= 2 indices it omits the leading sub-view.
        "module": _closed("(pageRange.drop 1).map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that begins the walk one index late (e.g. "
                      "iterating the index sequence from its second element) OMITS "
                      "the first sub-view of every multi-index collection. The "
                      "failing test paginates a 3-item collection at 2 per page and "
                      "compares the FIRST pulled sub-view against [1,2]; dropping "
                      "the first index makes that [3], so the first subtest's "
                      "assertion fails. It would NOT resolve.",
        "rationale": "REJECT from `out = pageSeq pageRange` (COUNT/leading-element "
                     "half): the rival's result is one element shorter than "
                     "`pageSeq` on any non-empty run, so they are unequal. Refuted "
                     "at a three-index run where the rival drops the head sub-view; "
                     "the divergence is a length mismatch, visible WITHOUT any "
                     "assumption about the opaque `pageOf` — the witness binds only "
                     "the count hypothesis the carrier needs to name three indices "
                     "at all, and nothing about the selector.",
        "witness": _witness("(hn : 3 ≤ numPages) ", _lst([1, 2, 3]), ""),
    },

    # ---- COUNT clause, THROUGH THE SATURATING ARITHMETIC: drop the LAST index ----
    # The rival for the `Nat`-algebra half of the map. It computes its own bound
    # with the truncated subtraction `pageRange.length - 1`, which is what makes it
    # interesting rather than a mirror image of drop-first: on the EMPTY run
    # `0 - 1` saturates to `0`, so `take 0 = []` is CORRECT there, and the rival is
    # wrong only on non-empty runs. A refutation therefore cannot be taken at the
    # empty run — the arithmetic hides the bug at exactly the point the
    # spurious-leading rival is refuted at — and the battery ends up exercising
    # `Nat.sub`'s saturation in the reject lane, not just in an assert.
    {
        "id": "truncated-arith-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("(pageRange.take (pageRange.length - 1)).map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that stops one index early (iterating "
                      "`page_range[:len(page_range) - 1]`, the realization of the "
                      "truncated `Nat` bound per mapping.md §2.1) omits the LAST "
                      "sub-view of every collection. The failing test paginates a "
                      "3-item collection at 2 per page and pulls TWO sub-views, "
                      "comparing the second against [3]; a counterpart that emits "
                      "only the first raises StopIteration on the second pull, so "
                      "the test errors. It would NOT resolve. (Contrast the trailing "
                      "EXTRA sub-view discussed under boundary-empty-spurious-"
                      "leading, which the test would not notice: a missing trailing "
                      "sub-view is caught, an extra one is not, which is why one "
                      "rival drops from the end and the other adds at the front.)",
        "rationale": "REJECT from `out = pageSeq pageRange` (COUNT/trailing-element "
                     "half): the rival's result is one element shorter than "
                     "`pageSeq` on every non-empty run. Refuted at the one-index run "
                     "`[⟨2,_⟩]`, where the rival returns `[]` and the spec demands "
                     "`[pageOf ⟨2,_⟩]` — a length mismatch, so the witness needs NO "
                     "assumption about the opaque `pageOf`, only the count "
                     "hypothesis the carrier requires to name index 2 at all. A NEW "
                     "refutation point: no other case in this battery is refuted at "
                     "a one-index run whose index is 2. Not subsumed by drop-first, "
                     "which is wrong at the HEAD and is refuted at a three-index "
                     "run, nor by the spurious-leading boundary rival, which this "
                     "one AGREES with the spec against (both are correct on `[]`, "
                     "and this one only because `Nat` subtraction saturates there — "
                     "that is the point of the case).",
        "witness": _witness("(hn : 2 ≤ numPages) ", _lst([2]), ""),
    },

    # ---- COUNT clause: bound computed through the EUCLIDEAN Int remainder ----
    # The reject-lane case for the THIRD recorded finding, built the same way the
    # `Nat` one was: route a real behavioural bug THROUGH the algebra the map had
    # not covered, so the corrected realization is exercised where a rival is
    # rejected and not only where a positive verifies. `(5 : Int) % (-3) = 2` in
    # Lean (Euclidean, non-negative) and `-1` in Python, so this bound is
    # `length - 2` in Lean — and the rival is wrong for that reason, not for the
    # divergence: the point of the case is that a battery member's bug is now
    # stated in `Int` arithmetic, which no case did before.
    {
        "id": "emod-convention-drop-last-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("(pageRange.take (pageRange.length "
                          "- ((5 : Int) % (-3)).toNat)).map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that stops TWO indices early (iterating "
                      "`page_range[:len(page_range) - 2]`, the realization of this "
                      "bound per mapping.md §2.1: `(5 : Int) % (-3)` is `2`, then "
                      "`Nat` subtraction truncates) omits the last two sub-views of "
                      "every collection. The failing test paginates a 3-item "
                      "collection at 2 per page and pulls TWO sub-views; a "
                      "counterpart that emits NEITHER raises StopIteration on the "
                      "first pull, so the test errors. It would NOT resolve. Note "
                      "the counterpart a NAIVE translation would write instead — "
                      "`len(page_range) - (5 % -3)` = `len + 1` — is a DIFFERENT "
                      "program, which is the whole point of the finding this case "
                      "belongs to.",
        "rationale": "REJECT from `out = pageSeq pageRange` (COUNT/trailing half, at "
                      "width two): the rival's result is two elements shorter than "
                      "`pageSeq` on every run of length ≥ 2, so they are unequal. "
                      "Refuted at the two-index run `[⟨2,_⟩, ⟨3,_⟩]`, where the rival "
                      "returns `[]` and the spec demands two sub-views — a length "
                      "mismatch, so the witness needs NO assumption about the opaque "
                      "`pageOf`, only the count hypothesis the carrier requires to "
                      "name index 3. A NEW refutation point: no other case in this "
                      "battery is refuted at a two-index run that starts at index 2 "
                      "(the order rival's two-index point is `[⟨1,_⟩, ⟨2,_⟩]`, and "
                      "its bug is order, which this rival gets right). What separates "
                      "it from truncated-arith-drop-last is WIDTH and ALGEBRA, and "
                      "the width is what makes the separation observable: at a "
                      "ONE-index run this rival returns `[]` and so does that one, "
                      "but at the two-index run `[⟨2,_⟩, ⟨3,_⟩]` that rival returns "
                      "one sub-view where this one returns none, so the two rivals "
                      "are distinguished at this very point. Its bound is computed "
                      "by `Int.emod` where that "
                      "one's is computed by `Nat.sub`, which is the lane this case "
                      "was added for.",
        "witness": _witness("(hn : 3 ≤ numPages) ", _lst([2, 3]), ""),
    },

    # ---- COUNT clause: bound computed through a DERIVED LENGTH ----------------
    # The reject-lane case for the FOURTH recorded finding, built exactly the way
    # the `Nat` and `Int` ones were: route a real behavioural bug THROUGH the
    # construct the map had mis-realized, so the corrected realization is exercised
    # where a rival is REJECTED and not only where a positive verifies.
    # `(List.replicate 3 (0 : Int)).length` is `3` by `List.length_replicate` — a
    # bound Lean computes without building anything, and a bound no `Nat` or `Int`
    # operation in this battery computes. The rival is wrong because it drops three
    # sub-views, not because of the divergence; the point of the case is that a
    # battery member's bug is now stated in a derived length.
    {
        "id": "derived-length-drop-last-three",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("(pageRange.take (pageRange.length "
                          "- (List.replicate 3 (0 : Int)).length)).map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that stops THREE indices early (iterating "
                      "`page_range[:len(page_range) - 3]`, the realization of this "
                      "bound per mapping.md §2.1 rule R2: "
                      "`(List.replicate 3 0).length` realizes as `3` — NOT as "
                      "`len([0] * 3)`, though at this size the two agree, and that "
                      "agreement is exactly why R2 has to be stated as a rule rather "
                      "than discovered per case — then `Nat` subtraction truncates) "
                      "omits the last three sub-views of every collection. The failing "
                      "test paginates a 3-item collection at 2 per page and pulls TWO "
                      "sub-views; a counterpart that emits NEITHER raises "
                      "StopIteration on the first pull, so the test errors. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `out = pageSeq pageRange` (COUNT/trailing half, at "
                     "width three): the rival's result is three elements shorter than "
                     "`pageSeq` on every run of length ≥ 3, so they are unequal. "
                     "Refuted at the THREE-index run `[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩]`, where "
                     "the rival returns `[]` and the spec demands three sub-views — a "
                     "length mismatch, so the witness needs NO assumption about the "
                     "opaque `pageOf`, only the count hypothesis the carrier requires "
                     "to name index 4. A NEW refutation point: no other case in this "
                     "battery is refuted at a three-index run starting at index 2 "
                     "(`partial-domain-drop-first` uses a three-index run, but it "
                     "starts at index 1 and its bug is at the HEAD, which this rival "
                     "gets right). What separates it from the two sibling drop rivals "
                     "is WIDTH and the ROUTE the bound takes, and the width makes the "
                     "separation observable: at the two-index run `[⟨2,_⟩, ⟨3,_⟩]` "
                     "`truncated-arith-drop-last` returns one sub-view and "
                     "`emod-convention-drop-last-two` returns none, while at THIS "
                     "point all three return `[]` and only a three-element demand "
                     "distinguishes this one's bound from theirs. Its bound is "
                     "computed by `List.length_replicate` where theirs are computed by "
                     "`Nat.sub` and `Int.emod`, which is the lane this case was added "
                     "for.",
        "witness": _witness("(hn : 4 ≤ numPages) ", _lst([2, 3, 4]), ""),
    },

    # ---- COUNT clause, THROUGH `Nat.pow`: drop the last FOUR indices ----
    # The reject-lane companion of the FIFTH finding. The four shapes that round
    # closed all route through `Nat.pow` — `2 ^ (64 + n)` as a loop bound, and
    # `2 ^ (2 ^ (64 + n))` both as a bound and inside a guard — and `Nat.pow` was
    # the one operation in mapping.md §2.1's `Nat` table still claiming to be
    # realized by its Python spelling unconditionally. It is now side-conditioned,
    # so the battery should exercise it in the REJECT lane too and not only in an
    # assert and a pile of positives: this rival computes its (wrong) bound with
    # `pageRange.length - 2 ^ 2`, where the three sibling drop rivals use
    # `Nat.sub` on a literal, `Int.emod` and `List.length_replicate`.
    {
        "id": "pow-bound-drop-last-four",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("(pageRange.take (pageRange.length - 2 ^ 2)).map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that stops four indices early — iterating "
                      "`page_range[:len(page_range) - 2 ** 2]`, the realization of "
                      "this bound per mapping.md §2.1 (the `^` row applies here "
                      "because `2 ** 2` is a value Python holds; that is what the "
                      "row's new side condition is about) — omits the last four "
                      "sub-views of every collection. The failing test paginates a "
                      "3-item collection at 2 per page and pulls TWO sub-views; a "
                      "counterpart that emits none raises StopIteration on the first "
                      "pull, so the test errors. It would NOT resolve.",
        "rationale": "REJECT from `out = pageSeq pageRange` (COUNT half, width FOUR): "
                     "the rival's result is four elements shorter than `pageSeq` on "
                     "every run of at least four indices. Refuted at the four-index "
                     "run `[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩, ⟨5,_⟩]`, where the rival returns `[]` "
                     "and the spec demands four sub-views — a length mismatch, so the "
                     "witness needs NO assumption about the opaque `pageOf`, only the "
                     "count hypothesis the carrier requires to name index 5 at all. A "
                     "NEW refutation point: at the three-index run `[⟨2,_⟩, ⟨3,_⟩, "
                     "⟨4,_⟩]` this rival and `derived-length-drop-last-three` both "
                     "return `[]`, so nothing shorter separates them, exactly as the "
                     "widths one, two and three had to lengthen the point each time. "
                     "What makes it a distinct case rather than a fourth spelling of "
                     "the same bug is the ROUTE of the bound: `Nat.pow`, the operation "
                     "the fifth finding's five verifying shapes are all built out of "
                     "and the one whose realization row was unconditioned until this "
                     "round.",
        "witness": _witness("(hn : 5 ≤ numPages) ", _lst([2, 3, 4, 5]), ""),
    },

    # ---- COUNT clause: the bound carried by a LIVE local (R4's side condition) ----
    # The reject-lane half of the sixth finding. R4 licenses DROPPING a binding
    # nothing reads; this rival's binding IS read, and dropping it would turn a
    # refuted impl into gold — which is exactly why deadness is decided by
    # `impl_reads_binding` rather than asserted by the translator.
    {
        "id": "live-local-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_BODY,
            "    let z : Nat := pageRange.length - 5\n"
            "    return ((pageRange.take z).map pageOf)"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that stops five indices early — iterating "
                      "`page_range[:z]` where `z = _nat_sub(len(page_range), 5)`, the "
                      "realization of a LIVE local per mapping.md §2.1 (R4 does NOT "
                      "apply: `impl_reads_binding` counts one read of `z`, at the "
                      "return) — omits the last five sub-views of every collection. "
                      "The failing test paginates a 3-item collection at 2 per page "
                      "and pulls TWO sub-views; a counterpart that emits none raises "
                      "StopIteration on the first pull, so the test errors. It would "
                      "NOT resolve. Dropping the local instead, as R4 would license if "
                      "it were dead, yields `pageRange.map pageOf` — gold — and that "
                      "difference is the whole content of the side condition.",
        "rationale": "REJECT from `out = pageSeq pageRange` (COUNT half, width FIVE): "
                     "the rival's result is five elements shorter than `pageSeq` on "
                     "every run of at least five indices. Refuted at the five-index "
                     "run `[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩, ⟨5,_⟩, ⟨6,_⟩]`, where the rival "
                     "returns `[]` and the spec demands five sub-views — a length "
                     "mismatch, so the witness needs NO assumption about the opaque "
                     "`pageOf`, only the count hypothesis the carrier requires to name "
                     "index 6 at all. A NEW refutation point, and it has to be: at the "
                     "four-index run this rival and `pow-bound-drop-last-four` both "
                     "return `[]`, while at five indices they separate (that one "
                     "returns one sub-view, this one none), exactly as widths one, two, "
                     "three and four each had to lengthen the point. What makes it a "
                     "distinct case rather than a fifth spelling of the same bug is the "
                     "ROUTE of the bound: it is carried by a local the impl READS, the "
                     "one shape mapping.md §2.1's R4 must not be applied to. The "
                     "battery therefore records both sides of R4's side condition — "
                     "pos-control-dead-pow-local verifies with an UNREAD local, this "
                     "rival is refuted with a READ one, and the same module with the "
                     "local dropped is pos-control-closed-form, which verifies.",
        "witness": _witness("(hn : 6 ≤ numPages) ", _lst([2, 3, 4, 5, 6]), ""),
    },

    # ---- ORDER clause: reverse the run (conditioned on pageOf) ----
    {
        "id": "order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Same count and same multiset of sub-views, but built in REVERSE index
        # order. The order-preservation half fails for any run with >= 2 distinct
        # sub-views.
        "module": _closed("pageRange.reverse.map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that walks the index sequence back to front "
                      "(e.g. iterating it reversed) yields the sub-views in reverse "
                      "order. The failing test compares the first pulled sub-view "
                      "against [1,2]; reversed, the first pulled one is [3], so the "
                      "first subtest's assertion fails. It would NOT resolve.",
        "rationale": "REJECT from `out = pageSeq pageRange` (ORDER half): on a "
                     "two-index run the rival returns "
                     "`[pageOf ⟨2,_⟩, pageOf ⟨1,_⟩]` where the spec demands "
                     "`[pageOf ⟨1,_⟩, pageOf ⟨2,_⟩]`. These are unequal whenever the "
                     "two sub-views differ, so the witness conditions on the single "
                     "satisfiable hypothesis `pageOf ⟨1,_⟩ ≠ pageOf ⟨2,_⟩` (a "
                     "non-constant selector exists) — exactly the sub-domain the "
                     "rival is wrong on. Count and multiset are RIGHT here, so the "
                     "drop-first rival's length argument does not subsume this one.",
        # The tail is wrapped in `try` for the gold-side SIGNATURE, not for the
        # refutation: against the reference `simp` has already collapsed the goal to
        # `False`, so a bare `intro` reports `no additional binders` — a `shape`-tier
        # (weak) signature for a build that had in fact decided the claim. Wrapped,
        # the residual IS the reduct (`unsolved goals ... ⊢ False`, tier `reduced`).
        # It cannot hide a broken witness: the rival side must still CLOSE (measured
        # exit 0), and the forgery still inverts (reference 0, rival 1).
        "witness": _witness(
            f"(hn : 2 ≤ numPages) (h : pageOf {_idx(1)} ≠ pageOf {_idx(2)}) ",
            _lst([1, 2]), "  try (intro _; exact h)\n"),
    },

    # ---- VALUE clause: ask for the NEXT index (the recorded attack, guarded) ----
    # THE case this revision exists for. The recorded hole was an implementation
    # that applied the accessor at an index the object does not name and discarded
    # the result: under the old total accessor that VERIFIED, and its counterpart
    # hit the accessor's refusal and did not resolve. The carrier now makes the
    # unguarded form unwritable (`omega could not prove the goal` on the
    # membership), so the attack's expressible residue is this: ask for the index
    # AFTER each one, proving membership where it holds and falling back where it
    # does not. It is rejected by the clause, with a witness, and its counterpart
    # still does not resolve — so the class is closed on both sides.
    {
        "id": "partial-domain-shifted-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(_GUARD_SHIFT),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that asks the accessor for the sub-view one "
                      "index PAST each requested index, and hands back an empty "
                      "sub-view when the object does not name that one, returns the "
                      "wrong sub-view everywhere. On the failing test's 2-sub-view "
                      "collection the first pulled sub-view is the SECOND one ([3]) "
                      "where the test demands the first ([1,2]), so the first "
                      "subtest's assertion fails; the second pull hands back an "
                      "empty sub-view for the same reason the unguarded version "
                      "cannot be written at all — the object refuses the index past "
                      "its last. It would NOT resolve. This is the recorded attack "
                      "in the only form the carrier still admits.",
        "rationale": "REJECT from `out = pageSeq pageRange` (VALUE half): on a "
                     "one-index run `[⟨1,_⟩]` with the object presenting at least "
                     "two sub-views, the rival returns `[pageOf ⟨2,_⟩]` where the "
                     "spec demands `[pageOf ⟨1,_⟩]`. Refuted under the single "
                     "satisfiable hypothesis `pageOf ⟨1,_⟩ ≠ pageOf ⟨2,_⟩` — the "
                     "value clause pins the sub-view of THAT index, and asking for "
                     "the next one violates it. The witness discharges the rival's "
                     "own guard (`dif_pos`) from its count hypothesis, so the "
                     "refutation is against the branch the rival actually takes, not "
                     "against its fallback. A near-miss the drop-first (wrong LENGTH) "
                     "and reversed (wrong ORDER) rivals do not subsume: right "
                     "length, right order, wrong element — hence its own, shorter "
                     "refutation point.",
        "witness": _witness(
            f"(hn : 2 ≤ numPages) (h : pageOf {_idx(1)} ≠ pageOf {_idx(2)}) ",
            _lst([1]),
            # `try`-wrapped for the gold-side signature; see order-reversed above.
            "  try (intro heq\n"
            "       rw [dif_pos (show 2 ≤ numPages by omega)] at heq\n"
            "       first | exact h heq | exact h heq.symm)\n"),
    },

    # ---- EMPTY boundary: a spurious sub-view emitted before the walk ----
    {
        "id": "boundary-empty-spurious-leading",
        "kind": "uniqueness",
        "expect": "reject",
        # The right per-index image, but with one extra sub-view emitted
        # unconditionally in FRONT of it — so an EMPTY index sequence yields one
        # sub-view instead of none, and every non-empty run is shifted by one.
        # The extra element is the empty family rather than a copy of the head:
        # after the carrier change, naming index 1 out of thin air would need
        # `1 ≤ numPages`, which no implementation of this method is given, so
        # `pageOf ⟨1,_⟩ :: ...` does not elaborate (measured: `omega could not
        # prove the goal`). Nothing is lost — the boundary this case defends is
        # `[] -> []`, and a spurious leading element of any value breaks it.
        "module": _closed("[[]] ++ pageRange.map pageOf"),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that emits one sub-view before walking the "
                      "index sequence yields one sub-view too many, and the extra "
                      "one FIRST. On the failing test's 3-item collection at 2 per "
                      "page the first pulled sub-view is the spurious one rather "
                      "than [1,2], so the first subtest's assertion fails; and on a "
                      "collection with no sub-views at all it hands back one that "
                      "does not exist, which the passing index-sequence tests "
                      "contradict. It would NOT resolve. (A counterpart emitting the "
                      "extra sub-view LAST would resolve — the test pulls exactly "
                      "two — which is why this rival puts it first.)",
        "rationale": "REJECT from `out = pageSeq pageRange` at the EMPTY boundary: "
                     "the clause pins `[] -> []`, and the rival returns a "
                     "one-element list for the empty run — a non-empty result where "
                     "the fold demands none. Refuted at `[]`, the one point at which "
                     "the postcondition's base case is the whole content, and the "
                     "only reject point in this battery where NO index is traversed. "
                     "The witness binds NOTHING at all: the empty run needs no index, "
                     "hence no count hypothesis, and the contradiction is a length "
                     "mismatch needing no assumption about `pageOf`. The other seven "
                     "rivals are all CORRECT on the empty run, so this boundary is "
                     "otherwise undefended.",
        "witness": _witness("", "([] : List PageIdx)", ""),
    },

    # ---- VALUE clause, the sibling's OWN rival: index by POSITION, not value ----
    # The clause is claimed at EVERY `pageRange : List PageIdx`, not only at the
    # sequence the deployed caller passes, so a rival that reads the accessor by
    # 1-based POSITION agrees with the spec on all of [1..n] and violates it off
    # that sub-domain. Distinct from shifted-index: shifted-index is wrong on
    # EVERY non-empty run including [1..n]; this one is right there and wrong
    # only elsewhere.
    {
        "id": "value-indexed-by-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(_GUARD_POSITION),
        "witness_reference": _REFERENCE,
        "refinement": "a counterpart that walks positions and asks the accessor for "
                      "the sub-view at the POSITION rather than at the index it read "
                      "from the sequence agrees with the faithful one whenever the "
                      "sequence happens to be 1..n, and diverges as soon as it is "
                      "not — e.g. any caller that iterates a narrowed or reordered "
                      "index sequence gets the sub-views of 1..n back instead of the "
                      "ones it named. Stated plainly: on the failing test's fixture "
                      "this counterpart WOULD resolve, because there the sequence IS "
                      "1..n. It is nonetheless a distinct, generally incorrect "
                      "traversal of the modeled domain, and a spec that ADMITTED it "
                      "would be attesting to a coincidence of the deployed input "
                      "rather than to the behaviour, so it must be rejected on pain "
                      "of SPEC-TOO-WEAK.",
        "rationale": "REJECT from `out = pageSeq pageRange` (VALUE half, off the "
                     "[1..n] sub-domain): the clause is claimed at EVERY "
                     "`pageRange : List PageIdx`, and on the one-index run "
                     "`[⟨5,_⟩]` the rival returns `[pageOf ⟨1,_⟩]` where the spec "
                     "demands `[pageOf ⟨5,_⟩]`. Refuted under the single satisfiable "
                     "hypothesis `pageOf ⟨1,_⟩ ≠ pageOf ⟨5,_⟩`, at a NEW refutation "
                     "point no other case in this battery uses — and one whose index "
                     "is deliberately not a position, since that is the whole "
                     "distinction. Not subsumed by shifted-index: this rival is "
                     "correct on all of [1..n], where shifted-index is wrong "
                     "everywhere, so the two attack different halves of the value "
                     "clause. (Sibling: partial-domain-index-not-value, ported "
                     "directly — see the accounting footer.)",
        "witness": _witness(
            f"(hn : 5 ≤ numPages) (h : pageOf {_idx(1)} ≠ pageOf {_idx(5)}) ",
            _lst([5]),
            # `try`-wrapped for the gold-side signature; see order-reversed above.
            "  try (intro heq\n"
            "       rw [dif_pos (show 1 ≤ numPages by omega)] at heq\n"
            "       first | exact h heq | exact h heq.symm)\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation, 3 uniqueness rivals) plus a
# 2-case AXIOM lane. This bundle models the SAME purely-functional core (walk an
# index sequence, mapping each index through one accessor, in order), so the
# value/order/count rivals port 1:1; only the two frame cases are genuinely
# vacuous on this carrier.
#
#   sibling case                       -> here                            disposition
#   -----------------------------------------------------------------------------
#   pos-control-localvar-reshape       -> pos-control-localvar-reshape     PORTED
#   admissibility-f2p-shaped           -> admiss-postimage-grounded-       RE-AIMED
#                                         at-f2p-shape
#   frame-mutation-store               -> (none)                          VACUOUS
#   frame-mutation-append              -> (none)                          VACUOUS
#   partial-domain-drop-first          -> partial-domain-drop-first        PORTED
#   partial-domain-index-not-value     -> value-indexed-by-position        PORTED
#   order-reversed-append              -> order-reversed                   PORTED
#   (no sibling case)                  -> pos-control-closed-form          ADDED
#   (no sibling case)                  -> pos-control-forward-loop         ADDED
#   (no sibling case)                  -> pos-control-in-domain-selection  ADDED
#   (no sibling case)                  -> admiss-accessor-domain-carried   ADDED
#   (no sibling case)                  -> pos-control-dead-nat-arith       ADDED
#   (no sibling case)                  -> pos-control-dead-saturating-loop ADDED
#   (no sibling case)                  -> admiss-nat-semantics-carried     ADDED
#   (no sibling case)                  -> truncated-arith-drop-last        ADDED
#   (no sibling case)                  -> pos-control-dead-int-arith       ADDED
#   (no sibling case)                  -> pos-control-emod-convention      ADDED
#   (no sibling case)                  -> pos-control-emod-guarded-branch  ADDED
#   (no sibling case)                  -> pos-control-fixed-width-         ADDED
#                                         wraparound
#   (no sibling case)                  -> admiss-int-semantics-carried     ADDED
#   (no sibling case)                  -> emod-convention-drop-last-two    ADDED
#   (no sibling case)                  -> partial-domain-shifted-index     ADDED
#   (no sibling case)                  -> boundary-empty-spurious-leading  ADDED
#   (no sibling divergence case)       -> (none)                           KNOWN HOLE
#   AXIOM_TESTS (2)                    -> (none)                           DROPPED (G-AX)
#
# PORTED (4): the localvar reshape ports onto the loop body (same backward
#   direction, same fold), and the drop-first, reversed and index-not-value rivals
#   port directly onto the single `out = pageSeq pageRange` clause. Their
#   refinement arguments carry over: dropping the first index omits the leading
#   sub-view, reversing yields the sub-views out of order — both make the FIRST
#   sub-view the failing test pulls the wrong one — and indexing by position
#   returns the sub-views of 1..n instead of the ones actually named. drop-first is
#   refuted purely structurally (length mismatch, no `pageOf` assumption); the
#   other two condition on one `pageOf a ≠ pageOf b`.
# RE-AIMED (admissibility): the sibling self-calls to prove the fractional-
#   permission precondition admits a test-shaped input. This bundle declares no
#   `require`, so that exact probe has no precondition to admit — but the LANE is
#   not vacuous. The total-carrier analogue is the obligation being unsatisfiable
#   or DEGENERATE at exactly an F2P-shaped input, which a positive that discharges
#   the obligation at that concrete input — by evaluation, in-region, while the
#   frozen obligation closes verbatim — tests directly. Landed as
#   `admiss-postimage-grounded-at-f2p-shape`, liveness measured by a negative
#   control (the same case claiming length 3 leaves the claim unsolved).
# ADDED (22):
#   * pos-control-closed-form — a much stronger soundness positive than the
#     localvar reshape (the loop is gone entirely, not reshaped) which doubles as
#     the shared `witness_reference`. Required by the carrier, see WITNESS SUBJECT.
#   * pos-control-forward-loop — the localvar reshape is DEFINITIONALLY the frozen
#     impl (the `let` hoist closes by `rfl`), so it probes only surface spelling.
#     The forward loop walks the run front-to-back and appends, so its invariant is
#     `take i` where the frozen one is `drop i`: the frozen invariant is FALSE of
#     it at every step and the frozen rewrite has no goal to fire on. It VERIFIES,
#     so the clause admits a faithful traversal in the opposite direction — it is
#     not SPEC-TOO-STRONG on traversal order.
#   * pos-control-in-domain-selection — the control for THIS revision's carrier
#     change: an extra accessor application at an index the object names must
#     still verify, or the restriction would be rejecting faithful impls rather
#     than off-domain ones. Measured against its own negative (the same probe one
#     index past the count does not elaborate).
#   * admiss-accessor-domain-carried — the strengthening as a positive, in-region
#     obligation: every index of the carrier is in the accessor's domain. Measured
#     live against a negative control (`2 ≤ p.val` fails with a type mismatch
#     naming the carrier's real bound).
#   * partial-domain-shifted-index — asks the accessor for the index one past each
#     requested one, guarded (the unguarded form no longer elaborates). This is the
#     recorded G-EQ / G-PANEL-1 attack in its expressible form, and its counterpart
#     does NOT resolve: the first sub-view the failing test pulls is the second one.
#   * boundary-empty-spurious-leading — the sibling's rivals are all correct on the
#     EMPTY run, so nothing in the ported set probed `[] -> []`, the one clause
#     sub-obligation with no traversed index. It emits its spurious sub-view FIRST
#     because the failing test pulls exactly two and would not notice a trailing
#     one.
#   * pos-control-dead-nat-arith / pos-control-dead-saturating-loop — the two
#     shapes of the SECOND recorded G-EQ / G-PANEL-1 finding (arithmetic totality
#     drift), shipped as POSITIVES because they are correct: `n / (n - n)` is 0 in
#     `Nat` and a `k := k - 2` countdown from an odd start lands on 0 because
#     `Nat.sub` saturates. Rejecting either would be SPEC-TOO-STRONG. They are
#     here to put on the record, in the battery, that these impls verify — so the
#     reason their submitted counterparts failed can only be the mistranslation of
#     the arithmetic, which is where the fix went (mapping.md §2.1). See the
#     ARITHMETIC TOTALITY DRIFT block in the module docstring for why no clause
#     could have closed the class, measured with literal-only variants.
#   * admiss-nat-semantics-carried — the Lean half of mapping.md §2.1 as an
#     in-region obligation: the four `Nat` laws (`b ≤ a → (a-b)+b = a`,
#     `a ≤ b → a-b = 0`, `a/0 = 0`, `a%0 = a`), which are exactly the laws
#     `conformance_check.check_nat_algebra` measures of the Python realization.
#     Live against three negative controls, each leaving the false claim as the
#     residual goal; the sharpest is dropping the hypothesis from the cancellation
#     law, which fails precisely BECAUSE the subtraction truncates.
#   * truncated-arith-drop-last — the reject rival for the same class: it computes
#     its bound with the truncated `pageRange.length - 1`, so it is CORRECT on the
#     empty run (where the arithmetic hides the bug) and wrong on every non-empty
#     one. Refuted at a new point, the one-index run `[⟨2,_⟩]`, structurally. It
#     also covers the trailing-element half of the count clause, which the
#     leading-element rival (drop-first) and the leading-extra boundary rival do
#     not; its counterpart raises StopIteration on the failing test's second pull.
#   * pos-control-dead-int-arith / pos-control-emod-convention /
#     pos-control-emod-guarded-branch — the three shapes of the THIRD recorded
#     G-EQ / G-PANEL-1 finding: the same arithmetic class one type over, in `Int`.
#     All three are CORRECT in Lean — `(n : Int) / 0` is 0, `(1 : Int) % (-2)` is
#     1 (Euclidean, non-negative remainder), and `1 < 0` is false — so all three
#     are POSITIVES; rejecting any would be SPEC-TOO-STRONG. The third one is the
#     load-bearing addition: its `Int` value is consumed by a GUARD rather than
#     discarded, so the battery records that the class reaches control flow, which
#     is why the docstring's inexpressibility argument now rests on CLOSEDNESS
#     rather than on the value being dead.
#   * pos-control-fixed-width-wraparound — the shape NOT submitted by any auditor:
#     `((200 : UInt8) + 100).toNat - 43`, which is 1 in Lean's modular fixed-width
#     arithmetic and 257 under Python's unbounded `+`. It VERIFIES. Shipped so the
#     next type over is covered by a measured case rather than by a promise, which
#     is the same reason mapping.md §2.1 became a LAW (R0/R1) instead of gaining
#     one more table row.
#   * admiss-int-semantics-carried — the Lean half of §2.1's `Int` rows as an
#     in-region obligation: `∀ a : Int, a / 0 = 0`, `∀ a : Int, a % 0 = a`, and the
#     four convention fixtures `(1 : Int) % (-2) = 1`, `(7 : Int) / (-2) = -3`,
#     `(-7 : Int) / (-2) = 4`, `(-7 : Int) % (-2) = 1` — exactly what
#     `conformance_check.check_int_algebra` measures of the Python realization.
#     Live against FIVE negative controls, one per convention fixture plus
#     `a % 0 = 0`, each leaving the false claim as the residual goal.
#   * emod-convention-drop-last-two — the reject rival for the `Int` half: its
#     bound is `pageRange.length - ((5 : Int) % (-3)).toNat`, i.e. drop the last
#     TWO, and the 2 is computed by `Int.emod` (Python's `%` would give -2 there,
#     `.toNat` 0, and no drop at all). Refuted at a new point, the two-index run
#     `[⟨2,_⟩, ⟨3,_⟩]`: at every ONE-index run it and the frozen impl agree on
#     `[]`, so it is not refutable anywhere shorter, and its refutation point is
#     shared with no other rival. Structural (a length mismatch, no `pageOf`
#     assumption). So the `Int` algebra is exercised in the reject lane too and not
#     only in an assert.
#   * pos-control-dead-range-materialization / pos-control-replicate-materialization
#     / pos-control-range-guarded-branch — the three shapes of the FOURTH recorded
#     G-EQ / G-PANEL-1 finding. This one needed no new TYPE: it attacked
#     COMPOSITION, assembling `len(list(range(n)))` out of two rows §2.1 already
#     carried, which raises `OverflowError` for `n ≥ 2^63` while Lean's
#     `(List.range n).length` answers `n` for every `n : Nat`. All three verify —
#     `0 * k = 0`, `k * 0 = 0`, `¬(0 > 0)` — so all three are POSITIVES. The third
#     carries the value into a GUARD, and the second uses a different constructor
#     (`List.replicate`), which together record that the class is about the
#     composition rule and not about one library function.
#   * admiss-derived-length-carried — the Lean half of §2.1's rule R2 as an
#     in-region obligation: the five derived-length equations
#     (`(List.range n).length = n`, `(List.replicate n a).length = n`,
#     `(xs.map f).length = xs.length`, `(xs.take k).length = min k xs.length`,
#     `(xs ++ ys).length = xs.length + ys.length`) — exactly what
#     `conformance_check.check_container_realization` measures of the Python
#     realization. Live against three negative controls, each leaving the false
#     claim as the residual goal; the sharpest drops the `min` from the `take`
#     length, which is true of a Python slice only when `k ≤ len(xs)`.
#   * derived-length-drop-last-three — the reject rival for the container half: its
#     bound is `pageRange.length - (List.replicate 3 (0 : Int)).length`, i.e. drop
#     the last THREE, and the 3 is computed by `List.length_replicate` rather than
#     by any `Nat` or `Int` operation. Refuted at a new point, the three-index run
#     `[⟨2,_⟩, ⟨3,_⟩, ⟨4,_⟩]`: at the two-index run it and the `Int.emod` rival
#     agree on `[]`, so it is not refutable anywhere shorter, and the point is
#     shared with no other rival (drop-first's three-index run starts at index 1).
#     Structural — a length mismatch, no `pageOf` assumption.
#   * admiss-postcondition-single-valued — the reason NONE of the four findings was
#     closable by a clause, as a machine-checked obligation instead of a paragraph:
#     exactly one `o` satisfies `o = pageSeq pr` for every input (the `∃!` spelled
#     out, because the notation is measured not to be discharged by this bundle's
#     tactic), hence any two verifying impls agree everywhere. A spec that pins its
#     output uniquely is MAXIMALLY STRONG on its observable interface, so no
#     strengthening could reject any of the nine arithmetic/container positives
#     without also rejecting gold. This replaces two earlier arguments that a case in
#     this battery has since refuted — "a postcondition cannot constrain a discarded
#     local" (refuted by pos-control-emod-guarded-branch) and CLOSEDNESS (refuted by
#     pos-control-dead-range-materialization, whose closed variant does not even
#     verify). Discharged IN-REGION under the frozen proof body, not as a new
#     theorem — a same-spec variant may not add declarations, and the first form of
#     this case was correctly refused by G-PBT for doing so. Live against four
#     negative controls, each leaving the false claim as the residual goal.
# VACUOUS (two frame-mutation rivals): the sibling carries these MANDATORY because
#   its index run is held at a fractional heap permission an impl can illegally
#   store into / append to. This backend is referentially transparent and declares
#   no `mut` binder — `pageRange` is an immutable value with no heap footprint —
#   so there is no read-only input to overwrite and no substitute probe. Not
#   fabricated.
# CLOSED BY THE SPEC (divergence / non-termination): the nagini sibling carries no
#   such case, so nothing was dropped in porting, and the class is no longer a hole
#   here. The bundle opens `TotalCorrectness`, so the measure is load-bearing and
#   every loop must be proven to terminate. Measured on this cell, one build each:
#   the frozen impl VERIFIES under the total `open` (its measure `i` is real and
#   falls by one per step), and the same impl with its `i := i - 1` step deleted
#   and its measure removed is REJECTED with "Decreasing annotations are required
#   in total correctness semantics". A non-terminating rival therefore no longer
#   satisfies `out = pageSeq pageRange` vacuously. Still no reject case is shipped
#   for the class, and for a reason that survives the flip: a reject case requires
#   a witness that refutes the rival AT A CONCRETE INPUT, and a diverging rival is
#   rejected by the verifier's own termination obligation rather than by any input
#   point — it has no output to disagree with `pageSeq`. The forward-loop positive
#   is what keeps the strengthened obligation HONEST in this battery: it must now
#   prove termination too, so the battery records that the total scope still admits
#   a faithful traversal and is not merely rejecting loops.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates the
#   opaque `pageOf` A-reference == the real accessor, domain included); this bundle
#   consumes no axiom `ensures`, and the gate ignores AXIOM_TESTS regardless.
#
# THE CARRIER CHANGE, CASE BY CASE. This revision replaced the total
#   `pageOf : Nat → List Int` with `pageOf : PageIdx → List Int` over
#   `PageIdx = {n // 1 ≤ n ∧ n ≤ numPages}`, closing the recorded hole (an impl
#   could apply the accessor off its domain, discard the result, and verify). Every
#   case above was re-derived against the new carrier and re-measured; three of the
#   five rivals could no longer be written as they stood, and are shipped in the
#   form the carrier admits rather than dropped:
#     * partial-domain-shifted-index: `pageOf (n + 1)` -> the guarded
#       `if h : p.val + 1 ≤ numPages then pageOf ⟨p.val + 1, _, h⟩ else []`.
#       Still refuted, at the same one-index point, under the same hypothesis; the
#       guard is discharged in the witness so the refutation is against the branch
#       taken. The unguarded form was measured: it does not elaborate.
#     * value-indexed-by-position: `pageOf (k + 1)` for a position `k` -> the same
#       guarded shape over `List.range pageRange.length`. Still refuted at
#       `[⟨5,_⟩]` under `pageOf ⟨1,_⟩ ≠ pageOf ⟨5,_⟩`.
#     * boundary-empty-spurious-leading: `pageOf 1 :: ...` needs `1 ≤ numPages`,
#       which no implementation is given, so the spurious leading element is the
#       empty family instead. The boundary it defends (`[] -> []`) is unchanged and
#       the refutation is still a length mismatch with no hypothesis at all.
#   Nothing was retired, no reject case was weakened into a positive, and the
#   reject count went from five to eight (the three added are
#   `truncated-arith-drop-last`, `emod-convention-drop-last-two` and
#   `derived-length-drop-last-three`, one per round of the arithmetic/container
#   class below).
#
# THE REALIZATION CLASS, CASE BY CASE. THREE recorded findings (the second, third
#   and fourth against this cell) are the same class — a verified impl performing an
#   operation whose naive Python spelling is a DIFFERENT function — and NONE is
#   closable by any clause of this spec. That last claim is no longer argued from
#   literal-only variants (which the fourth finding refuted: its closed variant does
#   not verify at all, it times out); it is now a machine-checked case,
#   `admiss-postcondition-single-valued`. The fix went into the refinement map all
#   three times, and it went in as a LAW rather than as more rows: mapping.md §2.1
#   states R0 (a closed sub-expression realizes as the value Lean evaluates it to),
#   R1 (an open one as a TOTAL Python function extensionally equal to the Lean
#   operation) and R2 (a composite from its OWN defining equation, never by chaining
#   rows through an intermediate Python cannot represent), with tables for `Nat`,
#   `Int`, fixed-width, `Float` and the derived container lengths under them and an
#   explicit obligation to transcribe a row for anything not yet tabled;
#   refinement.md §B''/§B'''/§B'''' record the findings and the measured resolve
#   outcomes under the corrected realization (all eight counterparts resolve 1/1,
#   20/20). This battery's job is to keep that fix from being a paper claim.
#   Sixteen cases:
#     * the eight attack shapes as POSITIVES (`pos-control-dead-nat-arith`,
#       `pos-control-dead-saturating-loop` for `Nat`; `pos-control-dead-int-arith`,
#       `pos-control-emod-convention`, `pos-control-emod-guarded-branch` for `Int`;
#       `pos-control-dead-range-materialization`,
#       `pos-control-replicate-materialization`,
#       `pos-control-range-guarded-branch` for the container lengths) — they verify,
#       and they must, so the failure of their submitted counterparts is
#       attributable to the mistranslation and to nothing about the spec. Plus
#       `pos-control-fixed-width-wraparound`, the shape nobody submitted yet, which
#       verifies too: the law is tested one type ahead of the attacks.
#     * `admiss-nat-semantics-carried`, `admiss-int-semantics-carried` and
#       `admiss-derived-length-carried` — the Lean side of the corrected map, as
#       in-region obligations over exactly the laws the Python side is measured
#       against (`check_nat_algebra`, `check_int_algebra`,
#       `check_container_realization`). These are the cases a future revision would
#       have to break in order to silently change any of the algebras back.
#     * `truncated-arith-drop-last`, `emod-convention-drop-last-two` and
#       `derived-length-drop-last-three` — REJECT rivals whose bugs run through the
#       saturating, the Euclidean and the derived-length arithmetic respectively, so
#       every round of the class is exercised in the reject lane too.
#     * `admiss-postcondition-single-valued` — the class-level statement that ends
#       the regress: the obligation is single-valued, so it is maximally strong on
#       its observable interface, so a fourth round of "the spec is too weak" for a
#       CORRECT impl is answerable by a proof rather than by another table row.
#   No reject case is shipped for the drift ITSELF, for the same reason as the
#   divergence class: the drifting modules are correct, so there is no input at
#   which they disagree with `pageSeq`, hence no witness to build. And one honest
#   gap: the `Float` leg of §2.1 has NO positive control and cannot have one — it
#   is measured UNREACHABLE by any verifying impl of this method, because Lean's
#   `Float` operations are `@[extern]` and do not reduce, so the frozen invariant
#   `i ≤ pageRange.length` cannot be discharged for a `Float`-offset counter (the
#   probe fails with the invariant unsolved). The rows are fixed in the map anyway;
#   R0 covers every closed `Float` term regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has a single input binder,
#   `pageRange : List PageIdx`, and a single top-level clause, `out = pageSeq
#   pageRange`, with four independent sub-obligations (count, order, per-position
#   value, empty base case). The eight reject witnesses probe eight DISTINCT points
#   (`[⟨1⟩,⟨2⟩,⟨3⟩]`, `[⟨1⟩,⟨2⟩]`, `[⟨1⟩]`, `[]`, `[⟨5⟩]`, `[⟨2⟩]`, `[⟨2⟩,⟨3⟩]`,
#   `[⟨2⟩,⟨3⟩,⟨4⟩]`), so `pageRange` is genuinely varied — length moves across
#   3/2/1/0 and CONTENTS move independently of length, which is what makes the
#   variation meaningful rather than eight spellings of one point: `[⟨1⟩]`, `[⟨5⟩]`
#   and `[⟨2⟩]` are the same length and differ in whether the index equals its
#   position and in which end of the run is at stake; `[⟨1⟩,⟨2⟩]` vs `[⟨2⟩,⟨3⟩]` are
#   the same length and differ in which end is at stake; and `[⟨1⟩,⟨2⟩,⟨3⟩]` vs
#   `[⟨2⟩,⟨3⟩,⟨4⟩]` are the same length and differ in whether the run starts at the
#   first page, which is what separates the leading-element count rival from the
#   trailing-three one. Those differences are exactly what separate the value rivals
#   and the four count rivals (each satisfies the others' spec at the others'
#   points). Sub-obligations: count by drop-first at the LEADING element
#   (structurally, no `pageOf` assumption), by truncated-arith-drop-last at the
#   TRAILING one, by emod-convention-drop-last-two at the trailing TWO and by
#   derived-length-drop-last-three at the trailing THREE (likewise structurally),
#   order by reversed, value by shifted-index (wrong everywhere) AND by
#   indexed-by-position (wrong only off [1..n]), the empty base case by the
#   spurious-leading boundary rival. The thirteen positive controls defend the whole
#   obligation at thirteen shapes — the frozen loop's own (definitionally, so a
#   minimal control only), a forward loop with a different invariant, no loop at all,
#   the frozen loop plus an extra in-domain accessor application, the frozen loop
#   plus a provably-zero `Nat` quotient feeding its counter, the frozen loop preceded
#   by a second, saturating, provably terminating one, and seven more that reach the
#   counter or the loop guard through the OTHER algebras (a zero-divisor `Int`
#   quotient, a Euclidean `Int` remainder, a Euclidean remainder consumed by an `if`
#   guard, a wrapping `UInt8` sum, a provably-zero product with the length of an
#   astronomically large `List.range`, the same with a `List.replicate`, and such a
#   length consumed by an `if` guard) — and the six admissibility cases defend it
#   against degeneracy at the F2P-shaped input and record the carrier's domain claim,
#   all three realization algebras' laws and the obligation's single-valuedness
#   in-region. No two rivals are refuted at the same point.
#
# WITNESS SUBJECT — why every reject case names a `witness_reference`. The FROZEN
#   impl cannot be the witnesses' second subject, and this was measured with real
#   builds rather than assumed. Its `while` loop under
#   `loom.semantics.choice "demonic"` elaborates through `Classical.choice`, which
#   the kernel cannot unfold, so every goal keeps an un-normalised
#   `forIn Lean.Loop.mk` term and a TRIVIALLY TRUE claim fails against the frozen
#   impl with the same unsolved-goal shape as each refutation. A frozen-side exit
#   code therefore attests to nothing, and a forged witness claiming the rival is
#   CORRECT would clear both halves of the discrimination check. The shared
#   reference (`pos-control-closed-form`) is checked by the gate to share the frozen
#   spec and to VERIFY before any witness is refuted against it; measured here, it
#   genuinely DECIDES and each of the eight witnesses fails against it SEMANTICALLY,
#   leaving a residual `⊢ False` or a residual equation between two `pageOf`
#   applications — i.e. the equality really holds there — not a stuck reduction.
#   Each witness ELABORATES against its own rival.
#   THE FORGERY TEST (re-measured for this revision, all eight cases, both subjects)
#   is what makes that a measurement rather than a reading of error text. For each
#   case, a file differing from the witness ONLY in its CLAIM — the equality in
#   place of its negation, asserting the impl is CORRECT there — exits 0 against the
#   reference and 1 against the rival, the rival-side residual naming the concrete
#   disagreement (listed in the module docstring). So the reference-side exit code
#   tracks the claim in BOTH directions, which is exactly what the frozen impl fails
#   to do and exactly what a discriminating subject must do; a forged witness
#   asserting the rival is correct would be caught, not recorded as a rejection.
#   The seven witnesses that bind anything (all but the empty-run one, which binds
#   nothing) have jointly satisfiable hypotheses: each
#   consistency probe leaves `False` unsolved against the reference (measured), and
#   each probe is stated over the module's own vocabulary (`numPages`, `pageOf`), so
#   it really elaborates rather than failing for an unknown name.
#   No `sorry`/`admit`/`native_decide`/`axiom` appears anywhere in this battery, and
#   no rival weakens or removes an obligation.
AXIOM_TESTS = []
