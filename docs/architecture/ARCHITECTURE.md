# LilRAE architecture

LilRAE is the complete personal and local RAES backend. It remains downstream
and non-normative: the current repository establishes the engineering and
migration landing zone and intentionally contains no backend yet.

## Authority boundary

RAES owns portable contracts, schemas, semantic validation, backend protocols,
diagnostics, and conformance. LilRAE consumes the exact released RAES
distribution and the public import surfaces declared in repository policy.
LilRAE does not copy, wrap, or reinterpret those authorities.

## Product and migration boundary

LilRAE is generalized and migrated from `Brad-Edwards/aptl` with useful source
history intact. Scenario-agnostic realization, lifecycle, readiness, evidence,
recovery, safety, and packaging behavior belong in LilRAE. TechVault-specific
packs, verification plugins, scenario MCPs, and research apparatus remain
experience-owned integrations outside the backend core.

APTL is therefore an advanced TechVault experience on LilRAE, not a third
backend. BigRAE is the separate organizational/SaaS product migrated from
Shifter. LilRAE does not absorb BigRAE responsibilities such as multitenancy,
centralized organizational policy, billing, or managed service operations.

## Current package boundary

The `lilrae` distribution contains one import package and one console command.
They expose installed metadata, help, and version only. There is no backend
module, service layer, transport, configuration framework, persistence,
authentication, logging framework, or plugin registry.

## Future composition seam

The migrated backend composes at the application or CLI root against a published
RAES backend protocol. Concrete runtime values and native exceptions stay
behind that seam; portable outputs use RAES-owned closed models and diagnostics.

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
