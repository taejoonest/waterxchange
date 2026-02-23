//
//  BasinMapView.swift
//  WaterXchange
//
//  Interactive Central Valley aquifer map with wells and transactions
//

import SwiftUI

// MARK: - Basin Data Model
struct BasinInfo: Identifiable {
    let id = UUID()
    let name: String
    let shortName: String
    let position: CGPoint        // Relative position (0-1 range)
    let color: Color
    let isCritical: Bool
    let allocation: Double       // Total AF
    let currentUsage: Double     // Percentage used
    let wells: [WellInfo]
    let gspPolicies: [GSPPolicy]
    let totalTraded: Double      // Total AF traded
    let activeSellers: Int
    let activeBuyers: Int
}

struct WellInfo: Identifiable {
    let id = UUID()
    let name: String
    let owner: String
    let offsetX: CGFloat         // Offset from basin center
    let offsetY: CGFloat
    let totalPumped: Double      // AF
    let totalTraded: Double      // AF
    let lastTradePrice: Double   // $/AF
    let tradeType: String        // "buy" or "sell"
}

struct GSPPolicy: Identifiable {
    let id = UUID()
    let title: String
    let section: String
    let summary: String
    let fullText: String
    let isRestriction: Bool
    let category: PolicyCategory
}

enum PolicyCategory: String, CaseIterable {
    case transfer = "Transfer Rules"
    case pumping = "Pumping Limits"
    case reporting = "Reporting"
    case sustainability = "Sustainability"
    case fees = "Fees & Charges"
    
    var icon: String {
        switch self {
        case .transfer: return "arrow.left.arrow.right.circle"
        case .pumping: return "arrow.down.to.line"
        case .reporting: return "doc.text"
        case .sustainability: return "leaf.circle"
        case .fees: return "dollarsign.circle"
        }
    }
    
    var color: Color {
        switch self {
        case .transfer: return .cyan
        case .pumping: return .orange
        case .reporting: return .purple
        case .sustainability: return .green
        case .fees: return .yellow
        }
    }
}

// MARK: - Main Basin Map View
struct BasinMapView: View {
    @State private var selectedBasin: BasinInfo?
    @State private var showDetail = false
    @State private var mapScale: CGFloat = 1.0
    @State private var mapOffset: CGSize = .zero
    @State private var showPolicyView = false
    @State private var selectedPolicy: GSPPolicy?
    
    let basins = SampleData.centralValleyBasins
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(red: 0.05, green: 0.1, blue: 0.2)
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Stats Header
                    MapStatsHeader(basins: basins)
                    
                    // Map Area
                    GeometryReader { geometry in
                        ZStack {
                            // Valley background shape
                            CentralValleyShape()
                                .fill(
                                    LinearGradient(
                                        colors: [
                                            Color(red: 0.1, green: 0.25, blue: 0.15).opacity(0.4),
                                            Color(red: 0.05, green: 0.2, blue: 0.1).opacity(0.3)
                                        ],
                                        startPoint: .top,
                                        endPoint: .bottom
                                    )
                                )
                                .overlay(
                                    CentralValleyShape()
                                        .stroke(Color.cyan.opacity(0.3), lineWidth: 1)
                                )
                            
                            // River lines
                            RiverLines()
                                .stroke(
                                    Color.cyan.opacity(0.25),
                                    style: StrokeStyle(lineWidth: 2, lineCap: .round, dash: [8, 4])
                                )
                            
                            // Basin bubbles
                            ForEach(basins) { basin in
                                BasinBubble(
                                    basin: basin,
                                    isSelected: selectedBasin?.id == basin.id,
                                    containerSize: geometry.size
                                )
                                .position(
                                    x: basin.position.x * geometry.size.width,
                                    y: basin.position.y * geometry.size.height
                                )
                                .onTapGesture {
                                    withAnimation(.spring(response: 0.4)) {
                                        selectedBasin = basin
                                        showDetail = true
                                    }
                                }
                            }
                            
                            // Transaction flow lines between basins
                            TransactionFlowLines(basins: basins, containerSize: geometry.size)
                            
                            // Map labels
                            VStack {
                                HStack {
                                    Text("CENTRAL VALLEY")
                                        .font(.caption2.bold())
                                        .foregroundColor(.white.opacity(0.3))
                                        .tracking(3)
                                    Spacer()
                                }
                                Spacer()
                                HStack {
                                    Spacer()
                                    VStack(alignment: .trailing, spacing: 2) {
                                        HStack(spacing: 4) {
                                            Circle().fill(Color.red.opacity(0.6)).frame(width: 6, height: 6)
                                            Text("Critical")
                                        }
                                        HStack(spacing: 4) {
                                            Circle().fill(Color.green.opacity(0.6)).frame(width: 6, height: 6)
                                            Text("Stable")
                                        }
                                        HStack(spacing: 4) {
                                            RoundedRectangle(cornerRadius: 1)
                                                .fill(Color.yellow.opacity(0.6))
                                                .frame(width: 12, height: 2)
                                            Text("Trades")
                                        }
                                    }
                                    .font(.caption2)
                                    .foregroundColor(.white.opacity(0.5))
                                }
                            }
                            .padding()
                        }
                    }
                    .padding(.horizontal, 8)
                }
            }
            .navigationTitle("Aquifer Map")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showDetail) {
                if let basin = selectedBasin {
                    BasinDetailView(basin: basin)
                }
            }
        }
    }
}

// MARK: - Stats Header
struct MapStatsHeader: View {
    let basins: [BasinInfo]
    
    var totalTraded: Double {
        basins.reduce(0) { $0 + $1.totalTraded }
    }
    var totalWells: Int {
        basins.reduce(0) { $0 + $1.wells.count }
    }
    var criticalCount: Int {
        basins.filter { $0.isCritical }.count
    }
    
    var body: some View {
        HStack(spacing: 0) {
            StatPill(value: "\(basins.count)", label: "Basins", color: .cyan)
            StatPill(value: "\(totalWells)", label: "Wells", color: .blue)
            StatPill(value: String(format: "%.0f", totalTraded), label: "AF Traded", color: .green)
            StatPill(value: "\(criticalCount)", label: "Critical", color: .red)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
    }
}

struct StatPill: View {
    let value: String
    let label: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .foregroundColor(color)
            Text(label)
                .font(.system(size: 9))
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.05))
        .cornerRadius(8)
        .padding(.horizontal, 2)
    }
}

// MARK: - Basin Bubble
struct BasinBubble: View {
    let basin: BasinInfo
    let isSelected: Bool
    let containerSize: CGSize
    
    @State private var pulseAnimation = false
    
    var bubbleSize: CGFloat {
        let base: CGFloat = 52
        let scale = min(basin.totalTraded / 500, 1.5)
        return base + CGFloat(scale) * 16
    }
    
    var body: some View {
        ZStack {
            // Outer glow for critical basins
            if basin.isCritical {
                Circle()
                    .fill(Color.red.opacity(0.15))
                    .frame(width: bubbleSize + 20, height: bubbleSize + 20)
                    .scaleEffect(pulseAnimation ? 1.2 : 1.0)
                    .opacity(pulseAnimation ? 0.3 : 0.6)
                    .animation(
                        .easeInOut(duration: 2).repeatForever(autoreverses: true),
                        value: pulseAnimation
                    )
            }
            
            // Main bubble
            Circle()
                .fill(
                    LinearGradient(
                        colors: [
                            basin.isCritical ? Color.red.opacity(0.7) : Color.cyan.opacity(0.6),
                            basin.isCritical ? Color.red.opacity(0.4) : Color.blue.opacity(0.5)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: bubbleSize, height: bubbleSize)
                .overlay(
                    Circle()
                        .stroke(
                            isSelected ? Color.white : Color.white.opacity(0.3),
                            lineWidth: isSelected ? 3 : 1
                        )
                )
                .shadow(color: (basin.isCritical ? Color.red : Color.cyan).opacity(0.4), radius: 8)
            
            // Basin label
            VStack(spacing: 1) {
                Text(basin.shortName)
                    .font(.system(size: 9, weight: .bold))
                    .foregroundColor(.white)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
                
                Text("\(Int(basin.totalTraded))")
                    .font(.system(size: 7, weight: .medium, design: .rounded))
                    .foregroundColor(.white.opacity(0.8))
                + Text(" AF")
                    .font(.system(size: 6))
                    .foregroundColor(.white.opacity(0.6))
            }
            .frame(width: bubbleSize - 8)
            
            // Well dots around basin
            ForEach(basin.wells) { well in
                WellDot(well: well)
                    .offset(x: well.offsetX, y: well.offsetY)
            }
        }
        .scaleEffect(isSelected ? 1.15 : 1.0)
        .onAppear { pulseAnimation = true }
    }
}

// MARK: - Well Dot
struct WellDot: View {
    let well: WellInfo
    
    var body: some View {
        Circle()
            .fill(well.tradeType == "sell" ? Color.orange : Color.green)
            .frame(width: 7, height: 7)
            .overlay(
                Circle()
                    .stroke(Color.white.opacity(0.5), lineWidth: 0.5)
            )
            .shadow(color: (well.tradeType == "sell" ? Color.orange : Color.green).opacity(0.5), radius: 3)
    }
}

// MARK: - Central Valley Shape
struct CentralValleyShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let w = rect.width
        let h = rect.height
        
        // Simplified Central Valley outline
        path.move(to: CGPoint(x: w * 0.35, y: h * 0.02))
        path.addCurve(
            to: CGPoint(x: w * 0.55, y: h * 0.15),
            control1: CGPoint(x: w * 0.45, y: h * 0.03),
            control2: CGPoint(x: w * 0.52, y: h * 0.08)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.7, y: h * 0.35),
            control1: CGPoint(x: w * 0.62, y: h * 0.2),
            control2: CGPoint(x: w * 0.68, y: h * 0.28)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.75, y: h * 0.6),
            control1: CGPoint(x: w * 0.73, y: h * 0.42),
            control2: CGPoint(x: w * 0.76, y: h * 0.52)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.6, y: h * 0.92),
            control1: CGPoint(x: w * 0.73, y: h * 0.72),
            control2: CGPoint(x: w * 0.68, y: h * 0.85)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.4, y: h * 0.95),
            control1: CGPoint(x: w * 0.55, y: h * 0.94),
            control2: CGPoint(x: w * 0.45, y: h * 0.96)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.2, y: h * 0.7),
            control1: CGPoint(x: w * 0.3, y: h * 0.92),
            control2: CGPoint(x: w * 0.22, y: h * 0.82)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.2, y: h * 0.4),
            control1: CGPoint(x: w * 0.18, y: h * 0.58),
            control2: CGPoint(x: w * 0.18, y: h * 0.48)
        )
        path.addCurve(
            to: CGPoint(x: w * 0.35, y: h * 0.02),
            control1: CGPoint(x: w * 0.22, y: h * 0.25),
            control2: CGPoint(x: w * 0.28, y: h * 0.08)
        )
        path.closeSubpath()
        
        return path
    }
}

// MARK: - River Lines
struct RiverLines: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let w = rect.width
        let h = rect.height
        
        // Sacramento River (top to middle)
        path.move(to: CGPoint(x: w * 0.4, y: h * 0.0))
        path.addCurve(
            to: CGPoint(x: w * 0.45, y: h * 0.35),
            control1: CGPoint(x: w * 0.42, y: h * 0.12),
            control2: CGPoint(x: w * 0.38, y: h * 0.25)
        )
        
        // San Joaquin River (middle to bottom)
        path.move(to: CGPoint(x: w * 0.45, y: h * 0.35))
        path.addCurve(
            to: CGPoint(x: w * 0.5, y: h * 0.75),
            control1: CGPoint(x: w * 0.5, y: h * 0.5),
            control2: CGPoint(x: w * 0.45, y: h * 0.65)
        )
        
        // Kings River
        path.move(to: CGPoint(x: w * 0.65, y: h * 0.55))
        path.addCurve(
            to: CGPoint(x: w * 0.45, y: h * 0.62),
            control1: CGPoint(x: w * 0.58, y: h * 0.58),
            control2: CGPoint(x: w * 0.5, y: h * 0.6)
        )
        
        // Kern River
        path.move(to: CGPoint(x: w * 0.7, y: h * 0.78))
        path.addCurve(
            to: CGPoint(x: w * 0.48, y: h * 0.82),
            control1: CGPoint(x: w * 0.62, y: h * 0.8),
            control2: CGPoint(x: w * 0.55, y: h * 0.82)
        )
        
        return path
    }
}

// MARK: - Transaction Flow Lines
struct TransactionFlowLines: View {
    let basins: [BasinInfo]
    let containerSize: CGSize
    
    // Define trade connections between basins
    let connections: [(from: Int, to: Int, volume: Double)] = [
        (0, 1, 120),  // Sacramento → Colusa
        (2, 4, 200),  // Merced → Fresno
        (4, 5, 350),  // Fresno → Tulare
        (5, 7, 280),  // Tulare → Kern
        (3, 4, 150),  // Madera → Fresno
        (6, 7, 90),   // Kings → Kern
    ]
    
    var body: some View {
        ForEach(Array(connections.enumerated()), id: \.offset) { _, conn in
            if conn.from < basins.count && conn.to < basins.count {
                let from = basins[conn.from]
                let to = basins[conn.to]
                
                TradeFlowLine(
                    start: CGPoint(
                        x: from.position.x * containerSize.width,
                        y: from.position.y * containerSize.height
                    ),
                    end: CGPoint(
                        x: to.position.x * containerSize.width,
                        y: to.position.y * containerSize.height
                    ),
                    volume: conn.volume
                )
            }
        }
    }
}

struct TradeFlowLine: View {
    let start: CGPoint
    let end: CGPoint
    let volume: Double
    
    @State private var dashPhase: CGFloat = 0
    
    var lineWidth: CGFloat {
        max(1, min(CGFloat(volume / 150), 3))
    }
    
    var body: some View {
        Path { path in
            path.move(to: start)
            // Create a slight curve
            let midX = (start.x + end.x) / 2
            let midY = (start.y + end.y) / 2
            let controlOffset: CGFloat = 20
            path.addQuadCurve(
                to: end,
                control: CGPoint(x: midX + controlOffset, y: midY - controlOffset)
            )
        }
        .stroke(
            Color.yellow.opacity(0.35),
            style: StrokeStyle(
                lineWidth: lineWidth,
                lineCap: .round,
                dash: [6, 4],
                dashPhase: dashPhase
            )
        )
        .onAppear {
            withAnimation(.linear(duration: 3).repeatForever(autoreverses: false)) {
                dashPhase = -20
            }
        }
    }
}

// MARK: - Sample Data
struct SampleData {
    static let centralValleyBasins: [BasinInfo] = [
        // Sacramento Valley
        BasinInfo(
            name: "Sacramento Valley",
            shortName: "SACRA\nMENTO",
            position: CGPoint(x: 0.38, y: 0.08),
            color: .green,
            isCritical: false,
            allocation: 45000,
            currentUsage: 62,
            wells: [
                WellInfo(name: "Davis Ranch Well", owner: "Davis Farms", offsetX: -28, offsetY: -15,
                        totalPumped: 1200, totalTraded: 150, lastTradePrice: 285, tradeType: "sell"),
                WellInfo(name: "Yolo Well #3", owner: "Yolo Ag Co", offsetX: 25, offsetY: -20,
                        totalPumped: 800, totalTraded: 80, lastTradePrice: 310, tradeType: "buy"),
            ],
            gspPolicies: SampleData.sacramentoPolicies,
            totalTraded: 230,
            activeSellers: 8,
            activeBuyers: 12
        ),
        
        BasinInfo(
            name: "Colusa Subbasin",
            shortName: "COLUSA",
            position: CGPoint(x: 0.55, y: 0.15),
            color: .green,
            isCritical: false,
            allocation: 28000,
            currentUsage: 55,
            wells: [
                WellInfo(name: "Glenn Well", owner: "Glenn Ranch", offsetX: -22, offsetY: 18,
                        totalPumped: 950, totalTraded: 120, lastTradePrice: 275, tradeType: "sell"),
            ],
            gspPolicies: SampleData.genericPolicies,
            totalTraded: 120,
            activeSellers: 4,
            activeBuyers: 6
        ),
        
        // San Joaquin Valley
        BasinInfo(
            name: "Merced Subbasin",
            shortName: "MERCED",
            position: CGPoint(x: 0.48, y: 0.32),
            color: .orange,
            isCritical: true,
            allocation: 32000,
            currentUsage: 88,
            wells: [
                WellInfo(name: "Merced Irrigation Well", owner: "Merced Irrigation Dist", offsetX: -25, offsetY: -18,
                        totalPumped: 2100, totalTraded: 280, lastTradePrice: 340, tradeType: "sell"),
                WellInfo(name: "Atwater Well #7", owner: "Atwater Farms", offsetX: 20, offsetY: 22,
                        totalPumped: 1500, totalTraded: 95, lastTradePrice: 355, tradeType: "buy"),
            ],
            gspPolicies: SampleData.criticalPolicies,
            totalTraded: 375,
            activeSellers: 6,
            activeBuyers: 15
        ),
        
        BasinInfo(
            name: "Madera Subbasin",
            shortName: "MADERA",
            position: CGPoint(x: 0.32, y: 0.42),
            color: .orange,
            isCritical: true,
            allocation: 22000,
            currentUsage: 91,
            wells: [
                WellInfo(name: "Madera Canal Well", owner: "Madera County WD", offsetX: 25, offsetY: -15,
                        totalPumped: 1800, totalTraded: 210, lastTradePrice: 380, tradeType: "sell"),
            ],
            gspPolicies: SampleData.criticalPolicies,
            totalTraded: 210,
            activeSellers: 5,
            activeBuyers: 9
        ),
        
        BasinInfo(
            name: "Kings Subbasin",
            shortName: "FRESNO\n/KINGS",
            position: CGPoint(x: 0.52, y: 0.52),
            color: .orange,
            isCritical: true,
            allocation: 55000,
            currentUsage: 85,
            wells: [
                WellInfo(name: "Fresno Well #12", owner: "Fresno Irrigation", offsetX: -28, offsetY: -18,
                        totalPumped: 3200, totalTraded: 420, lastTradePrice: 350, tradeType: "sell"),
                WellInfo(name: "Selma Deep Well", owner: "Selma Farms", offsetX: 22, offsetY: 20,
                        totalPumped: 2800, totalTraded: 310, lastTradePrice: 365, tradeType: "buy"),
                WellInfo(name: "Kingsburg Well #4", owner: "Kings River WD", offsetX: -18, offsetY: 25,
                        totalPumped: 1900, totalTraded: 180, lastTradePrice: 340, tradeType: "sell"),
            ],
            gspPolicies: SampleData.criticalPolicies,
            totalTraded: 910,
            activeSellers: 12,
            activeBuyers: 22
        ),
        
        BasinInfo(
            name: "Tulare Lake Subbasin",
            shortName: "TULARE\nLAKE",
            position: CGPoint(x: 0.38, y: 0.65),
            color: .red,
            isCritical: true,
            allocation: 48000,
            currentUsage: 94,
            wells: [
                WellInfo(name: "Tulare Irrigation Well", owner: "Tulare Irrigation Dist", offsetX: -25, offsetY: -20,
                        totalPumped: 4100, totalTraded: 580, lastTradePrice: 395, tradeType: "sell"),
                WellInfo(name: "Visalia Well #9", owner: "Visalia Farms", offsetX: 28, offsetY: -12,
                        totalPumped: 2200, totalTraded: 290, lastTradePrice: 410, tradeType: "buy"),
                WellInfo(name: "Pixley Well", owner: "Pixley Irrigation", offsetX: -15, offsetY: 28,
                        totalPumped: 3500, totalTraded: 450, lastTradePrice: 385, tradeType: "sell"),
            ],
            gspPolicies: SampleData.criticalPolicies,
            totalTraded: 1320,
            activeSellers: 18,
            activeBuyers: 28
        ),
        
        BasinInfo(
            name: "Kaweah Subbasin",
            shortName: "KAWEAH",
            position: CGPoint(x: 0.65, y: 0.6),
            color: .orange,
            isCritical: true,
            allocation: 18000,
            currentUsage: 87,
            wells: [
                WellInfo(name: "Kaweah Delta Well", owner: "Kaweah Delta WCD", offsetX: -20, offsetY: 18,
                        totalPumped: 1600, totalTraded: 190, lastTradePrice: 370, tradeType: "sell"),
            ],
            gspPolicies: SampleData.criticalPolicies,
            totalTraded: 190,
            activeSellers: 4,
            activeBuyers: 7
        ),
        
        BasinInfo(
            name: "Kern County Subbasin",
            shortName: "KERN\nCOUNTY",
            position: CGPoint(x: 0.52, y: 0.82),
            color: .red,
            isCritical: true,
            allocation: 62000,
            currentUsage: 96,
            wells: [
                WellInfo(name: "Bakersfield Well #1", owner: "Kern County WA", offsetX: -28, offsetY: -18,
                        totalPumped: 5200, totalTraded: 720, lastTradePrice: 420, tradeType: "sell"),
                WellInfo(name: "Shafter Well #6", owner: "Shafter-Wasco ID", offsetX: 25, offsetY: -22,
                        totalPumped: 3800, totalTraded: 510, lastTradePrice: 435, tradeType: "buy"),
                WellInfo(name: "Arvin Edison Well", owner: "Arvin Edison WSD", offsetX: -20, offsetY: 26,
                        totalPumped: 4500, totalTraded: 620, lastTradePrice: 445, tradeType: "sell"),
                WellInfo(name: "Lost Hills Well", owner: "Lost Hills WD", offsetX: 22, offsetY: 24,
                        totalPumped: 2900, totalTraded: 380, lastTradePrice: 400, tradeType: "buy"),
            ],
            gspPolicies: SampleData.kernPolicies,
            totalTraded: 2230,
            activeSellers: 22,
            activeBuyers: 35
        ),
    ]
    
    // MARK: - Sample GSP Policies
    
    static let sacramentoPolicies: [GSPPolicy] = [
        GSPPolicy(
            title: "Inter-basin Transfer Allowance",
            section: "GSP §4.2.1",
            summary: "Transfers up to 500 AF/year permitted without special review within Sacramento Valley subbasins.",
            fullText: "Water transfers within the Sacramento Valley groundwater basin are permitted up to 500 acre-feet per year per entity without requiring special review by the GSA. Transfers exceeding this threshold require a 30-day public comment period and GSA board approval. All transfers must demonstrate no adverse impact on neighboring wells within a 1-mile radius.",
            isRestriction: false,
            category: .transfer
        ),
        GSPPolicy(
            title: "Sustainable Yield Allocation",
            section: "GSP §3.1.4",
            summary: "Basin sustainable yield set at 45,000 AF/year. Individual allocations based on historical use and land acreage.",
            fullText: "The Sacramento Valley subbasin sustainable yield is determined to be 45,000 acre-feet per year based on water budget analysis. Individual allocations are calculated using a weighted formula: 60% historical beneficial use (2005-2015 average) and 40% irrigable acreage. Allocations are reviewed every 5 years.",
            isRestriction: false,
            category: .sustainability
        ),
        GSPPolicy(
            title: "Well Metering Requirement",
            section: "GSP §5.3.2",
            summary: "All extraction wells must have certified flow meters. Monthly reporting required.",
            fullText: "All groundwater extraction wells with a capacity exceeding 2 acre-feet per year must be equipped with a certified totalizing flow meter meeting AWWA standards. Readings must be reported monthly to the GSA through the online portal. Failure to report for 3 consecutive months results in temporary suspension of transfer privileges.",
            isRestriction: true,
            category: .reporting
        ),
    ]
    
    static let criticalPolicies: [GSPPolicy] = [
        GSPPolicy(
            title: "Critically Overdrafted Basin Restrictions",
            section: "SGMA §10720.7",
            summary: "Basins designated as critically overdrafted must achieve sustainability by 2040. Annual pumping reductions of 5-15% may be imposed.",
            fullText: "Under SGMA, critically overdrafted basins are required to achieve groundwater sustainability by January 31, 2040. GSAs in these basins must implement measurable objectives and interim milestones. Annual pumping allocations may be reduced by 5-15% per year to meet sustainability goals. The State Water Resources Control Board may intervene if inadequate progress is demonstrated.",
            isRestriction: true,
            category: .pumping
        ),
        GSPPolicy(
            title: "Transfer Review for Critical Basins",
            section: "GSP §6.4.1",
            summary: "All inter-basin transfers from critically overdrafted basins require GSA approval and environmental review.",
            fullText: "Any transfer of groundwater extraction rights out of a critically overdrafted basin requires: (1) Written application to the GSA at least 60 days prior, (2) Environmental impact assessment demonstrating no worsening of overdraft conditions, (3) GSA board approval by majority vote, (4) Notification to DWR. Transfers within the same basin are subject to a simplified 15-day review process.",
            isRestriction: true,
            category: .transfer
        ),
        GSPPolicy(
            title: "Pumping Allocation Caps",
            section: "GSP §5.1.3",
            summary: "Individual pumping capped at 80% of historical average. Unused allocations may be traded or carried over (max 20%).",
            fullText: "To achieve sustainability goals, individual groundwater extraction is capped at 80% of the 2005-2015 historical average. Unused allocations within a water year may be: (a) Transferred to another entity within the same basin via the approved exchange platform, or (b) Carried over to the next water year, up to a maximum of 20% of annual allocation. Carryover credits expire after 2 years if not used or transferred.",
            isRestriction: true,
            category: .pumping
        ),
        GSPPolicy(
            title: "Transaction Fee Schedule",
            section: "GSP §7.2.1",
            summary: "Intra-basin transfers: $5/AF fee. Inter-basin transfers: $15/AF fee plus environmental surcharge.",
            fullText: "The GSA imposes the following fees on groundwater transfers: Intra-basin transfers (within same subbasin): $5 per acre-foot. Inter-basin transfers (between subbasins): $15 per acre-foot base fee plus a $10 per acre-foot environmental mitigation surcharge. Fees are assessed on the seller and are payable within 30 days of transfer completion. Fee revenue is allocated: 60% to GSA operations, 25% to recharge projects, 15% to monitoring well maintenance.",
            isRestriction: false,
            category: .fees
        ),
        GSPPolicy(
            title: "Recharge Credit Program",
            section: "GSP §8.1.2",
            summary: "Landowners performing managed aquifer recharge earn tradeable credits at 75% of recharged volume.",
            fullText: "The GSA operates a Managed Aquifer Recharge (MAR) credit program. Landowners who actively recharge the aquifer through approved methods (flooding, injection wells, or recharge basins) receive tradeable credits equal to 75% of the verified recharged volume. Credits are verified through monitoring well data and must be certified by a licensed hydrogeologist. Credits may be used to: (a) Increase personal pumping allocation, (b) Sold on the WaterXchange platform, (c) Banked for up to 5 years.",
            isRestriction: false,
            category: .sustainability
        ),
    ]
    
    static let kernPolicies: [GSPPolicy] = criticalPolicies + [
        GSPPolicy(
            title: "Kern County Water Bank Integration",
            section: "GSP §9.3.1",
            summary: "Kern Water Bank stored water may be transferred via WaterXchange. Withdrawals require 14-day notice.",
            fullText: "Water stored in the Kern Water Bank facilities may be listed for transfer on the WaterXchange platform subject to the following: (1) Minimum storage period of 90 days before transfer eligibility, (2) 14-day advance notice for withdrawals exceeding 100 AF, (3) Verification of storage certificate by Kern Water Bank Authority, (4) Priority given to local agricultural users during drought declarations. Transfer pricing for banked water is subject to a floor price determined quarterly by the GSA.",
            isRestriction: true,
            category: .transfer
        ),
        GSPPolicy(
            title: "Subsidence Monitoring Zone Restrictions",
            section: "GSP §10.2.4",
            summary: "Areas with >1 inch/year subsidence face additional 10% pumping reduction. No new wells permitted.",
            fullText: "In designated subsidence monitoring zones where land subsidence exceeds 1 inch per year (as measured by InSAR and extensometer data): (1) An additional 10% reduction in pumping allocation is imposed beyond basin-wide reductions, (2) No new well permits will be issued, (3) Existing wells must reduce extraction by 20% within 2 years, (4) Transfers of water rights INTO subsidence zones are prohibited, (5) Transfers OUT of subsidence zones are permitted but subject to enhanced review.",
            isRestriction: true,
            category: .pumping
        ),
    ]
    
    static let genericPolicies: [GSPPolicy] = [
        GSPPolicy(
            title: "Standard Transfer Protocol",
            section: "GSP §4.1.1",
            summary: "Transfers within the same basin require 7-day notice. Both parties must have active well meters.",
            fullText: "Standard groundwater transfer protocol: (1) Both buyer and seller must have active, certified well meters, (2) A 7-day notification period to the GSA is required before transfer execution, (3) The GSA may object within the notification period if the transfer would cause adverse impacts, (4) Transfer volumes are debited from seller's allocation and credited to buyer's allocation within 3 business days of approval.",
            isRestriction: false,
            category: .transfer
        ),
        GSPPolicy(
            title: "Annual Reporting Requirements",
            section: "GSP §5.4.1",
            summary: "Annual water use reports due by March 1. Must include extraction volumes, crop types, and irrigation methods.",
            fullText: "All groundwater users within the basin must submit annual water use reports by March 1 of each year covering the previous water year (October 1 - September 30). Reports must include: (a) Total extraction volumes by well, (b) Crop types and acreages irrigated, (c) Irrigation method and estimated efficiency, (d) Any water transfers conducted, (e) Planned changes for upcoming year. Failure to submit timely reports results in a $500 penalty and suspension of transfer privileges until compliance.",
            isRestriction: true,
            category: .reporting
        ),
    ]
}

#Preview {
    BasinMapView()
}
