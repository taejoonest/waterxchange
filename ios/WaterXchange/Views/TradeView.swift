//
//  TradeView.swift
//  WaterXchange
//

import SwiftUI

struct TradeView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = TradeViewModel()
    
    @State private var selectedOrderType: OrderType = .buy
    @State private var quantity = ""
    @State private var price = ""
    @State private var showConfirmation = false
    
    var totalValue: Double {
        (Double(quantity) ?? 0) * (Double(price) ?? 0)
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Order type selector
                    OrderTypeSelector(selectedType: $selectedOrderType)
                    
                    // Price info
                    MarketInfoBar(
                        bestBid: viewModel.orderBook?.bids.first?.pricePerAF,
                        bestAsk: viewModel.orderBook?.asks.first?.pricePerAF
                    )
                    
                    // Order form
                    VStack(spacing: 20) {
                        // Quantity input
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Quantity")
                                    .foregroundColor(.gray)
                                Spacer()
                                Text("Balance: \(String(format: "%.0f", authManager.currentUser?.waterBalanceAF ?? 0)) AF")
                                    .font(.caption)
                                    .foregroundColor(.cyan)
                            }
                            
                            HStack {
                                TextField("0", text: $quantity)
                                    .keyboardType(.decimalPad)
                                    .font(.title2.bold())
                                    .foregroundColor(.white)
                                
                                Text("AF")
                                    .foregroundColor(.gray)
                                
                                // Quick fill buttons
                                HStack(spacing: 8) {
                                    QuickFillButton(title: "25%") {
                                        let bal = authManager.currentUser?.waterBalanceAF ?? 0
                                        quantity = String(format: "%.0f", bal * 0.25)
                                    }
                                    QuickFillButton(title: "50%") {
                                        let bal = authManager.currentUser?.waterBalanceAF ?? 0
                                        quantity = String(format: "%.0f", bal * 0.5)
                                    }
                                    QuickFillButton(title: "Max") {
                                        let bal = authManager.currentUser?.waterBalanceAF ?? 0
                                        quantity = String(format: "%.0f", bal)
                                    }
                                }
                            }
                            .padding()
                            .background(Color.white.opacity(0.05))
                            .cornerRadius(12)
                        }
                        
                        // Price input
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Price per AF")
                                    .foregroundColor(.gray)
                                Spacer()
                                if let market = viewModel.marketPrice?.displayPrice {
                                    Button {
                                        price = String(format: "%.0f", market)
                                    } label: {
                                        Text("Market: $\(String(format: "%.0f", market))")
                                            .font(.caption)
                                            .foregroundColor(.cyan)
                                    }
                                }
                            }
                            
                            HStack {
                                Text("$")
                                    .foregroundColor(.gray)
                                
                                TextField("0", text: $price)
                                    .keyboardType(.decimalPad)
                                    .font(.title2.bold())
                                    .foregroundColor(.white)
                                
                                Text("USD")
                                    .foregroundColor(.gray)
                            }
                            .padding()
                            .background(Color.white.opacity(0.05))
                            .cornerRadius(12)
                        }
                        
                        // Total value
                        HStack {
                            Text("Total Value")
                                .foregroundColor(.gray)
                            Spacer()
                            Text("$\(String(format: "%.2f", totalValue))")
                                .font(.title2.bold())
                                .foregroundColor(.white)
                        }
                        .padding()
                        .background(Color.white.opacity(0.03))
                        .cornerRadius(12)
                    }
                    .padding(.horizontal)
                    
                    // Submit button
                    Button {
                        showConfirmation = true
                    } label: {
                        HStack {
                            Image(systemName: selectedOrderType == .buy ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                            Text(selectedOrderType == .buy ? "Place Buy Order" : "Place Sell Order")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(selectedOrderType == .buy ? Color.green : Color.orange)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(quantity.isEmpty || price.isEmpty)
                    .opacity(quantity.isEmpty || price.isEmpty ? 0.5 : 1)
                    .padding(.horizontal)
                    
                    // Order book
                    OrderBookView(orderBook: viewModel.orderBook)
                        .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .background(Color(red: 0.05, green: 0.1, blue: 0.2))
            .navigationTitle("Trade")
            .task {
                await viewModel.loadData(basin: authManager.currentUser?.basin ?? "Kern County")
            }
            .alert("Confirm Order", isPresented: $showConfirmation) {
                Button("Cancel", role: .cancel) { }
                Button(selectedOrderType == .buy ? "Buy" : "Sell") {
                    Task {
                        await viewModel.placeOrder(
                            type: selectedOrderType,
                            quantity: Double(quantity) ?? 0,
                            price: Double(price) ?? 0
                        )
                        if viewModel.orderSuccess {
                            quantity = ""
                            price = ""
                        }
                    }
                }
            } message: {
                Text("\(selectedOrderType.displayName) \(quantity) AF at $\(price)/AF\nTotal: $\(String(format: "%.2f", totalValue))")
            }
            .alert("Order Placed!", isPresented: $viewModel.orderSuccess) {
                Button("OK") { }
            } message: {
                Text("Your \(selectedOrderType.displayName.lowercased()) order has been submitted to the market.")
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }
}

// MARK: - Order Type Selector
struct OrderTypeSelector: View {
    @Binding var selectedType: OrderType
    
    var body: some View {
        HStack(spacing: 0) {
            ForEach(OrderType.allCases, id: \.self) { type in
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        selectedType = type
                    }
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: type == .buy ? "arrow.down.circle" : "arrow.up.circle")
                            .font(.title2)
                        Text(type.displayName)
                            .font(.headline)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(
                        selectedType == type
                            ? (type == .buy ? Color.green : Color.orange)
                            : Color.clear
                    )
                    .foregroundColor(selectedType == type ? .white : .gray)
                }
            }
        }
        .background(Color.white.opacity(0.05))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}

// MARK: - Market Info Bar
struct MarketInfoBar: View {
    let bestBid: Double?
    let bestAsk: Double?
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("Best Bid")
                    .font(.caption)
                    .foregroundColor(.gray)
                Text(bestBid != nil ? "$\(String(format: "%.0f", bestBid!))" : "--")
                    .font(.headline)
                    .foregroundColor(.green)
            }
            
            Spacer()
            
            if let bid = bestBid, let ask = bestAsk {
                VStack {
                    Text("Spread")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text("$\(String(format: "%.0f", ask - bid))")
                        .font(.headline)
                        .foregroundColor(.white)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing) {
                Text("Best Ask")
                    .font(.caption)
                    .foregroundColor(.gray)
                Text(bestAsk != nil ? "$\(String(format: "%.0f", bestAsk!))" : "--")
                    .font(.headline)
                    .foregroundColor(.red)
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}

// MARK: - Quick Fill Button
struct QuickFillButton: View {
    let title: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.cyan.opacity(0.2))
                .foregroundColor(.cyan)
                .cornerRadius(4)
        }
    }
}

// MARK: - Order Book View
struct OrderBookView: View {
    let orderBook: OrderBook?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Order Book")
                .font(.headline)
                .foregroundColor(.white)
            
            HStack(alignment: .top, spacing: 16) {
                // Bids
                VStack(spacing: 8) {
                    HStack {
                        Text("Qty")
                        Spacer()
                        Text("Bid")
                    }
                    .font(.caption)
                    .foregroundColor(.gray)
                    
                    ForEach(orderBook?.bids ?? []) { bid in
                        HStack {
                            Text("\(String(format: "%.0f", bid.totalQuantityAF))")
                            Spacer()
                            Text("$\(String(format: "%.0f", bid.pricePerAF))")
                        }
                        .font(.subheadline)
                        .foregroundColor(.green)
                        .padding(.vertical, 2)
                        .background(
                            GeometryReader { geo in
                                Color.green.opacity(0.1)
                                    .frame(width: geo.size.width * min(bid.totalQuantityAF / 100, 1))
                            }
                        )
                    }
                }
                .frame(maxWidth: .infinity)
                
                // Asks
                VStack(spacing: 8) {
                    HStack {
                        Text("Ask")
                        Spacer()
                        Text("Qty")
                    }
                    .font(.caption)
                    .foregroundColor(.gray)
                    
                    ForEach(orderBook?.asks ?? []) { ask in
                        HStack {
                            Text("$\(String(format: "%.0f", ask.pricePerAF))")
                            Spacer()
                            Text("\(String(format: "%.0f", ask.totalQuantityAF))")
                        }
                        .font(.subheadline)
                        .foregroundColor(.red)
                        .padding(.vertical, 2)
                        .background(
                            GeometryReader { geo in
                                HStack {
                                    Spacer()
                                    Color.red.opacity(0.1)
                                        .frame(width: geo.size.width * min(ask.totalQuantityAF / 100, 1))
                                }
                            }
                        )
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

// MARK: - View Model
@MainActor
class TradeViewModel: ObservableObject {
    @Published var orderBook: OrderBook?
    @Published var marketPrice: MarketPrice?
    @Published var isLoading = false
    @Published var orderSuccess = false
    @Published var errorMessage: String?
    
    func loadData(basin: String) async {
        isLoading = true
        
        do {
            async let bookTask = APIService.shared.getOrderBook(basin: basin)
            async let priceTask = APIService.shared.getMarketPrice(basin: basin)
            
            orderBook = try await bookTask
            marketPrice = try await priceTask
        } catch {
            print("Error loading trade data: \(error)")
        }
        
        isLoading = false
    }
    
    func placeOrder(type: OrderType, quantity: Double, price: Double) async {
        isLoading = true
        errorMessage = nil
        
        do {
            _ = try await APIService.shared.createOrder(type: type, quantity: quantity, price: price)
            orderSuccess = true
            
            // Refresh order book
            if let basin = orderBook?.basin {
                await loadData(basin: basin)
            }
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
}

#Preview {
    TradeView()
        .environmentObject(AuthManager())
}
