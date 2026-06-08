//
//  AuthService.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

class AuthService: ObservableObject {
    static let shared = AuthService()
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let anonymousNameService = AnonymousNameService.shared
    
    private init() {
        checkAuthStatus()
    }
    
    func checkAuthStatus() {
        if let userData = UserDefaults.standard.data(forKey: "currentUser"),
           let user = try? JSONDecoder().decode(User.self, from: userData) {
            currentUser = user
            isAuthenticated = true
        }
    }
    
    func authenticate(telegramID: Int64, realName: String) {
        isLoading = true
        errorMessage = nil
        
        // Генерируем новое анонимное имя
        let anonymousName = anonymousNameService.generateNewName()
        
        // Создаём пользователя
        let user = User(
            id: UUID().uuidString,
            telegramID: telegramID,
            realName: realName,
            currentAnonymousName: anonymousName.name,
            subscriptionType: .basic,
            registrationDate: Date(),
            isCreator: false
        )
        
        // Сохраняем пользователя
        if let encoded = try? JSONEncoder().encode(user) {
            UserDefaults.standard.set(encoded, forKey: "currentUser")
        }
        
        currentUser = user
        isAuthenticated = true
        isLoading = false
    }
    
    func logout() {
        currentUser = nil
        isAuthenticated = false
        UserDefaults.standard.removeObject(forKey: "currentUser")
        anonymousNameService.regenerateName()
    }
    
    func updateSubscription(_ type: User.SubscriptionType) {
        guard var user = currentUser else { return }
        
        let updatedUser = User(
            id: user.id,
            telegramID: user.telegramID,
            realName: user.realName,
            currentAnonymousName: user.currentAnonymousName,
            subscriptionType: type,
            registrationDate: user.registrationDate,
            isCreator: user.isCreator
        )
        
        if let encoded = try? JSONEncoder().encode(updatedUser) {
            UserDefaults.standard.set(encoded, forKey: "currentUser")
        }
        
        currentUser = updatedUser
    }
}



