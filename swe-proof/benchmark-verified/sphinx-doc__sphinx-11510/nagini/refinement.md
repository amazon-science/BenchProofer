# refinement.md — sphinx-doc__sphinx-11510

The operation-by-operation correspondence between `model.py`'s implementation
(the `forward_with_source_read` impl region, the `transformed` pure spec, and
the live `emit_and_collect` axiom) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == a real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The forwarding step — `Include.run` / the installed `_insert_input`

Gold hunk (`sphinx/directives/other.py`, inside `Include.run`):
```python
def _insert_input(include_lines, path):
    text = "\n".join(include_lines[:-2])
    docname = self.env.path2doc(os_path(path))
    arg = [text]
    self.env.app.events.emit("source-read", docname, arg)
    text = arg[0]
    include_lines = text.splitlines() + include_lines[-2:]
    return StateMachine.insert_input(self.state_machine, include_lines, path)

if self.env.app.events.listeners.get('source-read'):
    self.state_machine.insert_input = _insert_input
```

| # | model.py impl op (`forward_with_source_read`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `lines: List[int]` | `include_lines: list[str]` argument of `_insert_input` | R | `list[str]` of gathered lines ↔ `List[int]` of opaque per-line identities (mapping.md §2). |
| A2 | `body = lines[:n - 2]` | `include_lines[:-2]` (inside `text = "\n".join(include_lines[:-2])`) | R + I | slicing off the final two framing markers is the identical list operation; the subsequent `"\n".join` is the line→text half of the round trip, modeled as the identity at line granularity (mapping.md §2; G-AX validates the round trip). |
| A3 | `markers = lines[n - 2:]` | `include_lines[-2:]` | I | the final two framing markers, taken verbatim. |
| A4 | `new_body = emit_and_collect(body)`, with `ToSeq(new_body) == hook(ToSeq(body))` | `arg = [text]; self.env.app.events.emit("source-read", docname, arg); text = arg[0]` (then `text.splitlines()`) | A-consumed | the unchanged `EventManager.emit('source-read', …)` machinery, wrapped by the text→line half of the round trip, offers the body to every registered listener and yields the rewritten body. The proof consumes the axiom's `Ensures` (`== hook(body)`). G-AX runs the real `EventManager` to confirm soundness (mapping.md §3.1). The docname routing `path2doc(os_path(path))` only selects which document the event reports and does not affect the forwarded lines; it is unchanged and exercised by G-AX, not separately modeled. |
| A5 | `result = new_body + markers` | `include_lines = text.splitlines() + include_lines[-2:]` | R + I | list concatenation of the rewritten body and the verbatim framing markers — the identical operation; `text.splitlines()` is the text→line half folded into A4. |
| A6 | `return result` | `return StateMachine.insert_input(self.state_machine, include_lines, path)` | R | the forwarded line sequence is what the parent `StateMachine.insert_input` consumes; the return wraps that delegation. `insert_input` is unchanged and depends only on the forwarded `include_lines` (mapping.md §1). The modeled value is exactly those forwarded lines. |

The discriminating content of the change — that the gathered body is offered to
the `source-read` hook **and the rewritten body replaces it**, while the two
framing markers bypass the hook — lives in the postcondition
`ToSeq(Result()) == transformed(ToSeq(lines))` where
`transformed(lines) = hook(lines.take(len-2)) + lines.drop(len-2)`. The
pre-patch `Include.run` installed no such forwarding (docutils' `insert_input`
received the gathered lines directly); `model_prepatch.py` reproduces that
(`result = lines[:n]`, the lines forwarded verbatim) and **fails** the
postcondition `ToSeq(Result()) == transformed(ToSeq(lines))`, which is exactly
the spec sensing the change (G-DIFF). The two F2P tests observe precisely this:
`test_include_source_read_event` checks the body text offered to the event
equals the markers-excluded join (`"\nBaz was here."`);
`test_include_source_read_event_nested_includes` checks the hook's rewrite
(`#magical`→`amazing`) reaches the parsed body.

## B. The listener guard (no separate failing model)

Gold hunk also adds:
```python
if self.env.app.events.listeners.get('source-read'):
    self.state_machine.insert_input = _insert_input
```
i.e. the forwarding closure is installed only when a `source-read` listener
exists; otherwise the unchanged path forwards the gathered lines verbatim. This
guard is observationally vacuous: when there are no listeners, `hook` is the
identity on the body (the dispatcher rewrites nothing), so `transformed(lines)`
already equals `lines` and the modeled `forward_with_source_read` returns the
same value the un-guarded path would. The model therefore covers both branches
with one contract; G-AX's `check_no_listener_means_no_change` confirms the
no-listener path equals verbatim forwarding on the real machinery. No separate
`model_prepatch_<k>` is needed: the single discriminating behaviour (body
offered-and-replaced vs. forwarded-verbatim) is exercised by `model_prepatch.py`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — routing the gathered body through the content-transformation hook
and splicing the result back between/around the framing markers — is modeled
**deeply and structurally** in `transformed` / `forward_with_source_read` (the
`take`/`drop` body/marker decomposition and the concatenation), with only the
unchanged event-dispatch+round-trip callee left as the single **A-consumed**
axiom `emit_and_collect`. There is no axiom about the function under change
(`Include.run`); the hook is an uninterpreted symbol, not an oracle the result
is pinned to (the result must be *produced by* applying the modeled dispatch to
the modeled body region, directive 8).

## D. verify(model) ⇒ resolved

`forward_with_source_read` verifies only if its output equals the hook-
transformed body followed by the two verbatim framing markers (A2–A6,
postconditions). By R (`list[str]` ↔ `List[int]` line identities, the
join/splitlines round trip at line granularity) the verified forwarding equals
`text.splitlines() + include_lines[-2:]` on the gathered lines; by A-consumed
the real `EventManager.emit('source-read', …)` meets the `emit_and_collect`
axiom (G-AX, real dispatcher); the unchanged `path2doc`/`os_path`/parent
`insert_input` callees are exercised by G-AX and depend only on the forwarded
lines. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the one audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
