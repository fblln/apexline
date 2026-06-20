# Changelog

## Unreleased

- Made lap-shape thresholds proportional to oracle circuit length and removed
  missing lap time as a rejection reason.
- Regenerated the complete 2025 race-session dataset and static evidence.
- Consolidated season artifacts under `data/<year>/all-events/<session>/`.
- Added effective-threshold provenance, gallery ordering, and custom output
  directory support.
- Added a machine-readable rejected-gallery schema.

## 0.1.0

- Split Apexline into a standalone package.
- Added single-session validation as the primary CLI workflow.
- Added batch validation, schema checking, fixture demo artifacts, and run manifests.
- Added static showcase documentation and checked-in 2025 example artifacts.
