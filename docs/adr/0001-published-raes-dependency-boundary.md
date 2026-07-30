# ADR 0001: Consume RAES only as a published dependency

- Status: Accepted
- Date: 2026-07-30
- Requirement: LILRAE-001

## Context

LilRAE is a downstream, non-normative implementation. A checkout of RAES is
therefore not an input to LilRAE's build or runtime, and RAES internals are not
LilRAE contracts. Allowing either would make unreleased source state a second
source of authority and would make clean builds differ from developer builds.

The repository is initially empty. There are no existing application schemas,
validators, exception types, logging facilities, or persistence abstractions to
extend. The existing workflow contract names `make policy` as the repository
policy entrypoint and `pre-commit run --all-files` as the local policy surface.

## Decision

LilRAE has exactly one RAES integration boundary: an installed, released
distribution consumed through interfaces that RAES documents as public.

The canonical project dependency manifest and its resolver-produced lock data
are the only sources of dependency truth. They must identify RAES using the
package ecosystem's normalized distribution identity and an allowed package
registry. Local paths, editable/workspace references, source-tree URLs, and VCS
references are forbidden even when they resolve to a tagged commit. A different
registry may be admitted only as an explicit repository policy change; developer
machine configuration must not silently weaken the rule.

RAES distribution identity, allowed registry source classes, and documented
public import roots belong in one versioned policy declaration. Manifest,
lockfile, import, and path checks must consume that declaration. The exact names
must be copied from released RAES metadata and public documentation when the
dependency is introduced; they must not be inferred from a checkout or repeated
as independent allowlists in several scripts.

First-party production code, tests, examples, executable documentation, build
and release tooling, and dependency metadata are all inside the boundary.
Generated and vendored content may be excluded only by explicit, narrow,
version-controlled paths. Tests and examples do not receive a source-checkout
exception.

The repository policy must reject:

- imports or dynamic loads below a RAES module that is not in the declared
  public surface, including private or internal modules regardless of whether
  their names use an underscore convention;
- import-by-file, source checkout discovery, or mutation of module search paths
  to locate RAES, including runtime path insertion and repository-relative
  `PYTHONPATH` setup;
- direct or resolved RAES dependencies whose source kind is local path,
  editable/workspace, VCS, or another source-tree mechanism; and
- configuration, scripts, fixtures, or CI setup that make a neighboring RAES
  checkout part of build, test, or runtime behavior.

Policy is a deterministic, offline, read-only verification operation. It parses
structured manifests, lock data, and source imports with the ecosystem's
canonical parsers where available. Text matching may supplement those parsers
for shell, CI, and environment configuration, but must not be the sole import or
dependency validator. Unknown or unparsable dependency source forms fail closed.

`make policy` is the single human and automation entrypoint. Pre-commit, CI, the
clean source-build verification command, and release readiness checks invoke
that entrypoint rather than reimplementing the rules. A clean build and smoke
test exercise the installed LilRAE artifact in an isolated environment, not an
import from the working tree.

## Cross-cutting guardrails

### Security and information exposure

- Dependency and lockfile shape validation happens before source classification;
  malformed input is a policy failure, not an ignored record.
- Registry credentials remain package-manager or CI secret inputs. Policy
  configuration stores source classes or sanitized origins, never credentials,
  and policy operation must not require secrets or network access.
- No token, credential-bearing URL, or secret value may be placed in process
  arguments, diagnostics, snapshots, or logs. Diagnostics report the repository
  path, rule identifier, and a normalized dependency/source kind; URLs are
  stripped of user information, query strings, and fragments.
- Environment bindings may select credentials for the package manager but may
  not select a weaker policy mode, add a RAES source path, or override the
  version-controlled RAES identity.
- Policy must be independent of the caller's current directory and ambient
  module search path. It must neither execute inspected project files nor import
  RAES to discover its API.

There is no application authentication, persistence, controller/service/DTO
layer, runtime error envelope, or observability pipeline in scope yet. Policy
failures use the repository's eventual common command diagnostic convention;
they do not create an application exception hierarchy or runtime logging
abstraction. If machine-readable diagnostics are later needed, they are another
renderer over the same findings, not a second validator.

### Maintainability and consistency

The dependency manifest and generated lockfile remain canonical for versions and
resolution. The single policy declaration is canonical for the RAES identity
and public-surface boundary. The single policy command is canonical for
orchestration. Package-manager validation, source-language parsing, existing
repository lint configuration, and existing diagnostic helpers must be reused
once chosen; parallel schemas, import scanners, exception trees, and CI-only
copies of the policy are prohibited.

Checks should emit stable rule identifiers so local, pre-commit, and CI output
refer to the same failure without coupling tests to prose. Positive fixtures
cover a registry release and public import; negative fixtures cover each
forbidden source and import form, aliases and multiline imports, dynamic/file
loads, path mutation, configuration indirection, and sanitized diagnostics.

### Extensibility

The deliberate seam is policy data, not validator branching: distribution
identity, public import roots, accepted published source classes, and narrow
scan exclusions are versioned inputs to shared checks. This permits a future
RAES package rename, public subpackage addition, or approved registry migration
to be reviewed as a boundary change without editing every validator. It must not
be exposed as an unchecked environment or command-line bypass.

## Consequences

Developer workflows cannot use an adjacent RAES checkout for convenience.
Changes requiring unreleased RAES behavior wait for a RAES release. Boundary
violations fail before build or release, and the same rules apply to production
code, tests, examples, and tooling.

This decision establishes dependency provenance and API visibility only. It
does not claim RAES conformance, copy RAES schemas into LilRAE, make RAES
normative through LilRAE, define backend behavior, or select package/CLI
identities beyond the RAES boundary.

## Anti-patterns

- A regex-only import checker or a filename-prefix heuristic for “private.”
- Separate hard-coded RAES names in manifest, lock, import, and CI checks.
- Importing RAES at policy time and treating whatever a local installation
  exports as the public contract.
- Allowing tagged Git commits, GitHub release source archives, editable installs,
  workspace links, or test-only path dependencies as equivalent to a published
  package dependency.
- Mutating `sys.path`, `PYTHONPATH`, loader paths, or the working directory to
  make a source checkout importable.
- Skipping tests, examples, documentation snippets, build hooks, or lockfiles
  because they are “not production.”
- A CI workflow that duplicates or weakens `make policy`, or a local override
  that turns violations into warnings.
- Printing raw dependency URLs or environment values in failure output.
