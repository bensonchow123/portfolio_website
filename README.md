# bensonc.how

Personal site: about me, projects, listening stats and résumé. Flask + Jinja2,
server rendered, Gunicorn on `:8080`. This repo is only the site image. Nginx
and the scrobble_vault the music page reads are each their own repo, and
production is the infrastructure repo running the published image.

```bash
docker compose pull && docker compose up -d     # published image, no host port
docker compose -f docker-compose.dev.yaml up    # dev, http://127.0.0.1:5500
```

Without containers, install `requirements-dev.txt`, then `python -m
scripts.build_pdf` for the résumé and `python app.py` to serve. Build scripts
run as modules from the repo root, that is what keeps `from app import` working
from inside `scripts/`. `tailwind.css` is committed so a
clone runs without Node. Rebuild with `npm run build:css`, never leaving a
session on `watch:css`, which writes unminified output.

## Adding images

Everything is AVIF in a width ladder that `srcset()` in `app.py` finds by
reading the directory. Drop a source in `static/images` or
`static/projects/<project>/` and run:

```bash
npm run build:images        # --force re-encodes, --prune deletes the sources
```

ffmpeg is the only image dependency and reads anything, AVIF included. Backdrops
get 768/1280/1920 plus full source width, photos get 400/800 capped at 1200.
Name files plainly, `name-<digits>` is reserved for the generated variants.
Project photos also need their path in `projects.json`, pointing at the `.avif`
with no width suffix. Restart after, the widths are cached per process.
`benson-chow.jpg` stays a JPEG because it is the `og:image`.

## Notes

Tailwind v4 is configured in `assets/app.css` alone and scans templates literally,
so never build a class name by concatenation in Jinja. No custom CSS except
`resume.css`, which the WeasyPrint PDF needs. Only two JS files exist and it
should stay that way. Environment is all optional, see `.env.example`, though
`PROXY_FIX_HOPS` breaks rate limiting when it is too low. Only a `v1.2.3` tag
publishes to ghcr.io.
