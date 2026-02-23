//
//  LoginView.swift
//  WaterXchange
//

import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    
    @State private var email = ""
    @State private var password = ""
    @State private var showRegister = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background gradient
                LinearGradient(
                    colors: [
                        Color(red: 0.05, green: 0.15, blue: 0.3),
                        Color(red: 0.1, green: 0.25, blue: 0.45)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                // Water wave pattern overlay
                WaveBackground()
                
                ScrollView {
                    VStack(spacing: 32) {
                        // Logo and title
                        VStack(spacing: 16) {
                            Image("Logo")
                                .renderingMode(.original)
                                .resizable()
                                .scaledToFit()
                                .frame(width: 120, height: 120)
                                .background(Color.clear)
                                .shadow(color: .cyan.opacity(0.5), radius: 20)
                            
                            Text("WaterXchange")
                                .font(.system(size: 36, weight: .bold, design: .rounded))
                                .foregroundColor(.white)
                            
                            Text("Trade water. Grow California.")
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.7))
                        }
                        .padding(.top, 60)
                        
                        // Login form
                        VStack(spacing: 20) {
                            // Email field
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Email")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.7))
                                
                                HStack {
                                    Image(systemName: "envelope")
                                        .foregroundColor(.white.opacity(0.5))
                                    TextField("farmer@example.com", text: $email)
                                        .textContentType(.emailAddress)
                                        .autocapitalization(.none)
                                        .keyboardType(.emailAddress)
                                        .foregroundColor(.white)
                                }
                                .padding()
                                .background(Color.white.opacity(0.1))
                                .cornerRadius(12)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                )
                            }
                            
                            // Password field
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Password")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.7))
                                
                                HStack {
                                    Image(systemName: "lock")
                                        .foregroundColor(.white.opacity(0.5))
                                    SecureField("••••••••", text: $password)
                                        .textContentType(.password)
                                        .foregroundColor(.white)
                                }
                                .padding()
                                .background(Color.white.opacity(0.1))
                                .cornerRadius(12)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                )
                            }
                            
                            // Error message
                            if let error = authManager.errorMessage {
                                HStack {
                                    Image(systemName: "exclamationmark.triangle")
                                    Text(error)
                                }
                                .font(.caption)
                                .foregroundColor(.red)
                                .padding(.horizontal)
                            }
                            
                            // Login button
                            Button {
                                Task {
                                    await authManager.login(email: email, password: password)
                                }
                            } label: {
                                HStack {
                                    if authManager.isLoading {
                                        ProgressView()
                                            .tint(.white)
                                    } else {
                                        Text("Sign In")
                                            .fontWeight(.semibold)
                                        Image(systemName: "arrow.right")
                                    }
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(
                                    LinearGradient(
                                        colors: [.cyan, .blue],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .foregroundColor(.white)
                                .cornerRadius(12)
                            }
                            .disabled(email.isEmpty || password.isEmpty || authManager.isLoading)
                            .opacity(email.isEmpty || password.isEmpty ? 0.6 : 1)
                            
                            // Register link
                            Button {
                                showRegister = true
                            } label: {
                                Text("Don't have an account? ")
                                    .foregroundColor(.white.opacity(0.7)) +
                                Text("Register")
                                    .foregroundColor(.cyan)
                                    .fontWeight(.semibold)
                            }
                            .padding(.top, 8)
                        }
                        .padding(.horizontal, 32)
                        
                        // Demo credentials hint
                        VStack(spacing: 4) {
                            Text("Demo Mode")
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.5))
                            Text("Register with any email to get started")
                                .font(.caption2)
                                .foregroundColor(.white.opacity(0.4))
                        }
                        .padding(.top, 32)
                        
                        Spacer()
                    }
                }
            }
            .sheet(isPresented: $showRegister) {
                RegisterView()
            }
        }
    }
}

// MARK: - Wave Background
struct WaveBackground: View {
    var body: some View {
        GeometryReader { geometry in
            Path { path in
                let width = geometry.size.width
                let height = geometry.size.height
                
                path.move(to: CGPoint(x: 0, y: height * 0.7))
                path.addCurve(
                    to: CGPoint(x: width, y: height * 0.75),
                    control1: CGPoint(x: width * 0.3, y: height * 0.6),
                    control2: CGPoint(x: width * 0.7, y: height * 0.85)
                )
                path.addLine(to: CGPoint(x: width, y: height))
                path.addLine(to: CGPoint(x: 0, y: height))
                path.closeSubpath()
            }
            .fill(Color.white.opacity(0.03))
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthManager())
}
