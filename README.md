# 🌊 WaterXchange

**A water trading platform for California farmers with SGMA compliance powered by AI.**

## Features

- 📱 **Native iOS App** (SwiftUI) — Beautiful farmer trading interface
- 🤖 **SGMA AI Assistant** — Knowledge graph + LLM for regulatory compliance
- ⚡ **Algorithmic Matching** — Automated water transfer matching engine
- 🔐 **Secure Authentication** — JWT-based farmer accounts

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    iOS App (SwiftUI)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Login   │ │Dashboard│ │ Trading │ │ SGMA    │           │
│  │         │ │         │ │         │ │ Chat    │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Python)                    │
│  /auth  /orders  /matching  /chat  /balance                 │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   PostgreSQL      Knowledge Graph      LLM API
   (Users/Orders)  (SGMA Rules)        (Claude/OpenAI)
```

## Project Structure

```
waterxchange/
├── ios/                      # SwiftUI iOS App
│   └── WaterXchange/
│       ├── App/
│       ├── Views/
│       ├── ViewModels/
│       ├── Models/
│       ├── Services/
│       └── Resources/
│
├── backend/                  # FastAPI Backend
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── knowledge_graph/
│
├── data/                     # Seed data
│   └── sgma_regulations.json
│
└── README.md
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### iOS App

1. Open `ios/WaterXchange.xcodeproj` in Xcode
2. Select your target device/simulator
3. Update `Config.swift` with your backend URL
4. Build and run (⌘+R)

## Demo Flow

1. **Login** — Farmer authenticates with email/password
2. **Dashboard** — View water balance, market prices, active orders
3. **Trade** — Create buy/sell orders for water rights
4. **SGMA Chat** — Ask AI about transfer compliance
5. **Match** — System automatically matches compatible orders

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Authenticate farmer |
| `/auth/register` | POST | Create new account |
| `/orders` | GET | List user's orders |
| `/orders` | POST | Create new order |
| `/orders/{id}` | DELETE | Cancel order |
| `/market/book` | GET | Get order book |
| `/market/price` | GET | Get current market price |
| `/chat` | POST | SGMA AI assistant |
| `/balance` | GET | Get water balance |

## Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost/waterxchange
JWT_SECRET=your-secret-key
OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY
```

## License

MIT
