//
//  Chat.swift
//  WaterXchange
//

import Foundation

struct ChatMessage: Codable, Identifiable {
    let id: UUID
    let role: String  // "user" or "assistant"
    let content: String
    let timestamp: Date
    
    init(role: String, content: String) {
        self.id = UUID()
        self.role = role
        self.content = content
        self.timestamp = Date()
    }
    
    var isUser: Bool {
        role == "user"
    }
}

struct ChatRequest: Codable {
    let message: String
    let conversationHistory: [ChatHistoryItem]
    
    enum CodingKeys: String, CodingKey {
        case message
        case conversationHistory = "conversation_history"
    }
}

struct ChatHistoryItem: Codable {
    let role: String
    let content: String
}

struct ChatResponse: Codable {
    let response: String
    let sources: [String]
    let complianceCheck: ComplianceCheck?
    
    enum CodingKeys: String, CodingKey {
        case response, sources
        case complianceCheck = "compliance_check"
    }
}

struct ComplianceCheck: Codable {
    let allowed: Bool
    let reason: String
    let requiresPermit: Bool?
    let rules: [String]?
    
    enum CodingKeys: String, CodingKey {
        case allowed, reason, rules
        case requiresPermit = "requires_permit"
    }
}

struct QuickCheckResponse: Codable {
    let fromBasin: String
    let toBasin: String
    let quantityAF: Double
    let isAllowed: Bool
    let reason: String
    let requiresPermit: Bool
    let relevantRules: [String]
    
    enum CodingKeys: String, CodingKey {
        case reason
        case fromBasin = "from_basin"
        case toBasin = "to_basin"
        case quantityAF = "quantity_af"
        case isAllowed = "is_allowed"
        case requiresPermit = "requires_permit"
        case relevantRules = "relevant_rules"
    }
}
