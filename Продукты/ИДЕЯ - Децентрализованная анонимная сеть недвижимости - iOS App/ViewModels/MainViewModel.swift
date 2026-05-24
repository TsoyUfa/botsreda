//
//  MainViewModel.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import Combine

@MainActor
class MainViewModel: ObservableObject {
    @Published var threads: [Thread] = []
    @Published var popularThreads: [Thread] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let telegramService = TelegramService.shared
    
    func loadData() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let loadedThreads = try await telegramService.getThreads()
            threads = loadedThreads
            popularThreads = Array(loadedThreads.prefix(5))
            isLoading = false
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
}



