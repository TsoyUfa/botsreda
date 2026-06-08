//
//  TelegramService.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

class TelegramService: ObservableObject {
    static let shared = TelegramService()
    
    private let baseURL = "https://api.telegram.org/bot"
    private let botToken: String
    
    @Published var isConnected = false
    @Published var errorMessage: String?
    
    private init() {
        // Получаем токен из констант или настроек
        self.botToken = Constants.telegramBotToken
    }
    
    func sendMessage(text: String, threadID: String, anonymousName: String) async throws -> Message {
        // Здесь будет интеграция с Telegram Bot API
        // Пока возвращаем мок-данные
        
        return Message(
            id: UUID().uuidString,
            threadID: threadID,
            anonymousName: anonymousName,
            text: text,
            timestamp: Date(),
            likes: 0,
            isLiked: false
        )
    }
    
    func getThreads() async throws -> [Thread] {
        // Здесь будет запрос к API для получения веток
        // Пока возвращаем мок-данные
        
        return [
            Thread.mock,
            Thread(
                id: UUID().uuidString,
                title: "Реальные цены на новостройки в Уфе",
                category: .prices,
                creatorAnonymousName: "Анонимный_Пользователь_789",
                createdAt: Date().addingTimeInterval(-172800),
                lastMessageAt: Date().addingTimeInterval(-7200),
                messageCount: 42,
                isPinned: true,
                isLocked: false,
                isPremium: false
            )
        ]
    }
    
    func getMessages(threadID: String) async throws -> [Message] {
        // Здесь будет запрос к API для получения сообщений
        // Пока возвращаем мок-данные
        
        return [
            Message.mock,
            Message(
                id: UUID().uuidString,
                threadID: threadID,
                anonymousName: "Случайный_Пользователь_456",
                text: "Я работал с несколькими застройщиками, могу поделиться опытом.",
                timestamp: Date().addingTimeInterval(-1800),
                likes: 3,
                isLiked: false
            )
        ]
    }
}



