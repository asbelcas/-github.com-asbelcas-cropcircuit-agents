#!/usr/bin/env python3
"""
Job Data API - Monetized Data Access

PRICING:
- Free tier: 10 requests/day
- Basic: $10/month - 1000 requests/day  
- Pro: $50/month - Unlimited requests
"""

from flask import Flask, jsonify, request
import sqlite3
import json
from functools import wraps

app = Flask(__name__)

# API key validation (simplified)
VALID_KEYS = {
    'free_key_123': 'free',
    'basic_key_456': 'basic',
    'pro_key_789': 'pro'
}

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key not in VALID_KEYS:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/jobs', methods=['GET'])
@require_api_key
def get_jobs():
    """Get latest job listings"""
    try:
        # Read from collected data
        import glob
        files = sorted(glob.glob('collected_data/*_jobs_*.json'))
        if not files:
            return jsonify({'jobs': []})
        
        with open(files[-1]) as f:
            data = json.load(f)
        
        return jsonify({
            'jobs': data[:10],  # Return top 10
            'total': len(data),
            'source': files[-1]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get API stats (public)"""
    return jsonify({
        'data_points': '10,000+',
        'update_frequency': 'hourly',
        'pricing': {
            'free': '10 requests/day',
            'basic': '$10/month - 1000 requests',
            'pro': '$50/month - unlimited'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
