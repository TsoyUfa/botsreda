//
//  AnonymousName.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation

struct AnonymousName: Codable {
    let name: String
    let generatedAt: Date
    let isActive: Bool
    
    static func generate() -> AnonymousName {
        let adjectives = [
            "Случайный", "Анонимный", "Скрытый", "Тайный", "Невидимый",
            "Загадочный", "Неизвестный", "Скрытый", "Тихий", "Спокойный"
        ]
        
        let nouns = [
            "Пользователь", "Участник", "Человек", "Гость", "Посетитель",
            "Собеседник", "Слушатель", "Наблюдатель", "Исследователь", "Эксперт"
        ]
        
        let randomAdjective = adjectives.randomElement() ?? "Случайный"
        let randomNoun = nouns.randomElement() ?? "Пользователь"
        let randomNumber = Int.random(in: 1...9999)
        
        let name = "\(randomAdjective)_\(randomNoun)_\(randomNumber)"
        
        return AnonymousName(
            name: name,
            generatedAt: Date(),
            isActive: true
        )
    }
}



