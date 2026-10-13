#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13344 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`initMiddleware`) is exactly one op:

    let out := construct handlerIsAsync
    return out

`construct` is the deep model of the *unchanged* canonical middleware
construction routine (`MiddlewareMixin.__init__` -> `_async_check`), tagged
**A-reference** in refinement.md. The impl region therefore contains NO R/I
(type-refinement or identical-concrete) op to differential-test:

  * There is no input-dependent R/I computation transliterable to Python over a
    real repo type. The whole impl is the single A-reference call to `construct`,
    whose only content (asyncCapable := handlerIsAsync) is validated against the
    real callee by axiom_check.py (G-AX), not by this gate.
  * The observable the change governs — `asyncio.iscoroutinefunction(instance)`
    after construction — materializes only by instantiating a real middleware
    subclass with a real (a)sync handler. That IS what the F2P test
    `test_coroutine` does; it is not a pure, DB-free R/I shadow this gate can
    fuzz over >=1e5 inputs. The behavioural soundness of `construct` against the
    real routine is already exercised by G-AX (2006 handlers, async + sync).

Per SPEC_GUIDE section 3 / WORKER_PROMPT: when the impl region is all-A-tagged
(here, the single A-reference `construct`), set meta.json conf_skip=true and
ship this status=skip stub. The A leg is covered by G-AX (axiom_check.py); the
spec-strength and discrimination legs are covered by G-VERIFY (the spec provably
forces out.asyncCapable = handlerIsAsync) and G-DIFF (the prepatch, which always
records asyncCapable = false, fails exactly that clause). See mapping.md section
3 and refinement.md section C.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-13344 — the modeled do-block is a "
          "single A-reference call (construct = the unchanged canonical "
          "middleware construction routine); the impl region is all-A-tagged "
          "with no input-dependent R/I shadow to differential-test. "
          "conf_skip=true. Soundness covered by G-AX + G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
