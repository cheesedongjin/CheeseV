# Contributing Guide

Thank you for your interest in contributing! Before you start, please be aware of several restrictions defined in `AGENTS.md`.

## Repository Restrictions

- **Protected files** — `AGENTS.md` and `README.md` must never be modified.
- **Owner-managed content** — Everything inside `content/` is maintained manually by the project owner. Do not add to or edit files in this directory.
- **Auto-generated output** — The `docs/` directory is produced by scripts. Generated files should not be committed. If running the site generator changes files here, revert them before committing.

## Generating the Site Locally

Use Python 3 and run:

```bash
python generate_site.py
```

This command reads from `content/` and writes HTML to `docs/`. Review the output locally but keep those changes out of commits.

## Continuous Deployment

GitHub Actions runs the same script on every push to the `main` branch. The workflow in `.github/workflows/build.yml` builds the site and deploys it to GitHub Pages. Local changes to templates or scripts will be reflected once the action completes.
