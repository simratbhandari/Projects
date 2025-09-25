import os
import time
import sqlite3
from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Flask, request, render_template, redirect, url_for, abort, g, jsonify, flash
)
from dotenv import load_dotenv

from config import Config
from detectors import extract_surface, heuristic_assess
from rate_limit import TokenBucketLimiter
from ai_guard import AIGuard
from firewall import MitigationGenerator

# Setup 
load_dotenv()
config = Config()
app = Flask(__name__)
app.config.from_object(config)

limiter = TokenBucketLimiter(
    per_minute=config.RATE_LIMIT_PER_MIN,
    burst=config.RATE_LIMIT_BURST,
)
ai_guard = AIGuard(
    api_key=config.OPENAI_API_KEY,
    model=config.AI_MODEL,
    min_confidence=config.AI_MIN_CONFIDENCE,
)
mitigator = MitigationGenerator(
    api_key=config.OPENAI_API_KEY,
    model=config.AI_MODEL,
)

BLOCKLIST = {}  # ip -> unblock_time (epoch seconds)
DB_PATH = os.path.join(os.path.dirname(__file__), 'incidents.db')

# DB

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

with app.app_context():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            ip TEXT,
            path TEXT,
            method TEXT,
            user_agent TEXT,
            surface TEXT,
            heuristic_score REAL,
            heuristic_hits TEXT,
            ai_verdict TEXT,
            ai_confidence REAL,
            ai_categories TEXT,
            ai_explanation TEXT,
            action TEXT,
            mitigation_script TEXT
        );
        """
    )
    db.commit()

#  Helpers

def is_blocked(ip: str) -> bool:
    now = time.time()
    until = BLOCKLIST.get(ip)
    if until and now < until:
        return True
    elif until and now >= until:
        BLOCKLIST.pop(ip, None)
    return False


def block_ip(ip: str):
    BLOCKLIST[ip] = time.time() + app.config['BLOCK_DURATION_SECONDS']


def log_incident(**kwargs):
    db = get_db()
    db.execute(
        """INSERT INTO incidents (
            ts, ip, path, method, user_agent, surface,
            heuristic_score, heuristic_hits, ai_verdict, ai_confidence,
            ai_categories, ai_explanation, action, mitigation_script
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            datetime.utcnow().isoformat(),
            kwargs.get('ip'),
            kwargs.get('path'),
            kwargs.get('method'),
            kwargs.get('user_agent'),
            kwargs.get('surface'),
            kwargs.get('heuristic_score', 0.0),
            ",".join(kwargs.get('heuristic_hits', [])),
            kwargs.get('ai_verdict'),
            kwargs.get('ai_confidence', 0.0),
            ",".join(kwargs.get('ai_categories', [])),
            kwargs.get('ai_explanation'),
            kwargs.get('action'),
            kwargs.get('mitigation_script'),
        )
    )
    db.commit()

# Security Middleware 

@app.before_request
def guard_request():
    # Skip for health/static/dashboard endpoints to avoid locking yourself out
    safe_paths = {'/dashboard', '/static', '/blocked'}
    if any(request.path.startswith(p) for p in safe_paths):
        return

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if is_blocked(ip):
        return redirect(url_for('blocked'))

    # Rate limiting
    if not limiter.allow(ip):
        block_ip(ip)
        log_incident(
            ip=ip,
            path=request.path,
            method=request.method,
            user_agent=request.headers.get('User-Agent','-'),
            surface='(rate limit exceeded)',
            heuristic_score=1.0,
            heuristic_hits=['RATE_LIMIT'],
            ai_verdict='MALICIOUS',
            ai_confidence=1.0,
            ai_categories=['RATE_LIMIT'],
            ai_explanation='Excessive requests from single IP.',
            action='blocked',
            mitigation_script='(auto) temporary IP block',
        )
        return redirect(url_for('blocked'))

    # Heuristic prefilter
    surface = extract_surface(request)
    heur = heuristic_assess(surface, request.headers.get('User-Agent','-'))

    # If clearly suspicious or random sample, ask AI to classify
    ai_result = {'verdict': 'UNKNOWN', 'confidence': 0.0, 'categories': [], 'explanation': ''}
    if heur['score'] >= 0.35 or request.args.get('force_ai') == '1':
        features = {
            'ip': ip,
            'method': request.method,
            'path': request.path,
            'query': request.args.to_dict(flat=False),
            'headers': {k: v for k, v in request.headers.items() if k.lower() in ['user-agent', 'referer', 'content-type']},
            'body_len': request.content_length or 0,
            'surface': surface[:1500],
        }
        ai_result = ai_guard.classify(features)

    # Decide action
    action = 'allow'
    if heur['score'] >= 0.8 or ai_guard.should_block(ai_result):
        action = 'block'

    if action == 'block':
        block_ip(ip)
        # Ask AI to produce a small mitigation script for incident response
        incident = {
            'ip': ip,
            'path': request.path,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent','-'),
            'heuristic_hits': heur['hits'],
            'ai': ai_result,
        }
        script = mitigator.generate(incident)
        log_incident(
            ip=ip,
            path=request.path,
            method=request.method,
            user_agent=request.headers.get('User-Agent','-'),
            surface=surface,
            heuristic_score=heur['score'],
            heuristic_hits=heur['hits'],
            ai_verdict=ai_result.get('verdict'),
            ai_confidence=ai_result.get('confidence'),
            ai_categories=ai_result.get('categories'),
            ai_explanation=ai_result.get('explanation'),
            action='blocked',
            mitigation_script=script,
        )
        return redirect(url_for('blocked'))

    # Otherwise allow and optionally log suspicious-but-allowed
    if heur['score'] >= 0.35:
        log_incident(
            ip=ip,
            path=request.path,
            method=request.method,
            user_agent=request.headers.get('User-Agent','-'),
            surface=surface,
            heuristic_score=heur['score'],
            heuristic_hits=heur['hits'],
            ai_verdict=ai_result.get('verdict'),
            ai_confidence=ai_result.get('confidence'),
            ai_categories=ai_result.get('categories'),
            ai_explanation=ai_result.get('explanation'),
            action='allowed',
            mitigation_script='',
        )

# ----------- Routes -----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/blocked')
def blocked():
    return render_template('blocked.html')

@app.route('/dashboard')
def dashboard():
    db = get_db()
    rows = db.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 200").fetchall()
    return render_template('dashboard.html', rows=rows, blocklist=BLOCKLIST)

@app.route('/dashboard/unblock/<ip>', methods=['POST'])
def unblock(ip):
    BLOCKLIST.pop(ip, None)
    flash(f"Unblocked {ip}")
    return redirect(url_for('dashboard'))

@app.route('/echo')
def echo():
    # innocuous endpoint to test rate limiting / AI analysis
    msg = request.args.get('msg', 'hello')
    return jsonify({'ok': True, 'echo': msg})

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_ENV') == 'development')