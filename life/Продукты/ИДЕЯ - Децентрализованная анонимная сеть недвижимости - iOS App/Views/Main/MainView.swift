//
//  MainView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct MainView: View {
    @EnvironmentObject var authService: AuthService
    @StateObject private var viewModel = MainViewModel()
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Приветствие
                    WelcomeCard()
                    
                    // Статистика
                    StatsView()
                    
                    // Популярные ветки
                    PopularThreadsView(threads: viewModel.popularThreads)
                    
                    // Категории
                    CategoriesView()
                }
                .padding()
            }
            .navigationTitle("Недвижимость Анонимно")
            .refreshable {
                await viewModel.loadData()
            }
            .task {
                await viewModel.loadData()
            }
        }
    }
}

struct WelcomeCard: View {
    @EnvironmentObject var authService: AuthService
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "lock.shield.fill")
                    .font(.system(size: 40))
                    .foregroundColor(.purple)
                
                VStack(alignment: .leading) {
                    Text("Добро пожаловать!")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    if let user = authService.currentUser {
                        Text("Ваше анонимное имя: \(user.currentAnonymousName)")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
            }
            
            Text("Задавайте вопросы без стыда. Общайтесь анонимно.")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(
            LinearGradient(
                gradient: Gradient(colors: [Color.purple.opacity(0.1), Color.blue.opacity(0.1)]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(16)
    }
}

struct StatsView: View {
    var body: some View {
        HStack(spacing: 15) {
            StatCard(title: "Активных", value: "1,234", icon: "person.2.fill", color: .blue)
            StatCard(title: "Веток", value: "567", icon: "bubble.left.and.bubble.right.fill", color: .green)
            StatCard(title: "Сообщений", value: "8,901", icon: "message.fill", color: .orange)
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(value)
                .font(.title3)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct PopularThreadsView: View {
    let threads: [Thread]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Популярные ветки")
                .font(.title3)
                .fontWeight(.bold)
                .padding(.horizontal)
            
            ForEach(threads.prefix(3)) { thread in
                NavigationLink(destination: ChatView(thread: thread)) {
                    ThreadRowView(thread: thread)
                }
            }
        }
    }
}

struct ThreadRowView: View {
    let thread: Thread
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: thread.category.icon)
                .font(.title2)
                .foregroundColor(.purple)
                .frame(width: 40)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(thread.title)
                    .font(.headline)
                    .lineLimit(2)
                
                HStack {
                    Text(thread.category.displayName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Label("\(thread.messageCount)", systemImage: "message.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }
}

struct CategoriesView: View {
    let categories = Thread.ThreadCategory.allCases
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Категории")
                .font(.title3)
                .fontWeight(.bold)
                .padding(.horizontal)
            
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(categories, id: \.self) { category in
                    CategoryCard(category: category)
                }
            }
            .padding(.horizontal)
        }
    }
}

struct CategoryCard: View {
    let category: Thread.ThreadCategory
    
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: category.icon)
                .font(.title)
                .foregroundColor(.purple)
            
            Text(category.displayName)
                .font(.subheadline)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(
            LinearGradient(
                gradient: Gradient(colors: [Color.purple.opacity(0.1), Color.blue.opacity(0.1)]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(12)
    }
}

#Preview {
    MainView()
        .environmentObject(AuthService.shared)
}



