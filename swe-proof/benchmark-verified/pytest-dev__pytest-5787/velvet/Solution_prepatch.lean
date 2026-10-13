import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged foreign callee is axiomatized. The serialization is modeled
   directly as a pure data-flow over the report's structure. The per-link
   rendered text and one-line summary of each exception are carried by an
   unchanged, pre-existing per-link codec, modeled here as verbatim-preserved
   content tokens (an R refinement — mapping.md §2/§3). There is therefore no
   consumed axiom and no deep-model reference to a foreign callee. -/
-- axioms-end

-- pure-start
/- A titled supplementary text block attached to a report: (title, content,
   separator). Such blocks travel with the report and must survive a
   serialization round-trip unchanged. -/
abbrev Extra := String × String × String

/- One link of an exception chain. `text` and `summary` are opaque content
   tokens standing for, respectively, the rendered text of this link's exception
   and its one-line summary; both are carried verbatim by the unchanged per-link
   codec (mapping.md §2). `desc` is the connecting phrase shown between this link
   and the next ("the above exception was the direct cause of the following
   exception" / "during handling of the above exception, another occurred"),
   absent on the final link. -/
structure Link where
  text    : Nat
  summary : Nat
  desc    : Option String
deriving DecidableEq, Inhabited, Repr

/- A rendered exception report, in one of two shapes:
   * `simple t s xs`  — a single exception: its rendered text token `t`, its
                        summary token `s`, and attached supplementary blocks `xs`;
   * `chained ls xs`  — an exception chain: the ordered list of links `ls` (each
                        a cause/context of the next) plus attached blocks `xs`.
                        The whole chain is the content that must survive a
                        serialization round-trip — not just its last link. -/
inductive TraceReport where
  | simple  (text : Nat) (summary : Nat) (extras : List Extra)
  | chained (links : List Link) (extras : List Extra)
deriving DecidableEq, Inhabited, Repr

/- The serialized (builtin-only) form of a report: a text token, a summary
   token, the attached blocks, and — for a chain — the ordered list of its
   links. A simple report carries no link list (`none`); a chained report
   carries `some links`. The top-level `text`/`summary` of a chain echo its
   final link (the outermost exception), mirroring the rendered object. -/
structure Serialized where
  text    : Nat
  summary : Nat
  extras  : List Extra
  chain   : Option (List Link)
deriving DecidableEq, Inhabited, Repr

/- Serialize a report to its builtin-only form. A simple report stores its
   text/summary and no link list. A chained report stores the full ordered link
   list and echoes its final link's text/summary at top level. -/
def encode (r : TraceReport) : Serialized :=
  match r with
  | .simple t s xs => { text := t, summary := s, extras := xs, chain := none }
  | .chained ls xs =>
      let last := (ls.getLast?).getD default
      { text := last.text, summary := last.summary, extras := xs, chain := some ls }

/- Reconstruct a report from its serialized form. A stored link list rebuilds
   the chain (preserving every link, in order); its absence rebuilds a simple
   report from the stored text/summary. Attached blocks are restored in both
   cases. -/
def decode (s : Serialized) : TraceReport :=
  match s.chain with
  | some ls => .chained ls s.extras
  | none    => .simple s.text s.summary s.extras

@[simp] lemma decode_encode (r : TraceReport) : decode (encode r) = r := by
  cases r <;> rfl
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Serialization step: produce the builtin-only form of a report, preserving the
   entire exception chain when the report is chained. Read-only input (`r` is not
   `mut`; serialization produces a fresh value — directive 5). -/
method serializeReport (r : TraceReport) return (s : Serialized)
  ensures s = encode r
  do
    -- impl-start
    -- Pre-image skeleton: a chained report is serialized by keeping only its
    -- outermost exception's text/summary and DROPPING the link list
    -- (`chain := none`). The frozen spec requires `s = encode r`, which stores
    -- the full link list (`chain := some ls`) for a chain, so prove_correct
    -- MUST fail on the chained arm.
    match r with
    | .simple t s xs => pure { text := t, summary := s, extras := xs, chain := none }
    | .chained ls xs =>
        let last := (ls.getLast?).getD default
        pure { text := last.text, summary := last.summary, extras := xs, chain := none }
    -- impl-end

prove_correct serializeReport by
  loom_solve <;> simp_all [encode]

/- Reconstruction step: rebuild a report from its serialized form. A stored link
   list rebuilds the full chain; its absence rebuilds a simple report. Read-only
   input (`s` is not `mut` — directive 5). -/
method deserializeReport (s : Serialized) return (r : TraceReport)
  ensures r = decode s
  do
    -- impl-start
    match s.chain with
    | some ls => pure (.chained ls s.extras)
    | none    => pure (.simple s.text s.summary s.extras)
    -- impl-end

prove_correct deserializeReport by
  loom_solve <;> simp_all [decode]

/- Round-trip: serialize a report and reconstruct it. The reconstructed report
   equals the original — in particular every link of an exception chain (and its
   connecting descriptions and attached blocks) is preserved, not collapsed to a
   single exception. -/
method roundTripReport (r : TraceReport) return (out : TraceReport)
  ensures out = r
  do
    -- impl-start
    let s ← serializeReport r
    let out ← deserializeReport s
    return out
    -- impl-end

prove_correct roundTripReport by
  loom_solve
  simp_all [decode_encode]
