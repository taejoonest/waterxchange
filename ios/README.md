# WaterXchange iOS App

A SwiftUI iOS application for water trading in California.

## Requirements

- Xcode 15.0+
- iOS 17.0+
- macOS Sonoma 14.0+ (for development)

## Setup

### 1. Create Xcode Project

Since we can't generate `.xcodeproj` files directly, follow these steps:

1. Open Xcode
2. Create a new project: **File → New → Project**
3. Select **iOS → App**
4. Configure:
   - Product Name: `WaterXchange`
   - Team: Your Apple Developer Team
   - Organization Identifier: `com.yourcompany`
   - Interface: **SwiftUI**
   - Language: **Swift**
   - Storage: **None**
5. Save to the `ios/` folder

### 2. Add Source Files

After creating the project:

1. Delete the auto-generated `ContentView.swift` and `WaterXchangeApp.swift`
2. Drag all files from the `WaterXchange/` folder into your Xcode project
3. Make sure "Copy items if needed" is **unchecked** (files are already in place)
4. Ensure all files are added to the target

### 3. Configure the Project

1. Select the project in the navigator
2. Go to **Signing & Capabilities**
3. Add your Team for signing
4. Enable **App Transport Security** exceptions for local development

### 4. Update API URL

In `Config.swift`, update the `apiBaseURL`:

```swift
// For simulator (localhost works)
static let apiBaseURL = "http://localhost:8000"

// For physical device (use your Mac's IP)
static let apiBaseURL = "http://192.168.1.XXX:8000"
```

Find your Mac's IP: **System Preferences → Network**

## Project Structure

```
WaterXchange/
├── WaterXchangeApp.swift    # App entry point
├── ContentView.swift        # Root view with auth routing
├── Config.swift             # API configuration
│
├── Models/
│   ├── User.swift           # User & auth models
│   ├── Order.swift          # Order models
│   ├── Market.swift         # Market data models
│   └── Chat.swift           # Chat message models
│
├── Views/
│   ├── LoginView.swift      # Login screen
│   ├── RegisterView.swift   # Registration screen
│   ├── DashboardView.swift  # Main dashboard
│   ├── TradeView.swift      # Buy/sell interface
│   ├── OrdersView.swift     # Order management
│   └── SGMAChatView.swift   # SGMA AI assistant
│
├── Services/
│   ├── APIService.swift     # API client
│   └── AuthManager.swift    # Authentication state
│
├── Assets.xcassets/         # App icons & colors
└── Info.plist               # App configuration
```

## Features

### 1. Authentication
- Email/password login
- Registration with basin selection
- Persistent login with Keychain

### 2. Dashboard
- Water balance display
- Market price ticker
- Quick action buttons
- Order book preview
- Recent transactions

### 3. Trading
- Buy/sell order form
- Real-time order book
- Market price integration
- Quick fill buttons (25%, 50%, Max)

### 4. Order Management
- View all orders
- Filter by status
- Cancel open orders
- Progress tracking for partial fills

### 5. SGMA Assistant
- AI-powered chat interface
- Knowledge graph retrieval
- Compliance checking
- Suggested questions

## Running the App

### With Simulator

1. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. In Xcode, select an iPhone simulator
3. Press ⌘+R to build and run

### With Physical Device

1. Start the backend with your Mac's IP:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --reload
   ```

2. Update `Config.swift` with your Mac's IP
3. Connect your iPhone via USB
4. Select your device in Xcode
5. Press ⌘+R to build and run

## Troubleshooting

### "Could not connect to server"
- Ensure backend is running
- Check the API URL in `Config.swift`
- For physical device, ensure phone and Mac are on same network

### "Invalid certificate" errors
- The app allows arbitrary loads for development
- For production, use HTTPS with valid certificate

### Build errors
- Clean build folder: ⌘+Shift+K
- Delete derived data: Xcode → Preferences → Locations → Derived Data

## Design System

### Colors
- Primary: Cyan (#00D4EA)
- Background: Dark blue (#0D1A33)
- Buy/Bid: Green
- Sell/Ask: Orange/Red

### Typography
- System fonts with rounded design
- Bold headers, regular body text

### Spacing
- 16pt base unit
- 20-24pt section spacing
- 12pt component spacing
