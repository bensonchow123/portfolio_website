"""
Render the resume PDF once, at build time.
`python -m scripts.build_pdf`, from the repo root so `app` imports.
"""
import os

import weasyprint
from flask import render_template

from app import PDF_DIR, PDF_NAME, app, get_static_file, get_static_json, order_projects_by_weight

# resume_body.html builds absolute links with _external=True, so the host is
# baked in here rather than read off a request. Override when the site moves.
SITE_URL = os.getenv("SITE_URL", "https://bensonc.how")


def render():
    """Return the PDF bytes for the print-only template."""
    projects = get_static_json("static/projects/projects.json")['projects']
    projects.sort(key=order_projects_by_weight, reverse=True)

    # A request context, not a bare Jinja environment, because the template
    # calls url_for.
    with app.test_request_context(base_url=SITE_URL):
        html = render_template('resume_pdf.html', featured_projects=projects[:6])

    # base_url is a filesystem path, which is what resolves the stylesheet's
    # relative href off disk.
    return weasyprint.HTML(string=html, base_url=get_static_file('')).write_pdf()


def main():
    out_dir = get_static_file(PDF_DIR)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, PDF_NAME)

    with open(out_path, 'wb') as handle:
        handle.write(render())

    print("wrote %s (%d bytes)" % (out_path, os.path.getsize(out_path)))


if __name__ == '__main__':
    main()
