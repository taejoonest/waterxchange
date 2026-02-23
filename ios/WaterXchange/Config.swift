//
//  Config.swift
//  WaterXchange
//
//  Configuration for API endpoints
//

import Foundation

struct Config {
    // MARK: - API Configuration
    
    /// Base URL for the WaterXchange API
    /// Change this to your deployed backend URL
    static let apiBaseURL = "http://localhost:8000"
    
    // For testing on device, use your machine's IP:
    // static let apiBaseURL = "http://192.168.1.100:8000"
    
    // For production:
    // static let apiBaseURL = "https://api.waterxchange.com"
    
    // MARK: - API Endpoints
    struct Endpoints {
        static let login = "/auth/login"
        static let register = "/auth/register"
        static let me = "/auth/me"
        
        static let orders = "/orders"
        static let orderBook = "/market/book"
        static let marketPrice = "/market/price"
        static let basins = "/market/basins"
        
        static let balance = "/balance"
        static let history = "/balance/history"
        
        static let chat = "/chat"
        static let quickCheck = "/chat/quick-check"
    }
    
    // MARK: - App Settings
    static let appName = "WaterXchange"
    static let appVersion = "1.0.0"
}
