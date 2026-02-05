# Agentic Honey-Pot – AI Scam Engagement System

A production-ready FastAPI backend that detects scam attempts and autonomously engages scammers to extract intelligence while maintaining a believable human persona.

## 🎯 Features

- **Scam Detection**: Keyword-based + optional LLM-based intent detection
- **Autonomous Agent**: AI agent that engages scammers with realistic responses
- **Intelligence Extraction**: Extracts bank accounts, UPI IDs, and phishing URLs
- **Multi-turn Conversations**: Maintains conversation state and metrics
- **Fault Tolerant**: Never crashes, always returns valid JSON
- **Bearer Token Auth**: Secure API key authentication

## 📋 Requirements

- Python 3.10+
- FastAPI
- OpenAI API key (optional, for enhanced LLM features)

## 🚀 Quick Start

### 1. Clone/Download the Project

```bash
cd agentic-honeypot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set your API key:

```env
API_KEY=your_secret_api_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional
PORT=10000
```

**IMPORTANT**: `API_KEY` is mandatory. Without it, all requests will return 401.

### 4. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 10000
```

Or use the built-in runner:

```bash
python main.py
```

The API will be available at `http://localhost:10000`

## 📡 API Usage

### Authentication

All requests require Bearer token authentication:

```bash
Authorization: Bearer YOUR_API_KEY
```

### Endpoint: POST /api/agentic-honeypot

**Request Body:**

```json
{
  "conversation_id": "conv_123",
  "message": "Your account has been blocked. Send payment to unlock.",
  "history": [
    {"role": "scammer", "content": "Hello, this is bank support"},
    {"role": "user", "content": "What's wrong?"}
  ]
}
```

**Response:**

```json
{
  "scam_detected": true,
  "agent_activated": true,
  "agent_reply": "Oh no! What should I do to fix this?",
  "engagement_metrics": {
    "turn_count": 2,
    "engagement_duration": "45s"
  },
  "extracted_intelligence": {
    "bank_accounts": ["1234567890"],
    "upi_ids": ["scammer@paytm"],
    "phishing_urls": ["http://fake-bank.com"]
  },
  "status": "success"
}
```

### Health Check

```bash
GET /health
```

## 🧪 Testing

### Test with curl:

```bash
# Health check
curl http://localhost:10000/health

# Test scam detection
curl -X POST http://localhost:10000/api/agentic-honeypot \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test_123",
    "message": "Your account is blocked. Send OTP to verify.",
    "history": []
  }'
```

### Test with Python:

```python
import requests

API_KEY = "your_api_key"
url = "http://localhost:10000/api/agentic-honeypot"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "conversation_id": "conv_001",
    "message": "Urgent: Your account will be blocked. Click here to verify KYC.",
    "history": []
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

## 🏗️ Project Structure

```
agentic-honeypot/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── .env.example                    # Environment variables template
├── README.md                       # This file
└── app/
    ├── __init__.py                # Package initialization
    ├── models.py                  # Pydantic request/response models
    ├── intent_detector.py         # Scam detection logic
    ├── agent.py                   # AI engagement agent
    ├── intelligence_extractor.py  # Extract bank accounts, UPI IDs, URLs
    ├── conversation_manager.py    # Conversation state management
    └── response_builder.py        # Response formatting (single source of truth)
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | Bearer token for API authentication |
| `OPENAI_API_KEY` | No | OpenAI API key for enhanced LLM features |
| `PORT` | No | Server port (default: 10000) |

### Without OpenAI API Key

The system works fully without OpenAI:
- Uses keyword-based scam detection (fast, reliable)
- Uses template-based agent responses (consistent)
- Uses regex-based intelligence extraction

### With OpenAI API Key

Enhanced capabilities:
- LLM-based scam detection for complex cases
- Context-aware agent responses
- Improved intelligence extraction

## 🚢 Deployment

### Deploy to Render

1. Create new Web Service on Render
2. Connect your repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
4. Add environment variables:
   - `API_KEY`: Your secret key
   - `OPENAI_API_KEY`: (optional)

### Deploy to Railway

1. Create new project on Railway
2. Connect repository
3. Configure:
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
4. Add environment variables in settings

### Deploy with Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

Build and run:

```bash
docker build -t agentic-honeypot .
docker run -p 10000:10000 -e API_KEY=your_key agentic-honeypot
```

## 🛡️ Security Features

- **Authentication**: Bearer token on all requests
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Never exposes internal errors
- **Safe Defaults**: All errors return neutral responses
- **No Data Persistence**: In-memory only (no database attacks)

## 🐛 Troubleshooting

### 401 Unauthorized

- Check that `API_KEY` is set in environment variables
- Verify Bearer token is correctly formatted: `Authorization: Bearer YOUR_KEY`

### Missing Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Port Already in Use

Change port in `.env`:

```env
PORT=8000
```

Or specify when running:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📊 Response Schema

The API ALWAYS returns this exact structure:

```typescript
{
  scam_detected: boolean,
  agent_activated: boolean,
  agent_reply: string,
  engagement_metrics: {
    turn_count: number,
    engagement_duration: string
  },
  extracted_intelligence: {
    bank_accounts: string[],
    upi_ids: string[],
    phishing_urls: string[]
  },
  status: "success" | "error"
}
```

**Never null, never missing keys, always valid JSON.**

## 🎓 How It Works

1. **Request arrives** with scammer message
2. **Intent Detector** analyzes for scam patterns
3. **Agent activates** if scam detected
4. **Agent generates** believable human response
5. **Extractor scans** for intelligence (accounts, UPIs, URLs)
6. **Response built** with strict schema compliance
7. **JSON returned** to client

## 📝 License

MIT License - use freely for hackathons and commercial projects.

## 🤝 Support

For issues or questions:
1. Check logs: `tail -f app.log`
2. Verify environment variables
3. Test with curl examples above

---

**Built for stability, evaluated by machines, ready for production.**
