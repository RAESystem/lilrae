# Project governance

LilRAE is a maintainer-led open source project. The maintainer decides scope,
accepts changes, manages releases, and protects the downstream boundary with
RAES.

RAES remains authoritative for portable semantics, schemas, contracts,
protocols, diagnostics, and conformance. LilRAE owns only concrete reference
realization and its host/runtime boundary. Architecture decisions in this
repository may constrain LilRAE but cannot redefine RAES.

Pull requests target `dev`. Reviewed promotion moves `dev` to `main`. Release
Please owns version and changelog state on `main`; release changes return to
`dev` through review. A Release Please pull request is not merged while the
repository contains only the backend-empty baseline.

Material architecture and governance decisions are recorded under
[`docs/adr/`](docs/adr/). See [CONTRIBUTING.md](CONTRIBUTING.md) for the working
process and [MAINTAINERS.md](MAINTAINERS.md) for current ownership.
