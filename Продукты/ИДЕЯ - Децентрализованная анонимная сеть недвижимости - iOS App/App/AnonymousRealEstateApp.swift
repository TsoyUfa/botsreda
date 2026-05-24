//
//  AnonymousRealEstateApp.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

@main
struct AnonymousRealEstateApp: App {
    @StateObject private var authService = AuthService.shared
    @StateObject private var telegramService = TelegramService.shared
    
    init() {
        // Настройка внешнего вида приложения
        setupAppearance()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authService)
                .environmentObject(telegramService)
                .onAppear {
                    authService.checkAuthStatus()
                }
        }
    }
    
    private func setupAppearance() {
        // Настройка цветовой схемы
        let appearance = UINavigationBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor.systemBackground
        appearance.titleTextAttributes = [.foregroundColor: UIColor.label]
        appearance.largeTitleTextAttributes = [.foregroundColor: UIColor.label]
        
        UINavigationBar.appearance().standardAppearance = appearance
        UINavigationBar.appearance().scrollEdgeAppearance = appearance
    }
}



