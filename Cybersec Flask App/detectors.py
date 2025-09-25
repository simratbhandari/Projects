import re
from urllib.parse import unquote

# Lightweight signature patterns (heuristic pre-filter)
SQLI = re.compile(r"(\bOR\b|\bAND\b).*?=|\bUNION\b|--|#|/\*|\bSELECT\b|\bDROP\b|\bINSERT\b|\bUPDATE\b", re.I)
XSS = re.compile(r"<\s*script|onerror\s*=|onload\s*=|javascript:\\S|<\s*img|<\s*svg|<\s*iframe", re.I)
LFI = re.compile(r"\.\./|\.\.\\|/etc/passwd|\\boot\.ini", re.I)
RCE = re.compile(r"(;|\|\||&&)\s*(cat|ls|id|uname|curl|wget|sh|bash)\b|`[^`]+`|\$\([^\)]+\)", re.I)
SSRF = re.compile(r"https?://(127\.0\.0\.1|0\.0\.0\.0|localhost|169\.254\.169\.254|\[::1\])", re.I)
SCANNER_UA = re.compile(r"sqlmap|nikto|nmap|curl|wget|acunetix|nessus", re.I)

CATEGORIES = {
    'SQLI': SQLI,
    'XSS': XSS,
    'LFI': LFI,
    'RCE': RCE,
    'SSRF': SSRF,
}


def extract_surface(request):
    """Extracts string surface from Flask request for heuristic and AI analysis."""
    parts = [
        f"method={request.method}",
        f"path={request.path}",
        f"query={request.query_string.decode('utf-8', 'ignore')}",
        f"ip={request.remote_addr}",
        f"ua={request.headers.get('User-Agent','-')}",
    ]
    # Safely include body (only small bodies)
    try:
        if request.content_length and request.content_length < 4096:
            body = request.get_data(as_text=True) or ""
            parts.append(f"body={body}")
    except Exception:
        pass
    return unquote("\n".join(parts))


def heuristic_assess(surface: str, user_agent: str) -> dict:
    score = 0.0
    hits = []

    for name, regex in CATEGORIES.items():
        if regex.search(surface):
            hits.append(name)
            score += 0.35

    if SCANNER_UA.search(user_agent or ""):
        hits.append('SCANNER')
        score += 0.3

    # Normalize score to 0..1
    score = min(1.0, score)
    return {
        'score': score,
        'hits': hits,
    }