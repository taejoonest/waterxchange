//
//  ContentView.swift
//  WaterXchange
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        Group {
            if authManager.isAuthenticated {
                MainTabView()
                    .transition(.opacity)
            } else {
                LoginView()
                    .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.3), value: authManager.isAuthenticated)
    }
}

// MARK: - Main Tab View
struct MainTabView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        TabView(selection: $appState.selectedTab) {
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "chart.line.uptrend.xyaxis")
                }
                .tag(AppState.Tab.dashboard)
            
            BasinMapView()
                .tabItem {
                    Label("Map", systemImage: "map.fill")
                }
                .tag(AppState.Tab.map)
            
            TradeView()
                .tabItem {
                    Label("Trade", systemImage: "arrow.left.arrow.right")
                }
                .tag(AppState.Tab.trade)
            
            OrdersView()
                .tabItem {
                    Label("Orders", systemImage: "list.bullet.clipboard")
                }
                .tag(AppState.Tab.orders)
            
            SGMAChatView()
                .tabItem {
                    Label("SGMA", systemImage: "bubble.left.and.bubble.right")
                }
                .tag(AppState.Tab.chat)
        }
        .tint(.cyan)
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthManager())
        .environmentObject(AppState())
}
