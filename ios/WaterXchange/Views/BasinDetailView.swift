//
//  BasinDetailView.swift
//  WaterXchange
//
//  Basin detail view with wells, transactions, and SGMA policies
//

import SwiftUI

struct BasinDetailView: View {
    let basin: BasinInfo
    @Environment(\.dismiss) var dismiss
    @State private var selectedTab = 0
    @State private var selectedPolicy: GSPPolicy?
    @State private var showPolicyDetail = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Basin Summary Header
                    BasinSummaryCard(basin: basin)
                    
                    // Tab selector
                    Picker("View", selection: $selectedTab) {
                        Text("Wells & Trades").tag(0)
                        Text("SGMA Policies").tag(1)
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                    
                    if selectedTab == 0 {
                        // Wells and Transactions
                        WellsSection(basin: basin)
                        TradeActivitySection(basin: basin)
                    } else {
                        // SGMA/GSP Policies
                        PoliciesSection(
                            policies: basin.gspPolicies,
                            onSelect: { policy in
                                selectedPolicy = policy
                                showPolicyDetail = true
                            }
                        )
                    }
                }
                .padding()
            }
            .background(Color(red: 0.05, green: 0.1, blue: 0.2))
            .navigationTitle(basin.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
            .sheet(isPresented: $showPolicyDetail) {
                if let policy = selectedPolicy {
                    PolicyDetailView(policy: policy, basinName: basin.name)
                }
            }
        }
    }
}

// MARK: - Basin Summary Card
struct BasinSummaryCard: View {
    let basin: BasinInfo
    
    var body: some View {
        VStack(spacing: 16) {
            // Status badge
            HStack {
                HStack(spacing: 6) {
                    Circle()
                        .fill(basin.isCritical ? Color.red : Color.green)
                        .frame(width: 8, height: 8)
                    Text(basin.isCritical ? "CRITICALLY OVERDRAFTED" : "STABLE")
                        .font(.caption.bold())
                        .foregroundColor(basin.isCritical ? .red : .green)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background((basin.isCritical ? Color.red : Color.green).opacity(0.15))
                .cornerRadius(20)
                
                Spacer()
                
                Text("106%")
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundColor(.cyan)
                + Text(" alloc")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            
            // Key metrics
            HStack(spacing: 0) {
                MetricBox(
                    title: "Allocation",
                    value: formatAF(basin.allocation),
                    unit: "AF/yr",
                    color: .cyan
                )
                MetricBox(
                    title: "Usage",
                    value: "\(Int(basin.currentUsage))%",
                    unit: "of alloc",
                    color: basin.currentUsage > 90 ? .red : (basin.currentUsage > 75 ? .orange : .green)
                )
                MetricBox(
                    title: "Traded",
                    value: formatAF(basin.totalTraded),
                    unit: "AF total",
                    color: .yellow
                )
            }
            
            // Buyer/Seller count
            HStack(spacing: 16) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.down.circle.fill")
                        .foregroundColor(.green)
                    Text("\(basin.activeBuyers) Active Buyers")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.7))
                }
                
                Spacer()
                
                HStack(spacing: 6) {
                    Image(systemName: "arrow.up.circle.fill")
                        .foregroundColor(.orange)
                    Text("\(basin.activeSellers) Active Sellers")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.7))
                }
            }
        }
        .padding(20)
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
    
    func formatAF(_ value: Double) -> String {
        if value >= 1000 {
            return String(format: "%.1fK", value / 1000)
        }
        return String(format: "%.0f", value)
    }
}

struct MetricBox: View {
    let title: String
    let value: String
    let unit: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 4) {
            Text(title)
                .font(.caption2)
                .foregroundColor(.gray)
            Text(value)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(unit)
                .font(.system(size: 9))
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .background(Color.white.opacity(0.05))
        .cornerRadius(12)
        .padding(.horizontal, 2)
    }
}

// MARK: - Wells Section
struct WellsSection: View {
    let basin: BasinInfo
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "drop.circle")
                    .foregroundColor(.cyan)
                Text("Wells (\(basin.wells.count))")
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
            }
            
            ForEach(basin.wells) { well in
                WellCard(well: well)
            }
        }
    }
}

struct WellCard: View {
    let well: WellInfo
    @State private var expanded = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Main row
            HStack(spacing: 12) {
                // Well icon
                ZStack {
                    Circle()
                        .fill(well.tradeType == "sell" ? Color.orange.opacity(0.2) : Color.green.opacity(0.2))
                        .frame(width: 40, height: 40)
                    Image(systemName: "drop.fill")
                        .foregroundColor(well.tradeType == "sell" ? .orange : .green)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(well.name)
                        .font(.subheadline.bold())
                        .foregroundColor(.white)
                    Text(well.owner)
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 2) {
                    Text("\(Int(well.totalTraded)) AF")
                        .font(.subheadline.bold())
                        .foregroundColor(well.tradeType == "sell" ? .orange : .green)
                    Text(well.tradeType == "sell" ? "Sold" : "Bought")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Image(systemName: expanded ? "chevron.up" : "chevron.down")
                    .foregroundColor(.gray)
                    .font(.caption)
            }
            .padding()
            .contentShape(Rectangle())
            .onTapGesture {
                withAnimation(.spring(response: 0.3)) {
                    expanded.toggle()
                }
            }
            
            // Expanded details
            if expanded {
                VStack(spacing: 12) {
                    Divider().background(Color.gray.opacity(0.3))
                    
                    HStack(spacing: 20) {
                        DetailStat(label: "Total Pumped", value: "\(Int(well.totalPumped)) AF", icon: "arrow.down.to.line")
                        DetailStat(label: "Last Price", value: "$\(Int(well.lastTradePrice))/AF", icon: "dollarsign.circle")
                        DetailStat(label: "Trade Volume", value: "\(Int(well.totalTraded)) AF", icon: "arrow.left.arrow.right")
                    }
                    
                    // Mini trade history bar
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Pumped vs Traded")
                            .font(.caption2)
                            .foregroundColor(.gray)
                        
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                // Total pumped bar
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(Color.white.opacity(0.1))
                                    .frame(height: 8)
                                
                                // Traded portion
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(
                                        LinearGradient(
                                            colors: [.cyan, .blue],
                                            startPoint: .leading,
                                            endPoint: .trailing
                                        )
                                    )
                                    .frame(
                                        width: geo.size.width * CGFloat(well.totalTraded / well.totalPumped),
                                        height: 8
                                    )
                            }
                        }
                        .frame(height: 8)
                        
                        Text("\(Int(well.totalTraded / well.totalPumped * 100))% of pumped water traded")
                            .font(.caption2)
                            .foregroundColor(.cyan)
                    }
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
        }
        .background(Color.white.opacity(0.05))
        .cornerRadius(12)
    }
}

struct DetailStat: View {
    let label: String
    let value: String
    let icon: String
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(.cyan)
            Text(value)
                .font(.caption.bold())
                .foregroundColor(.white)
            Text(label)
                .font(.system(size: 8))
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Trade Activity Section
struct TradeActivitySection: View {
    let basin: BasinInfo
    
    // Generate mock recent trades
    var recentTrades: [(type: String, amount: Double, price: Double, timeAgo: String)] {
        [
            ("sell", 50, 385, "2h ago"),
            ("buy", 120, 370, "5h ago"),
            ("sell", 30, 395, "1d ago"),
            ("buy", 200, 360, "2d ago"),
            ("sell", 75, 390, "3d ago"),
        ]
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "arrow.left.arrow.right.circle")
                    .foregroundColor(.yellow)
                Text("Recent Trades")
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
                Text("\(Int(basin.totalTraded)) AF total")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            
            ForEach(Array(recentTrades.enumerated()), id: \.offset) { _, trade in
                HStack {
                    Image(systemName: trade.type == "sell" ? "arrow.up.circle" : "arrow.down.circle")
                        .foregroundColor(trade.type == "sell" ? .orange : .green)
                    
                    VStack(alignment: .leading, spacing: 1) {
                        Text("\(trade.type == "sell" ? "Sold" : "Bought") \(Int(trade.amount)) AF")
                            .font(.subheadline)
                            .foregroundColor(.white)
                        Text("@ $\(Int(trade.price))/AF")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing, spacing: 1) {
                        Text("$\(Int(trade.amount * trade.price))")
                            .font(.subheadline.bold())
                            .foregroundColor(.white)
                        Text(trade.timeAgo)
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
                .padding(.vertical, 6)
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(16)
    }
}

// MARK: - Policies Section
struct PoliciesSection: View {
    let policies: [GSPPolicy]
    let onSelect: (GSPPolicy) -> Void
    
    var groupedPolicies: [PolicyCategory: [GSPPolicy]] {
        Dictionary(grouping: policies, by: { $0.category })
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                Image(systemName: "doc.text.magnifyingglass")
                    .foregroundColor(.purple)
                Text("GSP / SGMA Policies")
                    .font(.headline)
                    .foregroundColor(.white)
                Spacer()
                Text("\(policies.count) policies")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            
            Text("Tap any policy to see full regulatory text and how it affects water transfers in this basin.")
                .font(.caption)
                .foregroundColor(.gray)
            
            // Policy cards grouped by category
            ForEach(PolicyCategory.allCases, id: \.rawValue) { category in
                if let catPolicies = groupedPolicies[category], !catPolicies.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        // Category header
                        HStack(spacing: 6) {
                            Image(systemName: category.icon)
                                .foregroundColor(category.color)
                            Text(category.rawValue)
                                .font(.subheadline.bold())
                                .foregroundColor(category.color)
                        }
                        .padding(.top, 8)
                        
                        ForEach(catPolicies) { policy in
                            PolicyCard(policy: policy)
                                .onTapGesture {
                                    onSelect(policy)
                                }
                        }
                    }
                }
            }
        }
    }
}

struct PolicyCard: View {
    let policy: GSPPolicy
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Restriction indicator
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(policy.isRestriction ? Color.red.opacity(0.15) : Color.green.opacity(0.15))
                    .frame(width: 36, height: 36)
                Image(systemName: policy.isRestriction ? "exclamationmark.triangle" : "checkmark.shield")
                    .font(.caption)
                    .foregroundColor(policy.isRestriction ? .red : .green)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(policy.title)
                    .font(.subheadline.bold())
                    .foregroundColor(.white)
                
                Text(policy.section)
                    .font(.caption2)
                    .foregroundColor(.cyan)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color.cyan.opacity(0.1))
                    .cornerRadius(4)
                
                Text(policy.summary)
                    .font(.caption)
                    .foregroundColor(.gray)
                    .lineLimit(2)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundColor(.gray)
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(12)
    }
}

// MARK: - Policy Detail View
struct PolicyDetailView: View {
    let policy: GSPPolicy
    let basinName: String
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header card
                    VStack(alignment: .leading, spacing: 12) {
                        // Category badge
                        HStack {
                            HStack(spacing: 4) {
                                Image(systemName: policy.category.icon)
                                Text(policy.category.rawValue)
                            }
                            .font(.caption.bold())
                            .foregroundColor(policy.category.color)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(policy.category.color.opacity(0.15))
                            .cornerRadius(20)
                            
                            Spacer()
                            
                            // Restriction badge
                            HStack(spacing: 4) {
                                Image(systemName: policy.isRestriction ? "exclamationmark.triangle.fill" : "checkmark.shield.fill")
                                Text(policy.isRestriction ? "Restriction" : "Allowance")
                            }
                            .font(.caption.bold())
                            .foregroundColor(policy.isRestriction ? .red : .green)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background((policy.isRestriction ? Color.red : Color.green).opacity(0.15))
                            .cornerRadius(20)
                        }
                        
                        // Title
                        Text(policy.title)
                            .font(.title2.bold())
                            .foregroundColor(.white)
                        
                        // Section reference
                        HStack(spacing: 8) {
                            Image(systemName: "book.closed")
                                .foregroundColor(.cyan)
                            Text(policy.section)
                                .font(.headline)
                                .foregroundColor(.cyan)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.cyan.opacity(0.1))
                        .cornerRadius(12)
                        
                        // Basin applicability
                        HStack(spacing: 8) {
                            Image(systemName: "mappin.circle.fill")
                                .foregroundColor(.orange)
                            Text("Applies to: **\(basinName)**")
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.8))
                        }
                    }
                    .padding(20)
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
                    
                    // Summary
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "text.justify.left")
                                .foregroundColor(.purple)
                            Text("Summary")
                                .font(.headline)
                                .foregroundColor(.white)
                        }
                        
                        Text(policy.summary)
                            .font(.body)
                            .foregroundColor(.white.opacity(0.9))
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.white.opacity(0.05))
                            .cornerRadius(12)
                    }
                    
                    // Full regulatory text
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "doc.text")
                                .foregroundColor(.cyan)
                            Text("Full Regulatory Text")
                                .font(.headline)
                                .foregroundColor(.white)
                        }
                        
                        Text(policy.fullText)
                            .font(.body)
                            .foregroundColor(.white.opacity(0.85))
                            .lineSpacing(6)
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.white.opacity(0.05))
                            .cornerRadius(12)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.cyan.opacity(0.2), lineWidth: 1)
                            )
                    }
                    
                    // Impact on transfers
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "arrow.left.arrow.right.circle")
                                .foregroundColor(.yellow)
                            Text("Impact on Water Transfers")
                                .font(.headline)
                                .foregroundColor(.white)
                        }
                        
                        VStack(alignment: .leading, spacing: 8) {
                            if policy.isRestriction {
                                ImpactRow(icon: "exclamationmark.circle", text: "This policy restricts certain transfer activities", color: .red)
                                ImpactRow(icon: "clock", text: "Additional review time may be required", color: .orange)
                                ImpactRow(icon: "doc.badge.gearshape", text: "Documentation requirements apply", color: .yellow)
                            } else {
                                ImpactRow(icon: "checkmark.circle", text: "This policy enables or simplifies transfers", color: .green)
                                ImpactRow(icon: "bolt.circle", text: "Streamlined approval process available", color: .cyan)
                            }
                            
                            ImpactRow(icon: "person.2.circle", text: "Affects all users in \(basinName)", color: .purple)
                        }
                        .padding()
                        .background(Color.white.opacity(0.05))
                        .cornerRadius(12)
                    }
                    
                    // Ask SGMA Assistant button
                    Button {
                        // This would navigate to the SGMA chat with context
                        dismiss()
                    } label: {
                        HStack {
                            Image(systemName: "bubble.left.and.bubble.right.fill")
                            Text("Ask SGMA Assistant About This Policy")
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            LinearGradient(
                                colors: [.cyan, .blue],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(16)
                    }
                }
                .padding()
            }
            .background(Color(red: 0.05, green: 0.1, blue: 0.2))
            .navigationTitle("Policy Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

struct ImpactRow: View {
    let icon: String
    let text: String
    let color: Color
    
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .foregroundColor(color)
                .frame(width: 20)
            Text(text)
                .font(.subheadline)
                .foregroundColor(.white.opacity(0.8))
        }
    }
}

#Preview {
    BasinDetailView(basin: SampleData.centralValleyBasins[4])
}
