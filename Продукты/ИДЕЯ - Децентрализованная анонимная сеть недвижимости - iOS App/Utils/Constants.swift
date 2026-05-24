//
//  Constants.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation

struct Constants {
    // Telegram Bot API Token
    // ВАЖНО: Замените на реальный токен вашего бота
    static let telegramBotToken = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    
    // API Endpoints
    static let apiBaseURL = "https://api.telegram.org/bot"
    static let channelID = "@anonymous_realestate" // Замените на ID вашего канала
    
    // Ограничения для базовой подписки
    static let basicMaxMessagesPerDay = 10
    static let premiumMaxMessagesPerDay = Int.max
    static let proMaxMessagesPerDay = Int.max
    
    // Цвета приложения
    struct Colors {
        static let primary = "primary"
        static let secondary = "secondary"
        static let accent = "accent"
    }
}



