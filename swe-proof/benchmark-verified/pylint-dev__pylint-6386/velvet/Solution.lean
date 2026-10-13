import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no opaque outside callee. The behaviour under spec is
   a single startup pre-processing pass that walks an ordered list of argument
   tokens and, for each one, either forwards it onward, consumes it (firing its
   local side effect), consumes it TOGETHER WITH the following token as its
   value, or abandons the whole pass. The pass is modeled DEEPLY below: a
   token's SYNTAX is the input, the standing table of recognised startup options the
   pass consults is spelled out as specification-level data, the per-token
   branch class is DERIVED from those two, and every branch the pass can take is
   a total function. There is no external opaque routine whose contract the
   proof consumes, and no branch class supplied from outside. See mapping.md §3
   and refinement.md §C. -/
-- axioms-end

-- pure-start
/- WHAT AN ARGUMENT TOKEN IS, AS THE PASS READS IT. A token's syntax has exactly
   two observable parts, and the pass reads them in this order: the token's BARE
   SPELLING — its text up to an inline `=`, which is the part the pass looks up —
   and whether an inline value followed that `=`. A token is therefore given here
   as one descriptor number packing both:

       descriptor = 10 * (bare-spelling index) + (0 if no inline value, else 1)

   The bare-spelling index NAMES the token's text and nothing else. It is a
   SYNTACTIC identity: two tokens share an index exactly when their bare
   spellings are the same text, and the index by itself says nothing about how
   the pass treats the token. What the pass does with a spelling is decided by
   the two pieces of DATA below — how deeply the spelling is option-marked, and
   what role the pass's standing table of recognised startup options gives it.
   Both are properties of the spelling and of that table, not decisions the pass
   makes, so they belong to the specification rather than to its input.

   The indices enumerate every spelling shape the pass can meet: one per key the
   table declares, one for an unmarked word, and one each for the two shapes that
   are marked but are not keys. -/

/- The token's bare-spelling index. -/
def bareOf (t : Nat) : Nat := t / 10

/- Whether the token carries an inline value. -/
def inlineOf (t : Nat) : Bool := t % 10 != 0

/- HOW DEEPLY EACH DECLARED BARE SPELLING IS OPTION-MARKED, as a capped count of
   its leading option markers: 0 = carries no marker at all, 1 = carries EXACTLY
   ONE marker, 2 = carries more than one. Data about the spellings; a renaming of
   the indices may permute the rows but may not change how deeply a given
   spelling is marked.

     0  an unmarked word — a path, a module name, a bare value, and anything
        else that does not open with the option marker (whether or not it
        happens to contain an `=`)
     1  the value-taking option whose side effect INTERPRETS the value it is
        handed instead of storing it
     2  a value-taking option whose side effect merely stores its value
     3  a second such option
     4  a third such option
     5  the no-value option whose side effect turns the flag on, in the spelling
        that carries more than one marker
     6  the SAME no-value flag option in a spelling that carries EXACTLY ONE
        marker followed by a single letter. The table declares both spellings and
        gives them the same role, so the two are interchangeable.
     7  the no-value option whose side effect leaves the flag alone
     8  a spelling carrying more than one marker that is not a key of the table
     9  a spelling carrying exactly one marker that is not a key of the table

   Indices from 10 up name no spelling the pass can meet. Rather than leave them
   to an implementation's discretion they are pinned to the marked-but-unknown
   row, which is where the previous shape of this model put them too. -/
def markersOf : Nat → Nat
  | 0 => 0
  | 1 => 2
  | 2 => 2
  | 3 => 2
  | 4 => 2
  | 5 => 2
  | 6 => 1
  | 7 => 2
  | 8 => 2
  | 9 => 1
  | _ => 2

/- THE TABLE, AS SPECIFICATION-LEVEL DATA: the role the pass's standing table of
   recognised startup options gives each bare spelling.

     0  not a key of the table at all
     1  a key demanding NO value, whose side effect turns the flag on
     2  a key demanding NO value, whose side effect leaves the flag alone
     3  a key demanding a value, whose side effect STORES the value it is handed
     4  a key demanding a value, whose side effect INTERPRETS the value it is
        handed as instructions

   Note the two rows carrying role 1: the flag option is a key of the table
   under BOTH the spelling that carries more than one marker (index 5) and the
   spelling that carries exactly one (index 6), and the table gives them the
   same role, so the same side effect fires for either. -/
def tableRole : Nat → Nat
  | 1 => 4
  | 2 => 3
  | 3 => 3
  | 4 => 3
  | 5 => 1
  | 6 => 1
  | 7 => 2
  | _ => 0

/- THE RECOGNITION THRESHOLD. A token enters recognition — is split at its inline
   `=` and has its bare spelling looked up in the table — iff its spelling
   carries AT LEAST ONE option marker. ONE marker is enough: a token whose
   spelling carries a single marker is NOT short-circuited past the lookup, it is
   looked up like any other marked token. Only a token carrying no marker at all
   short-circuits, and it is then forwarded whole without ever being looked up,
   inline `=` and all. -/
def isCandidate (s : Nat) : Bool := 1 ≤ markersOf s

/- THE PER-TOKEN BRANCH CLASS, DERIVED from the token's syntax and the table
   alone. Which of the ten branches the pass takes on this token:

     0  PLAIN     - carries no option marker, so it is never looked up. Forwarded
                    onward whole, and the ONLY shape that can serve as the
                    separate value of a value-taking option.
     1  FLAG_LONG - the recognised no-value flag option, in the spelling carrying
                    more than one marker. Consumed (not forwarded); turns the
                    flag on.
     2  FLAG_SHORT- the SAME recognised no-value flag option, in the spelling
                    carrying exactly one marker. Consumed and turns the flag on:
                    the two spellings are interchangeable.
     3  FOREIGN   - carries the option marker but its bare spelling is not a key
                    of the table. Forwarded onward whole, inline value and all;
                    never touches the flag.
     4  QUIET     - a recognised no-value option whose side effect is something
                    other than the flag. Consumed, and the flag is left exactly
                    as it was.
     5  INLINE    - a recognised value-taking option carrying its value inline,
                    whose side effect on that value is confined to state this
                    pass does not observe. Consumed on its own; no following
                    token is touched and the flag is left alone.
     6  SEPARATE  - the same, with no inline value. It consumes the FOLLOWING
                    token as its value, so BOTH tokens leave the forwarded list;
                    and if there is no following token, or the following token is
                    itself option-marked (i.e. is not PLAIN), the pass is
                    abandoned before any side effect fires.
     7  SURPLUS   - a recognised no-value option that nevertheless carries an
                    inline value. The pass is abandoned at once, before any side
                    effect fires. This is what the flag option becomes under
                    EITHER of its spellings when a value is attached to it.
     8  OPAQUE    - a recognised value-taking option whose side effect on the
                    value it receives is NOT confined: handed a value, it can do
                    anything at all to the state this pass reads and writes,
                    including turning the flag back OFF, abandoning the pass,
                    failing outright, editing the very table above, and reaching
                    into the forwarded list directly. No inline value, so it
                    would take the FOLLOWING token as its value.
     9  OPAQUE_IN - the same, carrying its value inline.

   WHY 8 AND 9 ARE SEGREGATED RATHER THAN GIVEN BEHAVIOUR. For every other
   class, the token decides the pass's observables. For these two the VALUE
   decides them, and it decides them without limit: the side effect is handed
   the value and interprets it as instructions. Two token lists with the same
   descriptor sequence therefore have different real observables, so no function
   of the descriptors — this model or any other — can agree with the pass on the
   shapes where that side effect fires. Segregating the class and confining the
   domain to the shapes where it PROVABLY does not fire (see the precondition) is
   what makes the descriptor sequence a well-defined determiner of the
   observables again. Both classes still carry behaviour on the shapes that
   remain admissible: an OPAQUE token whose following token is missing or
   option-marked abandons the pass exactly like a SEPARATE one, because the pass
   examines that following token FIRST and gives up before the side effect can
   run at all.

   ABANDONMENT is an observable of the pass in its own right (third output
   component). The forwarded list of an abandoned run is what the pass had
   forwarded up to the abandonment point: the tokens at or after that point are
   never examined, so they contribute neither to the list nor to the flag, while
   the tokens before it have already been forwarded and have already fired their
   side effects, so their contribution stands. -/
def kindOf (t : Nat) : Nat :=
  if !isCandidate (bareOf t) then 0
  else if tableRole (bareOf t) == 0 then 3
  else if tableRole (bareOf t) == 1 then
    (if inlineOf t then 7 else if markersOf (bareOf t) == 1 then 2 else 1)
  else if tableRole (bareOf t) == 2 then (if inlineOf t then 7 else 4)
  else if tableRole (bareOf t) == 3 then (if inlineOf t then 5 else 6)
  else (if inlineOf t then 9 else 8)

/- THE CLASSIFICATION IS ONTO ITS TEN CLASSES. Every descriptor whatsoever is
   placed in one of the ten branch classes above — including the descriptors
   naming no spelling the pass can meet, which the two data rows send to the
   marked-but-unknown row and hence to FOREIGN. So there is no residual family
   of tokens whose treatment an implementation could choose for itself. -/
@[grind] lemma kindOf_le_nine (t : Nat) : kindOf t ≤ 9 := by
  unfold kindOf
  split
  · omega
  · split
    · omega
    · split
      · split <;> [omega; (split <;> omega)]
      · split
        · split <;> omega
        · split
          · split <;> omega
          · split <;> omega

/- A token is forwarded onward iff its class is PLAIN or FOREIGN. -/
def keep (kind : Nat) : Bool := kind == 0 || kind == 3

/- A token turns the flag on iff it is the recognised no-value flag option, under
   EITHER of the two spellings the table declares for it. -/
def setsFlag (kind : Nat) : Bool := kind == 1 || kind == 2

/- A token can serve as the separate value of a value-taking option iff it
   carries no leading option marker. -/
def isValueTok (kind : Nat) : Bool := kind == 0

/- A token demands the FOLLOWING token as its value: the confined value-taking
   class and the unconfined one alike, since the lookahead the pass performs is
   decided by the option's arity and not by what its side effect then does. -/
def takesValue (kind : Nat) : Bool := kind == 6 || kind == 8

/- A token carries a value that its option does not accept, which abandons the
   pass on the spot. -/
def rejectsValue (kind : Nat) : Bool := kind == 7

/- The head token's unconfined side effect WOULD fire on this list: an
   inline-value OPAQUE_IN token always fires, and an OPAQUE token fires exactly
   when the following token is present and PLAIN, i.e. usable as its value. In
   every other OPAQUE shape the pass abandons at the lookahead and the side
   effect never runs. -/
def firesOpaque (t : Nat) (ts : List Nat) : Bool :=
  kindOf t == 9 ||
    (kindOf t == 8 &&
      (match ts with | v :: _ => isValueTok (kindOf v) | [] => false))

/- The modeled domain: no token's unconfined side effect fires anywhere in the
   list. -/
def opaqueConfined : List Nat → Bool
  | []      => true
  | t :: ts => !(firesOpaque t ts) && opaqueConfined ts

/- One step of the pass, applied to the head token `t`, the tail `ts` it can look
   ahead into, and the outcome `r` the tail already produced. Front recursive so
   a single unfold is available per loop step (the Velvet fold pattern), and
   factored out of the recursion so that the generic cons equation below holds by
   `rfl`.

   The four shapes, in the order the pass tests them: a SURPLUS token abandons
   the pass; a value-taking token with no inline value examines the following
   token FIRST and abandons the pass when it is absent or not PLAIN, and
   otherwise eats it as its value (dropping it from what the tail forwarded); a
   forwarded token contributes ITSELF, whole, in place; anything else is
   consumed, contributing only its flag effect. -/
def step (t : Nat) (ts : List Nat) (r : List Nat × Bool × Bool) :
    List Nat × Bool × Bool :=
  if rejectsValue (kindOf t) then ([], false, true)
  else if takesValue (kindOf t) then
    match ts with
    | []     => ([], false, true)
    | v :: _ => if isValueTok (kindOf v) then (r.1.tail, r.2) else ([], false, true)
  else if keep (kindOf t) then (t :: r.1, r.2)
  else (r.1, setsFlag (kindOf t) || r.2.1, r.2.2)
def runPass : List Nat → (List Nat × Bool × Bool)
  | []      => ([], false, false)
  | t :: ts => step t ts (runPass ts)

@[grind] lemma runPass_nil : runPass [] = ([], false, false) := rfl
@[grind] lemma runPass_cons (t : Nat) (ts : List Nat) :
    runPass (t :: ts) = step t ts (runPass ts) := rfl

@[grind] lemma runPass_reject (t : Nat) (ts : List Nat)
    (h : rejectsValue (kindOf t) = true) :
    runPass (t :: ts) = ([], false, true) := by
  simp [runPass, step, h]

@[grind] lemma runPass_keep (t : Nat) (ts : List Nat)
    (h1 : rejectsValue (kindOf t) = false) (h2 : takesValue (kindOf t) = false)
    (h3 : keep (kindOf t) = true) :
    runPass (t :: ts) = (t :: (runPass ts).1, (runPass ts).2) := by
  simp [runPass, step, h1, h2, h3]

@[grind] lemma runPass_consume (t : Nat) (ts : List Nat)
    (h1 : rejectsValue (kindOf t) = false) (h2 : takesValue (kindOf t) = false)
    (h3 : keep (kindOf t) = false) :
    runPass (t :: ts)
      = ((runPass ts).1, setsFlag (kindOf t) || (runPass ts).2.1,
         (runPass ts).2.2) := by
  simp [runPass, step, h1, h2, h3]

@[grind] lemma runPass_takearg_last (t : Nat)
    (h1 : rejectsValue (kindOf t) = false) (h2 : takesValue (kindOf t) = true) :
    runPass [t] = ([], false, true) := by
  simp [runPass, step, h1, h2]

@[grind] lemma runPass_takearg_noval (t v : Nat) (vs : List Nat)
    (h1 : rejectsValue (kindOf t) = false) (h2 : takesValue (kindOf t) = true)
    (h3 : isValueTok (kindOf v) = false) :
    runPass (t :: v :: vs) = ([], false, true) := by
  simp [runPass, step, h1, h2, h3]

@[grind] lemma runPass_value_head (v : Nat) (vs : List Nat)
    (h : isValueTok (kindOf v) = true) :
    runPass (v :: vs) = (v :: (runPass vs).1, (runPass vs).2) := by
  have hv : kindOf v = 0 := by simpa [isValueTok] using h
  simp [runPass, step, hv, rejectsValue, takesValue, keep]

@[grind] lemma runPass_takearg_value (t v : Nat) (vs : List Nat)
    (h1 : rejectsValue (kindOf t) = false) (h2 : takesValue (kindOf t) = true)
    (h3 : isValueTok (kindOf v) = true) :
    runPass (t :: v :: vs) = runPass vs := by
  rw [runPass_cons, runPass_value_head v vs h3]
  simp [step, h1, h2, h3]
-- pure-end

-- pre-conditions-start
/- The one domain restriction: the list must not contain a token whose unconfined
   side effect would fire. Inside this domain the descriptor sequence determines
   all three observables, so every admissible input has pinned behaviour and none
   is left to an implementation's discretion — including every descriptor naming
   no spelling the pass can meet, which is pinned to the marked-but-unknown row.
   Outside it no specification of this shape could be faithful (see the note on
   classes 8 and 9 above), so the restriction is exactly the boundary of what is
   specifiable rather than a convenience. -/
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The startup token pre-processing pass. `args` is the ordered list of incoming
   argument tokens, each given by its syntax descriptor; `flagIn` is whether the
   flag was already on entering the pass. Both are read-only inputs.

   Desired behaviour, pinned by the three clauses below. The forwarded list is
   exactly what the pass forwards: the tokens carrying no option marker, and the
   marked tokens whose bare spelling is not a key of the table, THEMSELVES and
   whole, in their original relative order — with every recognised startup option
   removed under EVERY spelling the table declares for it, however deeply that
   spelling is marked, and with the separate value of a value-taking option
   removed too, and with nothing at or after an abandonment point. The flag on
   exit is on iff it was already on or some examined token turned it on. The
   third component reports whether the pass was abandoned. -/
method forwardStartupTokens (flagIn : Bool) (args : List Nat)
    return (out : (List Nat) × Bool × Bool)
  require opaqueConfined args = true
  ensures out.1 = (runPass args).1
  ensures out.2.1 = (flagIn || (runPass args).2.1)
  ensures out.2.2 = (runPass args).2.2
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Peeling one element off the front of a suffix, in the two index shapes the
   loop needs. -/
lemma drop_succ (args : List Nat) (i : Nat) (h : i < args.length) :
    args.drop i = args[i]! :: args.drop (i + 1) := by
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem h, Option.getD_some]
  exact List.drop_eq_getElem_cons h

lemma drop_step (args : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    args.drop (i - 1) = args[i - 1]! :: args.drop i := by
  have hlt : i - 1 < args.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

/- The three value-taking outcomes, each stated ALREADY REWRITTEN over the suffix
   the loop invariant carries, so the goal can be closed by a single rewrite.
   (Stating them over `args.drop i` and rewriting afterwards is not equivalent in
   practice: `simp` re-folds `args[i]! :: args.drop (i+1)` back into
   `args.drop i` and the lookahead match gets stuck again.) -/
lemma cons_takearg_value (args : List Nat) (i : Nat) (hlt : i < args.length)
    (h1 : rejectsValue (kindOf args[i - 1]!) = false)
    (h2 : takesValue (kindOf args[i - 1]!) = true)
    (h3 : isValueTok (kindOf args[i]!) = true) :
    runPass (args[i - 1]! :: args.drop i)
      = ((runPass (args.drop i)).1.tail, (runPass (args.drop i)).2) := by
  rw [drop_succ args i hlt, runPass_takearg_value _ _ _ h1 h2 h3,
      runPass_value_head _ _ h3]
  simp

lemma cons_takearg_noval (args : List Nat) (i : Nat) (hlt : i < args.length)
    (h1 : rejectsValue (kindOf args[i - 1]!) = false)
    (h2 : takesValue (kindOf args[i - 1]!) = true)
    (h3 : isValueTok (kindOf args[i]!) = false) :
    runPass (args[i - 1]! :: args.drop i) = ([], false, true) := by
  rw [drop_succ args i hlt]
  exact runPass_takearg_noval _ _ _ h1 h2 h3

lemma cons_takearg_last (args : List Nat) (i : Nat) (hge : args.length ≤ i)
    (h1 : rejectsValue (kindOf args[i - 1]!) = false)
    (h2 : takesValue (kindOf args[i - 1]!) = true) :
    runPass (args[i - 1]! :: args.drop i) = ([], false, true) := by
  rw [List.drop_eq_nil_of_le hge]
  exact runPass_takearg_last _ h1 h2

prove_correct forwardStartupTokens by
  -- proof elided — supplied by the consumer
