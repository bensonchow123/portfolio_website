import datetime
import io
import json
import os
from requests import get, exceptions

from flask import Flask, render_template, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = Flask(__name__)
ALLOWED_EXTENSIONS = {'html', 'htm'}

@app.route('/')
def index():
    age = int((datetime.date.today() - datetime.date(2005, 11, 22)).days / 365)
    return render_template('home.html', age=age)

@app.route('/🤗guestbook🤗')
def guestbook():
    return render_template('guestbook.html')


@app.route('/🛒shop🛒')
def shop():
    return render_template('shop.html')


@app.route('/🚧projects🚧')
def projects():
    data = get_static_json("static/projects/projects.json")['projects']
    data.sort(key=order_projects_by_weight, reverse=True)

    tag = request.args.get('tags')
    if tag is not None:
        data = [project for project in data if tag.lower() in [project_tag.lower() for project_tag in project['tags']]]
    return render_template('projects.html', projects=data, tag=tag)


def order_projects_by_weight(projects):
    try:
        return int(projects['weight'])
    except KeyError:
        return 0

@app.route('/🚧projects🚧/<title>')
def project(title):
    projects = get_static_json("static/projects/projects.json")['projects']

    in_project = next((p for p in projects if p['link'] == title), None)

    if in_project is None:
        return render_template('404.html'), 404

    selected = in_project

    if 'description' not in selected:
        selected['description'] = io.open(get_static_file(
            'static/%s/%s/%s.html' % ("projects", selected['link'], selected['link'])), "r", encoding="utf-8").read()
    return render_template('project.html', project=selected)

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
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_input(user_input):
    user_input = user_input.strip()
    if not allowed_file(user_input):
        return None
    return user_input

@app.route('/chat-exporter', methods=['GET'])
@limiter.limit("10/minute")
def chat_exporter():
    url = request.args.get('url')
    if url:
        file_name = os.path.basename(url)
        file_path = sanitize_input(file_name)
        if file_path is None:
            return "Invalid file name"
        if not url.startswith("https://"):
            return "Invalid URL. Only https is allowed."
        try:
            response = get(url)
        except exceptions.RequestException as e:
            return "Error: Invalid URL or Unable to connect to the server"

        if response.ok:
            html = response.text
            return render_template('chat_exporter.html', html=html)
        else:
            return f"Error: {response.status_code} {response.reason}"
    else:
        return "Error: No URL provided"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
