#!/usr/bin/env python3
"""
Web Interface for Instagram Scraper
View results and control the scraper from your browser
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import pandas as pd
from dotenv import load_dotenv

from instagram_scraper import SafeInstagramScraper

load_dotenv()

app = Flask(__name__)
CORS(app)

# Global scraper instance
scraper_instance = None
scraper_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_action': 'Idle',
    'profiles_found': 0,
    'last_update': None
}

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
    results_dir = Path('scraped_data')
    if not results_dir.exists():
        return jsonify({'results': [], 'files': []})
    
    # Get all CSV files
    csv_files = sorted(results_dir.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Load the most recent file
    all_results = []
    files_info = []
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            files_info.append({
                'filename': csv_file.name,
                'size': csv_file.stat().st_size,
                'modified': datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat(),
                'count': len(df)
            })
            
            # If this is the most recent file, include its data
            if csv_file == csv_files[0]:
                all_results = df.to_dict('records')
        except Exception as e:
            continue
    
    return jsonify({
        'results': all_results,
        'files': files_info,
        'total_profiles': len(all_results)
    })

@app.route('/api/results/<filename>')
def get_results_file(filename):
    """Get results from a specific file"""
    file_path = Path('scraped_data') / filename
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    try:
        df = pd.read_csv(file_path)
        return jsonify({
            'results': df.to_dict('records'),
            'filename': filename,
            'count': len(df)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a CSV file"""
    file_path = Path('scraped_data') / filename
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    return send_file(file_path, as_attachment=True, mimetype='text/csv')

@app.route('/api/start', methods=['POST'])
def start_scraper():
    """Start the scraper"""
    global scraper_instance, scraper_status
    
    if scraper_status['running']:
        return jsonify({'error': 'Scraper is already running'}), 400
    
    try:
        # Get credentials
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        
        if not username or not password or username == 'your_username_here':
            return jsonify({'error': 'Please configure Instagram credentials in .env file'}), 400
        
        # Load config
        config_path = Path('config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {'search': {}, 'filters': {}}
        
        # Update status
        scraper_status = {
            'running': True,
            'progress': 0,
            'total': 0,
            'current_action': 'Starting...',
            'profiles_found': 0,
            'last_update': datetime.now().isoformat()
        }
        
        # Start scraper in background
        asyncio.create_task(run_scraper_async(username, password, config))
        
        return jsonify({'success': True, 'message': 'Scraper started'})
    except Exception as e:
        scraper_status['running'] = False
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_scraper():
    """Stop the scraper"""
    global scraper_instance, scraper_status
    
    if not scraper_status['running']:
        return jsonify({'error': 'Scraper is not running'}), 400
    
    # Note: This is a simple implementation. In production, you'd want proper task cancellation
    scraper_status['running'] = False
    scraper_status['current_action'] = 'Stopping...'
    
    return jsonify({'success': True, 'message': 'Scraper stop requested'})

async def run_scraper_async(username, password, config):
    """Run scraper asynchronously"""
    global scraper_instance, scraper_status
    
    try:
        scraper = SafeInstagramScraper(username, password, headless=True)
        scraper_instance = scraper
        
        # Update status during scraping
        scraper_status['current_action'] = 'Logging in...'
        scraper_status['last_update'] = datetime.now().isoformat()
        
        await scraper.init_browser()
        
        if await scraper.login():
            scraper_status['current_action'] = 'Searching profiles...'
            
            # Collect usernames
            all_usernames = []
            
            if 'hashtags' in config.get('search', {}):
                for hashtag in config['search']['hashtags']:
                    scraper_status['current_action'] = f'Searching hashtag: #{hashtag}'
                    usernames = await scraper.search_by_hashtag(hashtag, config['search'].get('max_per_hashtag', 50))
                    all_usernames.extend(usernames)
                    scraper_status['profiles_found'] = len(all_usernames)
                    await scraper.safe_delay(5, 10)
            
            if 'locations' in config.get('search', {}):
                for location in config['search']['locations']:
                    scraper_status['current_action'] = f'Searching location: {location}'
                    usernames = await scraper.search_by_location(location, config['search'].get('max_per_location', 50))
                    all_usernames.extend(usernames)
                    scraper_status['profiles_found'] = len(all_usernames)
                    await scraper.safe_delay(5, 10)
            
            # Scrape profiles
            unique_usernames = list(dict.fromkeys(all_usernames))
            scraper_status['total'] = len(unique_usernames)
            scraper_status['current_action'] = 'Scraping profiles...'
            
            matching_profiles = []
            for i, username in enumerate(unique_usernames):
                if not scraper_status['running']:
                    break
                
                scraper_status['progress'] = i + 1
                scraper_status['current_action'] = f'Scraping @{username} ({i+1}/{len(unique_usernames)})'
                scraper_status['last_update'] = datetime.now().isoformat()
                
                profile = await scraper.get_profile_data(username)
                await scraper.safe_delay()
                
                if profile and scraper.matches_filters(profile, config.get('filters', {})):
                    matching_profiles.append(profile)
                    scraper_status['profiles_found'] = len(matching_profiles)
            
            # Save results
            if matching_profiles:
                scraper.save_to_csv(matching_profiles)
                scraper_status['current_action'] = f'✅ Saved {len(matching_profiles)} profiles!'
            else:
                scraper_status['current_action'] = '⚠️ No profiles matched filters'
            
            await scraper.browser.close()
        else:
            scraper_status['current_action'] = '❌ Login failed'
        
    except Exception as e:
        scraper_status['current_action'] = f'❌ Error: {str(e)}'
    finally:
        scraper_status['running'] = False
        scraper_status['last_update'] = datetime.now().isoformat()

if __name__ == '__main__':
    port = 5001
    print("🌐 Starting web interface...")
    print(f"📊 Open http://localhost:{port} in your browser")
    app.run(debug=True, host='0.0.0.0', port=port)

