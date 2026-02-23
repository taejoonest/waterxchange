//
//  OrdersView.swift
//  WaterXchange
//

import SwiftUI

struct OrdersView: View {
    @StateObject private var viewModel = OrdersViewModel()
    @State private var selectedFilter: OrderFilter = .all
    
    enum OrderFilter: String, CaseIterable {
        case all = "All"
        case open = "Open"
        case filled = "Filled"
        case cancelled = "Cancelled"
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Filter tabs
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(OrderFilter.allCases, id: \.self) { filter in
                            FilterChip(
                                title: filter.rawValue,
                                isSelected: selectedFilter == filter
                            ) {
                                selectedFilter = filter
                                Task {
                                    await viewModel.loadOrders(filter: filter)
                                }
                            }
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical, 12)
                .background(Color.white.opacity(0.03))
                
                // Orders list
                if viewModel.isLoading {
                    Spacer()
                    ProgressView()
                        .tint(.cyan)
                    Spacer()
                } else if viewModel.orders.isEmpty {
                    EmptyOrdersView()
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(viewModel.orders) { order in
                                OrderCard(order: order) {
                                    Task {
                                        await viewModel.cancelOrder(id: order.id)
                                    }
                                }
                            }
                        }
                        .padding()
                    }
                }
            }
            .background(Color(red: 0.05, green: 0.1, blue: 0.2))
            .navigationTitle("My Orders")
            .refreshable {
                await viewModel.loadOrders(filter: selectedFilter)
            }
            .task {
                await viewModel.loadOrders(filter: selectedFilter)
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }
}

// MARK: - Filter Chip
struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? Color.cyan : Color.white.opacity(0.05))
                .foregroundColor(isSelected ? .black : .white)
                .cornerRadius(20)
        }
    }
}

// MARK: - Order Card
struct OrderCard: View {
    let order: Order
    let onCancel: () -> Void
    
    @State private var showCancelAlert = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                // Order type badge
                HStack(spacing: 4) {
                    Image(systemName: order.orderType == .buy ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                    Text(order.orderType.displayName.uppercased())
                        .font(.caption.bold())
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(order.orderType == .buy ? Color.green.opacity(0.2) : Color.orange.opacity(0.2))
                .foregroundColor(order.orderType == .buy ? .green : .orange)
                .cornerRadius(8)
                
                Spacer()
                
                // Status badge
                Text(order.status.displayName)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(statusColor.opacity(0.2))
                    .foregroundColor(statusColor)
                    .cornerRadius(8)
            }
            
            // Order details
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("\(String(format: "%.0f", order.quantityAF)) AF")
                        .font(.title2.bold())
                        .foregroundColor(.white)
                    
                    Text("@ $\(String(format: "%.0f", order.pricePerAF))/AF")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text("$\(String(format: "%.0f", order.totalValue))")
                        .font(.title3.bold())
                        .foregroundColor(.white)
                    
                    Text("Total Value")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
            
            // Progress bar for partially filled
            if order.status == .partiallyFilled || order.filledQuantityAF > 0 {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("Filled")
                            .font(.caption)
                            .foregroundColor(.gray)
                        Spacer()
                        Text("\(String(format: "%.0f", order.filledQuantityAF)) / \(String(format: "%.0f", order.quantityAF)) AF")
                            .font(.caption)
                            .foregroundColor(.white)
                    }
                    
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Rectangle()
                                .fill(Color.white.opacity(0.1))
                                .frame(height: 4)
                                .cornerRadius(2)
                            
                            Rectangle()
                                .fill(Color.cyan)
                                .frame(width: geo.size.width * (order.filledQuantityAF / order.quantityAF), height: 4)
                                .cornerRadius(2)
                        }
                    }
                    .frame(height: 4)
                }
            }
            
            // Footer with date and actions
            HStack {
                HStack(spacing: 4) {
                    Image(systemName: "clock")
                    Text(order.createdAt, style: .relative)
                }
                .font(.caption)
                .foregroundColor(.gray)
                
                Spacer()
                
                if order.status == .open || order.status == .partiallyFilled {
                    Button {
                        showCancelAlert = true
                    } label: {
                        Text("Cancel")
                            .font(.caption.bold())
                            .foregroundColor(.red)
                    }
                }
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(16)
        .alert("Cancel Order?", isPresented: $showCancelAlert) {
            Button("Keep Order", role: .cancel) { }
            Button("Cancel Order", role: .destructive) {
                onCancel()
            }
        } message: {
            Text("This will remove your order from the market.")
        }
    }
    
    var statusColor: Color {
        switch order.status {
        case .open: return .cyan
        case .partiallyFilled: return .yellow
        case .filled: return .green
        case .cancelled: return .gray
        }
    }
}

// MARK: - Empty State
struct EmptyOrdersView: View {
    @EnvironmentObject var appState: AppState
    
    var body: some View {
        VStack(spacing: 16) {
            Spacer()
            
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 64))
                .foregroundColor(.gray)
            
            Text("No Orders Found")
                .font(.title2.bold())
                .foregroundColor(.white)
            
            Text("Start trading to see your orders here")
                .font(.subheadline)
                .foregroundColor(.gray)
            
            Button {
                appState.selectedTab = .trade
            } label: {
                HStack {
                    Image(systemName: "plus.circle.fill")
                    Text("Place an Order")
                }
                .fontWeight(.semibold)
                .padding()
                .background(Color.cyan)
                .foregroundColor(.black)
                .cornerRadius(12)
            }
            .padding(.top)
            
            Spacer()
        }
    }
}

// MARK: - View Model
@MainActor
class OrdersViewModel: ObservableObject {
    @Published var orders: [Order] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    func loadOrders(filter: OrdersView.OrderFilter) async {
        isLoading = true
        
        do {
            let statusFilter: String? = filter == .all ? nil : filter.rawValue.lowercased()
            let response = try await APIService.shared.getOrders(status: statusFilter)
            orders = response.orders
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    func cancelOrder(id: Int) async {
        do {
            _ = try await APIService.shared.cancelOrder(id: id)
            // Remove from local list or reload
            orders.removeAll { $0.id == id }
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    OrdersView()
        .environmentObject(AppState())
}
