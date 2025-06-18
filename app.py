import io
import json
import os
from requests import get, exceptions
from urllib.parse import urlparse

from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = Flask(__name__)
ALLOWED_EXTENSIONS = {'html', 'htm'}

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/🤗guestbook🤗')
def guestbook():
    return render_template('guestbook.html')

@app.route('/guestbook')
def guestbook_redirect():
    return redirect(url_for('guestbook'))

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


def order_projects_by_weight(projects):
    try:
        return int(projects['weight'])
    except KeyError:
        return 0

@app.route('/🚧projects🚧/<title>')
def project(title):
    projects = get_static_json("static/projects/projects.json")['projects']

    in_project = next((p for p in projects if p['directory_name'] == title), None)

    if in_project is None:
        return render_template('404.html'), 404

    selected = in_project

    if 'description' not in selected:
        selected['description'] = io.open(get_static_file(
            'static/%s/%s/%s.html' % ("projects", selected['directory_name'], selected['directory_name'])), "r", encoding="utf-8").read()
    return render_template('project.html', project=selected)


@app.route('/projects/<title>')
def project_redirect(title):
    return redirect(url_for('project', title=title))

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory("static", request.path[1:])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def get_static_file(path):
    site_root = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(site_root, path)


def get_static_json(path):
    return json.load(open(get_static_file(path)))



def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_input(url):
    """Validate the URL and ensure it has an allowed file extension."""
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Ensure the URL has a valid scheme and netloc
    if not parsed_url.scheme or not parsed_url.netloc:
        return None
    
    # Extract the file name from the URL path
    file_name = os.path.basename(parsed_url.path)
    
    # Check if the file name has an allowed extension
    if not allowed_file(file_name):
        return None
    
    return url

if __name__ == '__main__':
    from livereload import Server
    server = Server(app.wsgi_app)
    server.serve()
