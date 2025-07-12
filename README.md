# CheeseV Developer Portfolio

This repository contains a minimal Python-based static site generator designed for GitHub Pages. It can render blog posts and program descriptions written in Markdown into a simple portfolio website.

## Usage

1. Place blog posts in `content/posts/` and program descriptions in `content/programs/`.
2. Run `python generate_site.py` to render the site into the `output/` directory. Generated pages include `posts/index.html` and `programs/index.html` for easy navigation.
3. Commit the contents of `output/` to a `gh-pages` branch or configure GitHub Pages to serve from that directory.

The generator script does not require external dependencies and provides a basic Markdown implementation for headings, paragraphs and lists.
