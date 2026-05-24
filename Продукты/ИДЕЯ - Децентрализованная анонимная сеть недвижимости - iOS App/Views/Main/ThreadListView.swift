//
//  ThreadListView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct ThreadListView: View {
    @StateObject private var viewModel = MainViewModel()
    @State private var selectedCategory: Thread.ThreadCategory?
    @State private var showingCreateThread = false
    
    var filteredThreads: [Thread] {
        if let category = selectedCategory {
            return viewModel.threads.filter { $0.category == category }
        }
        return viewModel.threads
    }
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Фильтр по категориям
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        CategoryFilterButton(
                            title: "Все",
                            isSelected: selectedCategory == nil
                        ) {
                            selectedCategory = nil
                        }
                        
                        ForEach(Thread.ThreadCategory.allCases, id: \.self) { category in
                            CategoryFilterButton(
                                title: category.displayName,
                                isSelected: selectedCategory == category
                            ) {
                                selectedCategory = category
                            }
                        }
                    }
                    .padding()
                }
                .background(Color(.systemGray6))
                
                // Список веток
                List {
                    ForEach(filteredThreads) { thread in
                        NavigationLink(destination: ChatView(thread: thread)) {
                            ThreadListRowView(thread: thread)
                        }
                    }
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("Ветки диалогов")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingCreateThread = true }) {
                        Image(systemName: "plus.circle.fill")
                            .font(.title2)
                    }
                }
            }
            .sheet(isPresented: $showingCreateThread) {
                CreateThreadView()
            }
            .refreshable {
                await viewModel.loadData()
            }
            .task {
                await viewModel.loadData()
            }
        }
    }
}

struct CategoryFilterButton: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.subheadline)
                .fontWeight(isSelected ? .semibold : .regular)
                .foregroundColor(isSelected ? .white : .primary)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(isSelected ? Color.purple : Color(.systemGray5))
                .cornerRadius(20)
        }
    }
}

struct ThreadListRowView: View {
    let thread: Thread
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: thread.category.icon)
                .font(.title2)
                .foregroundColor(.purple)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(thread.title)
                        .font(.headline)
                        .lineLimit(2)
                    
                    if thread.isPinned {
                        Image(systemName: "pin.fill")
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                    
                    if thread.isPremium {
                        Image(systemName: "star.fill")
                            .font(.caption)
                            .foregroundColor(.yellow)
                    }
                }
                
                HStack {
                    Text(thread.category.displayName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    Label("\(thread.messageCount)", systemImage: "message.fill")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text(thread.lastMessageAt, style: .relative)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 8)
    }
}

struct CreateThreadView: View {
    @Environment(\.dismiss) var dismiss
    @State private var title = ""
    @State private var selectedCategory: Thread.ThreadCategory = .questions
    @State private var message = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Название ветки") {
                    TextField("Введите название", text: $title)
                }
                
                Section("Категория") {
                    Picker("Категория", selection: $selectedCategory) {
                        ForEach(Thread.ThreadCategory.allCases, id: \.self) { category in
                            Text(category.displayName).tag(category)
                        }
                    }
                }
                
                Section("Первое сообщение") {
                    TextEditor(text: $message)
                        .frame(height: 100)
                }
            }
            .navigationTitle("Создать ветку")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Отмена") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Создать") {
                        // Здесь будет логика создания ветки
                        dismiss()
                    }
                    .disabled(title.isEmpty || message.isEmpty)
                }
            }
        }
    }
}

#Preview {
    ThreadListView()
}



