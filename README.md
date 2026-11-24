# drkunfeng.github.io

Personal academic website of Dr Kun Feng, served by GitHub Pages at https://drkunfeng.github.io.

## Pages

- `index.html`: home (about, research, contact)
- `publications.html`: full publication list, generated from Scopus
- `projects.html`: funded research projects
- `teaching.html`: teaching and service
- `assets/style.css`: shared styles

## Updating the publication list

1. In Scopus, open the author profile, select all documents and export them as RIS.
2. Save the export as `data/scopus.ris`.
3. Run `python3 tools/build_publications.py` from the repository root.
4. Commit and push.
