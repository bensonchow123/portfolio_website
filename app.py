import io
import json
import os
from urllib.parse import urlparse
import requests
from datetime import datetime

from flask import Flask, render_template, request, send_from_directory, redirect, url_for, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import weasyprint
from dotenv import load_dotenv

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = Flask(__name__)

# Last.fm API configuration
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_USERNAME = 'Benson_'  # Replace with your actual username
LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

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


@app.route('/📄resume📄')
def resume():
    # Load and sort projects by weight (descending)
    projects = get_static_json("static/projects/projects.json")['projects']
    projects.sort(key=order_projects_by_weight, reverse=True)
    featured_projects = projects[:6]
    return render_template('resume.html', featured_projects=featured_projects)


@app.route('/resume')
def resume_redirect():
    return redirect(url_for('resume'))


@app.route('/📄resume📄/download')
def download_resume():
    """Generate and download resume as PDF"""
    try:
        # Load and sort projects by weight (descending)
        projects = get_static_json("static/projects/projects.json")['projects']
        projects.sort(key=order_projects_by_weight, reverse=True)
        featured_projects = projects[:6]

        html = render_template('resume.html', featured_projects=featured_projects)
        pdf = weasyprint.HTML(string=html, base_url=os.path.abspath(os.path.dirname(__file__))).write_pdf()
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=Benson_Chow_Resume.pdf'
        
        return response
    except Exception as e:
        # Fallback - redirect to resume page if PDF generation fails
        return redirect(url_for('resume'))


@app.route('/resume/download')
def download_resume_redirect():
    return redirect(url_for('download_resume'))

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

@app.route('/🎵music🎵')
def music():
    try:
        # Get recent tracks
        recent_tracks = get_recent_tracks()
        
        # Get top albums with play counts
        top_albums = get_top_albums()
        
        # Get top artists
        top_artists = get_top_artists()
        
        return render_template('music.html', 
                             recent_tracks=recent_tracks, 
                             top_albums=top_albums,
                             top_artists=top_artists)
    except Exception as e:
        print(f"Error fetching Last.fm data: {e}")
        return render_template('music.html', 
                             recent_tracks=[], 
                             top_albums=[],
                             top_artists=[],
                             error="Unable to load music data")

@app.route('/music')
def music_redirect():
    return redirect(url_for('music'))

def get_recent_tracks(limit=12):
    """Fetch recent tracks from Last.fm API"""
    if not LASTFM_API_KEY or not LASTFM_USERNAME:
        return []
        
    params = {
        'method': 'user.getrecenttracks',
        'user': LASTFM_USERNAME,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        tracks = []
        now_playing_count = 0
        
        if 'recenttracks' in data and 'track' in data['recenttracks']:
            for track in data['recenttracks']['track']:
                is_now_playing = '@attr' in track and 'nowplaying' in track['@attr']
                
                # Count now playing tracks
                if is_now_playing:
                    now_playing_count += 1
                
                track_info = {
                    'name': track.get('name', 'Unknown'),
                    'artist': track.get('artist', {}).get('#text', 'Unknown Artist'),
                    'album': track.get('album', {}).get('#text', 'Unknown Album'),
                    'image': get_largest_image(track.get('image', [])),
                    'url': track.get('url', ''),
                    'nowplaying': is_now_playing,
                    'date': format_date(track.get('date', {}).get('#text')) if 'date' in track else 'Now playing'
                }
                tracks.append(track_info)
        
        # If we have now playing tracks, limit the total to the requested limit
        if now_playing_count > 0 and len(tracks) > limit:
            tracks = tracks[:limit]
        
        return tracks
    except Exception as e:
        print(f"Error fetching recent tracks: {e}")
        return []

def get_top_albums(period='1month', limit=15):  # Last 30 days
    # Could also use: '7day', '3month', '6month', '12month', 'overall'
    """Fetch top albums with play counts from Last.fm API"""
    if not LASTFM_API_KEY or not LASTFM_USERNAME:
        return []
        
    params = {
        'method': 'user.gettopalbums',
        'user': LASTFM_USERNAME,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'period': period,  # '1month' = last 30 days
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        albums = []
        if 'topalbums' in data and 'album' in data['topalbums']:
            for album in data['topalbums']['album']:
                album_info = {
                    'name': album.get('name', 'Unknown Album'),
                    'artist': album.get('artist', {}).get('name', 'Unknown Artist'),
                    'playcount': album.get('playcount', '0'),
                    'image': get_largest_image(album.get('image', [])),
                    'url': album.get('url', '')
                }
                albums.append(album_info)
        
        return albums
    except Exception as e:
        print(f"Error fetching top albums: {e}")
        return []

def get_top_artists(period='1month', limit=15):  # Last 30 days
    # Could also use: '7day', '3month', '6month', '12month', 'overall'
    """Fetch top artists with play counts from Last.fm API"""
    if not LASTFM_API_KEY or not LASTFM_USERNAME:
        return []
        
    params = {
        'method': 'user.gettopartists',
        'user': LASTFM_USERNAME,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'period': period,  # '1month' = last 30 days
        'limit': limit
    }
    
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        artists = []
        if 'topartists' in data and 'artist' in data['topartists']:
            for artist in data['topartists']['artist']:
                artist_info = {
                    'name': artist.get('name', 'Unknown Artist'),
                    'playcount': artist.get('playcount', '0'),
                    'url': artist.get('url', '')
                    # No image field needed
                }
                artists.append(artist_info)
        
        return artists
    except Exception as e:
        print(f"Error fetching top artists: {e}")
        return []

def get_largest_image(images):
    """Get the largest available image from Last.fm image array"""
    if not images:
        return ''
    
    size_priority = ['extralarge', 'large', 'medium', 'small']
    
    for size in size_priority:
        for img in images:
            if img.get('size') == size and img.get('#text'):
                return img['#text']
    
    return images[0].get('#text', '') if images else ''

def format_date(date_str):
    """Format Last.fm date string to a more readable format with UTC timezone"""
    if not date_str:
        return ''
    
    try:
        dt = datetime.strptime(date_str, "%d %b %Y, %H:%M")
        return dt.strftime("%b %d, %Y at %H:%M UTC")
    except:
        return date_str

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def get_static_file(path):
    site_root = os.path.realpath(os.path.dirname(__file__))
    return os.path.join(site_root, path)

def get_static_json(path):
    return json.load(open(get_static_file(path)))

if __name__ == '__main__':
    from livereload import Server
    server = Server(app.wsgi_app)
    server.serve()
