//
//  Order.swift
//  WaterXchange
//

import Foundation

enum OrderType: String, Codable, CaseIterable {
    case buy = "buy"
    case sell = "sell"
    
    var displayName: String {
        switch self {
        case .buy: return "Buy"
        case .sell: return "Sell"
        }
    }
    
    var color: String {
        switch self {
        case .buy: return "BuyGreen"
        case .sell: return "SellRed"
        }
    }
}

enum OrderStatus: String, Codable {
    case open = "open"
    case partiallyFilled = "partially_filled"
    case filled = "filled"
    case cancelled = "cancelled"
    
    var displayName: String {
        switch self {
        case .open: return "Open"
        case .partiallyFilled: return "Partial"
        case .filled: return "Filled"
        case .cancelled: return "Cancelled"
        }
    }
    
    var color: String {
        switch self {
        case .open: return "StatusOpen"
        case .partiallyFilled: return "StatusPartial"
        case .filled: return "StatusFilled"
        case .cancelled: return "StatusCancelled"
        }
    }
}

struct Order: Codable, Identifiable {
    let id: Int
    let orderType: OrderType
    let quantityAF: Double
    let filledQuantityAF: Double
    let pricePerAF: Double
    let basin: String
    let status: OrderStatus
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id, basin, status
        case orderType = "order_type"
        case quantityAF = "quantity_af"
        case filledQuantityAF = "filled_quantity_af"
        case pricePerAF = "price_per_af"
        case createdAt = "created_at"
    }
    
    var remainingQuantity: Double {
        quantityAF - filledQuantityAF
    }
    
    var totalValue: Double {
        quantityAF * pricePerAF
    }
}

struct CreateOrderRequest: Codable {
    let orderType: String
    let quantityAF: Double
    let pricePerAF: Double
    
    enum CodingKeys: String, CodingKey {
        case orderType = "order_type"
        case quantityAF = "quantity_af"
        case pricePerAF = "price_per_af"
    }
}

struct OrderListResponse: Codable {
    let orders: [Order]
    let total: Int
}
