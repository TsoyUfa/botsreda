//
//  AnonymousNameService.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

class AnonymousNameService: ObservableObject {
    static let shared = AnonymousNameService()
    
    @Published var currentName: AnonymousName?
    private var nameHistory: [AnonymousName] = []
    
    private init() {
        loadCurrentName()
    }
    
    func generateNewName() -> AnonymousName {
        let newName = AnonymousName.generate()
        currentName = newName
        nameHistory.append(newName)
        saveCurrentName()
        return newName
    }
    
    func getCurrentName() -> AnonymousName {
        if let current = currentName, current.isActive {
            return current
        }
        return generateNewName()
    }
    
    func regenerateName() {
        generateNewName()
    }
    
    private func saveCurrentName() {
        if let encoded = try? JSONEncoder().encode(currentName) {
            UserDefaults.standard.set(encoded, forKey: "currentAnonymousName")
        }
    }
    
    private func loadCurrentName() {
        if let data = UserDefaults.standard.data(forKey: "currentAnonymousName"),
           let name = try? JSONDecoder().decode(AnonymousName.self, from: data) {
            currentName = name
        }
    }
}



