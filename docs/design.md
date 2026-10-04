# UI/UX Design Specifications & Visual Guidelines

## Document: `docs/design.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)  
**GUI Framework:** CustomTkinter (Python 3.10+)  
**Theme:** Modern Cyber Dark Theme  

---

## 1. Design Aesthetic & Principles

The application interface is designed for speed, clarity, and zero cognitive load:
- **Dark Mode First:** Reduces eye fatigue during long operational sessions.
- **High-Contrast Data Visibility:** Color-coded status badges for instant recognition.
- **Live Responsiveness:** Real-time table updates as each account completes without UI freezes.
- **Frictionless Google Sheets Flow:** Prominent clipboard copy button with clear feedback.

---

## 2. Color Palette & Token Specifications

| Token Name | Hex Code | Visual Sample / Usage |
| :--- | :--- | :--- |
| **`BG_DARK`** | `#121214` | Main window background |
| **`BG_SURFACE`** | `#1A1A1E` | Card containers and side panels |
| **`BG_ELEVATED`** | `#24242A` | Table rows, input text fields, headers |
| **`BORDER_COLOR`**| `#33333A` | Subtle dividers and component borders |
| **`TEXT_PRIMARY`**| `#F3F4F6` | Primary headings, active values |
| **`TEXT_MUTED`**  | `#9CA3AF` | Secondary labels, timestamps, placeholders |
| **`ACCENT_BLUE`** | `#3B82F6` | Primary action buttons (`Start Checking`) |
| **`ACCENT_HOVER`**| `#2563EB` | Hover state for primary buttons |
| **`STATUS_ACTIVE`**| `#10B981` | Emerald Green badge for verified active accounts |
| **`STATUS_BANNED`**| `#EF4444` | Crimson Red badge for banned/suspended accounts |
| **`STATUS_WARN`**  | `#F59E0B` | Amber Gold badge for private accounts/checkpoints |
| **`STATUS_EMPTY`** | `#6B7280` | Neutral Gray for not found/unknown accounts |

---

## 3. Typography Hierarchy

- **Font Family:** `Segoe UI`, `Inter`, or Native System Sans-Serif.
- **Scale:**
  - **H1 Header:** `18pt` Bold (App title, Brand banner)
  - **Section Titles:** `13pt` Semi-Bold (Mode Selection, Account Input)
  - **Body / Table Cells:** `11pt` Regular (Usernames, Country names, Dates)
  - **Status Badges:** `10pt` Bold (All Caps: `ACTIVE`, `BANNED`, `PRIVATE`)
  - **Captions / Timers:** `9pt` Muted Regular (ETA counter, Elapsed time)

---

## 4. Layout Architecture & Component Blueprint

Default Window Size: **1150 x 750 pixels** (Resizable, minimum 950 x 600).

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ [Logo] MetaInspector Desktop    Session: [🟢 Connected: @dummy_checker] [⚙ Setup]│
├────────────────────────┬─────────────────────────────────────────────────────────┤
│ LEFT PANEL (320px)     │ RIGHT PANEL (Main Data Grid)                            │
│                        │                                                         │
│ Input Usernames:       │ Live Results Table:                                     │
│ ┌────────────────────┐ │ ┌────┬──────────┬────────┬──────────┬──────────┬──────┐ │
│ │ elif70566          │ │ │ #  │ Username │ Status │ Country  │ Joined   │ Time │ │
│ │ mert23933          │ │ ├────┼──────────┼────────┼──────────┼──────────┼──────┤ │
│ │ can572707          │ │ │ 01 │ elif70566│ ACTIVE │ Turkey   │ Sep 2026 │ 2.4s │ │
│ │ ...                │ │ │ 02 │ mert23933│ ACTIVE │ Iran     │ Sep 2026 │ 2.8s │ │
│ └────────────────────┘ │ │ 03 │ bad_user │ BANNED │ N/A      │ N/A      │ 1.1s │ │
│ [📁 Load .txt File]    │ └────┴──────────┴────────┴──────────┴──────────┴──────┘ │
│                        │                                                         │
│ Checking Mode:         │                                                         │
│ (•) Combined (IG + Th) │                                                         │
│ ( ) Instagram Only     │                                                         │
│ ( ) Threads Only       │                                                         │
│                        │                                                         │
│ Controls:              │                                                         │
│ [ ▶ Start Checking ]   │                                                         │
│ [ ❚❚ Pause ]  [ ■ Stop]│                                                         │
├────────────────────────┴─────────────────────────────────────────────────────────┤
│ BOTTOM ACTION BAR                                                                │
│ Progress: [██████████████████░░░░░░░░░░] 60/100 (60%) | Elapsed: 2m 14s | ETA: 1m│
│ [📋 Copy for Google Sheets]  [Export CSV]  [Export Excel]  [📜 View Run History] │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Micro-Interactions & User Feedback

1. **Clipboard Copy Feedback:**
   - Clicking `[📋 Copy for Google Sheets]` immediately triggers a green toast notification banner:
     *"Copied 100 accounts to clipboard! Press Ctrl+V in Google Sheets."*
   - Button text temporarily transforms to *"✓ Copied!"* for 2 seconds.
2. **Status Color Badging:**
   - Active cells display dark green surface with light green text (`#064E3B` / `#34D399`).
   - Banned cells display dark red surface with light red text (`#7F1D1D` / `#F87171`).
3. **Session Status Indicator:**
   - Header displays a live status dot:
     - 🟢 **Connected:** Cookies valid and ready for scraping.
     - 🔴 **Disconnected:** Prompts user to click `[Setup Login]`.
