"""
Intelligence Extraction Module
Extracts actionable scam intelligence using regex and optional LLM
"""

import os
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class IntelligenceExtractor:
    """
    Extracts scam intelligence from messages:
    1. Bank account numbers
    2. UPI IDs
    3. Phishing URLs
    
    Uses regex-based extraction (primary) with LLM fallback (secondary)
    """
    
    # Regex patterns for intelligence extraction
    
    # Indian bank account patterns (9-18 digits)
    BANK_ACCOUNT_PATTERNS = [
        r'\b\d{9,18}\b',  # General account number pattern
        r'\b[Aa]cc(?:oun)?t?\s*(?:[Nn]o\.?|[Nn]umber)?\s*[:=]?\s*(\d{9,18})\b',
        r'\b[Aa]/[Cc]\s*[:=]?\s*(\d{9,18})\b',
    ]
    
    # UPI ID patterns (username@provider)
    UPI_PATTERNS = [
        r'\b[\w\.-]+@(?:paytm|okaxis|okhdfcbank|okicici|oksbi|ybl|ibl|axl|upi)\b',
        r'\b[\w\.-]+@[\w]+\b(?=.*(?:upi|pay|payment))',
    ]
    
    # Phishing URL patterns
    URL_PATTERNS = [
        r'https?://[^\s]+',
        r'www\.[^\s]+',
        r'\b[a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?\b',
    ]
    
    # Suspicious domain keywords for phishing detection
    SUSPICIOUS_KEYWORDS = [
        'verify', 'secure', 'account', 'update', 'confirm', 'login',
        'bank', 'payment', 'kyc', 'blocked', 'suspended'
    ]
    
    def __init__(self):
        """Initialize the intelligence extractor"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Compile regex patterns for efficiency
        self.bank_patterns = [re.compile(p, re.IGNORECASE) for p in self.BANK_ACCOUNT_PATTERNS]
        self.upi_patterns = [re.compile(p, re.IGNORECASE) for p in self.UPI_PATTERNS]
        self.url_patterns = [re.compile(p, re.IGNORECASE) for p in self.URL_PATTERNS]
        
        if not self.openai_api_key:
            logger.info("OPENAI_API_KEY not set. Using regex-based extraction only.")
    
    def extract(self, message: str) -> Dict[str, List[str]]:
        """
        Extract all intelligence from a message.
        
        Args:
            message: The message to extract from
        
        Returns:
            Dict with 'bank_accounts', 'upi_ids', 'phishing_urls' (all lists, never null)
        """
        try:
            # Extract using regex (primary method)
            bank_accounts = self._extract_bank_accounts(message)
            upi_ids = self._extract_upi_ids(message)
            phishing_urls = self._extract_phishing_urls(message)
            
            # Try LLM enhancement if available and regex found nothing
            if self.openai_api_key and not (bank_accounts or upi_ids or phishing_urls):
                try:
                    llm_results = self._llm_extract(message)
                    if llm_results:
                        bank_accounts.extend(llm_results.get("bank_accounts", []))
                        upi_ids.extend(llm_results.get("upi_ids", []))
                        phishing_urls.extend(llm_results.get("phishing_urls", []))
                except Exception as e:
                    logger.warning(f"LLM extraction failed: {e}")
            
            # Remove duplicates and return
            result = {
                "bank_accounts": list(set(bank_accounts)),
                "upi_ids": list(set(upi_ids)),
                "phishing_urls": list(set(phishing_urls))
            }
            
            if any(result.values()):
                logger.info(f"Extracted intelligence: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in intelligence extraction: {e}")
            # NEVER return null - always return empty lists
            return {
                "bank_accounts": [],
                "upi_ids": [],
                "phishing_urls": []
            }
    
    def _extract_bank_accounts(self, message: str) -> List[str]:
        """Extract bank account numbers using regex"""
        accounts = []
        
        for pattern in self.bank_patterns:
            matches = pattern.findall(message)
            for match in matches:
                # Extract the account number (might be in a group)
                account = match if isinstance(match, str) else match[0] if match else ""
                # Validate: 9-18 digits, not all same digit
                if account and account.isdigit() and 9 <= len(account) <= 18:
                    if not all(d == account[0] for d in account):  # Not all same digit
                        accounts.append(account)
        
        return accounts
    
    def _extract_upi_ids(self, message: str) -> List[str]:
        """Extract UPI IDs using regex"""
        upi_ids = []
        
        for pattern in self.upi_patterns:
            matches = pattern.findall(message)
            for match in matches:
                upi_id = match if isinstance(match, str) else match[0] if match else ""
                if upi_id and '@' in upi_id:
                    upi_ids.append(upi_id.lower())
        
        return upi_ids
    
    def _extract_phishing_urls(self, message: str) -> List[str]:
        """Extract phishing URLs using regex and keyword matching"""
        urls = []
        
        for pattern in self.url_patterns:
            matches = pattern.findall(message)
            for match in matches:
                url = match if isinstance(match, str) else match[0] if match else ""
                if url:
                    # Check if URL contains suspicious keywords (likely phishing)
                    if self._is_suspicious_url(url):
                        # Ensure proper format
                        if not url.startswith('http'):
                            url = 'http://' + url
                        urls.append(url)
        
        return urls
    
    def _is_suspicious_url(self, url: str) -> bool:
        """Check if URL is likely phishing based on keywords"""
        url_lower = url.lower()
        
        # Check for suspicious keywords in domain
        if any(keyword in url_lower for keyword in self.SUSPICIOUS_KEYWORDS):
            return True
        
        # Check for typosquatting (common bank names with variations)
        suspicious_domains = [
            'hdfc', 'icici', 'sbi', 'axis', 'kotak', 'bank',
            'paytm', 'phonepe', 'googlepay', 'amazon', 'flipkart'
        ]
        
        if any(domain in url_lower for domain in suspicious_domains):
            # Likely phishing if it's not the official domain
            return True
        
        return False
    
    def _llm_extract(self, message: str) -> Dict[str, List[str]]:
        """
        LLM-based extraction fallback.
        Returns None on failure.
        """
        try:
            import openai
            
            prompt = f"""Extract the following information from this message:
1. Bank account numbers (9-18 digits)
2. UPI IDs (format: username@provider)
3. Phishing URLs

Message: {message}

Respond in JSON format:
{{
  "bank_accounts": [...],
  "upi_ids": [...],
  "phishing_urls": [...]
}}

If nothing found, return empty arrays."""

            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data extraction expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except ImportError:
            logger.warning("OpenAI library not installed")
            return None
        except Exception as e:
            logger.warning(f"LLM extraction error: {e}")
            return None
