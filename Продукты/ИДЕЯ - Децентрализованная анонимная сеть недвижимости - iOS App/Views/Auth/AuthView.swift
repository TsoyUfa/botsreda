//
//  AuthView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct AuthView: View {
    @EnvironmentObject var authService: AuthService
    @State private var telegramID: String = ""
    @State private var realName: String = ""
    
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            // Логотип и заголовок
            VStack(spacing: 16) {
                Image(systemName: "lock.shield.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.purple)
                
                Text("Недвижимость Анонимно")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Безопасное пространство для открытых вопросов")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            
            Spacer()
            
            // Форма входа
            VStack(spacing: 20) {
                TextField("Telegram ID", text: $telegramID)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.numberPad)
                
                TextField("Ваше имя (только для нас)", text: $realName)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                
                Button(action: {
                    if let id = Int64(telegramID), !realName.isEmpty {
                        authService.authenticate(telegramID: id, realName: realName)
                    }
                }) {
                    Text("Войти")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            LinearGradient(
                                gradient: Gradient(colors: [Color.purple, Color.blue]),
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(12)
                }
                .disabled(telegramID.isEmpty || realName.isEmpty)
            }
            .padding()
            
            // Информация
            VStack(spacing: 8) {
                Text("🔐 Ваши данные защищены")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("При входе вам будет присвоено случайное анонимное имя")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            .padding(.bottom, 40)
        }
        .padding()
    }
}

#Preview {
    AuthView()
        .environmentObject(AuthService.shared)
}



