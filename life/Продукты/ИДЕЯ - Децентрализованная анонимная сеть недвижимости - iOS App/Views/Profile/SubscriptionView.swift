//
//  SubscriptionView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct SubscriptionView: View {
    @EnvironmentObject var authService: AuthService
    @Environment(\.dismiss) var dismiss
    @State private var selectedSubscription: User.SubscriptionType?
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    Text("Выберите подписку")
                        .font(.title2)
                        .fontWeight(.bold)
                        .padding(.top)
                    
                    ForEach(User.SubscriptionType.allCases, id: \.self) { type in
                        SubscriptionCard(
                            type: type,
                            isSelected: selectedSubscription == type,
                            isCurrent: authService.currentUser?.subscriptionType == type
                        ) {
                            selectedSubscription = type
                        }
                    }
                    
                    if let selected = selectedSubscription,
                       selected != authService.currentUser?.subscriptionType {
                        Button(action: {
                            authService.updateSubscription(selected)
                            dismiss()
                        }) {
                            Text("Оформить подписку")
                                .font(.headline)
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.purple)
                                .cornerRadius(12)
                        }
                        .padding()
                    }
                }
                .padding()
            }
            .navigationTitle("Подписки")
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

struct SubscriptionCard: View {
    let type: User.SubscriptionType
    let isSelected: Bool
    let isCurrent: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(type.displayName)
                            .font(.title3)
                            .fontWeight(.bold)
                        
                        if type.price > 0 {
                            Text("\(type.price) ₽/месяц")
                                .font(.headline)
                                .foregroundColor(.purple)
                        } else {
                            Text("Бесплатно")
                                .font(.headline)
                                .foregroundColor(.green)
                        }
                    }
                    
                    Spacer()
                    
                    if isCurrent {
                        Text("Текущая")
                            .font(.caption)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Color.green.opacity(0.2))
                            .foregroundColor(.green)
                            .cornerRadius(8)
                    }
                    
                    if isSelected {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.purple)
                            .font(.title2)
                    }
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(type.features, id: \.self) { feature in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                                .font(.caption)
                            
                            Text(feature)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(isSelected ? Color.purple.opacity(0.1) : Color(.systemGray6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(isSelected ? Color.purple : Color.clear, lineWidth: 2)
                    )
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    SubscriptionView()
        .environmentObject(AuthService.shared)
}



