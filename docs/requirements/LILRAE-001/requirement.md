---
id: LILRAE-001
title: "Enforce the published RAES dependency boundary"
status: DRAFT
type: CONSTRAINT
priority: MUST
wave: 1
created_at: 2026-07-30T03:41:37.660288Z
updated_at: 2026-07-30T03:41:37.660288Z
---

# LILRAE-001 — Enforce the published RAES dependency boundary

## Statement

LilRAE SHALL consume RAES only through published distribution dependencies and public import surfaces. Repository policy SHALL reject imports of private RAES modules, RAES source-tree path manipulation, local path dependencies on RAES, and VCS dependencies that bypass released RAES artifacts.

## Rationale

LilRAE is a downstream, non-normative reference backend. Enforcing a released-artifact boundary prevents source-tree coupling and a silent second source of RAES authority.
