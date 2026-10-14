# Solstice GXP oil-control project site

Static HTML/CSS/JS, hosted by GitHub Pages. The public site includes three concept videos, prototype STEP/DXF/GLB downloads, editable CAD source, fabrication/measurement notes and sixteen manufacturer reference links.

The `dist/` directory is the published edition. Pushes to `main` automatically deploy it with GitHub Actions. The open page checks for a new edition every minute and when returning to the tab, then offers a **Load update** button. A refresh never interrupts reading or video automatically.

To update from the local CAD project, run `python3 site/publish.py` from the parent workspace. The exporter verifies the accepted, packaged candidate before copying the curated files. It does not regenerate CAD or publish unreviewed changes. Complete the project checks/review/package first when CAD or project evidence changes. GitHub does not read the local workspace by itself; the update command publishes the accepted edition.

`build.py` and `publish.py` are workspace-side helpers. They require the full local project as the parent directory; a standalone GitHub clone can edit the public `dist/` files and push them directly.

The public ZIP preserves STEP/DXF/BOM directory relationships and contains editable source and animation sidecars. It is a curated export, not the complete local evidence/validation workspace. Local paths, private review logs and third-party downloaded source archives are not published. Manufacturer reference links retain source attribution.

All models are nominal prototypes. Pan/pickup/mount geometry and physical performance remain unverified. No order, fabrication release or engine-use acceptance is implied.
