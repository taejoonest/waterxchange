//
//  RegisterView.swift
//  WaterXchange
//

import SwiftUI

struct RegisterView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) var dismiss
    
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var fullName = ""
    @State private var farmName = ""
    @State private var selectedBasin = "Kern County"
    @State private var waterBalance = "100"
    
    let basins = [
        "Kern County",
        "San Joaquin Valley",
        "Tulare Lake",
        "Kings County",
        "Fresno County",
        "Madera County"
    ]
    
    var isFormValid: Bool {
        !email.isEmpty &&
        !password.isEmpty &&
        password == confirmPassword &&
        !fullName.isEmpty &&
        password.count >= 6
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color(red: 0.05, green: 0.15, blue: 0.3)
                    .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 24) {
                        // Header
                        VStack(spacing: 8) {
                            Image(systemName: "person.badge.plus")
                                .font(.system(size: 48))
                                .foregroundColor(.cyan)
                            
                            Text("Create Account")
                                .font(.title.bold())
                                .foregroundColor(.white)
                            
                            Text("Join California's water marketplace")
                                .font(.subheadline)
                                .foregroundColor(.white.opacity(0.7))
                        }
                        .padding(.top, 20)
                        
                        // Form fields
                        VStack(spacing: 16) {
                            FormField(
                                title: "Full Name",
                                icon: "person",
                                text: $fullName,
                                placeholder: "John Farmer"
                            )
                            
                            FormField(
                                title: "Farm Name (Optional)",
                                icon: "leaf",
                                text: $farmName,
                                placeholder: "Green Valley Farm"
                            )
                            
                            FormField(
                                title: "Email",
                                icon: "envelope",
                                text: $email,
                                placeholder: "farmer@example.com",
                                keyboardType: .emailAddress
                            )
                            
                            // Basin picker
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Basin")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.7))
                                
                                HStack {
                                    Image(systemName: "map")
                                        .foregroundColor(.white.opacity(0.5))
                                    
                                    Picker("Basin", selection: $selectedBasin) {
                                        ForEach(basins, id: \.self) { basin in
                                            Text(basin).tag(basin)
                                        }
                                    }
                                    .pickerStyle(.menu)
                                    .tint(.white)
                                }
                                .padding()
                                .background(Color.white.opacity(0.1))
                                .cornerRadius(12)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                )
                            }
                            
                            // Water balance
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Starting Water Balance (AF)")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.7))
                                
                                HStack {
                                    Image(systemName: "drop")
                                        .foregroundColor(.white.opacity(0.5))
                                    TextField("100", text: $waterBalance)
                                        .keyboardType(.decimalPad)
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
                            
                            SecureFormField(
                                title: "Password",
                                icon: "lock",
                                text: $password,
                                placeholder: "Min 6 characters"
                            )
                            
                            SecureFormField(
                                title: "Confirm Password",
                                icon: "lock.fill",
                                text: $confirmPassword,
                                placeholder: "Confirm your password"
                            )
                            
                            // Password match indicator
                            if !password.isEmpty && !confirmPassword.isEmpty {
                                HStack {
                                    Image(systemName: password == confirmPassword ? "checkmark.circle" : "xmark.circle")
                                    Text(password == confirmPassword ? "Passwords match" : "Passwords don't match")
                                }
                                .font(.caption)
                                .foregroundColor(password == confirmPassword ? .green : .red)
                            }
                        }
                        .padding(.horizontal, 24)
                        
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
                        
                        // Register button
                        Button {
                            Task {
                                await authManager.register(
                                    email: email,
                                    password: password,
                                    fullName: fullName,
                                    farmName: farmName.isEmpty ? nil : farmName,
                                    basin: selectedBasin,
                                    waterBalance: Double(waterBalance) ?? 100
                                )
                                if authManager.isAuthenticated {
                                    dismiss()
                                }
                            }
                        } label: {
                            HStack {
                                if authManager.isLoading {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Text("Create Account")
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
                        .disabled(!isFormValid || authManager.isLoading)
                        .opacity(isFormValid ? 1 : 0.6)
                        .padding(.horizontal, 24)
                        
                        Spacer()
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                            .foregroundColor(.white)
                    }
                }
            }
        }
    }
}

// MARK: - Form Field Components
struct FormField: View {
    let title: String
    let icon: String
    @Binding var text: String
    let placeholder: String
    var keyboardType: UIKeyboardType = .default
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundColor(.white.opacity(0.7))
            
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.white.opacity(0.5))
                TextField(placeholder, text: $text)
                    .keyboardType(keyboardType)
                    .autocapitalization(keyboardType == .emailAddress ? .none : .words)
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
    }
}

struct SecureFormField: View {
    let title: String
    let icon: String
    @Binding var text: String
    let placeholder: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundColor(.white.opacity(0.7))
            
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.white.opacity(0.5))
                SecureField(placeholder, text: $text)
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
    }
}

#Preview {
    RegisterView()
        .environmentObject(AuthManager())
}
