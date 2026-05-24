//
//  ProfileView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var authService: AuthService
    @StateObject private var viewModel = ProfileViewModel()
    @State private var showingSubscription = false
    @State private var showingSettings = false
    
    var body: some View {
        NavigationView {
            List {
                if let user = authService.currentUser {
                    // Информация о пользователе
                    Section {
                        HStack {
                            Image(systemName: "person.circle.fill")
                                .font(.system(size: 60))
                                .foregroundColor(.purple)
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Анонимный пользователь")
                                    .font(.headline)
                                
                                Text(user.currentAnonymousName)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                                
                                Text("Подписка: \(user.subscriptionType.displayName)")
                                    .font(.caption)
                                    .foregroundColor(.purple)
                            }
                            
                            Spacer()
                        }
                        .padding(.vertical, 8)
                    }
                    
                    // Статистика
                    Section("Статистика") {
                        HStack {
                            Label("Сообщений отправлено", systemImage: "message.fill")
                            Spacer()
                            Text("\(viewModel.sentMessagesCount)")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Label("Веток создано", systemImage: "bubble.left.and.bubble.right.fill")
                            Spacer()
                            Text("\(viewModel.createdThreadsCount)")
                                .foregroundColor(.secondary)
                        }
                        
                        HStack {
                            Label("Лайков получено", systemImage: "heart.fill")
                            Spacer()
                            Text("\(viewModel.receivedLikesCount)")
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    // Подписка
                    Section("Подписка") {
                        Button(action: { showingSubscription = true }) {
                            HStack {
                                Label("Управление подпиской", systemImage: "star.fill")
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    
                    // Настройки
                    Section("Настройки") {
                        Button(action: { showingSettings = true }) {
                            Label("Настройки", systemImage: "gearshape.fill")
                        }
                        
                        Button(action: {
                            anonymousNameService.regenerateName()
                        }) {
                            Label("Сменить анонимное имя", systemImage: "arrow.triangle.2.circlepath")
                        }
                    }
                    
                    // Выход
                    Section {
                        Button(role: .destructive, action: {
                            authService.logout()
                        }) {
                            HStack {
                                Spacer()
                                Text("Выйти")
                                Spacer()
                            }
                        }
                    }
                }
            }
            .navigationTitle("Профиль")
            .sheet(isPresented: $showingSubscription) {
                SubscriptionView()
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
            }
        }
    }
    
    private var anonymousNameService: AnonymousNameService {
        AnonymousNameService.shared
    }
}

#Preview {
    ProfileView()
        .environmentObject(AuthService.shared)
}



