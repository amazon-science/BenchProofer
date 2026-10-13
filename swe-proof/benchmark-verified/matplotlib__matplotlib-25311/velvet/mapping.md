# mapping.md — matplotlib__matplotlib-25311

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 430fb1db88843300fb4baae3edc499bbfe073b0c`, states the type
abstraction (the Lean↔Python bijection the gates use), and gives the provenance
of every modeling assumption.

Repo file under change: `lib/matplotlib/offsetbox.py` (the constructor of the
drag-handler base class, `DraggableBase.__init__`, body lines 1503–1516; plus
the class-level accessor added at line 1516–1517).

`spec_provenance: "cold"` — the spec is derived from scratch from
`problem_statement`, the gold `patch`, and the repo source at `base_commit`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initHandler (useBlit supportsBlit : Bool)` | `DraggableBase.__init__(self, ref_artist, use_blit=False)` — `lib/matplotlib/offsetbox.py:1503` | the modeled changed function (the drag-handler constructor) |
| `Handler` (structure: `attrs`, `surfaceFromRef`) | the constructed instance: its persisted attribute dict (`self.__dict__`) plus whether the class exposes the rendering surface as a derived accessor | the object the constructor produces |
| `Attr.surface` | the live rendering surface `self.ref_artist.figure.canvas` (a backend GUI object, e.g. `FigureCanvasQTAgg`) | the **non-serializable** handle |
| `Attr.refHandle` | `self.ref_artist` (the reference artist) | a serializable stored reference (see §3) |
| `Attr.flag b` | `self.got_artist` (a status flag) / `self._use_blit` (a blit-enable flag) | serializable boolean state |
| `Attr.registration` | `self.cids` (the list of picklable callback registrations) | serializable state |
| `persistable` / `surfaceReachable` (pure preds) | the two observable behaviors the fix must satisfy (§4) | spec predicates |

The pre-patch repo line the change removes (refinement audit only, not in the
consumer spec view): `self.canvas = self.ref_artist.figure.canvas`
(`offsetbox.py:1508`). The post-patch line the change adds:
`canvas = property(lambda self: self.ref_artist.figure.canvas)`
(`offsetbox.py:1516-1517`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the instance `__dict__` (the bytes that go into the pickle stream) | `List Attr` (`Handler.attrs`) | each persisted attribute value ↔ one `Attr` token; the *set of values* is what the pickle stream embeds; order is irrelevant to the observed behavior |
| a live backend canvas (`FigureCanvasQtAgg`/`FigureCanvasAgg`) | `Attr.surface` | the distinguished non-serializable token; "a reference to it appears in the pickle stream" ↔ `Attr.surface ∈ attrs` |
| the reference artist `self.ref_artist` | `Attr.refHandle` | a serializable token (§3): storing it does NOT transitively embed the surface |
| `use_blit and self.canvas.supports_blit` (a `bool`) | `Attr.flag (useBlit && supportsBlit)` | `bool` ↔ `Bool`; `and` ↔ `&&` |
| `self.got_artist = False` | `Attr.flag false` | `False` ↔ `false` |
| `self.cids = [...]` (picklable callback ids) | `Attr.registration` | a serializable token |
| a class-level `property` exposing the surface, derived from the stored reference | `Handler.surfaceFromRef : Bool` | `true` ↔ "the class defines `canvas` as a derived accessor over `self.ref_artist`"; `false` ↔ "no such accessor" |

There is no real-number / string content here — the behavior under change is
purely **structural** (which values land in the persisted state, and whether the
surface stays reachable). Hence the spec lives in membership/absence predicates
over `List Attr`, not in an arithmetic or string model.

## 3. Modeling assumption: `Attr.refHandle` is serializable (provenance)

The fix relies on a pre-existing, **unchanged** matplotlib behavior: a figure
does not persist its own rendering surface. `Figure.__getstate__`
(`lib/matplotlib/figure.py`) deletes the `canvas` entry from the state dict
before pickling (`state.pop("canvas", None)` / sets it to `None`). Therefore the
reference artist (and, through it, its figure) can be stored and pickled without
dragging the live surface into the stream — the surface is embedded ONLY when an
object stores it *directly* as its own attribute, which is exactly what the
buggy line did.

This is an environment fact about an unchanged callee, not a contract the proof
consumes; it is encoded in the type bijection (`Attr.refHandle ≠ Attr.surface`)
and is the reason storing `refHandle` is sound while storing `surface` is the
bug. No `axiom` is introduced and the proof consumes none, so there is no G-AX
obligation (axioms = []). The F2P test `test_complete[png]` transitively
confirms this fact: with the gold patch, pickling the whole figure (which still
reaches `ref_artist.figure`) produces a stream with no `FigureCanvasAgg`
reference.

## 4. The observable behaviors the spec pins (verify ⟹ correct)

* **picklability** — `persistable out = (Attr.surface ∉ out.attrs)`: the
  persisted state embeds no non-serializable surface. This is what the F2P
  assertion `"FigureCanvasAgg" not in [arg for op,arg,pos in
  pickletools.genops(pkl)]` observes. The buggy constructor stored the surface
  directly, so it appeared in the stream → `TypeError: cannot pickle
  'FigureCanvasQTAgg'`.
* **surfaceReachable** — `out.surfaceFromRef ∧ Attr.refHandle ∈ out.attrs`
  (OR the surface is still stored directly): the surface remains obtainable.
  This is required because the constructor itself (and the drag callbacks) read
  the surface; removing the attribute WITHOUT providing the derived accessor
  would raise `AttributeError` on the very next line
  (`self._use_blit = use_blit and self.canvas.supports_blit`) and the F2P test
  would error rather than resolve. The accessor derives the surface from the
  stored reference, so reachability is grounded in `refHandle` being present.

Both clauses are load-bearing: dropping clause 1 admits the bug (stored
surface); dropping clause 2 admits a constructor that deletes the attribute but
provides no accessor (which crashes).

In addition to the two fix-discriminating clauses, the spec pins the full
persisted working inventory of the real post-patch constructor (all of which the
PASS_TO_PASS pickle suite and the drag callbacks rely on):

* `Attr.refHandle ∈ out.attrs` — `self.ref_artist = ref_artist` (unconditional);
* `Attr.flag (useBlit && supportsBlit) ∈ out.attrs` — `self._use_blit =
  use_blit and self.canvas.supports_blit`;
* `Attr.flag false ∈ out.attrs` — `self.got_artist = False` (the cleared
  drag-status bit; without it the drag callbacks misbehave);
* `Attr.registration ∈ out.attrs` — `self.cids = [...]` (the installed picklable
  event registrations; without them the handler receives no pick/release
  events at all).

These inventory clauses close the P1 weakness: a stripped constructor that
omits the event registrations or the cleared status bit no longer verifies.

Finally, `flagsExact out (useBlit && supportsBlit)` closes the inventory in the
other direction: every boolean status/mode bit the handler retains must be one
of the two the real constructor sets (`self.got_artist = False` ↔
`Attr.flag false`, `self._use_blit = use_blit and ...supports_blit` ↔
`Attr.flag (useBlit && supportsBlit)`). The real constructor at `base_commit`
(post-patch) sets exactly these two boolean attributes and no other, on every
input in `{True,False}²`, so the clause holds of the real object ∀ inputs (not
spec-too-strong). It rejects an implementation that smuggles an extra or
altered status bit into the persisted state (e.g. an unconditionally-set mode
bit), which is a genuinely different — and behaviorally wrong — object: the
drag callbacks read these bits, and a spurious enabled mode bit changes the
handler's drawing path. Only the gold shape — store the reference + exactly the
two flags + registrations, do NOT store the surface, expose the surface via the
derived accessor — satisfies the spec.

## 5. G-CONF / G-AX disposition

* **G-AX:** no axioms, no A-reference deep model of an unchanged callee; the
  changed op (construct the persisted state) is modeled deeply as the `do`
  block. No `axiom_check.py` obligation → G-AX skip.
* **G-CONF:** `conf_skip = true`. The impl region constructs an abstract
  object-state model; its only observable (a reference appearing / not appearing
  in a real pickle stream) materializes solely when a full
  figure+legend(draggable=True) is built and pickled — i.e. the F2P test itself,
  not a DB-free, input-dependent transliteration fuzzable over ≥10⁵ inputs. The
  construction is constant (does not depend on fuzzable repo inputs in a way
  reproducible outside the harness). Soundness is carried by G-VERIFY (the spec
  provably forces both clauses) + G-DIFF (the prepatch, which stores the
  surface, fails the picklability clause) + G-RESOLVE (the gold patch resolves).
  This mirrors the `django__django-11179` state-mutation precedent. The pinned
  fuzz seed is `25311` (unused while skipped; recorded for reproducibility).
