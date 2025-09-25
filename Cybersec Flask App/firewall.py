import json
from datetime import datetime
from openai import OpenAI

TEMPLATE_BASELINE = """#!/usr/bin/env bash
# Generated at {ts}
# Purpose: Apply temporary mitigation for suspected attack
IP="{ip}"
DURATION_MIN=15

echo "Blocking $IP for $DURATION_MIN minutes via iptables (example; review before applying)"
# Example iptables commands (review! may vary by distro)
iptables -I INPUT -s "$IP" -j DROP
# Optional: schedule unblock
# (crontab) echo "(sleep $((DURATION_MIN*60)); iptables -D INPUT -s $IP -j DROP) &" | at now

# Example NGINX snippet to drop obvious malicious payloads
cat > /etc/nginx/conf.d/ai-guard-snippet.conf <<'NGINX'
map $request_uri $ai_guard_block {
  default 0;
  ~*(<script>|select\s+.*from|\.{2}/|/etc/passwd) 1;
}
server {
  if ($ai_guard_block) { return 403; }
}
NGINX

systemctl reload nginx 2>/dev/null || true
"""

class MitigationGenerator:
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = model

    def generate(self, incident: dict) -> str:
        """Ask AI to produce a short shell script + config hints tailored to the incident.
        Falls back to a baseline template if AI is unavailable.
        """
        ip = incident.get('ip', '0.0.0.0')
        ts = datetime.utcnow().isoformat()
        if not self.client:
            return TEMPLATE_BASELINE.format(ip=ip, ts=ts)

        prompt = (
            "You are a defensive security assistant. Generate a short bash script (with comments) "
            "that a human can review to apply a **temporary** mitigation for the web attack described. "
            "NEVER include offensive commands. Prefer safe blocks, IP drop, and NGINX/WAF snippets. "
            "Keep it under ~80 lines. Include inline comments and reminders to review and roll back.\n\n"
            f"Incident (JSON):\n{json.dumps(incident, ensure_ascii=False, indent=2)}"
        )

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You help defenders mitigate web attacks safely."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return TEMPLATE_BASELINE.format(ip=ip, ts=ts)