//
//  SGMAChatView.swift
//  WaterXchange
//

import SwiftUI

struct SGMAChatView: View {
    @StateObject private var viewModel = SGMAChatViewModel()
    @State private var inputText = ""
    @FocusState private var isInputFocused: Bool
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Chat messages
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            // Welcome message
                            if viewModel.messages.isEmpty {
                                WelcomeCard()
                                    .padding(.top, 20)
                                
                                // Suggested questions
                                SuggestedQuestionsView { question in
                                    inputText = question
                                    sendMessage()
                                }
                            }
                            
                            // Messages
                            ForEach(viewModel.messages) { message in
                                ChatBubble(message: message)
                                    .id(message.id)
                            }
                            
                            // Typing indicator
                            if viewModel.isLoading {
                                TypingIndicator()
                            }
                        }
                        .padding()
                    }
                    .onChange(of: viewModel.messages.count) { _, _ in
                        if let lastMessage = viewModel.messages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                }
                
                // Input bar
                ChatInputBar(
                    text: $inputText,
                    isFocused: $isInputFocused,
                    isLoading: viewModel.isLoading
                ) {
                    sendMessage()
                }
            }
            .background(Color(red: 0.05, green: 0.1, blue: 0.2))
            .navigationTitle("SGMA Assistant")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        viewModel.clearChat()
                    } label: {
                        Image(systemName: "trash")
                    }
                    .disabled(viewModel.messages.isEmpty)
                }
            }
        }
    }
    
    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        
        inputText = ""
        Task {
            await viewModel.sendMessage(text)
        }
    }
}

// MARK: - Welcome Card
struct WelcomeCard: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "bubble.left.and.bubble.right.fill")
                .font(.system(size: 48))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.cyan, .blue],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
            
            Text("SGMA Assistant")
                .font(.title2.bold())
                .foregroundColor(.white)
            
            Text("Ask me anything about California's Sustainable Groundwater Management Act and water transfer regulations.")
                .font(.subheadline)
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
        }
        .padding(24)
        .background(Color.white.opacity(0.05))
        .cornerRadius(20)
    }
}

// MARK: - Suggested Questions
struct SuggestedQuestionsView: View {
    let onSelect: (String) -> Void
    
    let questions = [
        "Can I transfer water to Fresno County?",
        "Do I need a permit to sell 50 AF?",
        "What are the rules for my basin?",
        "Is my basin critically overdrafted?"
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Try asking:")
                .font(.caption)
                .foregroundColor(.gray)
            
            ForEach(questions, id: \.self) { question in
                Button {
                    onSelect(question)
                } label: {
                    HStack {
                        Image(systemName: "arrow.right.circle")
                            .foregroundColor(.cyan)
                        Text(question)
                            .foregroundColor(.white)
                        Spacer()
                    }
                    .padding()
                    .background(Color.white.opacity(0.05))
                    .cornerRadius(12)
                }
            }
        }
    }
}

// MARK: - Chat Bubble
struct ChatBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if message.isUser {
                Spacer(minLength: 60)
            } else {
                // Bot avatar
                Image(systemName: "drop.circle.fill")
                    .font(.title2)
                    .foregroundColor(.cyan)
            }
            
            VStack(alignment: message.isUser ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .font(.body)
                    .foregroundColor(.white)
                    .padding(12)
                    .background(
                        message.isUser
                            ? Color.cyan.opacity(0.3)
                            : Color.white.opacity(0.1)
                    )
                    .cornerRadius(16, corners: message.isUser
                        ? [.topLeft, .topRight, .bottomLeft]
                        : [.topLeft, .topRight, .bottomRight]
                    )
                
                Text(message.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundColor(.gray)
            }
            
            if !message.isUser {
                Spacer(minLength: 60)
            } else {
                // User avatar
                Image(systemName: "person.circle.fill")
                    .font(.title2)
                    .foregroundColor(.gray)
            }
        }
    }
}

// MARK: - Typing Indicator
struct TypingIndicator: View {
    @State private var animating = false
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "drop.circle.fill")
                .font(.title2)
                .foregroundColor(.cyan)
            
            HStack(spacing: 4) {
                ForEach(0..<3) { index in
                    Circle()
                        .fill(Color.gray)
                        .frame(width: 8, height: 8)
                        .scaleEffect(animating ? 1 : 0.5)
                        .animation(
                            .easeInOut(duration: 0.6)
                            .repeatForever()
                            .delay(Double(index) * 0.2),
                            value: animating
                        )
                }
            }
            .padding(16)
            .background(Color.white.opacity(0.1))
            .cornerRadius(16)
            
            Spacer()
        }
        .onAppear {
            animating = true
        }
    }
}

// MARK: - Chat Input Bar
struct ChatInputBar: View {
    @Binding var text: String
    var isFocused: FocusState<Bool>.Binding
    let isLoading: Bool
    let onSend: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            TextField("Ask about SGMA regulations...", text: $text, axis: .vertical)
                .focused(isFocused)
                .lineLimit(1...5)
                .padding(12)
                .background(Color.white.opacity(0.1))
                .cornerRadius(20)
                .foregroundColor(.white)
            
            Button(action: onSend) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title)
                    .foregroundColor(text.isEmpty || isLoading ? .gray : .cyan)
            }
            .disabled(text.isEmpty || isLoading)
        }
        .padding()
        .background(Color.black.opacity(0.3))
    }
}

// MARK: - Corner Radius Extension
extension View {
    func cornerRadius(_ radius: CGFloat, corners: UIRectCorner) -> some View {
        clipShape(RoundedCorner(radius: radius, corners: corners))
    }
}

struct RoundedCorner: Shape {
    var radius: CGFloat = .infinity
    var corners: UIRectCorner = .allCorners

    func path(in rect: CGRect) -> Path {
        let path = UIBezierPath(
            roundedRect: rect,
            byRoundingCorners: corners,
            cornerRadii: CGSize(width: radius, height: radius)
        )
        return Path(path.cgPath)
    }
}

// MARK: - View Model
@MainActor
class SGMAChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isLoading = false
    
    func sendMessage(_ text: String) async {
        // Add user message
        let userMessage = ChatMessage(role: "user", content: text)
        messages.append(userMessage)
        
        isLoading = true
        
        do {
            let response = try await APIService.shared.sendChatMessage(
                message: text,
                history: Array(messages.dropLast())  // Exclude the message we just added
            )
            
            // Add assistant response
            var responseText = response.response
            
            // Add compliance info if available
            if let compliance = response.complianceCheck {
                let emoji = compliance.allowed ? "✅" : "❌"
                responseText += "\n\n\(emoji) **Compliance Status**: \(compliance.allowed ? "Allowed" : "May be restricted")"
                
                if compliance.requiresPermit == true {
                    responseText += "\n⚠️ Permit Required"
                }
            }
            
            // Add sources
            if !response.sources.isEmpty {
                responseText += "\n\n📋 Sources: \(response.sources.joined(separator: ", "))"
            }
            
            let assistantMessage = ChatMessage(role: "assistant", content: responseText)
            messages.append(assistantMessage)
            
        } catch {
            // Add error message
            let errorMessage = ChatMessage(
                role: "assistant",
                content: "Sorry, I couldn't process your request. Please try again.\n\nError: \(error.localizedDescription)"
            )
            messages.append(errorMessage)
        }
        
        isLoading = false
    }
    
    func clearChat() {
        messages.removeAll()
    }
}

#Preview {
    SGMAChatView()
}
