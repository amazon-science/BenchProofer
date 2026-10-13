# P2 adversarial audit — django__django-14915

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Superseded audit round.** Everything between this line and the first
> `## Role` heading below was published by an EARLIER audit of this bundle
> titled "P2 Audit Verdict — django__django-14915", before this corpus rendered
> one section per audit role. It is kept verbatim because it is the only
> account of that round that ships in this bundle, and it is NOT this cell's
> record. The record is the audit gate entries in the `meta.json` beside this
> file, which are the source of truth for the cell's status; each role section
> below publishes its gate's `status (recorded)` and `machine verdict` straight
> from that entry. Each round authored and re-ran its own attacks, so a count
> in the text above is that round's own count and not this record's: where the
> two accounts differ, the record governs.

**Overall status: ACCEPTED**

Twin artifact for the gold patch `def __hash__(self): return hash(self.value)`
on `ModelChoiceIteratorValue`. The twin models this as a single method
`choiceValueHash (value : Int) return (h : Int)` with the lone clause
`ensures h = valueHash value`, where `valueHash : Int → Int` is `opaque` (sealed,
no asserted contract) modeling the builtin `hash(self.value)`.

## Per-gate verdict table

| Gate | Verdict | Basis |
|------|---------|-------|
| **G-EQ** | **pass** | G-EQ SOUND (all 6 spec-too-weak attacks REJECTED, verify exit 1; 3 positive controls verify exit 0 → non-vacuous) AND spec-strength TIGHT (sole clause `h = valueHash value`; injectivity correctly NOT pinned) AND no kind-3 refinement (refinement.md all R / A-consumed / I). |
| **G-PANEL** | **pass** | faithfulness FAITHFUL (in-container post-gold `hash(obj) == hash(obj.value)` held for ~2000 ints + str/tuple/float/bool; instance field never affects hash → F2P assertion 1; distinct pks → distinct hashes → F2P assertion 2; rc 0, 0 violations) AND G-AX VACUOUS (`valueHash` is bare `opaque Int → Int`, zero asserted `ensures`, no `axiom_check.py` — nothing for real `hash()` to violate) AND leakage NO-LEAKAGE (spec view names no patched file/symbol; discriminator fully derivable from the public problem_statement). |

Supporting gates (from meta.json, re-confirmed): G-VERIFY pass (1.5s), G-DIFF pass
(prepatch `return 0` fails with `⊢ 0 = valueHash value`, same_spec=True),
G-RESOLVE pass (gold resolved), G-CONF skip (legitimate: impl all-A-tagged, no
DB-free deterministic cross-language shadow of salt-dependent CPython `hash()`),
G-AX skip (no asserted axiom contract).

## Concrete defects + precise fixes

None. No verifying-but-wrong impl, no unfaithful divergence, no unsound axiom, no
genuine leak was found. No refinement required.

Note (not a defect): the spec pins "hash is a deterministic function of the
wrapped value" but does NOT pin injectivity (F2P's `hash(value_1) != hash(value_2)`).
This is correct — the real `hash(self.value)` does not guarantee injectivity
(collisions permitted); the test passes only incidentally for the chosen pks.
Pinning injectivity would over-claim. The modeled property is exactly what the fix
guarantees.

---

## Sub-review 1 — G-EQ / SPEC-WEAKNESS (verbatim)

VERDICT: G-EQ = SOUND, spec-strength = TIGHT.

Bundle: django__django-14915. The spec is minimal by design: one method `choiceValueHash (value : Int) return (h : Int)` with the single clause `ensures h = valueHash value`, where `valueHash : Int → Int` is `opaque` (sealed, no asserted contract) modeling builtin `hash(self.value)`. This is the gold patch's whole content (`def __hash__(self): return hash(self.value)`). All attacks were confined to the `-- impl-start … -- impl-end` region (axioms/pre/post/ensures byte-identical), confirmed via `same_spec(Solution, atk_n)=True` for every attack.

Spec-too-weak attacks (all share spec, all correctly REJECTED with verify exit 1, rejected by the lone clause `ensures_1: h = valueHash value`):
- atk_1 `return 0` (the prepatch bug — value-independent constant) → unsolved `⊢ 0 = valueHash value`
- atk_2 `return value` (echo the input value, not its hash) → `⊢ value = valueHash value`
- atk_3 `return valueHash value + 1` (off by one) → `⊢ valueHash value + 1 = valueHash value`
- atk_4 `return valueHash (value + 1)` (hash of the wrong value) → `⊢ valueHash (value + 1) = valueHash value`
- atk_5 `return valueHash 0` (hash of a constant, ignores input) → `⊢ valueHash 0 = valueHash value`
- atk_6 `return -(valueHash value)` (negated) → `⊢ -valueHash value = valueHash value`

Positive controls (share spec, MUST verify — all verify exit 0, proving non-vacuity):
- atk_7 `let x := valueHash value; return x` (binding form)
- atk_8 `if value = value then return valueHash value else return 0` (conditional, both correct branches)
- atk_9 `let h := valueHash value; let _ := value+1; return h` (dead-code form)

Ungrounded-oracle probe: NOT exploitable. The postcondition `h = valueHash value` is the opaque hash applied to the *input* `value`. Because `valueHash` is `opaque` (un-unfoldable) and asserts nothing about its concrete output, there is no "answer key" to echo — the only term that discharges the goal is `valueHash value` itself, which IS the fix. Any impl that ignores or perturbs the input (atk_2/4/5/6) is rejected because the solver cannot relate `valueHash <other>` or a literal to `valueHash value`. The opaque function ties the result to the input rather than masking a wrong impl.

Refinement audit: refinement.md table is all R (value↔Int) / A-consumed (the opaque hash) / I (`h = valueHash value`); no kind-3 hand-waved inexpressible op. conf_skip=true is legitimate: the only executable op is the opaque value-hash, all-A-tagged, and CPython `hash()` is salt-/implementation-dependent with no DB-free cross-language R/I shadow to fuzz. G-AX skip is correct (the opaque function asserts no contract, so there is nothing to validate against the real callee). Shipped `Solution_prepatch.lean` fails for the right reason: same_spec=True, verify exit 1, unsolved `⊢ 0 = valueHash value` — exactly the discriminating clause (value-independent pre-image of the unhashable bug). G-RESOLVE recorded resolved (gold verbatim).

Note on scope: the spec pins "hash is a deterministic function of the wrapped value" but does NOT pin injectivity (F2P's `hash(value_1) != hash(value_2)`). This is correct, not too-weak: the real `hash(self.value)` does not guarantee injectivity either (collisions are permitted); the test passes only incidentally for the chosen pks. Pinning injectivity would over-claim. The modeled property is exactly what the fix guarantees.

---

## Sub-review 2 — FAITHFULNESS + G-AX (verbatim)

Confirmed. `valueHash` is a bare `opaque Int → Int` with NO axioms/`ensures` asserting anything about its return values. The only `ensures` is `h = valueHash value`, which constrains the method's output relative to the opaque function, not the opaque function itself. There is nothing about the real `hash()` callee that could be violated — G-AX is genuinely VACUOUS, not a hidden unsound axiom.

**FAITHFULNESS: FAITHFUL.** **G-AX: VACUOUS.**

**Bundle modeling.** The gold patch adds `def __hash__(self): return hash(self.value)` to `ModelChoiceIteratorValue`. The twin models this as `method choiceValueHash (value : Int) return (h : Int) ensures h = valueHash value`, with `valueHash : Int → Int` declared `opaque` (no contract). Impl returns `valueHash value`. G-VERIFY passes (exit 0, 1.5s); G-DIFF prepatch (`return 0`) fails with exactly `⊢ 0 = valueHash value` (verified, exit 1); `same_spec(Solution, prepatch) = True` so G-DIFF is a real same-spec discriminator.

**Faithfulness (in-container, post-gold).** I extracted the real patched `ModelChoiceIteratorValue` class from `/testbed/django/forms/models.py` after applying `patch.diff` and exercised the real `__hash__`:
- `hash(obj) == hash(obj.value)` held for all ~2000 integer values plus `str`/`tuple`/`float`/`bool` values — exactly the spec's claim `h = valueHash value` (the spec's predicted output equals the real post-gold output, with `valueHash` ≙ the real `hash(self.value)`).
- The companion `instance` field never affects the hash → matches F2P assertion 1 (`hash(value_1) == hash(ModelChoiceIteratorValue(c1.pk, None))`).
- Distinct pks produced distinct hashes → F2P assertion 2 (`hash(value_1) != hash(value_2)`); object is hashable (no `TypeError`) → the bug-fix prerequisite. Verdict line printed `FAITHFUL`, violations: 0, rc 0.
- F2P input shapes (integer pks) are covered by the modeled domain (`Int`); the fix is value-generic and the test exercises integer pks.

**Spec is not too strong.** The spec does NOT over-claim hash injectivity — it only pins `h = valueHash value` (function of value alone). The real `hash()` is not injective; the F2P `assertNotEqual` passes by happenstance for those pks, and a faithful spec correctly avoids asserting distinctness. No correct behavior is rejected. The opaque, contract-free `valueHash` cannot mask a wrong impl: the sole `ensures` forces the output to be `valueHash value`, so `return valueHash value` is the only verifying impl (prepatch `return 0` correctly fails).

**G-AX VACUOUS.** No `axiom_check.py` is present. The only abstracted callee `valueHash` is a bare `opaque Int → Int` with zero asserted `ensures` (confirmed by grep: line 18 declaration, line 45 the only ensures is on the method output `h`). An opaque function asserting nothing about its return value has no contract for the real `hash()` to violate — soundness here rests on G-VERIFY + G-DIFF + G-RESOLVE, which all pass. CPython `hash()` being salt-/implementation-dependent is correctly not modeled, justifying the opaque (not axiom) choice; G-CONF skip (all-A-tagged, no DB-free deterministic shadow of `hash()`) is legitimate.

---

## Sub-review 3 — LEAKAGE (verbatim)

Verdict: NO-LEAKAGE.

**Problem statement (public, solver-visible) reveals:**
- The class name `ModelChoiceIteratorValue`
- That it "is not hashable" → `TypeError: unhashable type: 'ModelChoiceIteratorValue'`
- The use case: `value in self.show_fields` where `show_fields` is a **dict** — i.e. the value is used as a dict key, which requires hashing
- Contrast: `value in allowed_values` (an array) works fine — establishing that the issue is specifically about hashability for dict/set membership

So the public statement establishes both the affected object and the required property: **make it hashable** so it can be a dict key.

**Spec view reveals:**
- `choiceValueHash` — generic identifier, no echo of `ModelChoiceIteratorValue`, `__hash__`, or `models.py`.
- `valueHash : Int → Int` — opaque hashing of wrapped value; generic name.
- Docstring: a wrapper object with an underlying value + companion data, must "participate as a key in keyed/uniqued containers," and "asking the wrapper for its hash yields exactly the hash of the value it wraps."

**Reconstruction attempt from the spec view alone (no problem_statement):**
The spec view alone describes a value-wrapper that must be hashable as a container key, with `hash(wrapper) == hash(value)`. This is a textbook hashable-wrapper. With the problem statement added, the target object (`ModelChoiceIteratorValue`) and the required property (hashable for dict-key use) are already public. The standard Python fix for "make an object hashable, keyed on its wrapped value" is `def __hash__(self): return hash(self.value)` — which is exactly the one-line gold patch. This reconstruction is derivable entirely from the **public problem statement** (object X is not hashable; make it hashable; its identifying field is the wrapped value), not from anything the spec view adds.

**Leak-vector checks:**
- Patched file/symbol: NOT named. `models.py`, `ModelChoiceIteratorValue`, `__hash__`, `ModelChoiceIterator` — none appear. PASS.
- Diff line: The gold line is `return hash(self.value)`. The spec pins `h = valueHash value` (hash = hash of the wrapped value). This is the abstract desired behavior, not a quoted diff line, and it is the natural/only sensible implementation of "make this value-wrapper hashable" — which the public statement already calls for. Not a leak beyond PS.
- Repo-symbol-echoing identifier: `choiceValueHash`, `valueHash`, `value`, `h` — all generic. The name `choiceValueHash` faintly evokes "choice value" but `ModelChoiceIteratorValue` / "choice" is in the public statement context anyway (it's a forms ModelChoice value); even so it does not echo a patched symbol verbatim. Borderline-benign.
- Bug/fix narration: The docstring states abstract desired behavior ("must expose a hash determined by its underlying value... participates as a key in keyed/uniqued containers"). It does NOT narrate the mechanism (no "add `__hash__`", no "Python sets `__hash__ = None` when `__eq__` is defined", no "previously unhashable"). The prepatch diagnosis ("Python auto-set `__hash__ = None`") lives only in refinement.md, NOT in the spec view. PASS.

**"value-based equality" phrase check:** The docstring ends "...which is precisely the consistency a value-based equality demands." This alludes to `__eq__`. But the gold patch only adds `__hash__`; `__eq__` already exists at base_commit. The public problem statement is about hashability, and the hash/eq consistency contract is general Python knowledge, not a leak of the diff. It is abstract justification, not mechanism narration of the edit. Benign.

Everything in the spec view is derivable from the public problem statement, which already names the object and the "make it hashable" requirement. No hints-only vocabulary leaks (hints contain the literal `def __hash__(self): return hash(self.value)` — none of that mechanism, no `__hash__`, no `hash(self.value)` literal, appears in the spec view). meta.json G-LEAK = "pass" (not "relaxed") — a genuine clean pass: the discriminator (hashability of the value-wrapper) is fully public.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 10 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The per-attack account is recorded in this cell's audit record in the format that audit round used: a per-gate verdict table and each reviewer's account quoted in full, rather than the graded per-attack table later rounds emit. It is not restated here because summarising it would mean re-grading prose, and the record itself is the better source.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness (spec-too-strong / drift) check for django__django-14915, modeled method choiceValueHash ↔ ModelChoiceIteratorValue.`__hash__` added by the gold patch (body: return hash(self.value)).

### Verification performed
- same_spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True. spec_view confirms the spec region (opaque valueHash decl + `method choiceValueHash (value : Int) return (h : Int) ensures h = valueHash value`) is identical across gold and prepatch; only the impl body differs (return valueHash value vs return 0).
- lean_verify.sh on Solution.lean: exit 0 (verifies).
- Real repo at base_commit 903aaa35e5ceaa33bfc9b19b7f6da65ce5a91dd4 (git object): ModelChoiceIteratorValue.`__init__`(self, value, instance) stores self.value/self.instance; `__str__`/`__eq__` present; patch inserts def `__hash__`(self): return hash(self.value). Confirms mapping.md.

### FAITHFULNESS ANALYSIS (is the spec too strong / does it disagree with the real callee on any input?):
The spec pins exactly one property: h = valueHash value, where valueHash : Int → Int is fully OPAQUE with NO asserted contract about its return value. This is the weakest possible modeling of hash(self.value):
- It asserts nothing concrete about hash() output, so it cannot over-constrain a salt-/version-dependent builtin. Any real hash() satisfies it vacuously.
- The only structural claim is that the result is a deterministic function of `value` ALONE (independent of the companion `instance`). The real `__hash__` = hash(self.value) is precisely that — a function of the wrapped value and nothing else. Exact match.
- No stronger claim (no concrete value, no injectivity, no coupling to `__eq__`) is imposed, so the modeled function cannot demand more than the repo delivers.
- Value abstraction self.value → Int is a documented scoping choice (mapping.md §2; F2P test wraps integer pks). Within Int, hash(int) is total and deterministic, so no input drives the real callee to differ from valueHash value.

No diverging input exists. The modeled function agrees with the real callee on every input in the modeled domain; the spec is minimal, not too strong. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

same_spec (VelvetBackend tables) = True: spec regions are byte-identical between Solution.lean and Solution_prepatch.lean; impl and proof regions are elided in the spec view. Assessed the spec view (imports/options/axioms/pre/post/method signature+ensures/doc-comments) for leakage of the gold edit beyond the PUBLIC problem_statement (hints_text excluded).

**Gold edit:** add `def __hash__(self): return hash(self.value)` to ModelChoiceIteratorValue, making it hashable with a value-determined hash.

Public problem_statement content: title 'ModelChoiceIteratorValue is not hashable', the `TypeError: unhashable type: 'ModelChoiceIteratorValue'` symptom, and usage of the value as a dict key (`if value in self.show_fields`). It does NOT name `__hash__` or `hash(self.value)`; that specific method appears only in hints_text, which is out of scope.

Spec view leakage check — no leak found:
- No gold-specific identifiers appear: no `ModelChoiceIteratorValue`, `__hash__`, `self.value`, `hash()`, or filename. Language is fully abstracted ('wrapper object', 'underlying value', 'keyed/uniqued containers').
- Impl body is elided ('implementation elided — supplied by the consumer'); proof is elided. The gold code `return valueHash value` is not exposed.
- The pinned behavior — `ensures h = valueHash value` ("the wrapper's hash yields exactly the hash of the value it wraps") — is precisely the behavior the public problem_statement + public repo already force: the object must become hashable, must serve as a value-based dict key, and (given the pre-existing value-based `__eq__` visible in the repo) Python's eq/hash contract mandates that equal objects hash equal, i.e. the hash must be a function of the wrapped value. This is the unique sound fix, publicly derivable; the spec restates a required, public constraint rather than disclosing a non-obvious implementation choice.
- valueHash is modeled fully OPAQUE with no asserted concrete value, so the spec pins only the value-dependence structure, not any concrete hash output — nothing beyond the public contract.

G-LEAK gate in meta.json also reports pass with empty failures, consistent with this independent assessment.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
