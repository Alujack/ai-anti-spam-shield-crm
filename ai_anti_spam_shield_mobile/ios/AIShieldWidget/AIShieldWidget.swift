//
//  AIShieldWidget.swift
//  AIShieldWidget
//
//  Created by Yoeurn Yan on 21/1/26.
//

import WidgetKit
import SwiftUI

// MARK: - Widget Entry
struct AIShieldEntry: TimelineEntry {
    let date: Date
    let lastScanStatus: ScanStatus
    let totalScans: Int
    let spamDetected: Int

    static var placeholder: AIShieldEntry {
        AIShieldEntry(
            date: Date(),
            lastScanStatus: .none,
            totalScans: 0,
            spamDetected: 0
        )
    }
}

enum ScanStatus: String {
    case safe = "safe"
    case spam = "spam"
    case none = "none"

    var color: Color {
        switch self {
        case .safe: return Color(hex: "059669")
        case .spam: return Color(hex: "DC2626")
        case .none: return Color(hex: "4F46E5")
        }
    }
}

// MARK: - Widget Data Model
struct WidgetData: Codable {
    let lastScanStatus: String
    let totalScans: Int
    let spamDetected: Int
    let lastScanDate: String?
}

// MARK: - Timeline Provider
struct AIShieldTimelineProvider: TimelineProvider {
    private let appGroupID = "group.com.example.aiAntiSpamShieldMobile"
    private let userDefaultsKey = "widget_data"

    func placeholder(in context: Context) -> AIShieldEntry {
        AIShieldEntry.placeholder
    }

    func getSnapshot(in context: Context, completion: @escaping (AIShieldEntry) -> Void) {
        let entry = fetchWidgetData()
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<AIShieldEntry>) -> Void) {
        let entry = fetchWidgetData()
        let refreshDate = Calendar.current.date(byAdding: .minute, value: 15, to: Date())!
        let timeline = Timeline(entries: [entry], policy: .after(refreshDate))
        completion(timeline)
    }

    private func fetchWidgetData() -> AIShieldEntry {
        guard let userDefaults = UserDefaults(suiteName: appGroupID),
              let data = userDefaults.data(forKey: userDefaultsKey),
              let widgetData = try? JSONDecoder().decode(WidgetData.self, from: data) else {
            return AIShieldEntry.placeholder
        }

        return AIShieldEntry(
            date: Date(),
            lastScanStatus: ScanStatus(rawValue: widgetData.lastScanStatus) ?? .none,
            totalScans: widgetData.totalScans,
            spamDetected: widgetData.spamDetected
        )
    }
}

// MARK: - Small Widget View
struct AIShieldSmallWidgetView: View {
    let entry: AIShieldEntry
    @Environment(\.colorScheme) var colorScheme

    private let primaryColor = Color(hex: "4F46E5")
    private let secondaryColor = Color(hex: "7C3AED")

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [primaryColor, secondaryColor],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            VStack(spacing: 8) {
                Image(systemName: "shield.fill")
                    .font(.system(size: 40, weight: .semibold))
                    .foregroundColor(.white)

                Text("AI Shield")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)

                HStack(spacing: 4) {
                    Circle()
                        .fill(entry.lastScanStatus.color)
                        .frame(width: 8, height: 8)
                    Text(statusText)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundColor(.white.opacity(0.9))
                }
            }
        }
        .widgetURL(URL(string: "aishield://home"))
    }

    private var statusText: String {
        switch entry.lastScanStatus {
        case .none: return "Ready"
        case .safe: return "Protected"
        case .spam: return "Alert"
        }
    }
}

// MARK: - Medium Widget View
struct AIShieldMediumWidgetView: View {
    let entry: AIShieldEntry
    @Environment(\.colorScheme) var colorScheme

    private let primaryColor = Color(hex: "4F46E5")

    var body: some View {
        ZStack {
            backgroundColor

            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) {
                        Image(systemName: "shield.fill")
                            .font(.system(size: 24, weight: .semibold))
                            .foregroundColor(primaryColor)

                        Text("AI Shield")
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(textColor)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(entry.totalScans) Scans")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(secondaryTextColor)

                        Text("\(entry.spamDetected) Threats Blocked")
                            .font(.system(size: 11))
                            .foregroundColor(secondaryTextColor.opacity(0.8))
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                VStack(spacing: 8) {
                    HStack(spacing: 8) {
                        QuickActionButton(
                            icon: "doc.text.magnifyingglass",
                            label: "Scan",
                            color: primaryColor,
                            url: "aishield://scan"
                        )

                        QuickActionButton(
                            icon: "mic.fill",
                            label: "Voice",
                            color: Color(hex: "059669"),
                            url: "aishield://voice"
                        )
                    }

                    HStack(spacing: 8) {
                        QuickActionButton(
                            icon: "clock.arrow.circlepath",
                            label: "History",
                            color: Color(hex: "0EA5E9"),
                            url: "aishield://history"
                        )

                        QuickActionButton(
                            icon: "link",
                            label: "URL",
                            color: Color(hex: "D97706"),
                            url: "aishield://phishing-scanner"
                        )
                    }
                }
            }
            .padding(16)
        }
    }

    private var backgroundColor: some View {
        Group {
            if colorScheme == .dark {
                Color(hex: "1E293B")
            } else {
                Color.white
            }
        }
    }

    private var textColor: Color {
        colorScheme == .dark ? Color(hex: "F8FAFC") : Color(hex: "111827")
    }

    private var secondaryTextColor: Color {
        colorScheme == .dark ? Color(hex: "CBD5E1") : Color(hex: "4B5563")
    }
}

// MARK: - Quick Action Button
struct QuickActionButton: View {
    let icon: String
    let label: String
    let color: Color
    let url: String

    @Environment(\.colorScheme) var colorScheme

    var body: some View {
        Link(destination: URL(string: url)!) {
            VStack(spacing: 4) {
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(color.opacity(colorScheme == .dark ? 0.2 : 0.1))
                        .frame(width: 44, height: 44)

                    Image(systemName: icon)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(color)
                }

                Text(label)
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(colorScheme == .dark ?
                        Color(hex: "CBD5E1") : Color(hex: "4B5563"))
            }
        }
    }
}

// MARK: - Main Widget
struct AIShieldWidget: Widget {
    let kind: String = "AIShieldWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: AIShieldTimelineProvider()) { entry in
            AIShieldWidgetEntryView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("AI Shield")
        .description("Quick access to spam detection and security features.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Entry View
struct AIShieldWidgetEntryView: View {
    @Environment(\.widgetFamily) var family
    let entry: AIShieldEntry

    var body: some View {
        switch family {
        case .systemSmall:
            AIShieldSmallWidgetView(entry: entry)
        case .systemMedium:
            AIShieldMediumWidgetView(entry: entry)
        default:
            AIShieldSmallWidgetView(entry: entry)
        }
    }
}

// MARK: - Color Extension
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

#Preview(as: .systemSmall) {
    AIShieldWidget()
} timeline: {
    AIShieldEntry(date: Date(), lastScanStatus: .safe, totalScans: 42, spamDetected: 5)
}

#Preview(as: .systemMedium) {
    AIShieldWidget()
} timeline: {
    AIShieldEntry(date: Date(), lastScanStatus: .safe, totalScans: 42, spamDetected: 5)
}
