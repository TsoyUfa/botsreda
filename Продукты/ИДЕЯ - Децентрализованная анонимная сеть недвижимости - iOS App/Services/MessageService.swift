//
//  MessageService.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

class MessageService: ObservableObject {
    static let shared = MessageService()
    
    private let telegramService = TelegramService.shared
    private let anonymousNameService = AnonymousNameService.shared
    
    @Published var messages: [Message] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    func sendMessage(text: String, threadID: String) async {
        guard !text.isEmpty else { return }
        
        isLoading = true
        errorMessage = nil
        
        let anonymousName = anonymousNameService.getCurrentName()
        
        do {
            let message = try await telegramService.sendMessage(
                text: text,
                threadID: threadID,
                anonymousName: anonymousName.name
            )
            
            await MainActor.run {
                messages.append(message)
                isLoading = false
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
    
    func loadMessages(threadID: String) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let loadedMessages = try await telegramService.getMessages(threadID: threadID)
            
            await MainActor.run {
                messages = loadedMessages
                isLoading = false
            }
        } catch {
            await MainActor.run {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
}



