"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9320 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each case is a full ``Solution.lean`` variant that shares
the FROZEN spec byte-for-byte — region surgery touches ONLY text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct optionalPathValidator``
obligation survives with a byte-identical statement. Judged by the real
verifier: ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE. One modeled operation, one obligation:

    method optionalPathValidator (entry : List Char)
        return (out : Except Unit (List Char))
      require expansionAnswers entry = true                           -- (D)
      ensures entry = [] → out = Except.ok []                        -- (C1)
      ensures entry ≠ [] →                                           -- (C2)
        out = (if strictAccepts entry then Except.ok (pathExpanded entry)
               else Except.error ())

    prove_correct optionalPathValidator by loom_solve

(D) is the obligation's DOMAIN: the entry must be one whose expansion ANSWERS.
Nothing else about the entry is restricted, so (D) constrains the ENTRY alone and
not which entries are accepted — the whole accept / turn-away decision stays
inside C1 and C2. The empty entry, the entry the modeled change is about, is
INSIDE the domain (``expansionAnswers_empty``), which is what stops (D) from
excusing C1 at the point that matters: admiss-outcome-nondegenerate pins that
membership, and every reject witness at ``[]`` below discharges (D) with it.

The carrier is an optional path entry (``List Char``; the empty entry is ``[]``)
and an accept/turn-away outcome (``Except Unit (List Char)``: ``ok v`` = the
entry ``v`` is accepted, ``error ()`` = it is turned away). The strict path-name
validator is modeled in the ``axioms`` region as an opaque PROGRAM plus two
assumed facts, with a third assumed group about the primitives it is built from:

    opaque pathIsDir        : List Char → Bool         -- os.path.isdir (TOTAL)
    opaque expansionAnswers : List Char → Bool         -- WHERE expanduser answers
    axiom pathIsDir_empty        : pathIsDir [] = false
    axiom expansionAnswers_empty : expansionAnswers [] = true

    opaque rawExpansion : (entry : List Char) →        -- os.path.expanduser, and
      expansionAnswers entry = true → List Char        --   NOT total: readable
    axiom rawExpansion_empty (answered) :              --   only where it answers
      rawExpansion [] answered = []
    def pathExpanded (entry : List Char) : List Char := -- the GUARDED expansion:
      if answered : expansionAnswers entry = true       --   free to read ANYWHERE,
      then rawExpansion entry answered else []          --   guard in the term
    def strictAccepts (entry) : Bool := pathIsDir (pathExpanded entry)

    opaque strictPathValidator : List Char → VelvetM (List Char)
    axiom strictPathValidator_accepted   (entry) : expansionAnswers entry = true →
      strictAccepts entry = true →
      strictPathValidator entry = pure (pathExpanded entry)
    axiom strictPathValidator_turns_away (entry) : strictAccepts entry = false →
      ¬ triple (l := Prop) True (strictPathValidator entry) (fun _ => True)

FIVE assumed facts, all of them fuzz-checked against the real unchanged callee by
axiom_check.py (G-AX); ``pathExpanded_empty``, ``strictAccepts_empty`` and
``strictPathValidator_hands_back`` are THEOREMS derived from them, not further
assumptions. The five are jointly satisfiable, shown by a Lean-checked model
recorded in refinement.md §D (``mRawExpansion``/``mIsDir``/``mExpansionAnswers``/
``mValidator``, exit 0).

WHY THE MODEL LOOKS LIKE THAT — the hole this battery now covers. A previous
revision modeled the strict validator as an ``opaque`` PURE TOTAL function into
``Except``, and C2 read ``out = strictPathValidator entry``. Under that model,
handing the validator an entry was an act with no consequence: G-EQ recorded a
rival (hoisted delegation — bind the validator's answer for ``entry`` once, THEN
test emptiness and select) that verified while its faithful counterpart did NOT
resolve (FAIL_TO_PASS 0/1 on tests/test_quickstart.py, PASS_TO_PASS 9/9,
consistent over 3 attempts). The real callee does not return a rejection: it
RAISES, so a hoisted call on the empty entry raises before the emptiness test is
ever reached and the empty entry can never be accepted. Modeling the raise as a
returned value converted "calling it takes control away from you" into "calling
it produces a value you may ignore", and no clause over the RESULT can see the
difference.

The repair models the refusal instead of reifying it: the validator is a program
with no body and no total function underneath, guaranteed to come back only where
the entry is accepted (``strictPathValidator_accepted``) and with no termination
guarantee at all otherwise (``strictPathValidator_turns_away``, meaningful
because ``NoFailure DivM`` is declared inside ``PartialCorrectness`` and this
bundle opens ``TotalCorrectness``, so ``wp c (fun _ => True)`` really does express
"comes back"). Submitting an entry is therefore an act a program must EARN at the
point it hands the entry over, while DECIDING acceptance stays free
(``strictAccepts`` reads a total directory test and the GUARDED expansion, so it
answers everywhere — at every entry, derived ones included — in any order, as
often as a program likes). That is the control-flow fact the change
actually is, and weak-submission-hoisted / weak-unconsumed-probe below are the
rivals that witness it.

WHY THERE IS A DOMAIN AT ALL — the second hole this battery covers, on the other
side of the ledger. A previous revision carried no ``require``, so the domain was
every ``List Char``; and because the expansion was modeled as an opaque TOTAL
function, ``strictAccepts entry`` was a defined ``Bool`` at every entry and C2
therefore pinned an OUTCOME — an accepted value, or a turn-away — at every entry
without exception. The real expansion is not total. Asked to expand an entry that
begins with ``~`` whose first segment cannot be looked up (an embedded NUL byte in
that segment is the reachable witness — ``ValueError`` out of ``pwd.getpwnam``,
which ``expanduser`` does not catch — and a HIGH surrogate is another, via
``UnicodeEncodeError``; a LOW surrogate is NOT, since ``surrogateescape`` encodes
it and the lookup merely fails to find it, which IS caught), it
neither answers nor signals the refusal the consumer catches and re-prompts on: it
escapes with something else entirely, straight through the modeled function and
past the consumer's own handler. At such an entry the real post-change behavior
supplies NEITHER of the two outcomes C2 offered, so the obligation was too strong
there — a spec-side demand the code it models does not meet, on a sub-domain
nothing in the previous battery could see (axiom_check.py's and
conformance_check.py's alphabets contained no NUL, which is why the fuzzing agreed
with it).

(D) is the repair, and it is deliberately the SMALLEST one available. A third
opaque primitive ``expansionAnswers`` names the entries the expansion answers for;
the two places the expansion's ANSWER is read are guarded by it — the acceptance
equation ``strictPathValidator_accepted`` and the method's own ``require`` — while
the refusal fact ``strictPathValidator_turns_away`` stays UNGUARDED on purpose,
because an entry whose expansion does not answer does not come back from a
submission either, so guarding it would give away refutations for nothing. The
alternative — leaving the domain open and guarding the two ``ensures`` clauses
instead — was measured and rejected: an antecedent on the clauses leaves the
method's TERMINATION obligation standing at an entry where the modeled program
does not come back, so it does not close the hole at all.

(D) is also the one part of the obligation whose EXTENT is measured outside Lean,
in both directions, because a domain can fail two ways and only one of them is
visible from inside a battery. conformance_check.py (G-CONF) asserts, on 100029
real inputs at the patched commit, that IN the domain the real function always
comes back — a value or the ValidationError the consumer catches, never a third
outcome, so (D) is not too SMALL and no governed entry is unspecifiable — and that
OUT of it the real function never comes back at all, so (D) is not too LARGE and
excuses nothing that could have been specified. Both directions have recorded
negative controls: with the domain widened to every entry (the previous revision)
the gate fails at ``'~\\x00abc'``; with it widened to exclude every ``~`` entry it
fails at ``'~root'``. axiom_check.py (G-AX) buckets its own inputs the same way
and asserts each bucket non-empty, so neither checker can go blind to the region
again the way the previous alphabets did.

Nothing on the interesting sub-domain moved. ``expansionAnswers_empty`` puts the
empty entry inside the domain, so C1, the derived ``strictAccepts_empty`` and
every witness at ``[]`` are untouched, and the two rivals G-EQ measured as
verifying-but-not-resolving are still refuted at exactly the input they were
refuted at before. What the loosening could have cost is a licence to answer with
a turn-away wherever the entry is merely in the domain, or to read (D) as though
it said the entry is ACCEPTED; weak-domain-guard-as-verdict is the rival that
shows the first is not admitted, and pos-domain-guard-redundant is the control
showing the domain hypothesis is genuinely available to an impl rather than
vacuous.

WHY THE EXPANSION IS READ THROUGH A GUARD — the third hole this battery covers,
and the one the domain (D) did NOT close. (D) restricts the ENTRY the obligation is
claimed for. It says nothing about entries an impl DERIVES from that entry, and a
previous revision modeled the expansion as ``opaque pathExpanded : List Char →
List Char`` — a TOTAL function type — with a comment promising that reading it "can
never take control away from whoever reads it". A total function type licenses a
read at ANY argument, so G-EQ recorded three rivals that read the primitives at an
argument the ``require`` says nothing about, are outcome-NEUTRAL in Lean, and
therefore verify:

    if entry = [] then
      if pathIsDir (pathExpanded ('~' :: Char.ofNat 0 :: entry)) then
        return Except.ok []                       -- both arms identical, so the
      else                                        -- rival is value-identical to
        return Except.ok []                       -- the frozen impl everywhere
    else ...

Their faithful counterparts did NOT resolve (FAIL_TO_PASS 0/1 on
tests/test_quickstart.py::test_exits_when_existing_confpy, PASS_TO_PASS 9/9, two
attempts each, consistent): the Python for that read was
``path.isdir(path.expanduser('~\\x00' + x))``, which RAISES
ValueError('embedded null byte') on the F2P input ``x = ''`` — past the consumer's
``except ValidationError`` and out of ``ask_user`` — so the SystemExit that test
requires never happens. Two further rivals pulled the same lever through
``strictAccepts`` (the DERIVED decision) and at a CONSTANT entry that does not
mention ``entry`` at all.

The repair puts the guard in the TERM instead of in a comment, which is the only
place a refinement cannot drop it: the expansion proper (``rawExpansion``) takes a
PROOF that the entry is one it answers for, and the freely readable
``pathExpanded`` is the guarded reading of it — ``if answered : expansionAnswers
entry = true then rawExpansion entry answered else []``. Four consequences, each
measured through scripts/lean_verify.sh:

  * a read of the expansion at an entry NOT shown to be in the domain does not
    elaborate at all: ``pathIsDir (rawExpansion ('~' :: Char.ofNat 0 :: entry))``
    fails with ``Application type mismatch … has type expansionAnswers ('~' ::
    Char.ofNat 0 :: entry) = true → List Char but is expected to have type List
    Char`` (exit 1). The class is closed structurally rather than by prose — there
    is no unguarded read left to refine.
  * the G-EQ rival above still verifies (exit 0) — and MUST, being value-identical
    to the frozen impl at every entry — but what it reads is now the GUARDED
    expansion, whose refinement carries the guard with it (mapping.md §1.1:
    ``pathExpanded x`` ↔ ``path.expanduser(x) if _answers(x) else ''``). That
    refinement does not raise, so it RESOLVES; it is shipped as
    pos-derived-probe-guarded, a soundness positive and not a rival, because
    recording a resolving impl as a rival would assert something false.
  * reading a derived entry's decision is free; ANSWERING from it is not.
    weak-derived-probe-as-verdict is refuted (exit 1) on the goal
    ``⊢ entry = [] → Except.error () = Except.ok []``, so the licence to read is
    not a licence to decide — the same line pos-domain-guard-redundant and
    weak-domain-guard-as-verdict pin for (D).
  * ACTING on a derived read is licensed exactly where the derived entry is shown
    ACCEPTED — and that far only. The guard makes
    ``accepted_in_domain : strictAccepts entry = true → expansionAnswers entry =
    true`` a THEOREM (off the domain the guarded expansion is ``[]`` and
    ``pathIsDir_empty`` says ``[]`` names no directory), so a branch that shows a
    DERIVED entry accepted earns a submission of it: pos-derived-submission-earned
    verifies (exit 0), with the earned-submission side condition discharged from
    the branch hypothesis through that theorem. It is a positive rather than a
    rival because the same implication holds of the real code — ``path.isdir`` of
    the guarded expansion is true only where the expansion answered — so
    ``is_path`` of such an entry comes back (measured by axiom_check.py over
    22039 entries at three arguments each: 5300 accepted reads — 4475 at the entry,
    825 at the derived ``'~' + entry``, 0 at the derived ``'~' + NUL + entry``,
    which is the theorem's other half — every one of them in the domain, and every
    submission they earned came back with ``expanduser`` of that argument
    verbatim; and 17639 earned derived submissions in conformance_check.py).

    Two things this consequence does NOT give away, and both are checked: being in
    the domain still does not imply being accepted (the implication runs one way
    only, so no part of the accept/turn-away decision is handed over), and a
    submission at an entry NOT shown accepted is still refutable — that is what
    weak-submission-hoisted and weak-unconsumed-probe are, and they are still
    refuted here at ``[]``.

``pathIsDir`` keeps its total function type because the real directory test IS
total: ``os.path.isdir`` catches OSError and ValueError itself and answers
``false`` for an embedded NUL or a lone surrogate rather than taking control away
(measured in both regions by axiom_check.py, which asserts it never escapes).

THE OBLIGATION'S FOUR LOAD-BEARING PARTS:

  * (D) — the DOMAIN, and the two things it must not become. It must not exclude
    the empty entry (it does not: ``expansionAnswers_empty``, pinned by
    admiss-outcome-nondegenerate and leaned on by seven witnesses), and it must not
    leak into the OUTCOME (it does not: an impl may consult it, and
    pos-domain-guard-redundant shows an impl that branches on it still verifies,
    but an impl that ANSWERS from it is refuted). Attacked by
    weak-domain-guard-as-verdict.
  * (C1) — the empty entry is ACCEPTED, carrying the empty value. Together with
    ``strictAccepts_empty`` (an empty entry is never accepted by the strict
    validator, derived from the two boundary facts) this is the whole
    discriminating content of the modeled change: before it, the empty entry
    could only be turned away. Attacked by weak-delegate-everything,
    weak-reject-empty, weak-empty-sentinel-value, weak-branches-swapped,
    weak-domain-guard-as-verdict.
  * (C2) — every non-empty entry gets exactly the strict validator's own verdict:
    the expanded entry where the validator accepts it, and a turn-away
    everywhere else. This is the frame around C1 — it forbids the empty
    affordance from reaching into non-empty entries, forbids skipping the
    validator's decision, forbids corrupting the ARGUMENT the decision is taken
    on, and forbids REWRITING the answer. Attacked by weak-accept-everything,
    weak-affordance-overreach, weak-argument-reordered, weak-outcome-rewritten,
    weak-long-entry-refused, weak-constant-accept-empty.
  * (STRUCTURAL) — no entry is submitted to the strict validator unless it is
    shown accepted THERE. This is not a separate clause; it is what C1 and C2
    cost an impl once the validator is a program rather than a value. A program
    that hands over an unearned entry has no guarantee to offer at that point,
    whatever value it would have gone on to compute. Attacked by
    weak-submission-hoisted and weak-unconsumed-probe, the two rivals whose
    faithful counterparts G-EQ measured as NOT resolving.

    Note what this does NOT demand: pos-decision-inlined below verifies while
    submitting nothing at all. The obligation is behavioral — it constrains the
    OUTCOME and makes an unearned submission a liability; it never requires the
    validator to be consulted.

BINDER COVERAGE. ``entry`` is the SOLE input binder and the binder the whole
obligation turns on. The reject witnesses probe it at four concrete points —
``[]`` (the empty entry: C1's own sub-domain), ``['a']`` (length 1), ``['a','b']``
(length 2, where order is observable) and ``['a','b','c']`` (length 3, above any
ceiling the shorter points can see) — plus ONE symbolic point
(weak-argument-reordered, a universally quantified ``entry`` with hypotheses),
which is the only way to state "the argument was reordered" without also
assuming which of two literals a directory happens to be named by. A rival wrong
only on the empty entry, only on short non-empty entries, only on LONG ones, or
only in the ARGUMENT it forwards is each refuted at the input where it is
actually wrong, rather than all of them at one shared point that would say
nothing about the spec's dependence on ``entry``.

Every one of those points is INSIDE the domain (D), and each witness has to show
it: at ``[]`` from the frozen axiom ``expansionAnswers_empty``, and at each of the
three non-empty literals and the symbolic point from an explicit hypothesis
binder ``(answers : expansionAnswers E = true)``. That is deliberate and it is
what keeps the loosening honest — a refutation at an entry the spec does not
govern would prove nothing about the spec, so no witness below is allowed to
assume the entry is out of domain, and none of them does. The gate's own
consistency probe covers those added hypotheses along with the rest.

WITNESS MECHANICS ON THIS CARRIER (measured — read before editing a witness).
Velvet's tester route (``extract_program_for`` / ``derive_tester_for`` +
``decide``) does NOT work here, and the reason is the opaque vocabulary, not the
input: C2 mentions ``strictAccepts`` and ``pathExpanded``, so no ``Decidable``
instance for the postcondition can be synthesised at ALL and the derived tester
never reduces, even at the fully literal input ``[]``. So each witness refutes
the method's Hoare ``triple`` DIRECTLY, with (D) as the precondition and C1 and C2
restated verbatim at the witness's own entry.

THE PRECONDITION IS PART OF THE STATEMENT, and it has to be, in this direction:
``triple (D E) prog post`` is WEAKER than ``triple True prog post``, so refuting
the ``True``-preconditioned version would refute something the spec never claims
and would say nothing about the obligation. Every witness therefore states
``expansionAnswers E = true`` as its precondition — exactly the method's
``require``, neither strengthened nor dropped — and then has to DISCHARGE it to
reach a contradiction, from ``expansionAnswers_empty`` at ``[]`` or from the
``answers`` binder elsewhere. A witness that could not discharge it would fail
against its own rival rather than pass, so this is checked by construction on all
fourteen. There are exactly TWO routes, and which one a rival needs is decided by
HOW it is wrong:

  (1) THE VALUE ROUTE — for a rival that comes back with the wrong outcome:

        example <binders> : ¬ triple (l := Prop) (expansionAnswers E = true)
            (optionalPathValidator E) (fun out => C1(E) ∧ C2(E)) := by
          unfold optionalPathValidator
          rw [triple]
          simp only [<facts>, loomLogicSimp]
          intro hcon
          <closer>

      ``<facts>`` leads with the domain fact — ``expansionAnswers_empty`` at
      ``[]``, the ``answers`` binder at every other point — which reduces the
      precondition away and leaves ``hcon`` as the bare ``wp`` the closer
      contradicts; the rest of ``<facts>`` reduces the rival's branch selection
      and the restated clauses at ``E``, and the closer reduces the surviving
      ``wp (pure v) post`` (``wp_pure``) to a constructor clash. Where the rival's
      chosen branch legitimately submits an ACCEPTED entry, the closer first
      rewrites that submission with ``strictPathValidator_accepted`` — which is
      what the equation form of the acceptance fact is for: without it the opaque
      program has no upper bound and a wrong VALUE behind an earned submission
      could not be refuted at all. That equation now takes the domain fact for the
      SUBMITTED entry as its first argument, which is why the two closers that use
      it carry a hypothesis about the entry they submit (``answers`` at ``['a']``,
      and ``reverse_answers`` for the reversal weak-argument-reordered hands over).

  (2) THE SUBMISSION ROUTE — for a rival that hands over an entry it has not
      earned (weak-submission-hoisted, weak-unconsumed-probe). Nothing about the
      rival's VALUE is wrong, so there is nothing to clash; what is wrong is that
      the submission happens. The witness derives that directly from the refusal
      fact:

        example <binders> : ¬ triple (l := Prop) (expansionAnswers E = true)
            (optionalPathValidator E) (fun out => C1(E) ∧ C2(E)) := by
          intro hcon
          refine strictPathValidator_turns_away E <refusal> ?_
          unfold optionalPathValidator at hcon
          rw [triple] at hcon
          rw [wp_bind] at hcon
          rw [triple]
          exact le_trans (fun _ => <domain>)
            (le_trans hcon (wp_cons _ _ _ (fun _ _ => trivial)))

      Read it as: IF the rival satisfied the obligation at ``E``, then (since its
      program begins with the submission of ``E``) the submission itself would be
      guaranteed to come back — the leading ``le_trans`` step supplies ``<domain>``
      so that ``hcon``'s own precondition is met (this is the only place the
      witness needs the domain fact, and it needs it as a PROOF rather than as a
      rewrite), ``wp_bind`` splits the prefix off and ``wp_cons``
      weakens whatever the continuation established to ``fun _ => True``. That
      contradicts ``strictPathValidator_turns_away E`` at an ``E`` the validator
      does not accept. The step is monotonicity of ``wp``, so the route cannot be
      run against a rival that does NOT submit ``E``: there is no prefix for
      ``wp_bind`` to split, and the tactic fails. Measured: this route fails
      against the frozen solution (which submits nothing at ``[]``) and against
      pos-decision-inlined, and it is the route both hole-covering rivals use.

``triple``, ``wp_pure``, ``wp_bind``, ``wp_cons``, ``loomLogicSimp`` and the five
assumed facts all come from the frozen file and its ``Velvet.Std`` import;
nothing extra is imported and no helper is declared by any witness.

MEASURED, ALL OF IT, through this bundle's own checker (scripts/lean_verify.sh,
the script the velvet backend's ``check`` calls), 1200s cap, every build reaching
a verdict:

  * the seven positives and the admissibility case: exit 0;
  * all fourteen rivals: exit 1;
  * every witness against its own rival: exit 0; against the frozen solution:
    exit 1 — so each rejection is attributable to the spec and not to the frozen
    tactic script;
  * the gate's own ``example <binders> : False`` consistency probe for the eight
    witnesses that bind anything: exit 1 (``False`` unsolved) in all eight, so no
    refutation here rests on a contradiction. Six witnesses bind nothing and
    need no probe — the four at ``[]`` (which take the domain fact from the frozen
    axiom rather than from a binder) and the two submission-route ones.

TWO NOTES ON THE ADMISSIBILITY CASE, both traps worth recording. First,
``(Except.ok ['a'] : Except Unit (List Char)) ≠ Except.error ()`` is NOT
decidable on this carrier — there is no ``DecidableEq (Except Unit (List Char))``
instance, and ``decide`` fails with ``failed to synthesize Decidable`` (measured
in isolation, exit 1). The non-degeneracy it was meant to state is carried by the
``toOption.isSome`` projection instead, which is a ``Bool`` and decides. Second,
the DOMAIN conjunct ``expansionAnswers [] = true`` is not decidable either, and
for a more basic reason — ``expansionAnswers`` is ``opaque``, so it has no value
to evaluate; it is discharged from the frozen axiom instead, which is why that
case's tactic tail peels the conjunct with
``refine ⟨expansionAnswers_empty, ?_⟩`` before handing the rest to ``decide``
(measured: ``all_goals simp [expansionAnswers_empty]`` does NOT close the
``toOption`` conjuncts, exit 1, so the two halves need the two tactics).

MODELING ASYMMETRY, DISCLOSED AND MEASURED. The real callee signals refusal by
RAISING. Inside the modeled method nothing catches that raise, so it is modeled
as control not coming back. At the METHOD's own boundary the raise IS an outcome
— its consumer catches ValidationError and re-prompts — so there it is reified as
the value ``Except.error ()`` (mapping.md §2). Those are two faithful abstractions
of the same exception at two different boundaries, and they cost exactly one impl
SHAPE: the shape that submits every non-empty entry and lets the callee's raise
PROPAGATE,

    if entry = [] then return Except.ok []
    else let accepted ← strictPathValidator entry; return Except.ok accepted

does not verify here (measured: exit 1), because under
``loom.semantics.termination "total"`` a program that does not come back
satisfies no ``ensures`` at all. It is deliberately NOT shipped as a reject
rival: its faithful counterpart is the gold patch's own control flow, which
RESOLVES, so recording it as a rival would assert something false. What the
clauses demand is the patched function's BEHAVIOR with the raise reified at its
boundary, and the frozen impl refines exactly that — ``return is_path(x)``
answers with the expanded entry where the entry is accepted and raises
otherwise, which is ``Except.ok (pathExpanded entry)`` / ``Except.error ()`` under
mapping.md §2. The asymmetry restricts which SHAPES can be written; it adds no
obligation the real post-patch behavior violates. refinement.md §C records it as
a modeling limitation.

That asymmetry and the DOMAIN (D) are separate matters and are worth keeping
apart. The asymmetry costs impl SHAPES on a sub-domain where the clauses are
faithful; (D) removes the CLAUSES from a sub-domain where no clause of this shape
could be faithful, because the real behavior there is neither of the two outcomes
the carrier offers. The first is a restriction on the writer, the second is a
restriction on the reader, and each is disclosed where the other is not enough:
refinement.md §C now carries both, and mapping.md carries the boundary analysis
they share — §2.1 for the exception at the two boundaries, §2.2 for the third
outcome that is neither of them and for why it is answered with a domain rather
than a wider abstraction.

SATISFIABILITY OF EACH HYPOTHESIS AGAINST THE REAL UNCHANGED CALLEE. The real
callee expands the entry and accepts it iff the expansion names an existing
directory, so: ``strictAccepts ['a'] = false`` and ``strictAccepts ['a','b','c']
= false`` hold whenever those entries name nothing (the ordinary case);
``strictAccepts ['a'] = true``, ``strictAccepts ['a','b'] = true`` and
``pathExpanded ['a'] = ['a','b']`` are each realisable — by the entry naming a
real directory, and by an expansion that lengthens the entry (which is what
``~`` expansion does) respectively. The domain hypothesis every non-empty witness
now carries, ``expansionAnswers E = true``, is realisable at all of them and in
fact holds of every entry a user could type at a prompt: the expansion answers
unless the entry begins with ``~`` and its first segment cannot be looked up at
all, which no ordinary literal does — ``['a']``, ``['a','b']`` and ``['a','b','c']``
all answer, and so does ``[]`` (that one is the frozen axiom, checked by G-AX).
weak-argument-reordered's hypotheses
(``entry ≠ []``, ``strictAccepts entry.reverse = true``, ``strictAccepts entry =
false``, plus ``expansionAnswers entry = true`` and ``expansionAnswers
entry.reverse = true``) are jointly realisable by any entry whose reversal names a
directory and which names nothing itself. Each is a statement about a reachable
sub-domain,
which is all a witness needs; the gate's consistency probe confirms none of them
is self-contradictory (eight builds, ``False`` unsolved in all eight).

PORT DISPOSITION of the nagini sibling's classes — see ``assessment`` in the
submitted payload for the full accounting. In brief:

  * SOUNDNESS positives — ported, five of them: guard inversion, an equivalent
    emptiness test, a branch-per-constructor shape, an impl that takes the
    acceptance decision itself and submits nothing, and one that branches on the
    domain condition it is already given. All five keep the frozen ``loom_solve``
    verbatim. Two more positives are NOT ports but consequences of the read guard
    above, and they are the reason that class grew: pos-derived-probe-guarded (a
    guarded read at a DERIVED entry, discarded) and pos-derived-submission-earned
    (a submission of a derived entry inside the branch that shows it accepted).
    Seven positives in all; six of the seven keep the frozen ``loom_solve``, and
    only the last needs a tail (``accepted_in_domain`` for the earned-submission
    side condition), which is flagged where it is written.
  * ADMISSIBILITY — the sibling's precondition-admits-a-normal-input probe is
    live here, and it is the control the domain (D) needs: the case pins
    ``expansionAnswers [] = true``, so the ONE input the modeled change is about
    is inside the domain and C1 cannot be satisfied by the entry being out of it.
    The second residual risk on this carrier is that the post-image is DEGENERATE
    at that same point; the same in-region ``assert`` pins six further facts about
    it, seven conjuncts in all.
  * FRAME / PERMISSION MUTATION — the sibling's two rivals write to the read-only
    input. The DIRECT form is inexpressible and demonstrated so: assigning to
    ``entry`` inside the impl region does not produce a wrong-but-well-formed
    rival, it produces a file the front end refuses (``` `entry` cannot be
    mutated, only variables declared using `let mut` can be mutated ```). But the
    class is not inexpressible as a whole, and the honest disposition is
    SUBSUMED rather than inexpressible: ``let mut e := entry`` IS accepted, and a
    rival that then takes its verdict on the mutated local is well-formed and is
    REJECTED by the frozen obligation (measured, exit 1, both for ``e := []`` and
    for ``e := e ++ ['x']``). The ``e := []`` form is even fully witnessable
    (its witness elaborates against the rival and fails against the frozen
    solution). It is not shipped because it adds no discriminating power: the
    already-shipped weak-constant-accept-empty witness kills it unchanged
    (measured, exit 0), i.e. mutating the local to ``[]`` is behaviorally the same
    attack as answering the empty literal constantly. The ``++ ['x']`` form is
    spec-rejected but no witness for it was landed here, so it is recorded as an
    admitted, non-load-bearing gap rather than as a demonstrated impossibility.
  * THE SIBLING'S STRICT-VALIDATOR RIVALS (which reshape that validator's OWN
    body) — INEXPRESSIBLE for a carrier reason: on this carrier the validator has
    no body. It is ``opaque`` in the ``axioms`` region, which the consumer spec
    view KEEPS, so any rewrite of it changes the SPEC rather than the impl and
    ``variant_scope`` reports ``spec view differs (same_spec failed)``. Its
    behavioral fidelity is carried by G-AX against the real callee instead, which
    is where an assumed fact's fidelity belongs.
  * THE SIBLING'S CONSUMER-SIDE RIVALS (weak-abort-inverted, weak-abort-const-
    false, and the abort half of admiss-empty-and-nonempty) — the sibling models
    the consuming decision as a THIRD function; this carrier models one
    operation, so there is no separate abort obligation to invert. The
    constant-answer attack it aimed there IS expressible against this obligation
    and is shipped as weak-constant-accept-empty.
  * DIVERGENCE / NON-TERMINATION — no longer only a class to dispose of: the
    termination semantics is now LOAD-BEARING for two shipped rivals (route 2
    above rests on ``wp c (fun _ => True)`` meaning "comes back", which holds
    under ``open TotalCorrectness`` and would not under ``PartialCorrectness``).
    As a rival CLASS it stays inapplicable: the frozen impl is loop-free, so a
    diverging rival has to bring a loop of its own, and the semantics then makes
    it owe a descent obligation — re-measured on this bundle, a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    rejected on the measure's own goal (``case «decreasing_1: spin» … ⊢ spin <
    spin``), and dropping the clause is refused even earlier (``Decreasing
    annotations are required in total correctness semantics``). Nothing is
    shipped as a reject case even so, and for the WITNESS contract rather than a
    spec weakness — but NOT for the reason a first pass suggests. It is not that
    the rival's module fails to compile ahead of its witness: ``witness_file``
    STRIPS the ``prove_correct`` block, so the descent obligation is absent from
    the witness file, and the witness file of an annotated diverging rival
    compiles clean (measured: exit 0 with a trivial witness appended; only the
    UN-annotated form fails that early, on ``Decreasing annotations are
    required``). The real blocker is that the claim cannot be REACHED on this
    carrier: the loop elaborates to a ``forIn Lean.Loop.mk … decreasingGadget …``
    term that does not reduce, and ``Loop.forIn.loop`` is a ``partial_fixpoint``
    with no equation theorems, so every route into it stalls — measured across
    fourteen attempts spanning ``unfold`` (``Tactic unfold failed to unfold
    Lean.Loop.forIn``), ``rw``/``simp`` on the loop's own equations (``Failed to
    rewrite using equation theorems for `Loop.forIn` ``), and the two witness
    routes this battery already uses, where ``rw [wp_bind]`` and ``rw [wp_map]``
    both miss their pattern and a type-reveal shows the residual unreduced
    ``forIn`` term. That is precisely the shape the gate screens as
    ``_STUCK_UNIFICATION`` (``Type mismatch`` paired with ``forIn
    Lean.Loop.mk``). So: REJECTED-BY-SPEC is confirmed at the module level (the
    class IS caught by the frozen obligation, exit 1 on the measure goal), and
    the case is unshippable as a WITNESSED reject for a tooling reason in the
    loop encoding rather than any weakness of the spec. If ``Loop.forIn`` gains
    equation theorems, this class becomes expressible and should be ported.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 pins the result to a literal, and C2 pins it
    to a decision taken on the METHOD'S OWN INPUT, so there is no answer key an
    impl could echo without doing the work.
"""

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9320"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Both lie wholly inside a region the consumer spec view elides and
# both are unique in the file (asserted by _swap at load), so every variant
# below keeps `same_spec` and the frozen obligation statement by construction.
#
# _IMPL_BODY: the gold `do`-block body, WITHOUT the `-- impl-start` /
#   `-- impl-end` marker lines, so the markers survive every rewrite.
# _PROOF: the frozen tactic script. Exactly two cases touch it, and both only to
#   clear a goal the frozen script cannot see: the admissibility case (the extra
#   goal its in-region `assert` raises) and pos-derived-submission-earned (the
#   earned-submission side condition at the entry it derives).
# _GOLD_INNER: gold's non-empty arm, reused verbatim by the rivals that attack
#   C1 alone and must leave C2's behavior untouched.
# ---------------------------------------------------------------------------

_IMPL_BODY = """    -- An empty entry is accepted verbatim and is never handed to the strict
    -- validator. A non-empty entry the strict validator accepts is submitted to
    -- it and comes back as the accepted value; one it does not accept is turned
    -- away.
    if entry = [] then
      return Except.ok []
    else
      if strictAccepts entry then
        let accepted ← strictPathValidator entry
        return Except.ok accepted
      else
        return Except.error ()"""

_PROOF = "prove_correct optionalPathValidator by\n  loom_solve"

_GOLD_INNER = """      if strictAccepts entry then
        let accepted ← strictPathValidator entry
        return Except.ok accepted
      else
        return Except.error ()"""

assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drift — re-sync _IMPL_BODY"
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"
assert _IMPL_BODY.count(_GOLD_INNER) == 1, "inner-arm anchor drift"


def _impl(body):
    """Solution.lean with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL_BODY, body)


def _impl_reproved(body, proof):
    """Solution.lean with the impl body AND the tactic script replaced."""
    return _swap(_swap(_BASE, _IMPL_BODY, body), _PROOF, proof)


# ---------------------------------------------------------------------------
# Witness builders. The obligation is a `method` CONTRACT, so a witness reaches
# it through the Hoare `triple` the frozen `prove_correct` discharges, restated
# at ONE entry with BOTH clauses spelled out verbatim. Checked in a file whose
# `prove_correct` block has been stripped, so no tactic script can mask the
# verdict. Two routes; see WITNESS MECHANICS above for which rival needs which.
# ---------------------------------------------------------------------------

def _post(e):
    return (f"(fun out => (({e} : List Char) = [] → out = Except.ok []) ∧\n"
            f"                (({e} : List Char) ≠ [] →\n"
            f"                  out = (if strictAccepts {e} then Except.ok (pathExpanded {e})\n"
            f"                         else Except.error ())))")


def _claim(e, binders):
    """The method's obligation at ONE entry, precondition included.

    The precondition is the method's `require` VERBATIM. It cannot be dropped:
    `triple (expansionAnswers e = true) prog post` is WEAKER than
    `triple True prog post`, so a witness against the `True`-preconditioned
    statement would refute something the spec never claims. Each witness
    discharges it instead — from `expansionAnswers_empty` at `[]`, from an
    `answers` binder elsewhere.
    """
    head = f"example {binders} :" if binders else "example :"
    return (f"{head} ¬ triple (l := Prop) (expansionAnswers {e} = true)\n"
            f"    (optionalPathValidator {e})\n"
            f"    {_post(e)}")


def _witness(e, binders, extras, closer):
    """Value route: reduce the rival's program to a `pure`, then contradict.

    `extras` leads with the domain fact, which is what collapses the
    precondition and leaves `hcon` as the bare `wp` the closer contradicts.
    """
    ex = "".join(f"{x}, " for x in extras)
    return f"""
{_claim(e, binders)} := by
  unfold optionalPathValidator
  rw [triple]
  simp only [{ex}loomLogicSimp]
  intro hcon
{closer}
"""


def _witness_submission(e, binders, refusal, domain, reducers):
    """Submission route: the rival hands `e` over without having earned it.

    `domain` is a PROOF of `expansionAnswers e = true` (not a rewrite): the
    leading `le_trans` uses it to meet `hcon`'s own precondition before `wp`
    monotonicity weakens the continuation away.
    """
    red = "".join(f"  {r}\n" for r in reducers)
    return f"""
{_claim(e, binders)} := by
  intro hcon
  refine strictPathValidator_turns_away {e} {refusal} ?_
  unfold optionalPathValidator at hcon
  rw [triple] at hcon
{red}  rw [wp_bind] at hcon
  rw [triple]
  exact le_trans (fun _ => {domain})
    (le_trans hcon (wp_cons _ _ _ (fun _ _ => trivial)))
"""


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS — structurally different but behaviourally IDENTICAL impls that
    # MUST verify. If a faithful correct reshape cannot verify, the obligation
    # is SPEC-TOO-STRONG on the SHAPE of the impl rather than on its behavior.
    # Six of the seven keep the frozen `loom_solve` verbatim (measured: all six
    # close); the seventh submits an entry it DERIVES, so `loom_solve` leaves the
    # earned-submission side condition at that entry and the tail discharges it
    # from the branch hypothesis via `accepted_in_domain`.
    # =====================================================================
    {
        "id": "pos-guard-inverted",
        "kind": "soundness",
        "expect": "verify",
        # Guard inverted: the non-empty case is tested FIRST and the empty case
        # becomes the fall-through. Sibling: pos-vae-reorder.
        "module": _impl(
            """    if entry ≠ [] then
      if strictAccepts entry then
        let accepted ← strictPathValidator entry
        return Except.ok accepted
      else
        return Except.error ()
    else
      return Except.ok []"""),
        "rationale": "the same two-way decision written with the guard inverted "
                     "(non-empty tested first, the empty entry as the "
                     "fall-through) returns the same outcome for every `entry` "
                     "and submits the entry at exactly the same points, so C1 "
                     "and C2 still hold on the whole domain and no submission "
                     "is unearned. A correct reshape MUST verify, else the "
                     "obligation is SPEC-TOO-STRONG on the impl's branch order. "
                     "(Sibling: pos-vae-reorder, re-expressed on this carrier.)",
    },
    {
        "id": "pos-emptiness-test-equivalent",
        "kind": "soundness",
        "expect": "verify",
        # The emptiness test is written with the carrier's own emptiness
        # predicate instead of an equation against the empty entry. Same
        # decision; the equality of the two tests is not syntactic.
        "module": _impl(f"""    if entry.isEmpty then
      return Except.ok []
    else
{_GOLD_INNER}"""),
        "rationale": "deciding emptiness with the carrier's own emptiness "
                     "predicate rather than an equation against the empty entry "
                     "selects exactly the same branch at every `entry`, so the "
                     "post-image is unchanged, both clauses still hold and the "
                     "empty entry is still never handed over. The two tests are "
                     "not syntactically equal, so this is a real reshape and not "
                     "a rename; it must verify, else SPEC-TOO-STRONG. (Sibling: "
                     "pos-abort-inline — the sibling's equivalent-expression "
                     "control.)",
    },
    {
        "id": "pos-branch-per-shape",
        "kind": "soundness",
        "expect": "verify",
        # Branch on the entry's SHAPE (empty / head-and-tail) with a return in
        # each arm. The non-empty arm forwards the entry REASSEMBLED from its
        # own head and tail, so the argument is unchanged without being
        # syntactically the same term. Sibling: pos-strict-reorder.
        "module": _impl(
            """    match entry with
    | [] => return Except.ok []
    | c :: cs =>
      if strictAccepts (c :: cs) then
        let accepted ← strictPathValidator (c :: cs)
        return Except.ok accepted
      else
        return Except.error ()"""),
        "rationale": "branching on the entry's shape and returning from each arm "
                     "is the same function: the empty arm yields the accepted "
                     "empty value (C1) and the non-empty arm takes the "
                     "acceptance decision on, and submits, the entry reassembled "
                     "from its own head and tail — i.e. unchanged (C2), and "
                     "earned in the same place. Two return sites instead of one; "
                     "must verify, else SPEC-TOO-STRONG on the impl's "
                     "control-flow shape. (Sibling: pos-strict-reorder.)",
    },
    {
        "id": "pos-decision-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Takes the acceptance decision itself and submits NOTHING: the outcome
        # is computed from the two total-typed primitives. Added with the model change,
        # and the control that keeps the structural obligation honest.
        "module": _impl(
            """    let decided : Except Unit (List Char) :=
      if strictAccepts entry then Except.ok (pathExpanded entry)
      else Except.error ()
    if entry = [] then
      return Except.ok []
    else
      return decided"""),
        "rationale": "this impl consults the two total-typed primitives, decides the "
                     "outcome itself, and never submits anything to the strict "
                     "validator — and it is behaviourally identical to the "
                     "frozen impl at every `entry` (the empty entry is accepted "
                     "as the empty value; a non-empty entry gets the expanded "
                     "entry exactly where it is accepted and a turn-away "
                     "otherwise). Its faithful counterpart performs the "
                     "expansion and the directory test inline instead of calling "
                     "the unchanged helper, which resolves. It MUST verify: the "
                     "obligation constrains the OUTCOME and makes an UNEARNED "
                     "submission a liability, and a spec that instead demanded "
                     "the helper be called would be too strong on the impl's "
                     "choice of route. It is also the control for witness route "
                     "2: the submission route cannot be run against an impl that "
                     "submits nothing (measured — it fails here as it fails "
                     "against gold).",
    },
    {
        "id": "pos-domain-guard-redundant",
        "kind": "soundness",
        "expect": "verify",
        # Branches on the DOMAIN condition the `require` already grants, and does
        # the gold thing on the branch where it holds. The other branch is
        # unreachable under the precondition, so this is the control that shows
        # (D) is a usable hypothesis rather than a vacuous one.
        "module": _impl(
            """    if expansionAnswers entry then
      if entry = [] then
        return Except.ok []
      else
        if strictAccepts entry then
          let accepted ← strictPathValidator entry
          return Except.ok accepted
        else
          return Except.error ()
    else
      return Except.error ()"""),
        "rationale": "an impl may consult the domain condition it is given: on "
                     "the branch where the expansion answers it does exactly what "
                     "the frozen impl does, and the other branch is unreachable "
                     "under the `require`, so it is behaviourally identical on the "
                     "whole domain and no submission is unearned. It MUST verify, "
                     "for two reasons. It is the SOUNDNESS control on the shape "
                     "(a spec that rejected an impl for re-testing a condition it "
                     "was handed would be too strong), and it is the control that "
                     "shows the precondition genuinely REACHES the impl — the "
                     "unreachable arm is discharged from `require_1` and from "
                     "nothing else, so if the domain hypothesis were not available "
                     "at that point this case would fail. Its faithful "
                     "counterpart is the gold function guarded by a test that is "
                     "true wherever it is called, which resolves.",
    },

    {
        "id": "pos-derived-probe-guarded",
        "kind": "soundness",
        "expect": "verify",
        # Reads the guarded expansion at an entry DERIVED from `entry` — the
        # shape G-EQ used to break the previous revision, where the expansion had
        # a TOTAL function type and the read refined to an unguarded
        # `path.expanduser('~\x00' + x)` that RAISES. Both arms are identical, so
        # the rival is value-identical to the frozen impl; with the guard in the
        # term its refinement is total and it resolves, so it belongs here rather
        # than among the rivals.
        "module": _impl(f"""    if entry = [] then
      if pathIsDir (pathExpanded ('~' :: Char.ofNat 0 :: entry)) then
        return Except.ok []
      else
        return Except.ok []
    else
{_GOLD_INNER}"""),
        "rationale": "an impl may CONSULT the guarded expansion at any entry it "
                     "likes, including one it derives from its own input, and this "
                     "one consults it at `'~' :: NUL :: entry` and then ignores "
                     "what it read — both arms are the same, so the impl is "
                     "value-identical to the frozen one at every entry and submits "
                     "nothing it has not earned. It MUST verify, and it is the "
                     "SOUNDNESS side of the third hole this battery covers. Its "
                     "faithful counterpart resolves: mapping.md §1.1 binds a read "
                     "of `pathExpanded x` to the GUARDED expansion "
                     "`path.expanduser(x) if _answers(x) else ''`, which is total, "
                     "so the read cannot escape and both arms still return the "
                     "empty entry accepted (measured: `_expanded('~\\x00') == ''` "
                     "and `path.isdir('')` is False). Under the previous revision, "
                     "where the expansion had a total FUNCTION TYPE and its read "
                     "refined to a bare `path.expanduser`, exactly this shape "
                     "verified while its counterpart did NOT resolve — that is the "
                     "hole the guard closes, and the reason this case is a positive "
                     "and not a rival. The companion control on the other side is "
                     "weak-derived-probe-as-verdict: reading is free, ANSWERING "
                     "from what was read is not.",
    },

    {
        "id": "pos-derived-submission-earned",
        "kind": "soundness",
        "expect": "verify",
        # The other half of the read licence, and the one that touches the CALLEE:
        # an impl that SUBMITS an entry it derived from its own input, inside the
        # branch where it has shown that derived entry accepted. `accepted_in_domain`
        # is what lets it earn that submission, and it is also what makes the
        # refinement safe — see the rationale. The derived family here is `'~' ::
        # entry` rather than the sibling's `'~' :: NUL :: entry` on purpose: this one
        # is genuinely accepted for the F2P input, so the submission branch is LIVE
        # in the refinement and G-CONF measures it instead of skipping it.
        "module": _impl_reproved(f"""    if entry = [] then
      if strictAccepts ('~' :: entry) then
        let _probe ← strictPathValidator ('~' :: entry)
        return Except.ok []
      else
        return Except.ok []
    else
{_GOLD_INNER}""",
            _PROOF + "\n  all_goals exact ⟨accepted_in_domain _ (by assumption), "
                     "by assumption⟩"),
        "rationale": "the read licence of mapping.md §1.1 extends to ACTING on what "
                     "was read, and this case fixes exactly how far: an impl may "
                     "submit an entry it derived from its own input, but only inside "
                     "a branch where it has shown that derived entry ACCEPTED. It "
                     "verifies (measured, exit 0), and the goal `loom_solve` leaves "
                     "is the earned-submission side condition at the derived entry, "
                     "`expansionAnswers ('~' :: entry) = true ∧ strictAccepts "
                     "('~' :: entry) = true` — discharged from the branch hypothesis "
                     "via the derived theorem `accepted_in_domain`, which is why the "
                     "tactic tail is retuned and why nothing here is assumed. Its "
                     "counterpart RESOLVES, for the same reason the theorem holds: "
                     "`path.isdir` of the guarded expansion can only be true where "
                     "the expansion answered (the guarded value is otherwise `''`, "
                     "and `path.isdir('')` is False), so inside that branch "
                     "`is_path('~' + x)` neither escapes nor raises — it returns "
                     "`path.expanduser('~' + x)`. Measured over 20014 entries at "
                     "three arguments each: 2928 accepted reads, every one in-domain, "
                     "every `is_path` came back with `expanduser` verbatim, 0 "
                     "violations; G-AX asserts the same implication on every input "
                     "and G-CONF runs this impl as a second shadow, where the "
                     "submission branch is LIVE (on the F2P input `x = ''` the "
                     "derived entry is `'~'`, which expands to the home directory and "
                     "is accepted, so the shadow really does submit it, gets "
                     "`/home/<user>` back, discards it and still accepts the empty "
                     "entry). The `'~' + NUL + x` family of its sibling would make "
                     "this branch DEAD in Python instead — the guarded expansion is "
                     "`''` and `path.isdir('')` is False — which is the same fact "
                     "from the other side: an entry whose expansion escapes can "
                     "never be shown accepted, so no verifying impl can submit one.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's probe shows a normal, F2P-shaped input is
    # in-domain, and with the `require` in place that probe is live: the FIRST
    # conjunct is `expansionAnswers [] = true`, i.e. the one input the modeled
    # change is about is inside the domain, so the restriction cannot be what
    # satisfies C1. What is ALSO at risk on this carrier is that the post-image is
    # DEGENERATE at that same point, in which case C1 and C2 would be satisfiable
    # without distinguishing anything. The in-region assert pins seven facts that
    # rule both out; the impl is kept verbatim so the method's own obligation still
    # discharges, and the proof is retuned only to clear the extra assert goal.
    # =====================================================================
    {
        "id": "admiss-outcome-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            """    assert (with_name_prefix `admiss
      ((expansionAnswers [] = true) ∧
       ((Except.ok [] : Except Unit (List Char)).toOption.isSome = true) ∧
       ((Except.error () : Except Unit (List Char)).toOption.isSome = false) ∧
       ((Except.ok ['a'] : Except Unit (List Char)).toOption.isSome ≠
          (Except.error () : Except Unit (List Char)).toOption.isSome) ∧
       (([] : List Char) = [] ↔ True) ∧ ((['a'] : List Char) = [] ↔ False) ∧
       ((if ([] : List Char) = [] then (0 : Nat) else 1) = 0)))
""" + _IMPL_BODY,
            "prove_correct optionalPathValidator by\n"
            "  loom_solve\n"
            "  all_goals refine ⟨expansionAnswers_empty, ?_⟩\n"
            "  all_goals decide"),
        "rationale": "the FIRST conjunct is the sibling's own "
                     "precondition-admits-a-normal-input probe, live here because "
                     "the obligation now has a domain: `expansionAnswers [] = "
                     "true` says the empty entry — the one input the modeled "
                     "change is about — is INSIDE it, so the restriction cannot be "
                     "what satisfies C1 and the domain is not empty at the point "
                     "that matters. It is discharged from the frozen axiom rather "
                     "than by `decide`, because `expansionAnswers` is opaque and "
                     "has no value to evaluate. What the remaining conjuncts "
                     "discharge is that the "
                     "post-image is NON-DEGENERATE at that same point. Six "
                     "facts: an acceptance IS an acceptance and a turn-away is "
                     "NOT one (so C1's `Except.ok []` is not vacuously equal to "
                     "a turn-away), an accepted non-empty value is "
                     "distinguishable from a turn-away, the emptiness test "
                     "genuinely separates the empty entry from a non-empty one "
                     "(so C1 and C2 govern disjoint sub-domains rather than one "
                     "collapsing into the other), and the frozen impl's OWN "
                     "branch selection at the concrete F2P-shaped entry — the "
                     "empty one — lands in the empty-affordance arm, so the "
                     "obligation is shown satisfiable AT that input by "
                     "evaluation. The third fact is stated over the "
                     "`toOption.isSome` projection rather than as `Except.ok "
                     "['a'] ≠ Except.error ()` because there is no `DecidableEq "
                     "(Except Unit (List Char))` instance and `decide` cannot "
                     "synthesise one (measured in isolation: `failed to "
                     "synthesize Decidable`, exit 1). If the assert could not "
                     "discharge, the obligation would be unsatisfiable at "
                     "exactly the interesting input; the impl is kept verbatim "
                     "so the method's own `ensures` discharges too. (Sibling: "
                     "admiss-empty-and-nonempty, re-aimed at the residual risk "
                     "on this carrier.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each is a wrong impl sharing the frozen
    # spec, and each carries a machine-checked refutation witness plus the
    # argument that its faithful real counterpart would NOT resolve — so a rival
    # that VERIFIED would be a true verify-does-not-imply-resolve break rather
    # than an artifact.
    #
    # ATTACKING C1 (the empty entry is accepted, carrying the empty value):
    #   weak-delegate-everything, weak-reject-empty, weak-empty-sentinel-value
    # ATTACKING C2 (a non-empty entry gets the validator's own verdict on the
    #   entry itself, unaltered):
    #   weak-accept-everything, weak-affordance-overreach,
    #   weak-argument-reordered, weak-outcome-rewritten, weak-long-entry-refused
    # ATTACKING BOTH:
    #   weak-constant-accept-empty, weak-branches-swapped
    # ATTACKING THE DOMAIN (D) — reading the domain condition as the verdict, so
    #   that the restriction becomes a licence to turn every governed entry away:
    #   weak-domain-guard-as-verdict
    # ATTACKING THE STRUCTURAL HALF (no unearned submission) — the two rivals
    #   G-EQ measured as verifying-but-not-resolving under the previous model:
    #   weak-submission-hoisted, weak-unconsumed-probe
    # =====================================================================
    {
        "id": "weak-delegate-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image: no empty affordance at all. Every entry, including the
        # empty one, is governed by the strict validator. Sibling:
        # weak-vae-prepatch-delegate-all.
        "module": _impl(
            """    if strictAccepts entry then
      let accepted ← strictPathValidator entry
      return Except.ok accepted
    else
      return Except.error ()"""),
        "witness": _witness(
            "[]", "", ["expansionAnswers_empty", "strictAccepts_empty",
                       "Bool.false_eq_true", "if_false", "wp_pure"],
            "  simp at hcon"),
        "rationale": "rejection comes from C1 at `entry = []`: the strict "
                     "validator does not accept an empty entry "
                     "(`strictAccepts_empty`, derived from the two boundary "
                     "facts), so this impl turns it away where C1 demands it be "
                     "accepted as the empty value. The witness needs no "
                     "hypothesis at all — the refusal at `[]` is a theorem of "
                     "the frozen axioms region, so the reduct is a constructor "
                     "clash.",
        "refinement": "this is the pre-image program: the strict validator alone "
                      "governs the entry, with no empty affordance in front of "
                      "it. It is precisely the reported failure — the empty "
                      "entry is not accepted, so the prompt cannot be satisfied "
                      "by supplying nothing and the program never gets to act on "
                      "an empty entry at all. The failing test supplies an empty "
                      "entry at that prompt and requires the program to "
                      "terminate as a result; under this impl the entry is "
                      "refused and the test does NOT resolve. A verifying rival "
                      "here would be the benchmark's central break.",
    },
    {
        "id": "weak-reject-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The empty entry is recognised — and then turned away. C1's acceptance
        # half is exactly inverted; C2 untouched.
        "module": _impl(f"""    if entry = [] then
      return Except.error ()
    else
{_GOLD_INNER}"""),
        "witness": _witness("[]", "", ["expansionAnswers_empty"],
                            "  simp [wp_pure] at hcon"),
        "rationale": "rejection comes from C1 at `entry = []`: the empty entry is "
                     "recognised by its own test and then turned away, where C1 "
                     "demands it be accepted carrying the empty value. The "
                     "non-empty arm is gold's verbatim, so this isolates C1's "
                     "acceptance half; no hypothesis is needed, the clash is "
                     "between two literals.",
        "refinement": "a faithful counterpart that recognised the empty entry and "
                      "then refused it reproduces the reported failure exactly: "
                      "the empty entry is still not accepted, the prompt still "
                      "cannot be satisfied by supplying nothing, and the program "
                      "still never terminates on it. The failing test does NOT "
                      "resolve.",
    },
    {
        "id": "weak-empty-sentinel-value",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss: the empty entry IS accepted (so C1's
        # acceptance half holds) but with a NON-EMPTY stand-in value.
        "module": _impl(f"""    if entry = [] then
      return Except.ok ['x']
    else
{_GOLD_INNER}"""),
        "witness": _witness("[]", "", ["expansionAnswers_empty"],
                            "  simp [wp_pure] at hcon"),
        "rationale": "rejection comes from C1's VALUE half at `entry = []`: the "
                     "empty entry is accepted, which is half the demand, but it "
                     "is accepted as some non-empty stand-in instead of as the "
                     "empty value. The nearest miss in the battery — it satisfies "
                     "the acceptance half and the whole of C2 — so it is what "
                     "shows C1 pins the VALUE and not merely the verdict.",
        "refinement": "a faithful counterpart that accepted the empty entry but "
                      "substituted some non-empty stand-in value for it would "
                      "make the entry look non-empty to everything downstream: "
                      "the empty-entry condition the program acts on never "
                      "holds, so it continues with the stand-in instead of "
                      "terminating. The failing test, which requires termination "
                      "on an empty entry, does NOT resolve — this is a verifying "
                      "rival that would ship a still-broken program.",
    },
    {
        "id": "weak-accept-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # No validation at all: every entry is accepted verbatim. C1 holds by
        # accident at the empty entry; C2 is abandoned entirely.
        "module": _impl("""    return Except.ok entry"""),
        "witness": _witness(
            "['a']", "(not_accepted : strictAccepts ['a'] = false)\n    "
                     "(answers : expansionAnswers ['a'] = true)",
            ["answers", "not_accepted", "Bool.false_eq_true", "if_false",
             "wp_pure"],
            "  simp at hcon"),
        "rationale": "rejection comes from C2 at `entry = ['a']` under the "
                     "hypotheses that the one-character entry is in the domain and "
                     "is not accepted: this impl "
                     "accepts every entry verbatim, so it accepts one the strict "
                     "validator turns away — and it also fails to expand the "
                     "ones it does accept. C1 holds by accident here (the empty "
                     "entry is returned as the empty value), which is why the "
                     "witness has to sit at a non-empty entry.",
        "refinement": "a faithful counterpart that accepted every entry verbatim "
                      "would destroy the pre-existing validation the change was "
                      "never meant to touch: a path that names nothing is "
                      "accepted and acted upon instead of being re-prompted, and "
                      "the entry is not expanded either. The failing test would "
                      "happen to pass, and the surrounding passing behavior "
                      "would break — verify would not imply resolved.",
    },
    {
        "id": "weak-affordance-overreach",
        "kind": "uniqueness",
        "expect": "reject",
        # The empty affordance reaches one character too far: entries of length
        # <= 1 are accepted as the empty value.
        "module": _impl(f"""    if entry.length ≤ 1 then
      return Except.ok []
    else
{_GOLD_INNER}"""),
        "witness": _witness(
            "['a']", "(not_accepted : strictAccepts ['a'] = false)\n    "
                     "(answers : expansionAnswers ['a'] = true)",
            ["answers", "not_accepted", "Bool.false_eq_true", "if_false"],
            "  simp [wp_pure] at hcon"),
        "rationale": "rejection comes from C2 at `entry = ['a']`: the affordance "
                     "meant for the empty entry is extended to every entry of "
                     "length at most one, so a genuine one-character entry is "
                     "accepted as the EMPTY value without the strict validator's "
                     "verdict being taken at all. C1 is satisfied exactly; this "
                     "is the rival that shows C2's sub-domain starts immediately "
                     "above the empty entry.",
        "refinement": "a faithful counterpart whose empty-entry affordance also "
                      "swallowed one-character entries would discard a real "
                      "entry and act as though nothing had been supplied. The "
                      "failing test supplies an empty entry, so it would happen "
                      "to pass, while a supplied one-character path is silently "
                      "thrown away: verify would not imply resolved.",
    },
    {
        "id": "weak-argument-reordered",
        "kind": "uniqueness",
        "expect": "reject",
        # The ARGUMENT is corrupted: the decision is taken on, and the entry
        # submitted as, its reversal. Stated at a symbolic entry — see the
        # rationale.
        "module": _impl(
            """    if entry = [] then
      return Except.ok []
    else
      if strictAccepts entry.reverse then
        let accepted ← strictPathValidator entry.reverse
        return Except.ok accepted
      else
        return Except.error ()"""),
        "witness": _witness(
            "entry",
            "(entry : List Char) (nonempty : entry ≠ [])\n    "
            "(answers : expansionAnswers entry = true)\n    "
            "(reverse_answers : expansionAnswers entry.reverse = true)\n    "
            "(reversed_accepted : strictAccepts entry.reverse = true)\n    "
            "(entry_not_accepted : strictAccepts entry = false)",
            ["answers", "entry_not_accepted", "Bool.false_eq_true", "if_false"],
            "  rw [if_neg nonempty] at hcon\n"
            "  rw [strictPathValidator_accepted entry.reverse reverse_answers\n"
            "        reversed_accepted] at hcon\n"
            "  simp [nonempty, reversed_accepted, wp_pure] at hcon"),
        "rationale": "rejection comes from C2's ARGUMENT at any non-empty entry "
                     "whose reversal is accepted while the entry itself is not: "
                     "the impl accepts and returns the expansion of the "
                     "REVERSAL, where C2 demands the verdict on the entry. This "
                     "is the one witness stated at a SYMBOLIC entry, and "
                     "deliberately: pinning it to two literals would require "
                     "assuming which of them a directory happens to be named "
                     "by, and the claim is about the argument the decision is "
                     "taken on rather than about any particular pair. The closer "
                     "rewrites the earned submission with the acceptance "
                     "equation — without it the opaque program has no upper "
                     "bound and a wrong value behind a legitimately guarded "
                     "submission could not be refuted at all.",
        "refinement": "a faithful counterpart that validated and returned the "
                      "reversal of the entry would accept paths the user never "
                      "supplied and refuse the ones they did, for every "
                      "non-palindromic entry. The failing test supplies an empty "
                      "entry (whose reversal is itself, so it would happen to "
                      "pass) while every real path prompt breaks: verify would "
                      "not imply resolved.",
    },
    {
        "id": "weak-outcome-rewritten",
        "kind": "uniqueness",
        "expect": "reject",
        # The validator IS consulted and submitted to, on the right argument,
        # and its answer is then thrown away and inverted on both arms.
        "module": _impl(
            """    if entry = [] then
      return Except.ok []
    else
      if strictAccepts entry then
        let _accepted ← strictPathValidator entry
        return Except.error ()
      else
        return Except.ok entry"""),
        "witness": _witness(
            "['a']", "(accepted : strictAccepts ['a'] = true)\n    "
                     "(answers : expansionAnswers ['a'] = true)",
            ["answers", "accepted", "if_true"],
            "  rw [strictPathValidator_accepted ['a'] answers accepted] at hcon\n"
            "  simp [wp_pure] at hcon"),
        "rationale": "rejection comes from C2's ANSWER at `entry = ['a']` under "
                     "the hypothesis that the entry IS accepted: the decision is "
                     "taken on the right argument and the entry is legitimately "
                     "submitted, and then the outcome is inverted — an accepted "
                     "entry is reported as turned away and a turned-away one is "
                     "accepted verbatim. This is the rival that shows C2 "
                     "constrains the VERDICT and not merely which call happens: "
                     "everything about this impl's control flow is earned.",
        "refinement": "a faithful counterpart that consulted the validator and "
                      "then inverted its answer would refuse every valid path "
                      "and accept every invalid one. The failing test supplies an "
                      "empty entry and would happen to pass; every other path "
                      "prompt is inverted: verify would not imply resolved.",
    },
    {
        "id": "weak-constant-accept-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # The input binder is ignored entirely: one constant outcome for every
        # entry. Sibling: weak-abort-const-false, re-aimed at this obligation.
        "module": _impl("""    return Except.ok []"""),
        "witness": _witness(
            "['a']", "(accepted : strictAccepts ['a'] = true)\n    "
                     "(answers : expansionAnswers ['a'] = true)\n    "
                     "(expanded : pathExpanded ['a'] = ['a', 'b'])",
            ["answers", "accepted", "expanded", "if_true", "wp_pure"],
            "  simp at hcon"),
        "rationale": "rejection comes from C2 at `entry = ['a']` under the "
                     "hypotheses that the entry is accepted and that expanding "
                     "it lengthens it: the impl ignores the input binder "
                     "altogether and answers with the accepted empty value for "
                     "every entry, so C1 holds by accident and C2 is abandoned "
                     "on the whole non-empty sub-domain. This is the rival that "
                     "makes the obligation's dependence on `entry` observable — "
                     "a spec both clauses of which could be met by a constant "
                     "would be attesting nothing.",
        "refinement": "a faithful counterpart that answered with the empty entry "
                      "whatever was supplied would discard every path the user "
                      "types. The failing test, which supplies nothing, would "
                      "happen to pass; every other prompt silently loses its "
                      "input: verify would not imply resolved.",
    },
    {
        "id": "weak-long-entry-refused",
        "kind": "uniqueness",
        "expect": "reject",
        # A CEILING on C2's reach: entries of length >= 3 are turned away
        # without the validator's verdict being taken.
        "module": _impl(f"""    if entry = [] then
      return Except.ok []
    else if entry.length ≥ 3 then
      return Except.error ()
    else
{_GOLD_INNER}"""),
        "witness": _witness(
            "['a', 'b', 'c']",
            "(accepted : strictAccepts ['a', 'b', 'c'] = true)\n    "
            "(answers : expansionAnswers ['a', 'b', 'c'] = true)",
            ["answers", "accepted", "if_true"], "  simp [wp_pure] at hcon"),
        "rationale": "rejection comes from C2 at `entry = ['a','b','c']` under "
                     "the hypothesis that the entry is accepted: this impl obeys "
                     "C2 only below length three and turns away everything above "
                     "it. It is the case that makes the UNBOUNDED reach of C2 "
                     "observable — every other rival in the battery agrees with "
                     "the frozen behavior from length three onward, so without "
                     "this one a spec whose delegation clause bound only short "
                     "entries would have been refuted by nothing.",
        "refinement": "a faithful counterpart that refused any entry longer than "
                      "two characters would reject essentially every real path "
                      "while never taking the validator's verdict on it. The "
                      "failing test supplies an empty entry, so it would happen "
                      "to pass, and the pre-existing prompt behavior is "
                      "destroyed for every realistic entry: verify would not "
                      "imply resolved.",
    },
    {
        "id": "weak-branches-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW inversion: the two arms are exchanged, so the empty entry
        # is governed by the strict validator and every non-empty entry gets the
        # empty affordance. Wrong on BOTH clauses. Sibling: weak-abort-inverted.
        "module": _impl(
            """    if entry = [] then
      if strictAccepts entry then
        let accepted ← strictPathValidator entry
        return Except.ok accepted
      else
        return Except.error ()
    else
      return Except.ok []"""),
        "witness": _witness(
            "['a', 'b']", "(accepted : strictAccepts ['a', 'b'] = true)\n    "
                          "(answers : expansionAnswers ['a', 'b'] = true)\n    "
                          "(expansion_nonempty : pathExpanded ['a', 'b'] ≠ [])",
            ["answers", "accepted", "if_true"],
            "  simp [wp_pure] at hcon\n"
            "  exact expansion_nonempty hcon"),
        "rationale": "rejection comes from C2 at `entry = ['a','b']` under the "
                     "hypotheses that the entry is accepted and that its "
                     "expansion is non-empty: with the arms exchanged a "
                     "non-empty entry receives the accepted EMPTY value instead "
                     "of its own expansion. It also violates C1 (the empty entry "
                     "is routed into the strict validator's arm, where "
                     "`strictAccepts_empty` sends it to a turn-away), which is "
                     "what distinguishes it from weak-affordance-overreach: that "
                     "rival satisfies C1 exactly and is wrong on a strictly "
                     "smaller sub-domain, so its witness sits at the input that "
                     "distinguishes it.",
        "refinement": "a faithful counterpart with the two arms exchanged inverts "
                      "the reported behavior: the empty entry is still refused "
                      "(so the prompt still cannot be satisfied by supplying "
                      "nothing and the failing test does NOT resolve) while "
                      "every non-empty entry is silently accepted as though "
                      "nothing had been supplied, discarding it. It fails the "
                      "failing test and breaks the passing ones.",
    },
    {
        "id": "weak-submission-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        # THE RECORDED HOLE (G-EQ atk_6). Value-identical to the frozen impl at
        # every entry; the ONLY difference is that the entry is submitted to the
        # strict validator BEFORE the emptiness test, so the empty entry is
        # handed over. Under the previous model — a pure total function into
        # `Except` — this VERIFIED, and its faithful counterpart did not resolve.
        "module": _impl(
            """    let submitted ← strictPathValidator entry
    if entry = [] then
      return Except.ok []
    else
      if strictAccepts entry then
        return Except.ok submitted
      else
        return Except.error ()"""),
        "witness": _witness_submission("[]", "", "strictAccepts_empty",
                                       "expansionAnswers_empty", []),
        "rationale": "the rejection is STRUCTURAL and nothing about the value is "
                     "wrong: at every entry this impl would answer exactly as "
                     "the frozen impl does. What it does is hand `entry` to the "
                     "strict validator before knowing anything about it, and at "
                     "`entry = []` that entry is one the validator does not "
                     "accept (`strictAccepts_empty`). The witness takes the "
                     "submission route: if the obligation held at `[]` then the "
                     "leading submission would be guaranteed to come back "
                     "(`wp_bind` splits the prefix off, `wp_cons` weakens the "
                     "continuation's postcondition to `True`), contradicting "
                     "`strictPathValidator_turns_away []`. This is the case that "
                     "covers the hole G-EQ recorded: under the previous model, "
                     "where the validator was a pure total function into "
                     "`Except`, this impl VERIFIED.",
        "refinement": "measured by the official harness, not argued: this is the "
                      "shape of the recorded G-EQ attack, whose materialized "
                      "patch was run three times (consistent, not flaky) and did "
                      "NOT resolve — FAIL_TO_PASS 0/1 on "
                      "tests/test_quickstart.py, PASS_TO_PASS 9/9. The "
                      "mechanism, confirmed by a standalone probe of the two "
                      "functions: the real callee RAISES for an entry it does "
                      "not accept, so hoisting the call raises on the empty "
                      "entry before the emptiness test is reached, the caller "
                      "catches it and re-prompts, the empty entry is never "
                      "accepted, and the program the failing test exercises "
                      "never terminates as the test requires. A verifying rival "
                      "here is exactly the verify-does-not-imply-resolve break "
                      "this repair closes.",
    },
    {
        "id": "weak-unconsumed-probe",
        "kind": "uniqueness",
        "expect": "reject",
        # The same hole from the other side (G-EQ atk_7): the frozen body is
        # kept verbatim and an unconsumed submission is put in front of it, so
        # the result is discarded rather than used.
        "module": _impl(f"""    let _probe ← strictPathValidator entry
    if entry = [] then
      return Except.ok []
    else
{_GOLD_INNER}"""),
        "witness": _witness_submission("[]", "", "strictAccepts_empty",
                                       "expansionAnswers_empty", []),
        "rationale": "the frozen body is kept verbatim and a submission whose "
                     "answer is never used is placed in front of it, so this "
                     "impl too is value-identical to the frozen one and is wrong "
                     "only in WHICH submissions happen. It is the companion to "
                     "weak-submission-hoisted and it closes the discarded-result "
                     "variant of the same shape: a spec that only forbade USING "
                     "an unearned answer would still admit this one. Refuted by "
                     "the submission route at `entry = []` for the same reason "
                     "— the leading submission would have to come back, and the "
                     "validator does not accept the empty entry.",
        "refinement": "measured: this is the second recorded G-EQ attack, whose "
                      "materialized patch also did NOT resolve (FAIL_TO_PASS "
                      "0/1, PASS_TO_PASS 9/9). Discarding the answer changes "
                      "nothing in the real program, because the call is not "
                      "answered at all for an entry the callee turns away: it "
                      "RAISES, the caller catches it and re-prompts, and the "
                      "empty entry is never accepted however carefully its "
                      "result is ignored afterwards.",
    },
    {
        "id": "weak-domain-guard-as-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        # THE DOMAIN RIVAL. It reads the domain condition (D) as the VERDICT: an
        # entry the expansion answers for is turned away, and one it does not
        # answer for is accepted as the empty value. Every entry the obligation
        # governs gets a turn-away, so it is wrong on C1 and on all of C2 — and
        # the ONLY thing that refutes it at the empty entry is that the empty
        # entry is IN the domain.
        "module": _impl(
            """    if expansionAnswers entry then
      return Except.error ()
    else
      return Except.ok []"""),
        "witness": _witness("[]", "", ["expansionAnswers_empty"],
                            "  simp [wp_pure] at hcon"),
        "rationale": "this is the rival the domain (D) has to answer for, and it "
                     "is refuted at `entry = []` by `expansionAnswers_empty` "
                     "alone: it turns away every entry the obligation governs, "
                     "including the empty one, where C1 demands the empty value be "
                     "accepted. It is the case that measures the two ways adding a "
                     "domain could have gone wrong. If the domain EXCLUDED the "
                     "empty entry, there would be no clause left at `[]` and this "
                     "impl would verify; if the domain condition were readable as "
                     "part of the OUTCOME rather than as a restriction on the "
                     "entry, an impl would be free to answer from it, and this is "
                     "the impl that does exactly that. Both are refused. Note the "
                     "contrast with pos-domain-guard-redundant, which branches on "
                     "the same condition and verifies: consulting (D) is allowed, "
                     "ANSWERING from it is not, and the two cases together are "
                     "what pin that line.",
        "refinement": "a faithful counterpart that turned away every entry whose "
                      "expansion answers — i.e. every entry a user can actually "
                      "type, the empty one included — and accepted only the "
                      "entries whose expansion escapes would refuse the empty "
                      "entry at the prompt, so the prompt still cannot be "
                      "satisfied by supplying nothing and the failing test does "
                      "NOT resolve; and it would destroy every other path prompt "
                      "as well. A verifying rival here would mean the domain "
                      "restriction had swallowed the behavior the change is "
                      "about.",
    },
    {
        "id": "weak-derived-probe-as-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        # THE DERIVED-READ RIVAL, and the companion of pos-derived-probe-guarded.
        # It reads the acceptance decision at an entry DERIVED from `entry` and
        # then ANSWERS from it: the empty entry is accepted only if the derived
        # entry happens to be accepted, and turned away otherwise. Reading is
        # free; answering from what was read is not.
        "module": _impl(f"""    if entry = [] then
      if strictAccepts ('~' :: Char.ofNat 0 :: entry) then
        return Except.ok []
      else
        return Except.error ()
    else
{_GOLD_INNER}"""),
        "witness": _witness(
            "[]",
            "(derived_not_accepted : strictAccepts ['~', Char.ofNat 0] = false)",
            ["expansionAnswers_empty", "derived_not_accepted",
             "Bool.false_eq_true", "if_false"],
            "  simp [wp_pure] at hcon"),
        "rationale": "rejection comes from C1 at `entry = []`: this impl consults "
                     "the acceptance decision at an entry it DERIVES from its own "
                     "input ('~' :: NUL :: entry) and then answers from what it "
                     "read, so the empty entry is turned away wherever that "
                     "derived entry is not accepted — which is the real case, since "
                     "the guarded expansion of a NUL-bearing `~` entry is the empty "
                     "entry and the empty entry names no directory. C2 is gold's "
                     "verbatim, so this isolates the question the third hole turns "
                     "on. Paired with pos-derived-probe-guarded, which reads the "
                     "same derived entry and ignores it and MUST verify, the two "
                     "cases pin the line exactly where pos-domain-guard-redundant "
                     "and weak-domain-guard-as-verdict pin it for (D): a program "
                     "may read anything the guarded primitives offer, at any entry, "
                     "and may answer from NOTHING except the obligation's own "
                     "clauses. The witness binds the one hypothesis it needs about "
                     "the derived entry and discharges the domain from "
                     "`expansionAnswers_empty`.",
        "refinement": "a faithful counterpart would test the guarded expansion of "
                      "'~\\x00' + x and refuse the empty entry because that test "
                      "is False (measured: `_expanded('~\\x00') == ''`, "
                      "`path.isdir('')` is False), so the empty entry is refused at "
                      "the prompt, the prompt cannot be satisfied by supplying "
                      "nothing, and the failing test does NOT resolve. Note the "
                      "contrast with the shape G-EQ broke the previous revision "
                      "with: that one IGNORED what it read and resolved (it is "
                      "shipped as a positive), while this one answers from it and "
                      "does not. The spec has to admit the first and refuse the "
                      "second, and it does.",
    },
]
