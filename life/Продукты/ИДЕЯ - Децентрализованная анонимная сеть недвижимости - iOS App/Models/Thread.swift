//
//  Thread.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation

struct Thread: Identifiable, Codable {
    let id: String
    let title: String
    let category: ThreadCategory
    let creatorAnonymousName: String
    let createdAt: Date
    let lastMessageAt: Date
    let messageCount: Int
    let isPinned: Bool
    let isLocked: Bool
    let isPremium: Bool
    
    enum ThreadCategory: String, Codable, CaseIterable {
        case developers = "developers"
        case prices = "prices"
        case problems = "problems"
        case tips = "tips"
        case questions = "questions"
        
        var displayName: String {
            switch self {
            case .developers: return "🏗️ Застройщики"
            case .prices: return "💰 Цены и сделки"
            case .problems: return "⚖️ Проблемы и решения"
            case .tips: return "💡 Советы и инсайты"
            case .questions: return "❓ Вопросы без стыда"
            }
        }
        
        var icon: String {
            switch self {
            case .developers: return "building.2.fill"
            case .prices: return "dollarsign.circle.fill"
            case .problems: return "exclamationmark.triangle.fill"
            case .tips: return "lightbulb.fill"
            case .questions: return "questionmark.circle.fill"
            }
        }
    }
}

extension Thread {
    static let mock = Thread(
        id: UUID().uuidString,
        title: "Какие застройщики в Уфе самые надёжные?",
        category: .developers,
        creatorAnonymousName: "Анонимный_Пользователь_42",
        createdAt: Date().addingTimeInterval(-86400),
        lastMessageAt: Date().addingTimeInterval(-3600),
        messageCount: 15,
        isPinned: false,
        isLocked: false,
        isPremium: false
    )
}



