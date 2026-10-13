# Backends

A backend is an adapter around one checker. It decides one question, "does this file
satisfy its own specification", and declares enough about itself that the rest of
Benchproofer can treat its verdicts correctly.

```bash
benchproofer catalog backends     # what this installation has
benchproofer doctor               # and which of them can actually run
```

| backend | language | an accepting verdict is | ships with | file |
| --- | --- | --- | --- | --- |
| `dafny` | Dafny | a proof | `scripts/install/dafny.sh` | `solution.dfy` |
| `lean4` | Lean 4 | a proof | `scripts/install/lean.sh` | `solution.lean` |
| `nagini` | annotated Python | a proof | `scripts/install/nagini.sh` | `solution.py` |
| `smt` | SMT-LIB2 | a proof | `pip install -e ".[smt]"` | `solution.smt2` |
| `velvet` | Lean 4 (Velvet) | a proof | `scripts/install/velvet.sh` | `solution.lean` |
| `crosshair` | Python | a failed search | `pip install -e ".[crosshair]"` | `solution.py` |
| `falsifier` | Python | a failed search | the base install | `solution.py` |

`scripts/setup.sh` installs the backends that are Python wheels. The rest are separate
downloads because they are large and version-pinned: `make toolchains` runs the three
quick installers, and `make velvet` builds the Lean workspace Velvet is checked in,
which is much larger than the other three together.

## Provers and falsifiers are not interchangeable

This is the distinction the whole of Benchproofer is arranged around. A prover that
accepts a file has established that the implementation meets the specification for every
input. A falsifier that accepts one has established that it did not find a counterexample
inside its budget, which is a much weaker statement, and the gates say so:

* `spec.verifies` (the paper's verification check) records the verdict either way, so a
  bundle can be certified under a falsifier. What it certifies is weaker, and the report
  names the backend.
* `spec.strength.mutation` (the mutation check) and `spec.strength.battery`
  (property-based falsification) report what the specification wrongly accepts as a
  finding under a prover and as `inconclusive` under a falsifier. A surviving mutant under a bounded search may only
  mean the search ran out, and a loaded machine must not be able to turn a sound artifact
  into a defect.

Start on `falsifier`, which needs nothing installed, and move to a prover when the
formalization is worth the cost.

## What each one reads

Every backend reads the same file layout: one file, divided into
[marker regions](concepts.md#marker-regions) by the backend's own line-comment token.
`benchproofer catalog backends` reports the token; `template()` on the backend is the
skeleton the docs and the scaffolding use.

One thing does not vary with the backend: the program that checks what a specification
assumes against the real callee, `axioms.py`, is Python whatever language the solution is
in, because it runs where the benchmark's own tests run rather than where the checker
does.

### `falsifier`

Hypothesis drives properties declared in the `spec` region against the implementation.
No external toolchain, so a fresh install runs the whole pipeline immediately.

```python
from hypothesis import given, strategies as st

# benchproofer:begin impl
def impl(xs):
    best = xs[0]
    for x in xs:
        if x > best:
            best = x
    return best
# benchproofer:end impl

# benchproofer:begin spec
@given(st.lists(st.integers(), min_size=1))
def property_returns_the_maximum(xs):
    r = impl(xs)
    assert r in xs
    assert all(r >= x for x in xs)
# benchproofer:end spec
```

Every function named `property_*` is a separate obligation. `@settings` is a banned
token, because a per-file override of the search budget is a way to make a weak
property look strong.

The example above is the shape to copy: it says what the returned value is true of. A
property that computes the expected result and asserts the implementation agrees with it
is a second implementation of the task in the one region whoever solves the formalized
task reads, which is what `audit.no_disclosure`, the adversarial half of the paper's
leakage gate, fails a bundle for.

### `crosshair`

The same language, symbolically executed against an SMT solver, with contracts in
CrossHair's PEP 316 form. Still a falsifier, but the search is over symbolic inputs
rather than sampled ones, so it reaches cases Hypothesis rarely generates.

```python
# benchproofer:begin spec
def solve(xs: list) -> int:
    """
    pre: len(xs) > 0
    pre: all(isinstance(x, int) for x in xs)
    post: __return__ in xs
    post: all(__return__ >= x for x in xs)
    """
    return _impl(xs)
# benchproofer:end spec

# benchproofer:begin impl
def _impl(xs: list) -> int:
    best = xs[0]
    for x in xs:
        if x > best:
            best = x
    return best
# benchproofer:end impl
```

The specification is ordinary Python that a reader of the task can check by eye, which
is why this backend is a good bridge from a test-shaped benchmark to a proof. As with
`falsifier`, the search is bounded by how much work it does rather than by a clock, so
a verdict says the same thing on a busy machine as on an idle one. `verify_timeout_s`
is the ceiling on the whole invocation, not the search budget.

### `nagini`

Still Python, but a prover: Nagini translates an annotated module into Viper and
discharges its obligations with a solver, so an accepting verdict covers every input.
Contracts are ordinary function calls, which makes this the shortest step from a
Python benchmark to a proof.

```python
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# benchproofer:begin spec
def double(n: int) -> int:
    Requires(n >= 0)
    Requires(MustTerminate(2))
    Ensures(Result() == n + n)
# benchproofer:end spec
# benchproofer:begin impl
    total = 2 * n
    return total
# benchproofer:end impl
```

One function is split across two regions: the signature and its `Requires`/`Ensures`
calls are the specification, the statements that follow are the implementation. That is
the same split as Dafny's, and it is what keeps a mutant or a rival from reaching the
contract it is judged against. It is also why an admissibility probe here is a function
of its own rather than statements in the body, which would call the method from inside
itself: written at the top level after the `end impl` line, it is moved into the
implementation region by the splice (see [the property-based test
suite](concepts.md#the-pre-fix-implementation-and-rivals)).

A `MustTerminate` obligation is required here and nowhere else, and `spec.hygiene` (the
paper's hygiene check) fails a Nagini solution without it. Nagini's postconditions hold
of the runs that reach the return, so a method whose loop never exits satisfies every
`Ensures` it declares, and an accepting verdict would then say nothing about what the
implementation computes. Every other backend checks termination itself: Dafny will not
accept a loop it cannot bound, a Lean `def` is total and `partial def` is banned, and
Velvet's total-correctness option is required while its opposite is banned. The
obligation applies to the body too, so each loop needs an
`Invariant(MustTerminate(bound))` whose bound strictly decreases and stays positive, and
anything the body calls needs its own obligation at a level strictly below the caller's,
which is why the entry declares level 2: a helper and the sequence constructor both have
to fit beneath it.

Nagini rejects a module in which any type is unknown, so every parameter and return is
annotated. `Assume` and `Refute` are banned tokens. Hygiene also rejects a
`# type: ignore`, which silences the type check the translation is built on, unless it
names `has-type` alone: that one lets a method read an attribute whose type mypy cannot
determine at that point, and hides nothing from the proof. Nagini reads nothing inside a
string, so a docstring naming one of them, `@ContractOnly` or `MustTerminate` is prose. A
`@ContractOnly` function has a contract and no body, so it is an assumption rather than a
shortcut, and belongs in the `axioms` region on the same terms as Dafny's `{:axiom}`.

The model is written at whatever abstraction states the behaviour cleanly, but a `str` the
fix reads or changes the text of is a `PSeq[int]` of code points, each a Unicode scalar
value (0 to 0x10FFFF outside 0xD800 to 0xDFFF), which the precondition requires of each
string the model takes as input, so the model admits no lone surrogate, which no UTF-8 text,
Python source included, can hold. An opaque handle represents a string only where neither the
fix nor the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or edits depend
on its text, never two values those tests can tell apart, and a mapping whose keys or values
the fix reads or those tests check is modelled with its keys and its values, not its values
alone. Which unchanged callee is modeled and which is an axiom, and when a repair may take one's
result as an input, is the rule [`spec.axioms_grounded`](gates.md#specaxioms_grounded) states. Under Nagini a model is a
`@Pure` function with a body under its `benchproofer:models <callee>` line. An axiom that
returns a value is `@Pure @ContractOnly`; one whose behaviour is an effect is a
`@ContractOnly` method whose postcondition states what it changes against `Old(...)`, never
a field the implementation sets itself. Every postcondition is vacuous on a run that raises,
so an `Exsures` that depends only on state the body can write lets a body that sets that
state and raises verify. A sequence is modelled as
`PSeq` and a set as `PSet`, pure values that have no permission predicate and that nothing
can modify, so an obligation written over one says what the caller passed. Where the
behaviour is about storage, an argument modified in place or a copy that must not share
storage with it, ownership is stated per location with permissions, never through the
result's Python type: an argument the operation only reads keeps a fractional permission
across the call, one it modifies is held in full with its post-state stated against
`Old(xs[i])`, and a copy is owned in full at every level the caller can still write, so a
result that shares a location with the argument does not verify.

An empty collection is built from a value of its element type -- `PSeq(x).take(0)`, or
`s.take(0)`, and `PSet(x) - PSet(x)` -- because a `@Pure` function with a `Decreases`
clause can hold no local, and Nagini rejects a bare `PSeq()` or `PSet()` anywhere but a
typed local. The drafting guidance contains this and the other idioms the pinned Nagini
insists on, each checked against it: the order of a contract's clauses, one `Exsures` per
exception class, the one-step unfolding of a recursive `@Pure` function at `i + 1`. A
result that is the per-element expansion of the input is stated, as in `verified-swebench`,
as equal to a front-recursive `@Pure` fold over `PSeq`, which unfolds once per step of a
loop that runs from the end; such a fold is the specification where it defines a notion
the task uses -- what is kept, what is dropped, in which order -- rather than the steps the
fix adds, which `audit.no_disclosure` asks about. Nagini runs through a small driver that turns two of its crashes into the errors Viper
reported, and that prints, for a crash inside its translator, the line and column of the
construct it was translating, which its traceback never names.

An invocation starts a JVM and takes ten to twenty seconds even on a small module, so
`verify_timeout_s` wants room and a gate that checks many rivals is slower here than
under a falsifier. Raising it does not fix every timeout, though: an obligation whose
bounds or indices multiply or divide two variables is nonlinear integer arithmetic, which
the solver does not come back from at any budget. A matrix modelled as a `PSeq` of rows
keeps that arithmetic linear where one flat `PSeq` of length `rows * cols` does not, and
the difference between the two is a verdict in twenty seconds against no verdict at all.

### `dafny`

Contracts in the `spec` region, the method body in `impl`, and a proof kept in the file:
loop invariants, lemmas, and the rest are part of the artifact the checker replays.

```dafny
// benchproofer:begin spec
method Max(xs: seq<int>) returns (r: int)
  requires |xs| > 0
  ensures r in xs
  ensures forall j :: 0 <= j < |xs| ==> r >= xs[j]
// benchproofer:end spec
// benchproofer:begin impl
{
  r := xs[0];
  var i := 1;
  while i < |xs|
    invariant 1 <= i <= |xs|
    invariant r in xs[..i]
    invariant forall j :: 0 <= j < i ==> r >= xs[j]
  {
    if xs[i] > r { r := xs[i]; }
    i := i + 1;
  }
}
// benchproofer:end impl
```

`assume`, `{:verify false}`, and `{:only}` are banned tokens: each of them discharges an
obligation without establishing it, and `spec.hygiene` rejects a file that uses one.
`{:axiom}` and `{:extern}` are assumptions rather than shortcuts, so they are allowed in
the `axioms` region, where they have to name the callee they represent and be grounded,
which means `axioms.py` checks them against that callee; see
[`spec.axioms_grounded`](gates.md#specaxioms_grounded), part of the paper's
axiom-soundness gate.

### `lean4`

A statement, a definition, and a theorem connecting them, elaborated by the plain
`lean` executable, or, where `BENCHPROOFER_LEAN_WORKSPACE` names a built Lake workspace, by
`lake env lean` run from that workspace. Under the plain executable a solution imports no
external library, Mathlib included, so a run does not depend on a library revision nobody
pinned. Inside a workspace a solution may import Mathlib and the workspace's other
packages, at the revisions the workspace pins, and the drafting guidance says which of the
two holds. The workspace is used when its `.lake` directory exists and a `lake` is found
for it, the one in a `lean/` directory beside the workspace or else the one on `PATH`;
`benchproofer doctor` names it. Velvet is checked in a workspace of its own, the one
`BENCHPROOFER_VELVET` names ([Finding the executable](#finding-the-executable)).

```lean
-- benchproofer:begin spec
def Spec (n : Nat) (r : Nat) : Prop :=
  r = n + n
-- benchproofer:end spec

-- benchproofer:begin impl
def impl (n : Nat) : Nat :=
  2 * n
-- benchproofer:end impl

-- benchproofer:begin proof
theorem impl_meets_spec (n : Nat) : Spec n (impl n) := by
  unfold Spec impl
  omega
-- benchproofer:end proof
```

Banned here: `sorry`, `admit`, `native_decide`, `unsafe`, `partial def`, `@[extern]`,
`@[implemented_by]`, and `set_option maxHeartbeats 0`. An `axiom` is an assumption, so it
is allowed in the `axioms` region on the same terms as Dafny's `{:axiom}`.

What `lean` reports is whether the file elaborated, and
`theorem nothing : True := by trivial` elaborates. So the theorem has to be about this
file, and `spec.hygiene` is what requires it: the `proof` region must state a claim, and
its statement must name what the `spec` and `impl` regions declare. Nothing in the
language ties the three together, which is why the check is Benchproofer's rather than
the checker's.

Because the proof is a declaration rather than an annotation on the implementation, it is
part of what a [variant](concepts.md#marker-regions) of the file writes: a rival or a
review's submission proves the solution file's claim for itself, since replaying a proof
written against another implementation fails for a reason the specification had nothing
to do with. `spec.strength.mutation` is the exception: a one-token corruption gets no new
proof, which is why the gate does not count a mutant the checker refuses.

### `velvet`

Also Lean, but a program verification language rather than a library: a method carries
its own precondition and postcondition, a loop carries its invariants and its measure,
and `prove_correct` discharges the conditions that say the body meets the contract. What
that buys over `lean4` is automation, because the obligations go to a solver instead of
to a proof you write by hand, and Mathlib is available to state the contract in.

```lean
import Velvet.Std

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

-- benchproofer:begin spec
method double (n : Int) return (out : Int)
  require n >= 0
  ensures out = n + n
-- benchproofer:end spec
-- benchproofer:begin impl
  do
    return n + n
-- benchproofer:end impl

-- benchproofer:begin proof
prove_correct double by
  loom_solve
-- benchproofer:end proof
```

The split is Dafny's and Nagini's: the `method` line with its `require`/`ensures`
clauses is the specification, the `do` block is the implementation, and the
`prove_correct` command is the proof. That command is also what asks for the method's
verification conditions at all: a file without it still elaborates, and elaborating is
all a contract nobody discharged establishes, so `spec.hygiene` requires the command and
requires it to name the method the specification declares.

As under `lean4`, the `proof` region is part of what a variant writes, since
`prove_correct` discharging the reference implementation's conditions says nothing about
someone else's body.

The two `set_option` lines are not decoration. Loom's semantics options have no default,
so a file that omits them does not elaborate, and the pair a solution must choose is
total correctness and demonic choice: an accepting verdict then says the method returns,
and says it for every run rather than for one. Their opposites are banned tokens in both
of the forms that reach them, the option and the scope Loom's own `set_option` opens:
`loom.semantics.termination "partial"` and `PartialCorrectness`,
`loom.semantics.choice "angelic"` and `AngelicChoice`. So is `partial def`, which reaches
partial correctness from Lean's side, since the termination obligations cover the
method's own loops rather than a callee that diverges, and so is `loom.linter.errors`,
which silences Velvet's own complaints about a method's annotations.

Two more tokens are banned here than under `lean4`, and the first is the one that matters
most: `trust_smt`. Velvet closes a goal an SMT solver reports unsatisfiable by citing an
axiom of that name, which puts Z3 and cvc5 in this checker's trusted base alongside Lean's
kernel. That is the same bargain Nagini strikes with Viper. Citing the axiom directly is
not part of the bargain, because it discharges any obligation at all. The second is
`loom_solve_async`, which says so itself: it admits the conditions it solved with `sorry`
instead of building their proof terms.

`scripts/install/velvet.sh` builds the workspace a solution is checked in: a pinned Lean
release, Velvet at one commit, and every library it uses at the revision Velvet's own
manifest names. Elaborating against Mathlib costs tens of seconds per file even before a
solver runs, so this is the slowest prover here by a wide margin, and its smoke case is
one of the slow ones.

### `smt`

An SMT-LIB2 script whose `spec` region asserts the negation of the obligation. `unsat`
is a verification, `sat` is a refutation with a model, and `unknown` is the solver
declining to decide, which is recorded as undecided rather than as either.

```smt2
; benchproofer:begin impl
(define-fun impl ((x Int)) Int (+ x x))
; benchproofer:end impl

; benchproofer:begin spec
(define-fun spec ((x Int) (r Int)) Bool (= r (* 2 x)))
(assert (not (forall ((x Int)) (spec x (impl x)))))
; benchproofer:end spec
```

This backend is the cheapest way to formalize a benchmark whose tasks are arithmetic
rather than algorithmic, such as GSM8K.

## Choosing a backend for a benchmark

| the task is | try |
| --- | --- |
| a small pure function (HumanEval, MBPP, QuixBugs) | `crosshair`, then `dafny` |
| an arithmetic word problem (GSM8K) | `smt` |
| a repository change (SWE-bench) | `falsifier`, then `crosshair`, then `nagini`, `lean4` or `velvet` |
| a loop over a container, proved with an invariant | `dafny`, then `velvet` |
| anything, on a machine with nothing installed | `falsifier` |

A repository task is rarely provable end to end. What a bundle formalizes there is the
behavior the change is about, and `impl.conformance`, the paper's conformance gate, is
what ties that back to the repository's own code: it runs the implementation and the
function the golden patch produces on the same inputs and compares them. Under a Python
backend that comparison runs the verified implementation itself; under Lean or Velvet it
runs the Python copy of it in `conformance.py`, which is a weaker claim, and the verdict
records which of the two it was.

## Finding the executable

A backend never hard-codes a path. It asks for a tool by name and takes the first hit,
in this order:

1. an explicit override naming the file: `BENCHPROOFER_DAFNY`, `BENCHPROOFER_LEAN`,
   `BENCHPROOFER_NAGINI`;
2. the repository-local `.toolchains/`, which is where `scripts/install/*.sh` write;
3. `PATH`.

Velvet is the exception, because what it needs is a built Lean workspace rather than an
executable: `BENCHPROOFER_VELVET` names that directory, and the `lake` that drives it is
the one beside it, or the one on `PATH`. `lean4` takes a workspace the same way, from
`BENCHPROOFER_LEAN_WORKSPACE`, and uses it in place of the executable when it names one
that is built ([`lean4`](#lean4)).

The override comes first so that a machine with a system verifier can be pointed at a
pinned one, and the local directory comes before `PATH` so that a checkout with pinned
toolchains is not silently judged by whatever happens to be installed. `benchproofer
doctor` prints the resolved path and version of every backend it found.

`.toolchains/` is relative to the working directory, so a run started somewhere else
looks somewhere else and reports the prover as absent, naming the directory it searched.
Point `BENCHPROOFER_TOOLCHAIN_DIR` at the checkout's `.toolchains/` to work from
anywhere:

```bash
export BENCHPROOFER_TOOLCHAIN_DIR=/path/to/benchproofer/.toolchains
```

On a platform the pinned archives do not cover, install the verifier some other way and
set the override:

```bash
export BENCHPROOFER_DAFNY=/opt/dafny/dafny
benchproofer doctor
```

The version is then whatever you installed, and a corpus judged with it is a corpus
judged by that verifier. `spec.verifies` records which backend gave the verdict and writes the
checker's own output to `evidence/verifies.log`, so the record shows what decided.

## Adding one

One class, one `check` method, one entry point. See
[Add a backend](guides/add-a-backend.md).
