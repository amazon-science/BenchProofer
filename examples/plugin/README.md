# Example plugin

A third-party package that adds a benchmark and a gate to Benchproofer. It exists to
show that nothing about the built-in components is privileged: they are registered
through the same five entry-point groups this package uses.

```bash
pip install -e examples/plugin
benchproofer catalog benchmarks | grep mini
benchproofer catalog gates | grep no_todo
```

Both components are now used by every command that would use a built-in one. The smoke
suite generates a case for each registered adapter, so installing this package adds one:

```bash
benchproofer smoke benchmarks.mini
```

The gate runs on every bundle that is judged, and can be selected by name like any
other. Formalizing needs a model provider, see
[bring your own model](../../docs/guides/bring-your-own-model.md):

```bash
benchproofer ingest mini --bundle-root /tmp/mini-corpus
benchproofer formalize mini --bundle-root /tmp/mini-corpus --backend falsifier
benchproofer check mini --bundle-root /tmp/mini-corpus --only spec.no_todo
```

To remove it again:

```bash
pip uninstall benchproofer-example-plugin
```

## What is in here

| file | shows |
| --- | --- |
| `pyproject.toml` | the two entry points, and that a plugin needs nothing else |
| `src/benchproofer_example/benchmark.py` | an adapter: describe, report availability, yield tasks in a stable order |
| `src/benchproofer_example/gate.py` | a gate: one question, an established failure, and an honest skip |

The benchmark ships its three tasks rather than downloading them, so the example runs
anywhere. A real adapter pins a dataset by revision and digest instead; see
[docs/guides/add-a-benchmark.md](../../docs/guides/add-a-benchmark.md).

The gate is registered but not required, so it is judged and reported on every bundle
without changing what certification means. The required set is fixed in the tool, which
is what makes "certified" comparable across corpora.
