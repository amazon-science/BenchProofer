import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The unchanged references the fitting tail and the scoring entry point sit on
   top of, abstracted here as free functions and seven free TYPES. No CONTRACT of
   theirs is consumed by the proofs — only their reference VALUES matter, and
   those are validated == the real callees by axiom_check.py (G-AX); see
   mapping.md §3.

   WHY THE MATRICES ARE OPAQUE TYPES AND NOT SEQUENCES OF NUMBERS. Every property
   below that a screen decides — whether it turns a matrix away, whether it
   reports a labelling discrepancy about it, whether the scorer can read its
   layout — is a property of the matrix AS AN OBJECT and not of the numbers it
   holds. Two objects holding bit-identical numbers can differ on every one of
   them: one presenting the per-column labelling the model recorded and one
   presenting none disagree about the labelling report; the same numbers arranged
   as two different widths disagree about refusal; the same numbers in two
   different sparse layouts disagree about readability (all three measured —
   axiom_check.py, `check_object_properties`). A reference over a bare sequence of
   numbers would therefore have to return two answers for one argument, i.e. it
   could not exist. So a matrix is modeled as an object. The two NUMERICAL
   arguments of the order statistic below are carriers as well, for a different
   measured reason — see WHY THE NUMERICAL ARGUMENTS ARE CARRIERS TOO.

   THE THREE KINDS OF MATRIX OBJECT:

   * `CallerHandle` — a matrix as a caller of the public scoring entry point
     supplies it: an object carrying, besides its numbers, the per-column
     labelling the caller attached to them (or the absence of one). It is opaque
     and nothing in this file constructs one, because nothing in this file can: a
     handle is something a CALLER brings in.
   * `Prepared` — the matrix a screen hands back: the caller's numbers in the
     working precision the scorer reads and in the arrangement that screen puts
     them in, with the labelling that arrived with them no longer attached.
     Whether the scorer can then consume that arrangement AS IT STANDS is a
     further question about the object — answered by `scorableAsGiven` below, and
     not answered by the screen's having accepted the matrix. This is what the fitting tail below
     holds, an earlier screen in fitting having already produced it. NOTHING IN
     THIS FILE PRODUCES A PREPARED MATRIX FROM A PRESENTED ONE — there is no
     `Presented → Prepared` here, and the screening method below hands back a
     verdict and not data. The only prepared matrix that can be named is the one
     a CALLER'S handle is prepared into (`preparedOf`, below), and naming it
     needs a caller's handle. So a text holding prepared data cannot re-prepare
     it, by a value reference or otherwise.
   * `Presented` — a matrix as PRESENTED TO A SCREEN. Either kind can be
     presented: `presentCaller` presents the handle a caller brought in (what the
     public entry point does with its argument), and `presentPrepared` presents an
     already-prepared matrix (what a fitting tail does when it screens its data a
     second time). Both are the identity in the repository — a screen accepts any
     matrix-like object — and neither is invertible: from a presented matrix
     nothing recovers the handle it may have come from, so no `Prepared` can be
     read back as a `CallerHandle`. That is the modeling counterpart of the plain
     fact that the fitting tail no longer holds the caller's labelled matrix, and
     it is why the tail cannot form an argument for the public entry point below.

   THE PREPARATION REFERENCE — the one term in this file that is a screen's own
   output, and it is confined to the caller's side:

   * `preparedOf` — the prepared matrix a screen hands back for a CALLER'S
     handle: that handle's numbers in the working precision the scorer reads and
     in the arrangement that screen puts them in, with the labelling consumed. It is a function of the caller's handle
     and of nothing else, so it can be named only where a caller's handle is in
     scope, which in this file is the public entry point below — the one place a
     caller's matrix is screened at all. Naming it there is that screen's own
     preparation step and not a further one (the R-VALUE rule, below). There is
     deliberately no counterpart for a matrix as presented, so no text here can
     name the matrix a further screen would hand back for data it already holds.
     Screening is value-neutral on the numbers: it converts the layout and
     consumes the labelling and does not move them (measured — axiom_check.py,
     `check_handle_properties` leg (b)).

   THE NUMERICAL REFERENCES:

   * `anomalyScores` — the per-sample anomaly score sequence the heavy ensemble
     scorer PRODUCES for a PREPARED matrix. It is a function of the prepared
     matrix only: it does not depend on whether, or how often, that matrix was
     screened, nor on what labelling the handle it came from presented. Hence the
     public entry point below serves exactly this sequence's numbers for what its
     screen handed back — screening changes what is reported about a matrix, never
     the numbers.
   * `scoreValues` — the scores a produced sequence holds, in order: one score
     per sample. In the repository a produced sequence IS its scores, so this is
     the identity there and reading it invokes nothing (measured —
     axiom_check.py, `check_value_equality`, where the public entry point's own
     result is exactly this reading of the screen-free sequence). It runs ONE WAY
     ONLY: there is no `List Score → Scores` here, so the scores of a sequence some
     scorer produced can be read off, and no text can present scores of its own
     as a produced sequence. Its ELEMENTS are carriers as well, for the reason the
     next block gives.
   * `percentileAt` — the order statistic of a PRODUCED score sequence at a
     REQUESTED percentile point. What it produces is a RECORDED OFFSET (`Offset`,
     below) and not a rational, for the measured reason the last carrier bullet
     gives.
   * `defaultOffset` — the threshold offset the OTHER fitting path records: the
     constant a fit that requests no contamination level writes down (-0.5 on
     every model measured — axiom_check.py, `check_offset_arithmetic_fences` leg
     (a)). It is the one recorded offset here that is an order statistic of
     nothing, and it is never the order statistic a requested contamination level
     determines (same leg), which is what makes it the value the fitting tail
     below must not report.

   WHY THE NUMERICAL ARGUMENTS ARE CARRIERS TOO, and it is the same kind of
   measured correction as the matrices: the callee `percentileAt` stands for is
   PARTIAL IN BOTH of them. Asked for the order statistic of no numbers at all it
   reports nothing and refuses the request (measured — axiom_check.py,
   `check_empty_handle_fences`), and asked for a point outside the range a
   percentage occupies it refuses likewise (measured —
   `check_percentile_point_fences`). A reference that is TOTAL over an argument
   type whose terms a text can WRITE DOWN therefore promises a value in a region
   where the repository derives none — and a restriction on a METHOD'S PARAMETER
   does not repair that: such a restriction fences the argument the method was
   CALLED with, while the reference may be named at any term of its argument type
   anywhere inside a body. The argument TYPE is the only fence covering every
   occurrence — the walls the fourth lesson leaves standing (declaration scope,
   argument types, the termination obligation), now against PARTIALITY where that
   lesson was about an ambient effect. Hence:

   * `Scores` — a score sequence AS A SCORER PRODUCED IT. Opaque, and nothing in
     this file constructs one, because nothing can: the only way to have one is
     `anomalyScores` of a prepared matrix. So no text here can ask for the order
     statistic of numbers no scorer produced. The sequences that do exist hold one
     score per sample (measured — axiom_check.py,
     `check_score_sequence_provenance`), which is what makes the sample fence on
     the fitting tail below the fence that keeps them non-empty.
   * `Point` — a percentile point AS A FITTING CALL SITE REQUESTS IT: the point
     the requested contamination level determines. Opaque for the same reason — no
     term of it can be written down, so no text here can ask for an order
     statistic at a point the callee refuses. That the points which DO reach the
     fitting tail are percentages is a repository fact rather than an assumption:
     the call site derives the point from the requested contamination level, and
     the estimator refuses a contamination level outside the range it admits, so
     every point reaching that tail lies inside the range the order statistic is
     defined at (measured — axiom_check.py, `check_point_provenance`).
   * `Score` — ONE per-sample score AS A SCORER PRODUCED IT, and it is a carrier
     for the same reason one step further in: READING A PRODUCED SEQUENCE IS
     ITSELF PARTIAL. Asked for the score at a position the sequence does not have,
     the repository reports nothing and refuses the read — measured at four
     sequence lengths, at a position far past the end, at the length itself, and at
     the mirror position before the start, and refused even where the value read is
     then cancelled away, since the refusal happens at the read (axiom_check.py,
     `check_score_index_fences`). A sequence whose ELEMENTS a text can write down
     admits an UNGUARDED read at any position — such a read needs only a default
     element to fall back on when the position is absent — and that promises a
     score in a region where the repository derives none. With the element a
     carrier there is no default to fall back on, so the reads a text can spell are
     the ones that report the ABSENCE of a position rather than inventing a score
     for it, together with the sequence's length; both are total in the repository
     too (measured, same leg: every position a sequence HAS is readable, and the
     order statistic of the whole sequence is defined). So this fence excludes
     exactly the read the repository refuses, and the reference values themselves
     are untouched by it.
   * `Offset` — the threshold offset A FITTING TAIL RECORDS, and it is a carrier
     one step further out again, for a partiality of ARITHMETIC. Divided by zero
     — by a written zero, or by its own difference with itself — a recorded
     offset yields no number at all: the repository refuses the division outright
     as a plain real, and reports a non-finite value together with a runtime
     warning in the working precision its scorer produces (measured —
     axiom_check.py, `check_offset_arithmetic_fences` legs (b) and (c), the
     second of which shows the divergence happens AT THE ARITHMETIC, so
     cancelling the quotient away does not avoid it). The reference language
     disagrees: its division is TOTAL and a quotient by zero is the rational 0.
     A reported offset that was a RATIONAL would therefore let a text derive a
     value the repository has none for, and a restriction on a parameter cannot
     fence that for the reason the paragraph above gives, one step further: the
     arithmetic may be named ANYWHERE inside a body, and a quotient a text
     DISCARDS is invisible to every postcondition, which is exactly where a
     clause about the reported value cannot reach. With the offset a carrier the
     only offsets a text can write down are the order statistic the reference
     above produces and the constant the other fitting path records — both
     values the repository really has. The controls bound the fence: the
     arithmetic the repository does perform on these numbers (negation, division
     by one and by two, the order statistic taken again, the count of the scores)
     is all finite and warns about nothing, and the reference values themselves
     are untouched by the change (same leg, (d)).

   THE SCREEN PROPERTIES, all properties of the matrix as PRESENTED, and all
   opaque, so nothing about any particular matrix follows from them:

   * `screenRefuses` — whether a screen REFUSES this matrix outright instead of
     handing anything back. A screen refuses a matrix whose width disagrees with
     the width recorded when the model was fitted, one holding no samples, one
     holding a magnitude the recorded working precision cannot represent, and one
     presenting a per-column labelling that DISAGREES with the recorded labelling
     (columns renamed, or presented in another order).
   * `screenAdvises` — whether a screen of this matrix draws the labelling
     ADVISORY, i.e. reports a discrepancy about the labelling it presents rather
     than about its numbers. A screen draws that advisory exactly when the matrix
     presents no per-column labelling while the model recorded one, or presents
     one while the model recorded none. The advisory is NOT a refusal: such a
     matrix is still scored, and to the very same values as the labelled matrix of
     the same numbers (measured — axiom_check.py, leg (iv)), which is why no
     clause below lets a labelling condition a score VALUE.
   Both are DECIDED BY INSPECTION. Whether a screen would turn a matrix away, and
   whether it would report a labelling discrepancy about it, are read off that
   matrix's width, its magnitudes, its element kind and the labelling it presents,
   against what the model recorded when it was fitted — no screen has to be
   performed to know either (measured — axiom_check.py,
   `check_inspection_decides`, which decides both from the matrix alone and agrees
   with the screened outcome on every fixture, with a negative control). So naming
   one of them carries no screening effect, which is why they may be named
   anywhere, and a text that BRANCHES on one has proved something about its data
   rather than done something to it.

   THE PREPARED-MATRIX PROPERTIES, likewise opaque:

   * `scorableAsGiven` — whether the heavy scorer can consume this prepared
     matrix exactly as it stands, with no conversion step in between. Two things
     about the matrix bear on that, and both are properties of it as an object:
     the arrangement its numbers are held in, and how wide it is. The scorer
     reads a dense arrangement of the width the model was fitted on and the older
     compressed-row container, and it refuses a compressed-column arrangement, an
     arrangement narrower than that width, and the NEWER sparse container even
     where that one holds its numbers compressed by row (measured —
     axiom_check.py, `check_handle_properties` leg (c) and
     `check_sparse_container_fence`), so none of those is a prepared matrix this
     reference calls scorable. A screen's having accepted a matrix does not settle
     this question: a screen converts the working precision and consumes the
     labelling, and it hands the newer container back unchanged in kind.
   * `hasSamples` — whether this prepared matrix holds at least one sample.

   What an OCCURRENCE of a value reference means (the R-VALUE rule, mapping.md §2
   — it settles how these terms are read back into repository text):
   `anomalyScores samples`, `scoreValues scores`, `percentileAt scores q` and
   `preparedOf handle` denote
   VALUES, namely the result the unchanged callee produces for those arguments. They are not actions
   and they carry no ordering or repetition content: an implementation that names
   such a value at several places reads back as the same repository text as one
   that names it once — the callee produces the value and the name is bound to it,
   and each occurrence is a use of that binding. Screening, by contrast, IS an
   action here: it has exactly one spelling in this file (the screening method
   below), its VERDICT is what that method reports, and it restricts which matrices
   it will accept at all.

   What an occurrence of ARITHMETIC means (the R-ARITH rule, mapping.md §2.2):
   with the offset a carrier there is no number left in this file that models a
   repository quantity — `Rat`, `Int` and `Nat` appear in no declaration above and
   in no method's type. An arithmetic term a text writes down is therefore a
   CONSTANT of the reference language: it denotes the number it evaluates to, it
   invokes no repository callee, and it reads back into repository text as that
   number. The rule is grounded by measurement in BOTH directions. Toward the
   repository: the reference language's rational arithmetic is exact where the
   repository's on these numbers is not (axiom_check.py,
   `check_offset_arithmetic_fences` leg (e)). Toward the reference language: its
   arithmetic is total, and truncating where the repository's is neither —
   `(1 : Rat) / 0`, `(0 : Rat)⁻¹`, `(1 : Int) / 0` and `(5 : Nat) / 0` are all `0`
   and `(3 : Nat) - 5` is `0`, while the repository raises for the first of those
   and reports `-2` for the last. So the two are not the same operation, and no
   arithmetic term can be read as the repository doing arithmetic on anything.
   A number a text computes and then DISCARDS is dead text in particular — one
   built from written constants, one built from a screening verdict this file
   exposes, and one built from a produced sequence's length alike, which is the
   whole of what this rule excuses and is measured as such in §2.2. -/
axiom CallerHandle : Type
axiom Prepared : Type
axiom Presented : Type
axiom Scores : Type
axiom Point : Type
axiom Score : Type
axiom Offset : Type
axiom presentCaller : CallerHandle → Presented
axiom presentPrepared : Prepared → Presented
axiom screenRefuses : Presented → Bool
axiom screenAdvises : Presented → Bool
axiom preparedOf : CallerHandle → Prepared
axiom anomalyScores : Prepared → Scores
axiom scoreValues : Scores → List Score
axiom percentileAt : Scores → Point → Offset
axiom defaultOffset : Offset
axiom scorableAsGiven : Prepared → Bool
axiom hasSamples : Prepared → Bool
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section

/- THE SCREEN — the only spelling of a screening action in this file, and the
   first declaration in it, so it is the one action every method below can name.
   It takes a matrix as presented and reports the screen's verdict on it: whether
   the matrix was accepted, or turned away as unusable. It computes NO score, and
   it hands back NO data — a screen's data is reached, where it is reached at all,
   as the caller-side value `preparedOf` (see the axiom block), so that no text
   holding already-prepared data can obtain a re-prepared form of it from this
   method either.

   What is pinned is exactly the screen's VERDICT:

   * a matrix the screen REFUSES is reported as not accepted — the caller is told
     the matrix is unusable rather than handed something to go on with;
   * every other matrix is reported as accepted.

   Its argument has to be a matrix this screen has nothing to ADVISE about
   (`require screenAdvises presented = false`): one presenting the per-column
   labelling the model recorded when it was fitted, in that same order, or — for a
   model that recorded no labelling — one presenting none. An already-prepared
   matrix, whose labelling an earlier screen consumed while the model did record
   one, is exactly the matrix this screen reports a labelling discrepancy about
   that the caller's own data does not have. That report is an AMBIENT effect with
   no returned value for a caller to drop, which is why it is carried as a
   restriction on the argument instead of as a clause about the result: a
   call-site restriction is not a value an implementation may discard, cancel, or
   restore. So this method is callable exactly on the matrices whose screening the
   caller cannot observe as a spurious report, and nowhere else. -/
method screenHandle (presented : Presented) return (accepted : Bool)
  require screenAdvises presented = false
  ensures accepted = if screenRefuses presented then false else true
  do
    -- impl-start
    -- Consult the verdict: report the matrix turned away, or report it accepted.
    if screenRefuses presented then
      return false
    else
      return true
    -- impl-end

prove_correct screenHandle by
  loom_solve

/- THE PUBLIC SCORING ENTRY POINT, for a handle a caller brings in: it screens the
   incoming matrix and hands back the per-sample anomaly scores of the matrix that
   screen prepares from it. Being typed on `CallerHandle`, it is reachable only from outside this
   file — see the fitting tail below, which is exactly the caller that must not
   reach it. What is pinned is again the verdict and what it governs:

   * a handle the screen REFUSES yields no scores at all — the caller is told the
     handle is unusable rather than served numbers derived from it. So an
     implementation cannot serve a value the verdict does not sanction, and it
     cannot reach the served value without the verdict being settled;
   * every other handle this method accepts yields the per-sample anomaly scores
     of `preparedOf handle` — the numbers of the score sequence the scorer
     produces for the prepared form of ITS OWN numbers — WHATEVER
     per-column labelling the handle does or does not present. Screening consumes the labelling the handle
     arrived with; it does not move the numbers. The unlabelled handle of a
     labelled model's own numbers is in particular scored to exactly the values the
     labelled handle is, so the labelling may not condition this value, and no
     labelling reference appears in this clause.

   Its argument has to be a handle this screen has nothing to ADVISE about
   (`require screenAdvises (presentCaller handle) = false`), for the same reason
   the screen itself carries that restriction: the advisory is ambient, so it is
   carried where an implementation cannot drop it.

   It also has to be a handle whose PREPARED FORM the scorer can consume as it
   stands (`require scorableAsGiven (preparedOf handle) = true`) — the same kind of
   domain fence the fitting tail below carries, imposed here at the only prepared
   matrix this method can name. That a screen accepted the handle does not make its
   prepared form consumable: the screen converts the working precision and consumes
   the labelling, and it does not rearrange every matrix it accepts. A matrix held
   in the newer sparse container is accepted — the screen hands back a prepared
   matrix of the same numbers, compressed by row, in the working precision — and
   the scorer then refuses that matrix and reports nothing for it, as does the
   public entry point itself, while the dense matrix and the older sparse
   containers of those same numbers are all consumed and all scored to the values
   this entry point serves (measured — axiom_check.py,
   `check_sparse_container_fence`, refusals and controls together). So the fence
   excludes exactly the handles the repository has no scores for, and no others:
   in particular every arrangement the graded scoring surface uses lies inside it.
   Being a restriction on the argument, it is also not a value an implementation
   could discard. -/
method scorePublic (handle : CallerHandle) return (result : Option (List Score))
  require screenAdvises (presentCaller handle) = false
  require scorableAsGiven (preparedOf handle) = true
  ensures result = if screenRefuses (presentCaller handle) then none
                   else some (scoreValues (anomalyScores (preparedOf handle)))
  do
    -- impl-start
    -- Fresh handle: screen it first, and serve the scores of what that screen
    -- prepared only where it accepted the handle.
    let accepted ← screenHandle (presentCaller handle)
    if accepted then
      return some (scoreValues (anomalyScores (preparedOf handle)))
    else
      return none
    -- impl-end

prove_correct scorePublic by
  loom_solve

/- THE FITTING TAIL that derives the model's threshold offset when a non-default
   contamination level is requested: the offset is the order statistic of the
   per-sample anomaly scores at the requested percentile point `q`.

   At this point in fitting the sample matrix has ALREADY been screened once
   (earlier in fitting), and what this method holds is the PREPARED matrix that
   screen handed back: data the scorer can consume exactly as it stands (`require
   scorableAsGiven samples = true`) and holding at least one sample (`require
   hasSamples samples = true` — a fit whose matrix holds no samples is refused
   before this tail is ever reached, and an order statistic of no numbers at all
   has no value to report).

   Both restrictions are DOMAIN FENCES of the same kind and are grounded the same
   way — each excludes a region where the repository reports nothing, and each is
   measured together with the control that it excludes no more than that
   (axiom_check.py, `check_empty_handle_fences`, `check_handle_properties` leg
   (c)). Neither says anything about screening; the screening discipline is
   carried entirely by what follows. The requested point carries no restriction of
   this kind, and it needs none: a point is a CARRIER here (see the axiom block),
   so the only points this tail can name are the ones a fitting call site
   requests. A restriction on the parameter would have left the order statistic
   nameable at some other point inside the body; the type does not.

   Deriving the offset must therefore reuse that prepared matrix: it must not
   report anything further about the caller's matrix, and it must not put the heavy
   scorer to work a second time. Three structural facts of this file carry that,
   and none of them is a value an implementation can write down and then correct:

   * NO SECOND SCORING IS REACHABLE FROM HERE. The one method in this file that
     invokes a scorer is the public entry point above, and its argument is a
     `CallerHandle`. This tail holds a `Prepared`, nothing maps a prepared matrix
     to a handle (see the axiom block: presenting a matrix to a screen is not
     invertible, and this file constructs no handle), so there is no argument with
     which this text could invoke it — for its own data or for any other. The
     screen-free scores are reached instead as the VALUE reference `anomalyScores
     samples` (R-VALUE, see the axiom block), which is one production of one score
     sequence however many times its name is used.
   * NO RE-PREPARED FORM OF THIS DATA IS REACHABLE FROM HERE EITHER, and this is
     the reason a screen's data is a caller-side value in this file. `preparedOf`
     takes a `CallerHandle`, which this tail cannot form; there is no
     `Presented → Prepared`; and the screening method hands back a verdict, not
     data. So the prepared matrix this tail holds is the only one it can name, and
     the numbers it scores are the ones the earlier screen in fitting produced.
   * NO REPORT ABOUT THE CALLER'S MATRIX IS REACHABLE FROM HERE. Screening has
     exactly one spelling — the screen above — and invoking it demands a matrix
     the screen has nothing to advise about. The prepared matrix here is not such
     a matrix whenever the model recorded a labelling, since the earlier screen
     consumed the labelling the caller's matrix presented; and nothing in this
     method's context discharges that demand — not for this matrix and not for any
     other it can present, the screen properties being opaque. So the re-screen
     this tail must not perform, the one that reports a labelling discrepancy the
     caller's own data does not have, is not merely unrecorded here: it is
     INADMISSIBLE, whatever an implementation does with what comes back.
   * WHAT REMAINS ADMISSIBLE IS ALSO HARMLESS, and this is stated rather than
     hidden. An implementation that can PROVE, before screening, that the screen
     has nothing to advise about the data it holds may present it again: such a
     re-screen reports nothing, hands back the prepared form of the same numbers,
     and computes no score. It is a redundant preparation step and not the defect
     this fit tail is about, which is precisely why the restriction is carried on
     the argument and not on the result.

   The offset value is identical whether or not the prepared matrix is screened
   again; what this method pins down is that no report and no second scoring can
   happen on this path. `samples` and `q` are read-only. -/
method fitComputeOffset (samples : Prepared) (q : Point) return (offset : Offset)
  require scorableAsGiven samples = true
  require hasSamples samples = true
  ensures offset = percentileAt (anomalyScores samples) q
  do
    -- impl-start
    -- PRE-PATCH: derive the offset by routing the already-prepared matrix back
    -- through the SCREEN — the step the public scoring entry point performs
    -- before it scores anything — so the fitting tail screens its data a second
    -- time and the labelling discrepancy that screen reports is a report about a
    -- matrix the caller never supplied. Screening does not move the numbers, so
    -- the order statistic is read off the scores of the same data either way;
    -- what the second screen adds is the report, not a different value.
    let rescreened ← screenHandle (presentPrepared samples)
    let scores := anomalyScores samples
    let off := percentileAt scores q
    return off
    -- impl-end

prove_correct fitComputeOffset by
  loom_solve

end
