# farach-colton.com

Personal academic website, served by GitHub Pages at https://www.farach-colton.com.

- `index.html` — home page (edit directly)
- `publications.html` — generated; don't edit by hand
- `style.css` — shared styles
- `cv.pdf` — compiled from the Overleaf CV

To refresh the publication list from the CV:

    cp ~/Overleaf/CV/paper.tdb data/paper.tdb
    python3 tools/build_pubs.py
