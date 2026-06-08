//
//  Extensions.swift
//  AnonymousRealEstate
//
//  Created by Anton Tsoy
//  Copyright © 2025. All rights reserved.
//

import Foundation
import SwiftUI

extension Date {
    func timeAgoDisplay() -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        formatter.locale = Locale(identifier: "ru_RU")
        return formatter.localizedString(for: self, relativeTo: Date())
    }
}

extension Color {
    static let appPurple = Color(red: 0.4, green: 0.49, blue: 0.92)
    static let appBlue = Color(red: 0.46, green: 0.29, blue: 0.64)
}



