//
//  DashboardView.swift
//  WaterXchange
//

import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = DashboardViewModel()
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Balance card
                    BalanceCard(
                        balance: viewModel.balance?.waterBalanceAF ?? authManager.currentUser?.waterBalanceAF ?? 0,
                        basin: viewModel.balance?.basin ?? authManager.currentUser?.basin ?? "Loading..."
                    )
                    
                    // Market price card
                    MarketPriceCard(price: viewModel.marketPrice)
                    
                    // Quick actions
                    QuickActionsRow()
                    
                    // Order book preview
                    OrderBookPreview(orderBook: viewModel.orderBook)
                    
                    // Recent transactions
                    RecentTransactionsCard(transactions: viewModel.recentTransactions)
                }
                .padding()
            }
            .background(Color(red: 0.05, green: 0.1, blue: 0.2))
            .navigationTitle("Dashboard")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button(role: .destructive) {
                            authManager.logout()
                        } label: {
                            Label("Sign Out", systemImage: "rectangle.portrait.and.arrow.right")
                        }
                    } label: {
                        Image(systemName: "person.circle")
                            .font(.title2)
                    }
                }
            }
            .refreshable {
                await viewModel.refresh()
            }
            .task {
                await viewModel.loadData(basin: authManager.currentUser?.basin ?? "Kern County")
            }
        }
    }
}

// MARK: - Balance Card
struct BalanceCard: View {
    let balance: Double
    let basin: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Water Balance")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.7))
                    
                    HStack(alignment: .firstTextBaseline, spacing: 4) {
                        Text(String(format: "%.0f", balance))
                            .font(.system(size: 48, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                        Text("AF")
                            .font(.title3)
                            .foregroundColor(.white.opacity(0.7))
                    }
                }
                
                Spacer()
                
                Image(systemName: "drop.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.cyan, .blue],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
            }
            
            HStack {
                Image(systemName: "mappin.circle")
                Text(basin)
            }
            .font(.caption)
            .foregroundColor(.white.opacity(0.6))
        }
        .padding(24)
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.1, green: 0.2, blue: 0.4),
                    Color(red: 0.15, green: 0.25, blue: 0.45)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(20)
        .shadow(color: .black.opacity(0.3), radius: 10, y: 5)
    }
}

// MARK: - Market Price Card
struct MarketPriceCard: View {
    let price: MarketPrice?
    
    var body: some View {
        HStack(spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Market Price")
                    .font(.caption)
                    .foregroundColor(.gray)
                
                HStack(alignment: .firstTextBaseline) {
                    Text("$\(String(format: "%.0f", price?.displayPrice ?? 0))")
                        .font(.title.bold())
                        .foregroundColor(.white)
                    Text("/AF")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text("24h Volume")
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Text("\(String(format: "%.0f", price?.volume24h ?? 0)) AF")
                    .font(.headline)
                    .foregroundColor(.white)
            }
            
            if let high = price?.high24h, let low = price?.low24h {
                VStack(alignment: .trailing, spacing: 4) {
                    HStack {
                        Image(systemName: "arrow.up")
                            .foregroundColor(.green)
                        Text("$\(String(format: "%.0f", high))")
                    }
                    HStack {
                        Image(systemName: "arrow.down")
                            .foregroundColor(.red)
                        Text("$\(String(format: "%.0f", low))")
                    }
                }
                .font(.caption)
                .foregroundColor(.white)
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(16)
    }
}

// MARK: - Quick Actions
struct QuickActionsRow: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        HStack(spacing: 12) {
            QuickActionButton(
                title: "Buy",
                icon: "arrow.down.circle.fill",
                color: .green
            ) {
                appState.selectedTab = .trade
            }
            
            QuickActionButton(
                title: "Sell",
                icon: "arrow.up.circle.fill",
                color: .orange
            ) {
                appState.selectedTab = .trade
            }
            
            QuickActionButton(
                title: "Ask SGMA",
                icon: "bubble.left.and.bubble.right.fill",
                color: .cyan
            ) {
                appState.selectedTab = .chat
            }
        }
    }
}

struct QuickActionButton: View {
    let title: String
    let icon: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                Text(title)
                    .font(.caption)
                    .foregroundColor(.white)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(Color.white.opacity(0.05))
            .cornerRadius(12)
        }
    }
}

// MARK: - Order Book Preview
struct OrderBookPreview: View {
    let orderBook: OrderBook?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Order Book")
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
                if let spread = orderBook?.spread {
                    Text("Spread: $\(String(format: "%.0f", spread))")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
            
            HStack(spacing: 16) {
                // Bids (Buy orders)
                VStack(alignment: .leading, spacing: 4) {
                    Text("BIDS")
                        .font(.caption2)
                        .foregroundColor(.green)
                    
                    ForEach(orderBook?.bids.prefix(3) ?? []) { bid in
                        HStack {
                            Text("\(String(format: "%.0f", bid.totalQuantityAF))")
                            Spacer()
                            Text("$\(String(format: "%.0f", bid.pricePerAF))")
                        }
                        .font(.caption)
                        .foregroundColor(.green.opacity(0.8))
                    }
                    
                    if orderBook?.bids.isEmpty ?? true {
                        Text("No bids")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
                .frame(maxWidth: .infinity)
                
                Divider()
                    .background(Color.gray)
                
                // Asks (Sell orders)
                VStack(alignment: .trailing, spacing: 4) {
                    Text("ASKS")
                        .font(.caption2)
                        .foregroundColor(.red)
                    
                    ForEach(orderBook?.asks.prefix(3) ?? []) { ask in
                        HStack {
                            Text("$\(String(format: "%.0f", ask.pricePerAF))")
                            Spacer()
                            Text("\(String(format: "%.0f", ask.totalQuantityAF))")
                        }
                        .font(.caption)
                        .foregroundColor(.red.opacity(0.8))
                    }
                    
                    if orderBook?.asks.isEmpty ?? true {
                        Text("No asks")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
                .frame(maxWidth: .infinity)
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(16)
    }
}

// MARK: - Recent Transactions
struct RecentTransactionsCard: View {
    let transactions: [TransactionHistory]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Recent Activity")
                .font(.headline)
                .foregroundColor(.white)
            
            if transactions.isEmpty {
                Text("No recent transactions")
                    .font(.caption)
                    .foregroundColor(.gray)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                ForEach(transactions.prefix(5), id: \.id) { tx in
                    HStack {
                        Image(systemName: tx.type == "bought" ? "arrow.down.circle" : "arrow.up.circle")
                            .foregroundColor(tx.type == "bought" ? .green : .orange)
                        
                        VStack(alignment: .leading) {
                            Text("\(tx.type.capitalized) \(String(format: "%.0f", tx.quantityAF)) AF")
                                .font(.subheadline)
                                .foregroundColor(.white)
                            Text("@ $\(String(format: "%.0f", tx.pricePerAF))/AF")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                        
                        Spacer()
                        
                        Text("$\(String(format: "%.0f", tx.totalValue))")
                            .font(.subheadline.bold())
                            .foregroundColor(.white)
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(16)
    }
}

// MARK: - View Model
@MainActor
class DashboardViewModel: ObservableObject {
    @Published var balance: Balance?
    @Published var marketPrice: MarketPrice?
    @Published var orderBook: OrderBook?
    @Published var recentTransactions: [TransactionHistory] = []
    @Published var isLoading = false
    
    func loadData(basin: String) async {
        isLoading = true
        
        async let balanceTask = APIService.shared.getBalance()
        async let priceTask = APIService.shared.getMarketPrice(basin: basin)
        async let bookTask = APIService.shared.getOrderBook(basin: basin)
        async let historyTask = APIService.shared.getTransactionHistory()
        
        do {
            balance = try await balanceTask
            marketPrice = try await priceTask
            orderBook = try await bookTask
            let history = try await historyTask
            recentTransactions = history.transactions
        } catch {
            print("Error loading dashboard: \(error)")
        }
        
        isLoading = false
    }
    
    func refresh() async {
        await loadData(basin: balance?.basin ?? "Kern County")
    }
}

#Preview {
    DashboardView()
        .environmentObject(AuthManager())
        .environmentObject(AppState())
}
