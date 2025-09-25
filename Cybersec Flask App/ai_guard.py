import json
from typing import Dict, Any

from openai import OpenAI

class AIGuard:
    def __init__(self, api_key: str, model: str, min_confidence: float = 0.65):
        self.model = model
        self.min_confidence = min_confidence
        self.client = OpenAI(api_key=api_key) if api_key else None

    def classify(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to classify a request as BENIGN or MALICIOUS and explain why.
        Returns: { verdict, confidence, categories, explanation }.
        If API unavailable, returns a neutral verdict with low confidence.
        """
        if not self.client:
            return {
                'verdict': 'UNKNOWN',
                'confidence': 0.0,
                'categories': [],
                'explanation': 'AI disabled (no API key).',
            }

        system = (
            "You are a web security classifier. Classify HTTP requests as BENIGN or MALICIOUS. "
            "Consider categories: SQLI, XSS, LFI, RCE, SSRF, SCANNER, AUTH_BRUTE_FORCE, OTHER. "
            "Be conservative: only return MALICIOUS if you are reasonably confident."
        )
        user = (
            "Analyze this request. Return compact JSON with keys: verdict (BENIGN|MALICIOUS), "
            "confidence (0..1), categories (array of strings), explanation (<=30 words).\n\n"
            f"RequestFeatures:\n{json.dumps(features, ensure_ascii=False)}"
        )

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            return {
                'verdict': data.get('verdict', 'UNKNOWN'),
                'confidence': float(data.get('confidence', 0.0)),
                'categories': data.get('categories', []) or [],
                'explanation': data.get('explanation', ''),
            }
        except Exception as e:
            return {
                'verdict': 'UNKNOWN',
                'confidence': 0.0,
                'categories': [],
                'explanation': f'AI error: {e}',
            }

    def should_block(self, ai_result: Dict[str, Any]) -> bool:
        return ai_result.get('verdict') == 'MALICIOUS' and ai_result.get('confidence', 0.0) >= self.min_confidence