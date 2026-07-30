# LilRAE architecture

LilRAE is a downstream, non-normative RAES implementation. The current
repository establishes engineering infrastructure and intentionally contains no
backend.

## Authority boundary

RAES owns portable contracts, schemas, semantic validation, backend protocols,
diagnostics, and conformance. LilRAE consumes the exact released RAES
distribution and the public import surfaces declared in repository policy.
LilRAE does not copy, wrap, or reinterpret those authorities.

## Current package boundary

The `lilrae` distribution contains one import package and one console command.
They expose installed metadata, help, and version only. There is no backend
module, service layer, transport, configuration framework, persistence,
authentication, logging framework, or plugin registry.

## Future composition seam

The first real backend composes at the application or CLI root against a
published RAES backend protocol. Concrete runtime values and native exceptions
stay behind that seam; portable outputs use RAES-owned closed models and
diagnostics.

The existing clean-wheel smoke will grow one real execution probe when that
backend exists. It must not be replaced by a second build or verification path.

## Verification and release

The root nox graph is authoritative. Make, hooks, Ground Control, CI, artifact
inspection, and release readiness delegate to named sessions. Feature pull
requests target `dev`; reviewed promotion reaches `main`; Release Please owns
version/changelog state; release commits return through a reviewed back-merge.
Pull-request route, title, and aggregate-check decisions execute only from the
protected base branch and never load policy code from the PR they judge.

Public package-index publication is not configured while the backend boundary
is empty.
