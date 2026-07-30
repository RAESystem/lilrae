# Issue 2 repository-baseline architecture guardrails

Status: pre-implementation guidance

Scope: repository, release, and migration-landing-zone baseline only

## Existing authorities and preflight state

The repository has no application, package, CI, release, controller, DTO,
service, repository, exception, logging, or persistence implementation to
extend. The incumbents that do exist are:

- `.ground-control.yaml` for project `lilrae`, repository
  `RAESystem/lilrae`, base branch `dev`, `make policy`, and the pre-commit
  entrypoint;
- ADR 0001 for the released-only RAES dependency and public-contract boundary;
- the published RAES contracts for future portable schemas, validation,
  protocols, diagnostics, and conformance behavior.

At preflight, GitHub reports `dev` as the default branch and exposes `dev` and
the issue branch; `main` does not yet exist. Repository protection/ruleset state
has not been established by files in this checkout and must not be reported as
satisfied without service-side evidence. Developer-local environment and tool
connector files are not product configuration, identity authorities, or release
inputs.

The product direction was clarified before this baseline merged: LilRAE is the
complete personal/local backend generalized and migrated from
`Brad-Edwards/aptl`, while BigRAE is the organizational/SaaS backend migrated
from Shifter. APTL's TechVault packs, plugins, scenario MCPs, and research
apparatus remain an advanced experience on LilRAE rather than becoming backend
core. Issue 2 still adds no execution behavior; it establishes the
Python-3.11-compatible landing zone for that history-preserving migration.

## Decisions

### Identity is a hard, single-name cut

LilRAE has exactly one identity on each public surface:

| Surface | Identity |
| --- | --- |
| GitHub repository | `RAESystem/lilrae` |
| Python distribution | `lilrae` |
| Python import package | `lilrae` |
| Console command | `lilrae` |
| Ground Control project | `lilrae` |
| Release Please component/package | `lilrae` |
| Release tag | `vX.Y.Z` |

SonarCloud imposes its own organization/project-key syntax. Those exact
service-side values must be confirmed during provisioning and recorded once in
the checked configuration and the project-services policy check; an
implementation must not guess a key from the repository name and then accept a
second fallback. “Consistent identity” means one checked one-to-one mapping
across these platform-specific forms, not a new universal identity DTO and not
necessarily byte-identical strings on every service.

There are no compatibility distributions, import packages, console-script
aliases, forwarding modules, or dual-read configuration names. Package version
has one runtime/package authority in `pyproject.toml`;
`.release-please-manifest.json` is synchronized release-orchestration state, not
an application version API. Release Please owns updates to both, and policy
checks their equality. `lilrae.__version__` and `lilrae --version` derive from
installed distribution metadata rather than becoming further version
authorities.

### RAES is upstream authority; LilRAE is non-normative

LilRAE is a downstream implementation. The current ecosystem contract baseline
is the exact released `raes==3.0.0` distribution from the public package index
and its public contract surfaces, principally `raes_contracts`,
`raes_backend_protocols`, and `raes_conformance`. A future RAES upgrade is one
reviewed dependency-pin and lock change exercised by the full verification
graph, not an ambient range upgrade. LilRAE does not import from a sibling
checkout, a Git/path dependency, RAES's `implementations/python` tree, a private
module path, the reference backend, backend stubs, or a concrete upstream
backend.
APTL is a migration source whose relevant history and implementation will move
into this repository; it is not a path, VCS, build-time, or runtime dependency.

RAES continues to own:

- portable DTOs, schemas, identifiers, enums, and semantic validation;
- backend protocols, diagnostic/result envelopes, and conformance machinery;
- runtime authentication, authorization, request limits, redaction, and
  persistence boundaries when those facilities are needed.

LilRAE must not copy, wrap, loosen, or independently reinterpret those
authorities. In particular, it must not create a second schema bundle, parser,
validation result, exception hierarchy, backend protocol, conformance profile,
fixture corpus, manifest format, concept catalog, or portable logging envelope.
Published schemas are resolved through the installed RAES resource APIs, never
by navigating an upstream source tree.

The initial distribution may expose import, version, help, and version-smoke
surfaces. It must not advertise a backend module, backend extra, execution
command, success result, capability declaration, or conformance claim until
real backend behavior exists.

### The backend execution boundary remains empty

Issue 2 establishes engineering infrastructure, not execution. It adds no
subprocess, container, VM, network listener, credential reader, environment
binding, cache, database, control-plane service, or persistent state.

The APTL backend migration must compose at the application/CLI composition root
against the published RAES backend protocol. That composition point is the
extension seam. Do not pre-build a parallel abstract base class, backend
registry, service locator, placeholder implementation, or generic plugin
system. Backend-native values and exceptions stay behind that boundary;
portable results pass through RAES-owned closed models and diagnostics.

`SECURITY.md` and `SUPPORT.md` must name this boundary explicitly: the baseline
does not execute a backend, while migrated backend execution is where untrusted
input, host effects, credentials, process arguments, native logs, and error
redaction become security-relevant.

### Verification has one authority

One repository-owned verification graph is authoritative for local development,
hooks, Ground Control, CI, and release validation. The selected authority is a
root `noxfile.py` invoked through pinned `nox[uv]`; `make verify` and
`.ground-control.yaml` are thin callers, not alternate test definitions. CI may
run graph stages in parallel. A `pull_request_target` workflow loaded from the
protected base branch validates PR metadata without checking out PR content,
authenticates the exact Release Please route, and aggregates the named Python
3.11 Verify, Python 3.12 Verify, and Sonar results into the required `PR Gate`.

The graph must cover:

- file hygiene and secret/private-key detection;
- formatting, linting (including security rules), and strict type checking;
- repository-policy tool tests and package tests with branch coverage;
- exact-lock validation;
- wheel and sdist build;
- clean wheel installation outside the checkout with `PYTHONPATH` cleared and
  safe-path behavior enabled;
- installed import, metadata version, and `lilrae --help`/`--version` smoke;
- strict documentation build if documentation tooling is included.

The artifact path is build once, inspect, then test that exact output: build the
sdist, build the wheel from the sdist so missing source files are observable,
inspect both for expected metadata/content and forbidden material, and install
the resulting wheel by explicit path. The smoke must not rebuild, perform an
editable install, or silently resolve a different local artifact. Dependency
installation remains lock-governed; the artifact probe must not turn into an
uncontrolled network-resolution path.

The clean-install probe, not an editable install, is the package smoke
authority. Distribution, import, CLI, and version identifiers should be
parameters/constants in that one probe/session so a future executable smoke
extends the existing boundary instead of creating a second build path.
The probe runs from a bounded temporary directory outside the checkout, clears
`PYTHONPATH`, enables safe-path/isolation behavior, and asserts that no import
origin or `sys.path` entry points at the checkout. SonarCloud consumes the
coverage and analysis outputs of canonical graph sessions; it does not rerun a
different test suite with different options.

### Repository policy is fail-closed and structured

The existing ecosystem convention is one `policy` session containing small,
tested checks. Issue 2 needs one repository-policy owner, not separate scanners
for CI, hooks, and release.

That owner must structurally inspect Python imports and package configuration
and reject at least:

- any private segment beneath an upstream RAES package;
- `raes_reference_backend`, `raes_backend_stubs`, concrete upstream backend
  packages, or imports addressed through RAES repository layout;
- `sys.path`/`PYTHONPATH` manipulation used to make a sibling checkout
  importable;
- path, editable, Git, direct-URL, or workspace source overrides for the
  `raes` distribution;
- copied RAES schemas/contracts or checkout-relative resource discovery.

The dependency check must parse `pyproject.toml` and the lock rather than rely
only on source-text matching, and must prove the locked RAES artifact comes from
the configured package registry. The import check should use Python's AST so
aliases and multiline imports cannot evade it. Narrow text checks may cover
non-Python configuration, but there must be no broad allowlist or generated-file
exemption. Policy tests must include negative fixtures for every forbidden
class.

Repository-service identity checks belong in the same policy boundary. One
project-services check should keep GitHub, Ground Control, SonarCloud, Release
Please, package metadata, and maintainer documentation consistent. Externally
provisioned identifiers must be confirmed rather than inferred from prose.
This check parses each native format and compares a single expected mapping; it
does not introduce a second configuration manifest or mirror the full schemas
owned by packaging, Ground Control, Release Please, GitHub, or SonarCloud.

### Promotion and release are separate trust boundaries

Feature pull requests target protected `dev`. Only a reviewed `dev` to `main`
promotion advances production history, and it preserves the Conventional
Commit subjects Release Please uses. Release commits return to `dev` through a
normal reviewed back-merge pull request; automation never force-pushes or
silently merges a protected branch.

Branch protection/rulesets enforce pull requests, reviews, required checks,
up-to-date heads, no deletion, and no force-push, but the promotion source rule
also needs a stable required policy check: a pull request whose base is `main`
fails unless its same-repository head is exactly `dev`. It reads the event
payload as data and never checks out or executes the head to make that decision.
Do not use `pull_request_target` to run untrusted code. The allowed flow is not
encoded twice in unrelated workflows; the aggregate gate consumes the one
policy result.

Release Please is the sole version/changelog authority. Feature work does not
hand-edit `CHANGELOG.md`, version literals, tags, or release notes. Actions are
full-SHA pinned, workflows have read-only top-level permissions, untrusted PR
metadata is read from the event payload rather than interpolated into shell,
and write permissions are job-local.

Issue 2 may make Release Please configuration and artifact verification ready,
but it must not configure or perform public package publication for a
placeholder backend. Local wheel/sdist build and clean-install validation are
required. PyPI OIDC Trusted Publishing, a publish job, post-index smoke, and any
backend-bearing first release remain gated on real backend behavior and an
explicit publication decision. No stored package-index token is introduced.
Release Please itself creates a tag and GitHub Release after its release PR is
merged; merging that PR is therefore a separate, explicit release authorization
and must not happen for the empty backend baseline. Merely keeping the Release
Please PR/configuration ready is not authorization to release.

Repository files alone do not activate branch protection, required checks,
SonarCloud assignment, GitHub environments, or trusted publishing. Service-side
settings are separate acceptance evidence and must match the checked-in
identities. Protected `main` and `dev` should require an up-to-date pull request,
dismiss stale approvals, prohibit deletion/force-push, and require the stable
gate names. SonarCloud must pass for same-repository pull requests; fork pull
requests must not receive its secret and must follow an explicit fail-safe skip
policy in the aggregate gate.

## Cross-cutting path

The baseline crosses these layers:

| Layer | Required behavior |
| --- | --- |
| Package/config shape | `pyproject.toml`, lock, Release Please manifest, and project-service identifiers agree; RAES is an exact registry dependency with no source override. |
| Import/resource validation | AST policy admits public installed RAES contracts and rejects private, reference-backend, concrete-backend, and checkout-layout imports; resources resolve from installed packages. |
| Auth and secrets | No product auth surface exists. Local secret files stay ignored; workflow secrets are job-scoped and never echoed or exposed to fork code. |
| Build/supply chain | Native packaging and lock parsers validate shape before policy classification; exact locked build tools create one artifact set, actions use immutable SHAs, and the release path tests rather than rebuilds those artifacts. |
| Environment and OS | No runtime env schema or backend process exists. Verification uses argument vectors rather than shell composition, bounded temporary directories, a clean environment, no checkout-derived `PYTHONPATH`, and no credential in process arguments. |
| Errors and observability | Baseline CLI/policy failures are concise, deterministic, and input-free. No payloads, environment dumps, tokens, native object representations, or tracebacks become portable output. Future backend failures use RAES diagnostics/results. |
| Persistence | None. Do not add a cache, database, registry, migration, or audit store for the baseline. Future durable runtime state reuses the RAES control-plane persistence boundary where applicable. |
| Workflow/release | The nox graph is canonical; hooks, Ground Control, CI, SonarCloud, branch protection, and Release Please call or gate that graph without reimplementing it. |

Native validators remain authoritative at every shape boundary:
`pyproject.toml` and the resolver lock use packaging/lock tooling;
Release Please config/manifest use Release Please's schema; Ground Control
config uses Ground Control's consumer/schema; workflows use GitHub Actions
workflow/security validation; and Sonar properties use Sonar's scanner
configuration. The repository policy adds only cross-file invariants after
those shape checks. It never copies their complete schemas into local DTOs.
Service-side GitHub rules and Sonar assignment are verified by a separate
read-only provisioning audit/evidence step so the offline verification graph
does not gain network credentials.

The extensibility seams are data at two existing boundaries: named nox session
parameters for artifact/identity probes, and the tested expected-identity/public
RAES-surface policy declarations. A future real backend adds one installed-wheel
execution smoke and one composition-root implementation against the RAES
protocol; it must not require a second build graph, identity schema, validator,
or workflow.

## Gotchas and prohibited conflations

- Cross-service identity consistency is a mapping invariant, not a reason to
  make every service accept one raw string or to add a universal project DTO.
- A successfully built skeleton is not a backend, and an import smoke is not a
  conformance or execution claim.
- APTL is a migration source and advanced TechVault experience, not a third
  backend or a checkout-relative runtime dependency.
- A GitHub Release is not the same boundary as PyPI publication; neither should
  be used to smuggle out a placeholder backend.
- A Release Please manifest is release state, not a second runtime version API;
  divergence from package metadata is a policy failure.
- A published Python package is not permission to import every module it ships.
  Contract/protocol surfaces and reference/concrete implementations have
  different authority.
- Structural schema validation, semantic RAES validation, backend realization,
  and conformance are distinct stages. Do not merge them into one local
  `validate()` function or accept an untyped dictionary between them.
- CLI errors, logs, portable diagnostics, and native backend exceptions are
  different surfaces. Do not make one exception class or serialized envelope
  serve all four.
- Branch-workflow files do not prove branch protection or external service
  provisioning. Capture service-side evidence separately.
- Protecting `main` does not by itself prove that only `dev` can promote to it;
  the source-branch invariant must be a stable required check.
- Do not duplicate the verification command in Make, hooks, CI, Ground Control,
  and release YAML. Those surfaces delegate to named sessions.
- Do not make SonarCloud a best-effort informational check for trusted pull
  requests, and do not expose `SONAR_TOKEN` to fork code.
- Do not introduce a second changelog tool, dynamic version source, backend
  registry, configuration framework, logging framework, or persistence layer
  “for later.”

## Non-goals and boundaries

- No backend behavior, extraction, adapter logic, executor, transport, or
  runtime service.
- No claim of RAES conformance, compatibility, reproducibility, replay,
  equivalence, or scientific validity.
- No new RAES concept, schema, DTO, validation rule, protocol, diagnostic,
  profile, fixture, or policy authority.
- No compatibility aliases or migration layer.
- No public package-index publication or placeholder backend release.
- No authentication, secret loading, runtime configuration schema, network
  listener, subprocess/container execution, persistence, telemetry, or
  operational logging.
- No abstraction for hypothetical multiple backends; reuse the published RAES
  protocol at the composition root when the first real backend arrives.
