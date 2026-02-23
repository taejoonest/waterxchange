//
//  Market.swift
//  WaterXchange
//

import Foundation

struct OrderBookEntry: Codable, Identifiable {
    var id: String { "\(pricePerAF)-\(totalQuantityAF)" }
    
    let pricePerAF: Double
    let totalQuantityAF: Double
    let orderCount: Int
    
    enum CodingKeys: String, CodingKey {
        case pricePerAF = "price_per_af"
        case totalQuantityAF = "total_quantity_af"
        case orderCount = "order_count"
    }
}

struct OrderBook: Codable {
    let bids: [OrderBookEntry]  // Buy orders
    let asks: [OrderBookEntry]  // Sell orders
    let spread: Double?
    let basin: String
}

struct MarketPrice: Codable {
    let basin: String
    let lastPrice: Double?
    let avgPrice24h: Double?
    let high24h: Double?
    let low24h: Double?
    let volume24h: Double
    let bestBid: Double?
    let bestAsk: Double?
    
    enum CodingKeys: String, CodingKey {
        case basin
        case lastPrice = "last_price"
        case avgPrice24h = "avg_price_24h"
        case high24h = "high_24h"
        case low24h = "low_24h"
        case volume24h = "volume_24h"
        case bestBid = "best_bid"
        case bestAsk = "best_ask"
    }
    
    var displayPrice: Double {
        lastPrice ?? avgPrice24h ?? bestBid ?? bestAsk ?? 0
    }
}

struct Balance: Codable {
    let waterBalanceAF: Double
    let annualAllocationAF: Double
    let usedThisYearAF: Double
    let availableToSellAF: Double
    let basin: String
    
    enum CodingKeys: String, CodingKey {
        case basin
        case waterBalanceAF = "water_balance_af"
        case annualAllocationAF = "annual_allocation_af"
        case usedThisYearAF = "used_this_year_af"
        case availableToSellAF = "available_to_sell_af"
    }
}

struct TransactionHistory: Codable {
    let id: Int
    let type: String
    let quantityAF: Double
    let pricePerAF: Double
    let totalValue: Double
    let counterpartyBasin: String
    let executedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id, type
        case quantityAF = "quantity_af"
        case pricePerAF = "price_per_af"
        case totalValue = "total_value"
        case counterpartyBasin = "counterparty_basin"
        case executedAt = "executed_at"
    }
}
