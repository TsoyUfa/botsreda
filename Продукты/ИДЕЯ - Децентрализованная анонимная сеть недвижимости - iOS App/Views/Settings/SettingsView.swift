//
//  SettingsView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct SettingsView: View {
    @Environment(\.dismiss) var dismiss
    @AppStorage("notificationsEnabled") private var notificationsEnabled = true
    @AppStorage("autoRegenerateName") private var autoRegenerateName = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("Уведомления") {
                    Toggle("Включить уведомления", isOn: $notificationsEnabled)
                }
                
                Section("Анонимность") {
                    Toggle("Автоматически менять имя при входе", isOn: $autoRegenerateName)
                    
                    Text("При включении этой опции ваше анонимное имя будет автоматически меняться при каждом входе в приложение.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Section("О приложении") {
                    HStack {
                        Text("Версия")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    Link(destination: URL(string: "https://antontsoy.ru")!) {
                        HStack {
                            Text("Веб-сайт")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Section("Поддержка") {
                    Link(destination: URL(string: "https://t.me/antontsoy")!) {
                        HStack {
                            Text("Telegram")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Настройки")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Готово") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    SettingsView()
}



