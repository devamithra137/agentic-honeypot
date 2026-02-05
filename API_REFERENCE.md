# API Quick Reference

## Base URL
```
http://localhost:10000
```

## Authentication
All requests require Bearer token:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### 1. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "agentic-honeypot"
}
```

### 2. Main Honeypot Endpoint
```
POST /api/agentic-honeypot
```

**Headers:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "conversation_id": "string (required)",
  "message": "string (required)",
  "history": [
    {
      "role": "scammer | user",
      "content": "string"
    }
  ]
}
```

**Response (Always 200 OK):**
```json
{
  "scam_detected": boolean,
  "agent_activated": boolean,
  "agent_reply": "string",
  "engagement_metrics": {
    "turn_count": number,
    "engagement_duration": "string"
  },
  "extracted_intelligence": {
    "bank_accounts": ["string"],
    "upi_ids": ["string"],
    "phishing_urls": ["string"]
  },
  "status": "success | error"
}
```

## Example Requests

### Example 1: Simple Scam Detection
```bash
curl -X POST http://localhost:10000/api/agentic-honeypot \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_001",
    "message": "Your account is blocked. Send OTP immediately.",
    "history": []
  }'
```

### Example 2: Multi-turn Conversation
```bash
curl -X POST http://localhost:10000/api/agentic-honeypot \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_001",
    "message": "Transfer to 1234567890 or account will be deleted",
    "history": [
      {"role": "scammer", "content": "Your account is blocked"},
      {"role": "user", "content": "What should I do?"}
    ]
  }'
```

### Example 3: Python
```python
import requests

url = "http://localhost:10000/api/agentic-honeypot"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

data = {
    "conversation_id": "conv_001",
    "message": "Send payment to scammer@paytm",
    "history": []
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Example 4: JavaScript
```javascript
fetch('http://localhost:10000/api/agentic-honeypot', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    conversation_id: 'conv_001',
    message: 'Click here to verify: http://fake-bank.com',
    history: []
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success (even on handled errors) |
| 401 | Unauthorized (invalid or missing API key) |
| 422 | Validation Error (malformed request body) |

## Response Status Field

- `"success"`: Request processed successfully
- `"error"`: Error occurred but safely handled (still returns valid JSON)

## Intelligence Extraction Patterns

### Bank Accounts
- 9-18 digit numbers
- Format: Account number or A/C: 1234567890

### UPI IDs
- Format: username@provider
- Providers: paytm, okaxis, okhdfcbank, okicici, oksbi, ybl, etc.

### Phishing URLs
- Any URL with suspicious keywords
- Keywords: verify, account, bank, payment, kyc, etc.

## Testing

Run the test suite:
```bash
# Set API_KEY environment variable
export API_KEY=your_test_key

# Run tests
python test_api.py
```

Or test manually:
```bash
# Health check
curl http://localhost:10000/health

# Test scam detection
curl -X POST http://localhost:10000/api/agentic-honeypot \
  -H "Authorization: Bearer test_key" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test", "message": "Your account is blocked", "history": []}'
```

## Notes

1. **Always valid JSON**: API never crashes, always returns proper JSON
2. **No null values**: Arrays are always empty `[]`, never `null`
3. **Consistent schema**: Every response has same structure
4. **Bearer auth required**: All requests need valid API key
5. **In-memory state**: Conversation state is not persisted across restarts
