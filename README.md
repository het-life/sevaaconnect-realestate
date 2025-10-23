# LandScout ROI (Real Estate Field ROI App)

## Overview
LandScout ROI is an intelligent real-estate field application that enables scouts and investors to drop pins on a map, log land prices and broker contacts, and instantly calculate construction feasibility and return on investment (ROI).

## Target Audience
- Small-scale developers, builders, and investors in India
- Real-estate scouts and brokers working in emerging urban-fringe zones such as Surat, Ahmedabad, and Vadodara
- Architecture and construction professionals evaluating project viability onsite

## Core Features
- Interactive map interface to drop pins anywhere and record land data
- Detailed pin entries capturing price per sqft/var, land type (NA/Agriculture), zone, and notes
- Broker contact attachment with name, phone, WhatsApp, and reliability rating
- Built-in deal analyzer that calculates feasibility and ROI from plot size, FSI, construction cost, taxes, and selling price
- Quick sensitivity analysis showing ROI changes with ±10% cost or selling price adjustments
- Search and filter capabilities for pins by area, land type, or price range
- Offline-first mode with automatic synchronization when online
- Data export to Excel or PDF
- Optional login for cloud backup via Google or Apple sign-in

## Monetization Strategy
- Free for personal use
- Future Pro version to include cloud sync with team collaboration, advanced analytics dashboards, and an API export for developers and consultants

## Platform Roadmap
- Initial release on iOS using SwiftUI
- Web mirror (React or Flutter Web) for desktop usage in future iterations

## Inspiration
- Google Maps for interaction design
- Notion and Airtable for structured data tagging
- MagicPlan or LandGlide for location-based valuation tools

## Build Goal
Create a location-based data-collection app that combines map pin tagging, contact logging, and ROI calculation in one lightweight mobile interface. The system should run locally first with simple sync, allow one-tap feasibility reports, and display ROI and profit visuals per project.

## Floot AI Prompt
Copy and paste the following prompt into [Floot.com](https://floot.com) to generate a runnable full-stack version of LandScout ROI:

```
🧠 Floot AI Prompt: LandScout ROI (Real Estate Field ROI App)

App Name:
LandScout ROI

One-Liner Summary:
An intelligent real-estate field app that lets users drop pins on Google Maps to log land data, broker contacts, and instantly calculate construction feasibility and ROI for each plot.

🧩 Platform

Primary: iOS & Android (built with Flutter or React Native)

Backend: Firebase (Firestore + Authentication + Storage)

Offline Mode: Enabled (Sync when back online)

Google Maps API integrated

👥 Target Users

Small-scale real estate developers and investors in India

Field scouts, brokers, and consultants

Architects evaluating onsite project viability

⚙️ Core Features
1. Interactive Map Interface

Show Google Map centered on user location

Long press or tap “+” Floating Button to drop a new pin

Each pin stores details: land type, zone, broker, price, and notes

Pin colors reflect reliability score (1–5 scale)

2. Pin Details & Data Entry

Fields:

Title / Label

Address (auto from lat/lng via reverse geocoding)

Land Type (NA, Agriculture, Industrial, Other)

Zone (e.g., R1, R2, I1, Agri)

Price and Unit (₹/sqft, ₹/sqyard, ₹/var — where 1 var = 9 sqft)

Notes / Remarks

Broker Info: Name, Phone, WhatsApp, Reliability (1–5)

Attach photos of site (upload to Firebase Storage)

3. Deal Analyzer (ROI Calculator)

Input:

Plot Size (sqft)

FSI

Construction Cost / sqft

Gov Taxes (%)

Other Costs

Expected Selling Price / sqft

Auto-calculated fields:

Buildable Area (plotSize * FSI)

Construction Cost

Land Cost (unit-aware)

Total Cost

Gross Revenue

Profit

ROI %

Sensitivity Analysis (±10% price or cost)

4. Quick Filters & Search

Search pins by area, land type, or price range

Filter toggle buttons: NA / Agri / Industrial

ROI color-coded marker view (red = low, green = high ROI)

5. Offline Mode

Data stored locally first, syncs automatically when online

Cloud backup linked to user’s Firebase Auth (Google sign-in)

6. Exports

Export selected analyses as:

CSV / Excel (for data)

PDF (for field report summary)

Include pin location map snapshot, broker contact, and ROI table.

💾 Firebase Collections

users

displayName, phone, createdAt

pins

title, lat, lng, address, landType, zone, price, priceUnit, notes, brokerId, reliability, photos[], ownerId, timestamps

brokers

name, phone, whatsapp, reliability, notes, ownerId

analyses

pinId, plotSizeSqft, fsi, buildableSqft, constructionCostPerSqft, constructionCost, landCost, totalCost, grossRevenue, profit, roiPct, sensitivity (+10%/-10%), ownerId

🧮 Formulas (for Floot Actions or Custom Code)

Buildable area:
buildableSqft = plotSizeSqft * fsi

Construction cost:
constructionCost = buildableSqft * constructionCostPerSqft

Land cost (unit-aware):

if priceUnit == 'INR_per_sqft'   → price * plotSizeSqft
if priceUnit == 'INR_per_sqyard' → price * (plotSizeSqft / 9)
if priceUnit == 'INR_per_var'    → price * (plotSizeSqft / 9)


Total cost:
totalCost = landCost + constructionCost + otherCosts + (govTaxesPct * (landCost + constructionCost))

Gross revenue:
grossRevenue = buildableSqft * avgSellPricePerSqft

Profit:
profit = grossRevenue - totalCost

ROI %:
roiPct = (profit / totalCost) * 100

Sensitivity (±10%):

sellPriceUp10   = ((buildableSqft * avgSellPricePerSqft * 1.10) - totalCost) / totalCost * 100
sellPriceDown10 = ((buildableSqft * avgSellPricePerSqft * 0.90) - totalCost) / totalCost * 100
costUp10        = (grossRevenue - (totalCost * 1.10)) / (totalCost * 1.10) * 100
costDown10      = (grossRevenue - (totalCost * 0.90)) / (totalCost * 0.90) * 100

🔐 Firebase Security Rules

Users can only read/write their own documents (match ownerId == auth.uid)

Collections protected: pins, brokers, analyses

💰 Monetization (Later Pro Version)

Free: single-user mode with local sync

Pro (subscription): Cloud team sync, analytics dashboards, API export

📱 Screen List

Splash & Auth (Google Sign-In)

Map Home (Google Map + Pins + Filters)

Add / Edit Pin Form

Broker List & Add Broker Modal

ROI Analyzer Form

ROI Report (PDF Export Page)

Settings / Account

🎨 UI Design Notes

Use Google Maps as full background

Floating buttons for “Add Pin” and “My Location”

Clean Notion-style sheets for data entry

ROI display with small bar chart

Offline indicator (grey cloud when disconnected)

📦 Deliverables (Floot should generate)

Fully linked front-end with Google Maps and Firebase Auth

Firestore structure (collections + rules)

ROI calculator logic (with formulas above)

Working CRUD for pins and brokers

Offline data persistence

Export actions (CSV & PDF)

Deployed version preview link
```

Would you like to extend this prompt with any of the following?

- ✅ A screen-by-screen wireframe plan
- ✅ A database schema for Supabase or Firebase
- ✅ A feature roadmap (MVP → V2 → Pro)

