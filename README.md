# LilRAE

LilRAE is the single non-normative reference backend for the
[Reproducible Agentic Environments System](https://github.com/RAESystem/rae).
It is a downstream implementation: RAES owns portable semantics, contracts,
backend protocols, diagnostics, and conformance.

This repository is at its engineering-baseline stage. The `lilrae` Python
distribution, import package, and command expose package metadata, help, and
version information only. They do not execute or emulate a backend and make no
conformance, reproducibility, or production-readiness claim.

## Authority boundary

LilRAE consumes the exact released `raes` distribution from the public package
registry. Only the public modules declared in
[`policy/repository.toml`](policy/repository.toml) may be imported. A sibling
RAES checkout, private modules, concrete upstream backends, copied schemas, and
path or VCS dependency overrides are rejected by repository policy.

Reference behavior in this repository never changes the meaning of a RAES
contract. Contract or protocol changes belong upstream in RAES and reach LilRAE
through a reviewed release-pin update.

## Backend execution boundary

The baseline has no backend implementation, runtime service, listener,
subprocess, container, credential reader, environment schema, cache, database,
or persistent state. A future backend will compose at the application boundary
against the published RAES backend protocol.

That future boundary owns concrete host effects, runtime security, readiness,
rollback, teardown, native diagnostics, and redaction. Portable results remain
RAES-owned closed models; native exceptions, logs, environment values, and
credentials must not cross into them.

## Develop

Prerequisites:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Git

Set up the locked environment and inspect the command:

```shell
uv sync --frozen
uv run lilrae --help
uv run lilrae --version
```

Run the complete repository gate:

```shell
make verify
```

The same nox graph drives local checks, hooks, Ground Control, CI, artifact
validation, and release readiness. It builds an sdist, builds a wheel from that
sdist, installs the exact wheel outside the source checkout, and probes the
installed import, metadata, help, and version surfaces.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and
[SUPPORT.md](SUPPORT.md) before opening a change or report.
