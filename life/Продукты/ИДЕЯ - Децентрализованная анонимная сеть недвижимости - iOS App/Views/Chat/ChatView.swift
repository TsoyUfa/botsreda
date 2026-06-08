//
//  ChatView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct ChatView: View {
    let thread: Thread
    @StateObject private var viewModel = ChatViewModel()
    @State private var messageText = ""
    @FocusState private var isTextFieldFocused: Bool
    
    var body: some View {
        VStack(spacing: 0) {
            // Список сообщений
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            MessageBubbleView(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) { _ in
                    if let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
            
            // Поле ввода
            MessageInputView(
                text: $messageText,
                onSend: {
                    Task {
                        await viewModel.sendMessage(text: messageText, threadID: thread.id)
                        messageText = ""
                    }
                }
            )
            .focused($isTextFieldFocused)
        }
        .navigationTitle(thread.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Button(action: {}) {
                        Label("Поделиться", systemImage: "square.and.arrow.up")
                    }
                    
                    Button(action: {}) {
                        Label("Пожаловаться", systemImage: "flag")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
        .task {
            await viewModel.loadMessages(threadID: thread.id)
        }
    }
}

struct MessageInputView: View {
    @Binding var text: String
    let onSend: () -> Void
    
    var body: some View {
        HStack(spacing: 12) {
            TextField("Написать сообщение...", text: $text, axis: .vertical)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .lineLimit(1...5)
            
            Button(action: onSend) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
                    .foregroundColor(text.isEmpty ? .gray : .purple)
            }
            .disabled(text.isEmpty)
        }
        .padding()
        .background(Color(.systemBackground))
    }
}

#Preview {
    NavigationView {
        ChatView(thread: Thread.mock)
    }
}



