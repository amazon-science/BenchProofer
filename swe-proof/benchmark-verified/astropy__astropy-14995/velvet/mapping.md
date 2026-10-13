# mapping.md — astropy__astropy-14995

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b16c7d12ccbc7b2d20364b89fb44285bcbfede54`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo file under change: `astropy/nddata/mixins/ndarithmetic.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveMask` (`method`) | `NDArithmeticMixin._arithmetic_mask(self, operation, operand, handle_mask, axis=None, **kwds)` — `astropy/nddata/mixins/ndarithmetic.py:485` (the case split at body lines 516–527) | the modeled changed function: decide the resulting mask of an elementwise operation |
| `selfMask : Option (List Int)` | `self.mask` | first operand's mask (present array, or `None`) |
| `operandMask : Option (List Int)` | `operand.mask` | second operand's mask (present array, or `None`) |
| `handleMaskNone : Bool` | `handle_mask is None` | the caller declined mask handling |
| `operandPresent : Bool` | `operand is not None` | a real second operand was given |
| `combine : List Int → List Int → List Int` | `handle_mask` (the caller-supplied combiner, e.g. `np.bitwise_or`, `np.logical_or`) | merges two present masks elementwise |
| `out : Option (List Int)` | the function's return value (`result_mask`) | the resulting mask, or `None` |

There is no separate callee modeled as an axiom: every branch of the function is
expressed directly, and the one callable the function delegates to
(`handle_mask`) is a parameter of the function under spec, so it is modeled as
the `combine` parameter — **not** an axiomatized library callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a mask: `None` or an integer `numpy.ndarray` (bitmask / boolean-as-int) | `Option (List Int)` | `None` ↔ `none`; a present array `m` ↔ `some <flattened element list>`; the spec is agnostic to array shape — only *presence* and the *combiner result* are observed. G-CONF compares full arrays via `np.array_equal`, so shape is preserved end-to-end on the real side. |
| `handle_mask is None` (decline mask handling) | `handleMaskNone : Bool` | `True ↔ true` |
| `operand is not None` (real second operand) | `operandPresent : Bool` | always `true` in the tested binary-operation path; see §3 |
| `handle_mask` callable (e.g. `np.bitwise_or`) | `combine : List Int → List Int → List Int` | applied to the two present mask values; G-CONF feeds the real callable to BOTH legs, so its concrete identity is irrelevant to the R/I diff (it is total only on equal-shape masks — comparable carriers — exactly the real binary-op domain) |
| `deepcopy(m)` (`ndarithmetic.py:522,524`) | identity on `Option (List Int)` | `deepcopy` preserves element content; the F2P test compares mask *values* (`np.testing.assert_equal`), not object identity. Identity on the carrier. |

The spec's domain is `operandPresent = true` (`require`). This is faithful: by
the time `_arithmetic_mask` is reached on the `else` branch of `_arithmetic`
(`ndarithmetic.py:335`), `operand` is the *wrapped* second operand — a real
`NDData`-like instance, never `None`. (`operand is None` only ever holds on the
collapse path, `use_masked_arith`, `ndarithmetic.py:265`, which does NOT call
`_arithmetic_mask`.) This is precisely why the pre-patch guard `operand is None`
is dead for binary ops and the bug manifests.

## 3. Callee provenance and flag dependencies

- **`handle_mask` (→ `combine`).** Not an axiomatized callee: it is a *parameter*
  of the function under spec, supplied by the caller (the F2P test passes
  `np.bitwise_or`). The default in `_arithmetic` is `np.logical_or`
  (`ndarithmetic.py:171`). It is invoked ONLY when both masks are present
  (the `else` arm), and only on two present mask values — never on `None`.
  Modeling it as `combine` and applying it exactly in the both-present arm is
  faithful; no contract about it is assumed.
- **Flag dependency.** The single behaviour-relevant flag is `handle_mask is
  None` (`handleMaskNone`). When set, the result is `None` regardless of the
  masks — modeled by the first `ensures`. There is no `quote=`-style hidden
  flag.
- **No A-consumed axioms, no A-reference deep models.** The changed operation is
  a pure case split, fully expressible in Velvet, so there is nothing to
  axiomatize or to deep-model-against-a-real-callee. `axiom_check.py` is
  therefore absent and G-AX skips (gates.py: "no axiom_check.py").

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` and `numpy.random.RandomState`
with **`14995`** so the consumer-side verdict (§11.3) is reproducible. The R/I
shadow it builds transliterates `resolveMask`'s `do` block to Python over the
real mask carriers; the oracle is the patched `_arithmetic_mask` applied at
base_commit (the harness applies patch.diff first). All ops are R/I — there is
no A-tagged callee to leave as a real-callee substitution.
