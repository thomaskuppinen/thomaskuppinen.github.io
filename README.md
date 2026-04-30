# Matt Kuppinen Website

Static site for Matt Kuppinen, built to work well with GitHub Pages.

## Local Preview

Do not open `index.html` directly with a `file://` URL. The YouTube embed can fail with `Error 153` when the page is not served from a real web server.

Run the site locally with Python:

```bash
cd /Users/tkuppinen/Documents/git/website
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080/index.html
```

You can also deploy the site to GitHub Pages. Serving it from GitHub Pages provides the HTTP referrer YouTube expects, so the embedded video works there too.

## News Feed Data

The two article sections on the page are driven by:

```text
data/news.json
```

That file is loaded by the page at runtime and is the source of truth for:

- `Popular posts and game reports`
- `News`

If `data/news.json` cannot be loaded, the page still keeps its built-in HTML fallback content.

## Refresh News Manually

To refresh the article summaries from the linked MaxPreps and Prep Hoops pages:

```bash
cd /Users/tkuppinen/Documents/git/website
python3 scripts/refresh_news.py
```

This script:

- fetches the live article HTML
- extracts the first 25 words of the first usable article text
- rewrites `data/news.json`

After running it, review the updated JSON and then commit the change if it looks good.

## Automated Refresh

GitHub Actions is configured at:

```text
.github/workflows/refresh-news.yml
```

That workflow can:

- run manually with `workflow_dispatch`
- run automatically every week

When the fetched summaries change, the workflow commits the updated `data/news.json` back to the repository.

## Notes

- The refresh script depends on live network access to MaxPreps and Prep Hoops.
- If either site changes its HTML structure, the extractor in `scripts/refresh_news.py` may need a small update.
- The YouTube embed and X embeds behave best when the site is served over `http://` or `https://`, not opened directly from disk.
