//
//  WaterXchangeApp.swift
//  WaterXchange
//
//  Water trading platform for California farmers
//

import SwiftUI

@main
struct WaterXchangeApp: App {
    @StateObject private var authManager = AuthManager()
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager)
                .environmentObject(appState)
        }
    }
}

// MARK: - App State
class AppState: ObservableObject {
    @Published var selectedTab: Tab = .dashboard
    
    enum Tab {
        case dashboard
        case map
        case trade
        case orders
        case chat
    }
}
