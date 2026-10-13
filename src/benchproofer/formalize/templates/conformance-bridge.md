Write the whole program again, comparing what it reports as `skipped` by reaching it another
way.
`skipped` is for a function nothing in this environment can call, and Benchproofer asks once
whether that is really so. Reach a method through its object, and compare a function that
takes a callable, or only passes a value through to one, by building it around
a stub of your own in that callable's place, as the first request describes; the
repository's own tests show how the function is set up. Keep the implementation the program
contains exactly as it is, and keep comparing everything it already compares.

If, having tried, you conclude that nothing here can call it, keep the `skipped` line
and say in one sentence before the program what stands in the way. The report then stands:
the conformance gate records that part as not compared, and the bundle is not certified on
it.
