//
//  ProfileViewModel.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var sentMessagesCount = 0
    @Published var createdThreadsCount = 0
    @Published var receivedLikesCount = 0
    @Published var isLoading = false
    
    func loadStats() async {
        isLoading = true
        
        // Здесь будет загрузка статистики с сервера
        // Пока используем мок-данные
        
        sentMessagesCount = 42
        createdThreadsCount = 5
        receivedLikesCount = 128
        
        isLoading = false
    }
}



