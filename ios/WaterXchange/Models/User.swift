//
//  User.swift
//  WaterXchange
//

import Foundation

struct User: Codable, Identifiable {
    let id: Int
    let email: String
    let fullName: String
    let farmName: String?
    let basin: String
    let gsa: String?
    var waterBalanceAF: Double
    var annualAllocationAF: Double
    
    enum CodingKeys: String, CodingKey {
        case id, email, basin, gsa
        case fullName = "full_name"
        case farmName = "farm_name"
        case waterBalanceAF = "water_balance_af"
        case annualAllocationAF = "annual_allocation_af"
    }
}

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct RegisterRequest: Codable {
    let email: String
    let password: String
    let fullName: String
    let farmName: String?
    let basin: String
    let waterBalanceAF: Double
    
    enum CodingKeys: String, CodingKey {
        case email, password, basin
        case fullName = "full_name"
        case farmName = "farm_name"
        case waterBalanceAF = "water_balance_af"
    }
}

struct AuthResponse: Codable {
    let accessToken: String
    let tokenType: String
    let user: UserInfo
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case user
    }
}

struct UserInfo: Codable {
    let id: Int
    let email: String
    let fullName: String
    let farmName: String?
    let basin: String
    let waterBalanceAF: Double
    
    enum CodingKeys: String, CodingKey {
        case id, email, basin
        case fullName = "full_name"
        case farmName = "farm_name"
        case waterBalanceAF = "water_balance_af"
    }
}
