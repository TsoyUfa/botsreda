//
//  ContentView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authService: AuthService
    @State private var selectedTab = 0
    
    var body: some View {
        Group {
            if authService.isAuthenticated {
                MainTabView(selectedTab: $selectedTab)
            } else {
                AuthView()
            }
        }
    }
}

struct MainTabView: View {
    @Binding var selectedTab: Int
    @StateObject private var mainViewModel = MainViewModel()
    
    var body: some View {
        TabView(selection: $selectedTab) {
            MainView()
                .tabItem {
                    Label("Главная", systemImage: "house.fill")
                }
                .tag(0)
            
            ThreadListView()
                .tabItem {
                    Label("Ветки", systemImage: "bubble.left.and.bubble.right.fill")
                }
                .tag(1)
            
            ProfileView()
                .tabItem {
                    Label("Профиль", systemImage: "person.fill")
                }
                .tag(2)
        }
        .environmentObject(mainViewModel)
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthService.shared)
        .environmentObject(TelegramService.shared)
}



