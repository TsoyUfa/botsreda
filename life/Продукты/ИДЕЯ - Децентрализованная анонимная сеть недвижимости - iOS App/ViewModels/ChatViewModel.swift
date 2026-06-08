//
//  ChatViewModel.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let messageService = MessageService.shared
    
    func loadMessages(threadID: String) async {
        isLoading = true
        errorMessage = nil
        
        await messageService.loadMessages(threadID: threadID)
        messages = messageService.messages
        isLoading = false
    }
    
    func sendMessage(text: String, threadID: String) async {
        await messageService.sendMessage(text: text, threadID: threadID)
        messages = messageService.messages
    }
}



