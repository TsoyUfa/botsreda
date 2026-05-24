//
//  MessageBubbleView.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import SwiftUI

struct MessageBubbleView: View {
    let message: Message
    @State private var isLiked = false
    @State private var likeCount = 0
    
    init(message: Message) {
        self.message = message
        _isLiked = State(initialValue: message.isLiked)
        _likeCount = State(initialValue: message.likes)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(message.anonymousName)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.purple)
                
                Spacer()
                
                Text(message.formattedTime)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Text(message.text)
                .font(.body)
                .padding(.vertical, 8)
            
            HStack {
                Button(action: {
                    isLiked.toggle()
                    likeCount += isLiked ? 1 : -1
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: isLiked ? "heart.fill" : "heart")
                            .foregroundColor(isLiked ? .red : .secondary)
                        
                        Text("\(likeCount)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .buttonStyle(PlainButtonStyle())
                
                Spacer()
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }
}

#Preview {
    VStack {
        MessageBubbleView(message: Message.mock)
        Spacer()
    }
    .padding()
}



