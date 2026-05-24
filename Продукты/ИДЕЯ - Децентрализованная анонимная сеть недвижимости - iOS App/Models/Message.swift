//
//  Message.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation

struct Message: Identifiable, Codable {
    let id: String
    let threadID: String
    let anonymousName: String
    let text: String
    let timestamp: Date
    let likes: Int
    let isLiked: Bool
    
    var formattedTime: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "ru_RU")
        return formatter.string(from: timestamp)
    }
    
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "ru_RU")
        return formatter.string(from: timestamp)
    }
}

extension Message {
    static let mock = Message(
        id: UUID().uuidString,
        threadID: "thread_1",
        anonymousName: "Анонимный_Пользователь_123",
        text: "Какие застройщики в Уфе сейчас самые надёжные?",
        timestamp: Date(),
        likes: 5,
        isLiked: false
    )
}



