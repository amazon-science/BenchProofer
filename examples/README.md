# Examples

| example | what it is |
| --- | --- |
| `tasks.jsonl` | three tasks in the local JSON Lines format, ready to ingest |
| `plugin/` | an installable third-party plugin adding a benchmark and a gate |

## Your own tasks

```bash
benchproofer ingest jsonl --extra source=examples/tasks.jsonl --extra name=demo
benchproofer formalize demo --backend falsifier --provider anthropic
benchproofer check demo --level oracle
benchproofer report demo
```

Each of the three tasks ships a broken module as its starting point and the fixed module
as its reference, which is the shape a repair benchmark has: the broken version becomes
the bundle's pre-fix twin, so `spec.discriminates` has something real to reject.

Formalizing needs a model provider. Without one, `bash scripts/smoke.sh` judges the
fixture bundles that ship with the tool instead.

## Your own plugin

```bash
pip install -e examples/plugin
benchproofer catalog benchmarks
benchproofer ingest mini --bundle-root /tmp/mini-corpus
```

See [plugin/README.md](plugin/README.md), and the guides under `docs/guides/` for the
interface each kind of component implements.
