//
//  User.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation

struct User: Identifiable, Codable {
    let id: String
    let telegramID: Int64
    let realName: String
    let currentAnonymousName: String
    let subscriptionType: SubscriptionType
    let registrationDate: Date
    let isCreator: Bool
    
    enum SubscriptionType: String, Codable, CaseIterable {
        case basic = "basic"
        case premium = "premium"
        case pro = "pro"
        
        var displayName: String {
            switch self {
            case .basic: return "Базовый"
            case .premium: return "Премиум"
            case .pro: return "Про"
            }
        }
        
        var price: Int {
            switch self {
            case .basic: return 0
            case .premium: return 1500
            case .pro: return 5000
            }
        }
        
        var features: [String] {
            switch self {
            case .basic:
                return [
                    "Ограниченное количество сообщений в день",
                    "Доступ к основным веткам",
                    "Базовые функции"
                ]
            case .premium:
                return [
                    "Неограниченное количество сообщений",
                    "Приоритет в создании веток",
                    "Доступ к закрытым веткам",
                    "Расширенная аналитика"
                ]
            case .pro:
                return [
                    "Всё из премиума",
                    "Доступ к агрегированной аналитике",
                    "Вопросы экспертам анонимно",
                    "Приоритетная поддержка"
                ]
            }
        }
    }
}

extension User {
    static let mock = User(
        id: UUID().uuidString,
        telegramID: 123456789,
        realName: "Антон Цой",
        currentAnonymousName: "Случайный_Пользователь_42",
        subscriptionType: .premium,
        registrationDate: Date(),
        isCreator: false
    )
}



