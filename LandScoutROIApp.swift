import SwiftUI
import MapKit

// MARK: - Core Models

enum LandType: String, CaseIterable, Identifiable, Codable {
    case na = "NA"
    case agriculture = "Agriculture"
    case industrial = "Industrial"
    case other = "Other"

    var id: String { rawValue }
}

enum PriceUnit: String, CaseIterable, Identifiable, Codable {
    case inrPerSqft = "INR_per_sqft"
    case inrPerSqyard = "INR_per_sqyard"
    case inrPerVar = "INR_per_var"

    var id: String { rawValue }

    var description: String {
        switch self {
        case .inrPerSqft: return "₹/sqft"
        case .inrPerSqyard: return "₹/sqyard"
        case .inrPerVar: return "₹/var"
        }
    }
}

struct Broker: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var phone: String
    var whatsapp: String
    var reliability: Int
    var notes: String

    init(
        id: UUID = UUID(),
        name: String = "",
        phone: String = "",
        whatsapp: String = "",
        reliability: Int = 3,
        notes: String = ""
    ) {
        self.id = id
        self.name = name
        self.phone = phone
        self.whatsapp = whatsapp
        self.reliability = reliability
        self.notes = notes
    }
}

struct LandPin: Identifiable {
    let id: UUID
    var title: String
    var coordinate: CLLocationCoordinate2D
    var address: String
    var landType: LandType
    var zone: String
    var price: Double
    var priceUnit: PriceUnit
    var notes: String
    var broker: Broker?
    var reliability: Int
    var photos: [URL]
    var createdAt: Date

    init(
        id: UUID = UUID(),
        title: String,
        coordinate: CLLocationCoordinate2D,
        address: String = "",
        landType: LandType = .na,
        zone: String = "",
        price: Double = 0,
        priceUnit: PriceUnit = .inrPerSqft,
        notes: String = "",
        broker: Broker? = nil,
        reliability: Int = 3,
        photos: [URL] = [],
        createdAt: Date = Date()
    ) {
        self.id = id
        self.title = title
        self.coordinate = coordinate
        self.address = address
        self.landType = landType
        self.zone = zone
        self.price = price
        self.priceUnit = priceUnit
        self.notes = notes
        self.broker = broker
        self.reliability = reliability
        self.photos = photos
        self.createdAt = createdAt
    }
}

struct ROIAnalysis: Identifiable, Codable {
    let id: UUID
    var pinID: UUID
    var plotSizeSqft: Double
    var fsi: Double
    var constructionCostPerSqft: Double
    var otherCosts: Double
    var govTaxesPct: Double
    var avgSellPricePerSqft: Double

    var buildableSqft: Double { plotSizeSqft * fsi }
    var constructionCost: Double { buildableSqft * constructionCostPerSqft }

    func landCost(for pin: LandPin) -> Double {
        switch pin.priceUnit {
        case .inrPerSqft:
            return pin.price * plotSizeSqft
        case .inrPerSqyard:
            return pin.price * (plotSizeSqft / 9.0)
        case .inrPerVar:
            return pin.price * (plotSizeSqft / 9.0)
        }
    }

    func totalCost(for pin: LandPin) -> Double {
        let baseCost = landCost(for: pin) + constructionCost + otherCosts
        return baseCost + (govTaxesPct / 100.0 * baseCost)
    }

    func grossRevenue() -> Double {
        buildableSqft * avgSellPricePerSqft
    }

    func profit(for pin: LandPin) -> Double {
        grossRevenue() - totalCost(for: pin)
    }

    func roiPercentage(for pin: LandPin) -> Double {
        let total = totalCost(for: pin)
        guard total != 0 else { return 0 }
        return (profit(for: pin) / total) * 100
    }

    func sensitivity(for pin: LandPin) -> SensitivityResult {
        let total = totalCost(for: pin)
        let revenue = grossRevenue()
        let sellUp = ((buildableSqft * avgSellPricePerSqft * 1.10) - total) / total * 100
        let sellDown = ((buildableSqft * avgSellPricePerSqft * 0.90) - total) / total * 100
        let costUp = (revenue - (total * 1.10)) / (total * 1.10) * 100
        let costDown = (revenue - (total * 0.90)) / (total * 0.90) * 100
        return SensitivityResult(
            sellPriceUp10: sellUp,
            sellPriceDown10: sellDown,
            costUp10: costUp,
            costDown10: costDown
        )
    }
}

struct SensitivityResult: Codable {
    var sellPriceUp10: Double
    var sellPriceDown10: Double
    var costUp10: Double
    var costDown10: Double
}

// MARK: - Persistence (Simple Local Storage)

protocol PinStorage {
    func save(pins: [LandPin])
    func load() -> [LandPin]
}

final class JSONPinStorage: PinStorage {
    private let fileURL: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    init(filename: String = "land_pins.json") {
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        fileURL = documents.appendingPathComponent(filename)
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    }

    func save(pins: [LandPin]) {
        do {
            let data = try encoder.encode(pins.map(SerializablePin.init))
            try data.write(to: fileURL, options: [.atomic])
        } catch {
            print("Failed to save pins: \(error)")
        }
    }

    func load() -> [LandPin] {
        guard let data = try? Data(contentsOf: fileURL) else { return [] }
        do {
            let serializablePins = try decoder.decode([SerializablePin].self, from: data)
            return serializablePins.map { $0.pin }
        } catch {
            print("Failed to load pins: \(error)")
            return []
        }
    }

    private struct SerializablePin: Codable {
        var id: UUID
        var title: String
        var latitude: Double
        var longitude: Double
        var address: String
        var landType: LandType
        var zone: String
        var price: Double
        var priceUnit: PriceUnit
        var notes: String
        var broker: Broker?
        var reliability: Int
        var photos: [URL]
        var createdAt: Date

        init(pin: LandPin) {
            id = pin.id
            title = pin.title
            latitude = pin.coordinate.latitude
            longitude = pin.coordinate.longitude
            address = pin.address
            landType = pin.landType
            zone = pin.zone
            price = pin.price
            priceUnit = pin.priceUnit
            notes = pin.notes
            broker = pin.broker
            reliability = pin.reliability
            photos = pin.photos
            createdAt = pin.createdAt
        }

        var pin: LandPin {
            LandPin(
                id: id,
                title: title,
                coordinate: .init(latitude: latitude, longitude: longitude),
                address: address,
                landType: landType,
                zone: zone,
                price: price,
                priceUnit: priceUnit,
                notes: notes,
                broker: broker,
                reliability: reliability,
                photos: photos,
                createdAt: createdAt
            )
        }
    }
}

// MARK: - View Model

@MainActor
final class LandScoutViewModel: ObservableObject {
    @Published var pins: [LandPin] = [] {
        didSet { storage.save(pins: pins) }
    }
    @Published var selectedPin: LandPin?
    @Published var analyses: [UUID: ROIAnalysis] = [:]
    @Published var activeFilters: Set<LandType> = []
    @Published var searchText: String = ""
    @Published var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 21.1702, longitude: 72.8311),
        span: MKCoordinateSpan(latitudeDelta: 0.1, longitudeDelta: 0.1)
    )

    private let storage: PinStorage

    init(storage: PinStorage = JSONPinStorage()) {
        self.storage = storage
        pins = storage.load()
        if pins.isEmpty {
            pins = Self.samplePins
        }
    }

    var filteredPins: [LandPin] {
        pins.filter { pin in
            let matchesFilter = activeFilters.isEmpty || activeFilters.contains(pin.landType)
            let matchesSearch = searchText.isEmpty || pin.title.localizedCaseInsensitiveContains(searchText) || pin.zone.localizedCaseInsensitiveContains(searchText)
            return matchesFilter && matchesSearch
        }
    }

    func addPin(_ pin: LandPin) {
        pins.append(pin)
        selectedPin = pin
    }

    func updatePin(_ pin: LandPin) {
        guard let index = pins.firstIndex(where: { $0.id == pin.id }) else { return }
        pins[index] = pin
        selectedPin = pin
    }

    func deletePin(_ pin: LandPin) {
        pins.removeAll { $0.id == pin.id }
        analyses.removeValue(forKey: pin.id)
    }

    func analysis(for pin: LandPin) -> ROIAnalysis {
        if let existing = analyses[pin.id] { return existing }
        let analysis = ROIAnalysis(
            id: UUID(),
            pinID: pin.id,
            plotSizeSqft: 2000,
            fsi: 2.0,
            constructionCostPerSqft: 2200,
            otherCosts: 500000,
            govTaxesPct: 5,
            avgSellPricePerSqft: 3200
        )
        analyses[pin.id] = analysis
        return analysis
    }

    func saveAnalysis(_ analysis: ROIAnalysis) {
        analyses[analysis.pinID] = analysis
    }

    static let samplePins: [LandPin] = [
        LandPin(
            title: "Surat Ring Road Plot",
            coordinate: CLLocationCoordinate2D(latitude: 21.2145, longitude: 72.8302),
            address: "Vesu, Surat",
            landType: .na,
            zone: "R2",
            price: 4500,
            priceUnit: .inrPerSqft,
            notes: "Upcoming metro corridor, high ROI potential",
            broker: Broker(name: "Rahul Patel", phone: "+91-90000-12345", whatsapp: "+91-90000-12345", reliability: 4, notes: "Has direct seller contact"),
            reliability: 4
        ),
        LandPin(
            title: "Vadodara Industrial",
            coordinate: CLLocationCoordinate2D(latitude: 22.3072, longitude: 73.1812),
            address: "Manjusar GIDC",
            landType: .industrial,
            zone: "I1",
            price: 2500,
            priceUnit: .inrPerSqyard,
            notes: "Close to highway, logistics park planned",
            broker: Broker(name: "Sneha Desai", phone: "+91-95555-45678", whatsapp: "+91-95555-45678", reliability: 5, notes: "Handled similar deals"),
            reliability: 5
        )
    ]
}

// MARK: - Views

struct LandScoutROIApp: App {
    @StateObject private var viewModel = LandScoutViewModel()

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                MapHomeView()
                    .environmentObject(viewModel)
            }
        }
    }
}

struct MapHomeView: View {
    @EnvironmentObject private var viewModel: LandScoutViewModel
    @State private var showingAddPinSheet = false
    @State private var editingPin: LandPin?
    @State private var showingAnalysis = false

    var body: some View {
        ZStack(alignment: .top) {
            Map(
                position: Binding(
                    get: { .region(viewModel.region) },
                    set: { newValue in
                        if case let .region(region) = newValue {
                            viewModel.region = region
                        }
                    }
                ),
                interactionModes: [.all],
                selection: Binding(
                    get: { viewModel.selectedPin?.id },
                    set: { id in
                        if let id, let pin = viewModel.pins.first(where: { $0.id == id }) {
                            viewModel.selectedPin = pin
                        }
                    }
                ),
                annotationItems: viewModel.filteredPins
            ) { pin in
                MapAnnotation(coordinate: pin.coordinate) {
                    Button {
                        viewModel.selectedPin = pin
                        showingAnalysis = true
                    } label: {
                        VStack(spacing: 4) {
                            Text(String(format: "%.0f%%", viewModel.analysis(for: pin).roiPercentage(for: pin)))
                                .font(.caption2.weight(.bold))
                                .padding(4)
                                .background(color(for: pin))
                                .clipShape(RoundedRectangle(cornerRadius: 6))
                            Image(systemName: "mappin.circle.fill")
                                .font(.title2)
                                .foregroundStyle(color(for: pin))
                        }
                    }
                }
            }
            .ignoresSafeArea()

            VStack {
                SearchBar(text: $viewModel.searchText)
                    .padding(.horizontal)
                    .padding(.top, 12)

                FilterBar(activeFilters: $viewModel.activeFilters)
                    .padding(.horizontal)
                    .padding(.bottom)

                Spacer()
            }
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showingAddPinSheet = true
                } label: {
                    Label("Add Pin", systemImage: "plus")
                }
            }
        }
        .sheet(isPresented: $showingAddPinSheet) {
            NavigationStack {
                PinEditorView(pin: LandPin(
                    title: "New Plot",
                    coordinate: viewModel.region.center
                )) { newPin in
                    viewModel.addPin(newPin)
                }
            }
        }
        .sheet(item: $editingPin) { pin in
            NavigationStack {
                PinEditorView(pin: pin) { updatedPin in
                    viewModel.updatePin(updatedPin)
                }
            }
        }
        .sheet(isPresented: $showingAnalysis) {
            if let pin = viewModel.selectedPin {
                NavigationStack {
                    ROIAnalyzerView(pin: pin, analysis: viewModel.analysis(for: pin)) { updated in
                        viewModel.saveAnalysis(updated)
                    } deleteAction: {
                        viewModel.deletePin(pin)
                    } editAction: {
                        editingPin = pin
                    }
                }
            }
        }
    }

    private func color(for pin: LandPin) -> Color {
        switch pin.reliability {
        case 4...5: return .green
        case 2...3: return .orange
        default: return .red
        }
    }
}

struct SearchBar: View {
    @Binding var text: String

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
            TextField("Search area, zone, broker…", text: $text)
                .textFieldStyle(.plain)
                .autocorrectionDisabled()
            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(10)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10))
    }
}

struct FilterBar: View {
    @Binding var activeFilters: Set<LandType>

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(LandType.allCases) { type in
                    FilterChip(
                        title: type.rawValue,
                        isActive: activeFilters.contains(type)
                    ) {
                        if activeFilters.contains(type) {
                            activeFilters.remove(type)
                        } else {
                            activeFilters.insert(type)
                        }
                    }
                }
            }
            .padding(.vertical, 8)
        }
        .background(.thinMaterial, in: Capsule())
    }
}

struct FilterChip: View {
    let title: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption.bold())
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isActive ? Color.blue.opacity(0.2) : .clear)
                .clipShape(Capsule())
        }
        .buttonStyle(.borderedProminent)
        .tint(isActive ? .blue : .gray.opacity(0.4))
    }
}

struct PinEditorView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var pin: LandPin
    @State private var broker: Broker
    let onSave: (LandPin) -> Void

    init(pin: LandPin, onSave: @escaping (LandPin) -> Void) {
        _pin = State(initialValue: pin)
        _broker = State(initialValue: pin.broker ?? Broker())
        self.onSave = onSave
    }

    var body: some View {
        Form {
            Section("Basics") {
                TextField("Title", text: $pin.title)
                TextField("Address", text: $pin.address)
                Picker("Land Type", selection: $pin.landType) {
                    ForEach(LandType.allCases) { type in
                        Text(type.rawValue).tag(type)
                    }
                }
                TextField("Zone", text: $pin.zone)
            }

            Section("Pricing") {
                TextField("Price", value: $pin.price, format: .number)
                    .keyboardType(.decimalPad)
                Picker("Unit", selection: $pin.priceUnit) {
                    ForEach(PriceUnit.allCases) { unit in
                        Text(unit.description).tag(unit)
                    }
                }
            }

            Section("Broker") {
                TextField("Name", text: $broker.name)
                TextField("Phone", text: $broker.phone)
                    .keyboardType(.phonePad)
                TextField("WhatsApp", text: $broker.whatsapp)
                    .keyboardType(.phonePad)
                ReliabilityStepper(value: $broker.reliability)
                TextField("Broker Notes", text: $broker.notes, axis: .vertical)
                ReliabilityStepper(value: $pin.reliability)
                TextField("Site Notes", text: $pin.notes, axis: .vertical)
            }

            Section("Coordinates") {
                Text(String(format: "Lat: %.4f", pin.coordinate.latitude))
                Text(String(format: "Lng: %.4f", pin.coordinate.longitude))
            }
        }
        .navigationTitle("Pin Details")
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("Cancel", role: .cancel) { dismiss() }
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button("Save") {
                    pin.broker = broker
                    onSave(pin)
                    dismiss()
                }
                .disabled(pin.title.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
    }
}

struct ReliabilityStepper: View {
    @Binding var value: Int

    var body: some View {
        Stepper(value: $value, in: 1...5) {
            HStack {
                Text("Reliability")
                Spacer()
                Label("\(value)", systemImage: "star.fill")
                    .foregroundStyle(Color.yellow)
            }
        }
    }
}

struct ROIAnalyzerView: View {
    @Environment(\.dismiss) private var dismiss
    let pin: LandPin
    @State private var analysis: ROIAnalysis
    let onSave: (ROIAnalysis) -> Void
    let deleteAction: () -> Void
    let editAction: () -> Void

    init(pin: LandPin, analysis: ROIAnalysis, onSave: @escaping (ROIAnalysis) -> Void, deleteAction: @escaping () -> Void, editAction: @escaping () -> Void) {
        self.pin = pin
        _analysis = State(initialValue: analysis)
        self.onSave = onSave
        self.deleteAction = deleteAction
        self.editAction = editAction
    }

    var body: some View {
        Form {
            Section("Plot & Build") {
                TextField("Plot Size (sqft)", value: $analysis.plotSizeSqft, format: .number)
                    .keyboardType(.decimalPad)
                TextField("FSI", value: $analysis.fsi, format: .number)
                    .keyboardType(.decimalPad)
                Text("Buildable Area: \(analysis.buildableSqft, format: .number) sqft")
            }

            Section("Costs") {
                TextField("Construction Cost / sqft", value: $analysis.constructionCostPerSqft, format: .number)
                    .keyboardType(.decimalPad)
                TextField("Other Costs", value: $analysis.otherCosts, format: .number)
                    .keyboardType(.decimalPad)
                TextField("Gov Taxes (%)", value: $analysis.govTaxesPct, format: .number)
                    .keyboardType(.decimalPad)
                Text("Construction Cost: ₹\(analysis.constructionCost, format: .number)")
                Text("Land Cost: ₹\(analysis.landCost(for: pin), format: .number)")
            }

            Section("Revenue") {
                TextField("Selling Price / sqft", value: $analysis.avgSellPricePerSqft, format: .number)
                    .keyboardType(.decimalPad)
                Text("Gross Revenue: ₹\(analysis.grossRevenue(), format: .number)")
            }

            Section("ROI Summary") {
                let totalCost = analysis.totalCost(for: pin)
                let profit = analysis.profit(for: pin)
                let roi = analysis.roiPercentage(for: pin)
                Text("Total Cost: ₹\(totalCost, format: .number)")
                Text("Profit: ₹\(profit, format: .number)")
                Text("ROI: \(roi, format: .number) %")

                let sensitivity = analysis.sensitivity(for: pin)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Sensitivity (±10%)")
                        .font(.headline)
                    Label(String(format: "Sell Price +10%% → %.1f%%", sensitivity.sellPriceUp10), systemImage: "arrow.up")
                    Label(String(format: "Sell Price -10%% → %.1f%%", sensitivity.sellPriceDown10), systemImage: "arrow.down")
                    Label(String(format: "Cost +10%% → %.1f%%", sensitivity.costUp10), systemImage: "arrow.up")
                    Label(String(format: "Cost -10%% → %.1f%%", sensitivity.costDown10), systemImage: "arrow.down")
                }
            }

            Section("Actions") {
                Button("Export Report") {
                    exportReport()
                }
                Button("Edit Pin") {
                    dismiss()
                    editAction()
                }
                Button("Delete Pin", role: .destructive) {
                    deleteAction()
                    dismiss()
                }
            }
        }
        .navigationTitle(pin.title)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("Close") { dismiss() }
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button("Save") {
                    onSave(analysis)
                    dismiss()
                }
            }
        }
    }

    private func exportReport() {
        // Placeholder for PDF/CSV export integration.
        print("Exporting report for pin: \(pin.title)")
    }
}

// MARK: - SwiftUI Preview

struct MapHomeView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationStack {
            MapHomeView()
                .environmentObject(LandScoutViewModel())
        }
    }
}
