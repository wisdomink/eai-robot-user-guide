# Product Manual Import Workflow

Use this workflow for a new product and whenever its DOCX source changes.

## 1. Add and assess the DOCX source

Place the source file in `input/`. Before importing, confirm the manual can be published: product name and model, safety/compliance text, warranty terms, final specifications, and image rights must all be approved.

## 2. Create or update the import configuration

Create `scripts/manuals/<product-id>.json`, using `scripts/manuals/aegis-max.json` as the template. It defines the source path, output pages, chapter boundaries, home-page review notice, figure handling, and repeatable editorial replacements.

## 3. Generate Markdown

Preview the update first:

```bash
cd apps/web
npm run manual:import -- --config scripts/manuals/<product-id>.json --dry-run
```

Then write the generated Markdown:

```bash
npm run manual:import -- --config scripts/manuals/<product-id>.json
```

The importer converts paragraphs, lists, tables and embedded DOCX images. Images are written to `public/images/<product-id>/` and inserted in the matching Markdown position. It removes only stale files with the matching `<product-id>-figure-` prefix when a DOCX update contains fewer images. Add semantic image alt text under `images.altText` in the product configuration before publication.

## 4. Editorial review

Review the generated pages for terminology, specification conflicts, placeholders, table formatting, image order, image alt text and links. Keep repeatable editorial corrections in the configuration's `replacements` list; reapply non-repeatable edits after importing.

## 5. Register the product in the sidebar

Add the product block to `src/content/sidebar.json` directly after the product that should precede it. The first page must be its home page. Product selection, search indexing, routes and static generation are derived from this file, so no separate product registry needs editing.

## 6. Optional download configuration

Only after an approved PDF is available, add its ID to `DOWNLOADABLE_PRODUCT_IDS` in `src/hooks/useProductContext.tsx` and its URL to `DEFAULT_MANUAL_DOWNLOAD_URLS` in `src/api/manualDownloadConfig.ts`.

## 7. Validate

```bash
cd apps/web
npm run build
git diff --check
```

Confirm the generated routes, navigation order, search results, mobile sidebar, tables and all added images before release.
