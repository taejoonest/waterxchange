//
//  AuthManager.swift
//  WaterXchange
//

import Foundation
import SwiftUI

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: UserInfo?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let tokenKey = "auth_token"
    private let userKey = "current_user"
    
    init() {
        loadStoredAuth()
    }
    
    // MARK: - Auth State
    
    private func loadStoredAuth() {
        if let token = UserDefaults.standard.string(forKey: tokenKey) {
            APIService.shared.setAuthToken(token)
            
            if let userData = UserDefaults.standard.data(forKey: userKey),
               let user = try? JSONDecoder().decode(UserInfo.self, from: userData) {
                self.currentUser = user
                self.isAuthenticated = true
            }
        }
    }
    
    private func saveAuth(token: String, user: UserInfo) {
        UserDefaults.standard.set(token, forKey: tokenKey)
        if let userData = try? JSONEncoder().encode(user) {
            UserDefaults.standard.set(userData, forKey: userKey)
        }
        APIService.shared.setAuthToken(token)
        self.currentUser = user
        self.isAuthenticated = true
    }
    
    func clearAuth() {
        UserDefaults.standard.removeObject(forKey: tokenKey)
        UserDefaults.standard.removeObject(forKey: userKey)
        APIService.shared.setAuthToken(nil)
        self.currentUser = nil
        self.isAuthenticated = false
    }
    
    // MARK: - Login
    
    func login(email: String, password: String) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response = try await APIService.shared.login(email: email, password: password)
            saveAuth(token: response.accessToken, user: response.user)
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    // MARK: - Register
    
    func register(
        email: String,
        password: String,
        fullName: String,
        farmName: String?,
        basin: String,
        waterBalance: Double
    ) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let request = RegisterRequest(
                email: email,
                password: password,
                fullName: fullName,
                farmName: farmName,
                basin: basin,
                waterBalanceAF: waterBalance
            )
            let response = try await APIService.shared.register(request: request)
            saveAuth(token: response.accessToken, user: response.user)
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    // MARK: - Logout
    
    func logout() {
        clearAuth()
    }
}
