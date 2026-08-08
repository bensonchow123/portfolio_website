import io
import json
import os
from urllib.parse import urlparse, urlunparse
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

import music as music_data

load_dotenv()

app = Flask(__name__)

# Off unless RATELIMIT_STORAGE_URI points at a shared store. Per-worker counters
# and a memory:// backend that resets on restart would not mean anything.
_storage_uri = os.getenv("RATELIMIT_STORAGE_URI")
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120 per minute"] if _storage_uri else [],
    storage_uri=_storage_uri or "memory://",
    enabled=bool(_storage_uri),
)
limiter.init_app(app)

# Fonts and images never change under a fixed name, so they keep for a year.
# CSS and JS revalidate because nothing versions their names.
_IMMUTABLE = ('.woff2', '.woff', '.ttf',
              '.avif', '.webp', '.png', '.jpg', '.jpeg', '.svg', '.ico')

app.get_send_file_max_age = (
    lambda filename: 31536000 if filename and filename.lower().endswith(_IMMUTABLE) else None
)

# Where build_pdf.py writes the resume, and where the download route reads it.
PDF_DIR = 'static/resume'
PDF_NAME = 'Benson_Chow_Resume.pdf'

# Both licences live at the repo root so GitHub picks them up. The home page
# links to them, so serve those same files rather than keeping a second copy.
LICENCES = {'code': 'LICENSE', 'content': 'LICENSE-CONTENT'}

# Thousands separators in templates: {{ 1234 | comma }} -> 1,234
app.jinja_env.filters['comma'] = music_data.comma

# Behind nginx or Cloudflare, makes request.host and request.scheme reflect the
# original client rather than the proxy. One hop per proxy in front, so raise it
# if anything else is chained ahead of the reverse proxy. Too low and every
# client looks like the nearest proxy, which breaks rate limiting by address.
_proxy_hops = int(os.getenv("PROXY_FIX_HOPS", "1"))

try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    # Only X-Forwarded-For accumulates a value per hop. Proto, host and port are
    # overwritten by each proxy, so counting hops on those finds nothing and
    # falls back to the scheme of the last connection, which is always http here.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=_proxy_hops, x_proto=1,
                            x_host=1, x_port=1)
except Exception:
    pass

@app.before_request
def redirect_to_new_domain():
    host = (request.host or '').split(':')[0].lower()
    old_hosts = {'bensonchow.cf', 'www.bensonchow.cf'}
    target_host = 'bensonc.how'

    if host in old_hosts and host != target_host:
        parsed = urlparse(request.url)
        new_parsed = parsed._replace(netloc=target_host)
        try:
            new_url = urlunparse(new_parsed)
        except Exception:
            # urlunparse can raise on a malformed URL.
            new_url = request.url.replace(request.host, target_host)
        return redirect(new_url, code=301)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/🚧projects🚧')
def projects():
    data = get_static_json("static/projects/projects.json")['projects']
    data.sort(key=order_projects_by_weight, reverse=True)

    tag = request.args.get('tags')
    if tag is not None:
        data = [project for project in data if tag.lower() in [project_tag.lower() for project_tag in project['tags']]]
    return render_template('projects.html', projects=data, tag=tag)


@app.route('/projects')
def projects_redirect():
    return redirect(url_for('projects'))


@app.route('/📄resume📄')
def resume():
    projects = get_static_json("static/projects/projects.json")['projects']
    projects.sort(key=order_projects_by_weight, reverse=True)
    featured_projects = projects[:6]
    return render_template('resume.html', featured_projects=featured_projects)


@app.route('/resume')
def resume_redirect():
    return redirect(url_for('resume'))


@app.route('/licence/<which>')
def licence(which):
    """Serve LICENSE and LICENSE-CONTENT from the repo root as plain text."""
    name = LICENCES.get(which)
    if name is None:
        return render_template('404.html'), 404
    return send_from_directory(app.root_path, name, mimetype='text/plain')


@app.route('/📄resume📄/download')
def download_resume():
    """Serve the PDF built by build_pdf.py"""
    pdf_path = get_static_file(os.path.join(PDF_DIR, PDF_NAME))
    if not os.path.exists(pdf_path):
        app.logger.error("Resume PDF missing, run build_pdf.py")
        return render_template('404.html'), 404

    return send_from_directory(get_static_file(PDF_DIR), PDF_NAME, as_attachment=True)


@app.route('/resume/download')
def download_resume_redirect():
    return redirect(url_for('download_resume'))

def order_projects_by_weight(projects):
    # Missing or non-numeric weights sort last rather than raising.
    try:
        return int(projects['weight'])
    except (KeyError, ValueError, TypeError):
        return 0

@app.route('/🚧projects🚧/<title>')
def project(title):
    projects = get_static_json("static/projects/projects.json")['projects']

    in_project = next((p for p in projects if p['directory_name'] == title), None)

    if in_project is None:
        return render_template('404.html'), 404

    selected = in_project

    if 'description' not in selected:
        description_path = get_static_file(
            'static/%s/%s/%s.html' % ("projects", selected['directory_name'], selected['directory_name']))
        with io.open(description_path, "r", encoding="utf-8") as handle:
            selected['description'] = handle.read()
    return render_template('project.html', project=selected)


@app.route('/projects/<title>')
def project_redirect(title):
    return redirect(url_for('project', title=title))

@app.route('/🎵music🎵')
def music():
    # A query param, not client state, so each view stays bookmarkable.
    period = request.args.get('period', music_data.DEFAULT_PERIOD)
    if period not in music_data.PERIOD_IDS:
        period = music_data.DEFAULT_PERIOD

    try:
        summary = music_data.fetch_summary()
        view = music_data.build_view(summary, period)
    except music_data.VaultUnavailable:
        app.logger.exception("Could not reach the scrobble vault")
        # 200, not 503, the rest of the page is fine.
        return render_template('music.html', view=None, error=True)

    return render_template('music.html', view=view, error=False)

@app.route('/music')
def music_redirect():
    return redirect(url_for('music'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def get_static_file(path):
    site_root = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(site_root, path)

def get_static_json(path):
    with open(get_static_file(path), encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == '__main__':
    from livereload import Server
    # Jinja caches compiled templates outside debug mode.
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    server = Server(app.wsgi_app)
    server.watch('templates/')
    server.watch('static/')
    # Loopback locally. In a container that would be unreachable from the host,
    # so docker-compose.dev.yaml sets this to 0.0.0.0.
    server.serve(host=os.getenv('DEV_HOST', '127.0.0.1'),
                 port=int(os.getenv('DEV_PORT', '5500')))
