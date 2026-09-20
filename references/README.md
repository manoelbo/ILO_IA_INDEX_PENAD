# Reference library

Zotero is the source of truth for bibliographic metadata and attachments. The
portable workspace copy uses the same citation key in three places:

- the entry key in `library.bib`;
- the PDF filename in `pdfs/`;
- the row key in `pdf_manifest.tsv` and `PDF_INDEX.md`.

For example, `chandar_tracking_2025` maps directly to
`pdfs/chandar_tracking_2025.pdf`.

## Refresh workflow

1. Export the Zotero collection to `references/library.bib` using BibLaTeX.
2. Run:

   ```bash
   node src/scripts/sync_reference_pdfs.mjs
   ```

3. Confirm that the command reports no missing PDF sources.

The script copies new or changed PDFs, rewrites each BibLaTeX PDF attachment to
a portable path relative to `references/library.bib`, and regenerates the index
and checksum manifest. Bibliographic sources that do not normally have a PDF,
such as legislation and official web pages, remain valid entries without a
`file` field. Existing orphan files are reported but never deleted.

Do not edit `PDF_INDEX.md` or `pdf_manifest.tsv` manually; both are generated.
