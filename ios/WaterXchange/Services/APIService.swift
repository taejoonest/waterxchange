//
//  APIService.swift
//  WaterXchange
//

import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case noData
    case decodingError
    case serverError(String)
    case unauthorized
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .noData: return "No data received"
        case .decodingError: return "Failed to decode response"
        case .serverError(let message): return message
        case .unauthorized: return "Please login again."
        case .networkError(let error): return error.localizedDescription
        }
    }
}

class APIService {
    static let shared = APIService()
    
    private let baseURL = Config.apiBaseURL
    private var authToken: String?
    
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
    
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()
    
    private init() {}
    
    // MARK: - Token Management
    
    func setAuthToken(_ token: String?) {
        self.authToken = token
    }
    
    // MARK: - Generic Request
    
    private func request<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Encodable? = nil,
        queryParams: [String: String]? = nil
    ) async throws -> T {
        var urlString = baseURL + endpoint
        
        // Add query parameters
        if let params = queryParams, !params.isEmpty {
            let queryString = params.map { "\($0.key)=\($0.value)" }.joined(separator: "&")
            urlString += "?\(queryString)"
        }
        
        guard let url = URL(string: urlString) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add auth token
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // Add body
        if let body = body {
            request.httpBody = try encoder.encode(body)
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.noData
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                return try decoder.decode(T.self, from: data)
            case 401:
                throw APIError.unauthorized
            default:
                // Try to decode error message
                if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                    throw APIError.serverError(errorResponse.detail)
                }
                throw APIError.serverError("Server error: \(httpResponse.statusCode)")
            }
        } catch let error as APIError {
            throw error
        } catch let error as DecodingError {
            print("Decoding error: \(error)")
            throw APIError.decodingError
        } catch {
            throw APIError.networkError(error)
        }
    }
    
    // MARK: - Auth Endpoints
    
    func login(email: String, password: String) async throws -> AuthResponse {
        let request = LoginRequest(email: email, password: password)
        return try await self.request(
            endpoint: Config.Endpoints.login,
            method: "POST",
            body: request
        )
    }
    
    func register(request: RegisterRequest) async throws -> AuthResponse {
        return try await self.request(
            endpoint: Config.Endpoints.register,
            method: "POST",
            body: request
        )
    }
    
    func getCurrentUser() async throws -> User {
        return try await self.request(endpoint: Config.Endpoints.me)
    }
    
    // MARK: - Orders Endpoints
    
    func getOrders(status: String? = nil) async throws -> OrderListResponse {
        var params: [String: String]? = nil
        if let status = status {
            params = ["status_filter": status]
        }
        return try await self.request(
            endpoint: Config.Endpoints.orders,
            queryParams: params
        )
    }
    
    func createOrder(type: OrderType, quantity: Double, price: Double) async throws -> Order {
        let request = CreateOrderRequest(
            orderType: type.rawValue,
            quantityAF: quantity,
            pricePerAF: price
        )
        return try await self.request(
            endpoint: Config.Endpoints.orders,
            method: "POST",
            body: request
        )
    }
    
    func cancelOrder(id: Int) async throws -> MessageResponse {
        return try await self.request(
            endpoint: "\(Config.Endpoints.orders)/\(id)",
            method: "DELETE"
        )
    }
    
    // MARK: - Market Endpoints
    
    func getOrderBook(basin: String) async throws -> OrderBook {
        return try await self.request(
            endpoint: Config.Endpoints.orderBook,
            queryParams: ["basin": basin]
        )
    }
    
    func getMarketPrice(basin: String) async throws -> MarketPrice {
        return try await self.request(
            endpoint: Config.Endpoints.marketPrice,
            queryParams: ["basin": basin]
        )
    }
    
    func getBasins() async throws -> BasinsResponse {
        return try await self.request(endpoint: Config.Endpoints.basins)
    }
    
    // MARK: - Balance Endpoints
    
    func getBalance() async throws -> Balance {
        return try await self.request(endpoint: Config.Endpoints.balance)
    }
    
    func getTransactionHistory() async throws -> TransactionHistoryResponse {
        return try await self.request(endpoint: Config.Endpoints.history)
    }
    
    // MARK: - Chat Endpoints
    
    func sendChatMessage(message: String, history: [ChatMessage]) async throws -> ChatResponse {
        let historyItems = history.map { ChatHistoryItem(role: $0.role, content: $0.content) }
        let request = ChatRequest(message: message, conversationHistory: historyItems)
        return try await self.request(
            endpoint: Config.Endpoints.chat,
            method: "POST",
            body: request
        )
    }
    
    func quickComplianceCheck(
        fromBasin: String,
        toBasin: String,
        quantity: Double
    ) async throws -> QuickCheckResponse {
        let params = [
            "from_basin": fromBasin,
            "to_basin": toBasin,
            "quantity_af": String(quantity)
        ]
        return try await self.request(
            endpoint: Config.Endpoints.quickCheck,
            method: "POST",
            queryParams: params
        )
    }
}

// MARK: - Response Types

struct ErrorResponse: Codable {
    let detail: String
}

struct MessageResponse: Codable {
    let message: String
}

struct BasinsResponse: Codable {
    let basins: [String]
}

struct TransactionHistoryResponse: Codable {
    let transactions: [TransactionHistory]
    let totalBoughtAF: Double
    let totalSoldAF: Double
    let netFlowAF: Double
    
    enum CodingKeys: String, CodingKey {
        case transactions
        case totalBoughtAF = "total_bought_af"
        case totalSoldAF = "total_sold_af"
        case netFlowAF = "net_flow_af"
    }
}
