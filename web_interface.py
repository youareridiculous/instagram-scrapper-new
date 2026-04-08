#!/usr/bin/env python3
"""
Web Interface for Instagram Scraper
View results and control the scraper from your browser
"""

import asyncio
import json
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

from instagram_scraper import SafeInstagramScraper

load_dotenv()

app = Flask(__name__)
CORS(app)

SCRAPED_DIR = Path('scraped_data')

scraper_instance: Optional[SafeInstagramScraper] = None
# Mutate in place only — background thread holds a reference to this dict.
scraper_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_action': 'Idle',
    'profiles_found': 0,
    'last_update': None,
}

_start_lock = threading.Lock()
_runner_thread: Optional[threading.Thread] = None


def is_safe_csv_filename(name: str) -> bool:
    if not name or Path(name).name != name:
        return False
    if '..' in name or '/' in name or '\\' in name:
        return False
    return bool(re.fullmatch(r'[A-Za-z0-9._-]+\.csv', name))


def resolve_csv_path(filename: str) -> Optional[Path]:
    if not is_safe_csv_filename(filename):
        return None
    SCRAPED_DIR.mkdir(exist_ok=True)
    base = SCRAPED_DIR.resolve()
    path = (base / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        return None
    return path


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current scraper status"""
    return jsonify(scraper_status)


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config_path = Path('config.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'error': 'Config file not found'}), 404


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        config = request.json
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/results')
def get_results():
    """Get all scraped results"""
    if not SCRAPED_DIR.exists():
        return jsonify({'results': [], 'files': []})

    csv_files = sorted(SCRAPED_DIR.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True)

    all_results = []
    files_info = []

    for csv_file in csv_files:
        if not is_safe_csv_filename(csv_file.name):
            continue
        try:
            df = pd.read_csv(csv_file)
            files_info.append({
                'filename': csv_file.name,
                'size': csv_file.stat().st_size,
                'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat(),
                'count': len(df),
            })

            if csv_file == csv_files[0]:
                all_results = df.to_dict('records')
        except Exception:
            continue

    return jsonify({
        'results': all_results,
        'files': files_info,
        'total_profiles': len(all_results),
    })


@app.route('/api/results/<filename>')
def get_results_file(filename):
    """Get results from a specific file"""
    path = resolve_csv_path(filename)
    if path is None or not path.is_file():
        return jsonify({'error': 'File not found'}), 404

    try:
        df = pd.read_csv(path)
        return jsonify({
            'results': df.to_dict('records'),
            'filename': filename,
            'count': len(df),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a CSV file"""
    path = resolve_csv_path(filename)
    if path is None or not path.is_file():
        return jsonify({'error': 'File not found'}), 404
    return send_file(path, as_attachment=True, mimetype='text/csv', download_name=filename)


def _run_scraper_thread(username: str, password: str, config: dict) -> None:
    global scraper_instance

    async def _go() -> None:
        global scraper_instance
        scraper = SafeInstagramScraper(username, password, headless=True)
        scraper_instance = scraper
        await scraper.run(
            config.get('search', {}),
            config.get('filters', {}),
            progress=scraper_status,
        )

    try:
        asyncio.run(_go())
    finally:
        scraper_status['running'] = False
        scraper_status['last_update'] = datetime.now().isoformat()
        scraper_instance = None


@app.route('/api/start', methods=['POST'])
def start_scraper():
    """Start the scraper in a background thread (Flask has no asyncio loop)."""
    global _runner_thread

    with _start_lock:
        if scraper_status.get('running'):
            return jsonify({'error': 'Scraper is already running'}), 400
        if _runner_thread is not None and _runner_thread.is_alive():
            return jsonify({'error': 'Scraper is already running'}), 400

        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')

        if not username or not password or username == 'your_username_here':
            return jsonify({'error': 'Please configure Instagram credentials in .env file'}), 400

        config_path = Path('config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {'search': {}, 'filters': {}}

        scraper_status.update({
            'running': True,
            'progress': 0,
            'total': 0,
            'current_action': 'Starting...',
            'profiles_found': 0,
            'last_update': datetime.now().isoformat(),
        })

        _runner_thread = threading.Thread(
            target=_run_scraper_thread,
            args=(username, password, config),
            daemon=True,
        )
        _runner_thread.start()

    return jsonify({'success': True, 'message': 'Scraper started'})


@app.route('/api/stop', methods=['POST'])
def stop_scraper():
    """Request cooperative stop; scraper checks scraper_status['running']."""
    if not scraper_status.get('running'):
        return jsonify({'error': 'Scraper is not running'}), 400

    scraper_status['running'] = False
    scraper_status['current_action'] = 'Stopping...'
    scraper_status['last_update'] = datetime.now().isoformat()

    return jsonify({'success': True, 'message': 'Scraper stop requested'})


if __name__ == '__main__':
    port = 5001
    print('🌐 Starting web interface...')
    print(f'📊 Open http://localhost:{port} in your browser')
    app.run(debug=True, host='0.0.0.0', port=port)
