-- Meridian Port Authority Database Schema
-- SQLite Database

CREATE TABLE vessels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vessel_name TEXT NOT NULL,
    imo_number TEXT UNIQUE NOT NULL,
    arrival_date DATE,
    departure_date DATE,
   status TEXT CHECK(status IN ('Arrived', 'Berthed', 'Departed'))
);

CREATE TABLE consignees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consignee_name TEXT NOT NULL,
    company_name TEXT,
    contact_phone TEXT,
    email TEXT UNIQUE,
    address TEXT
);

CREATE TABLE trucking_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    license_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Active', 'Suspended')),
    contact_phone TEXT
);

CREATE TABLE containers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_number TEXT UNIQUE NOT NULL,
    vessel_id INTEGER NOT NULL,
    consignee_id INTEGER NOT NULL,
    carrier_id INTEGER NOT NULL,
    container_type TEXT,
    hazmat BOOLEAN NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('In Yard', 'Released', 'On Hold')),
    arrival_date DATE,

    FOREIGN KEY (vessel_id) REFERENCES vessels(id),
    FOREIGN KEY (consignee_id) REFERENCES consignees(id),
    FOREIGN KEY (carrier_id) REFERENCES trucking_companies(id)
);

CREATE TABLE customs_holds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_id INTEGER NOT NULL,
    hold_reason TEXT NOT NULL,
    hold_status TEXT NOT NULL CHECK(hold_status IN ('Active', 'Released')),
    officer_name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    released_at DATETIME,

    FOREIGN KEY (container_id) REFERENCES containers(id)
);

CREATE TABLE release_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_id INTEGER NOT NULL,
    requested_by TEXT NOT NULL,
    approved_by TEXT,
    release_status TEXT NOT NULL CHECK(release_status IN ('Pending','Approved','Rejected')),
    release_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    released_at DATETIME,

    FOREIGN KEY (container_id) REFERENCES containers(id)
);

CREATE TABLE gate_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    container_id INTEGER NOT NULL,
    carrier_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('IN','OUT')),
    transaction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_by TEXT NOT NULL,

    FOREIGN KEY (container_id) REFERENCES containers(id),
    FOREIGN KEY (carrier_id) REFERENCES trucking_companies(id)
);

CREATE TABLE vessel_manifest_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vessel_id INTEGER NOT NULL,
    container_id INTEGER NOT NULL,
    manifest_status TEXT NOT NULL CHECK(manifest_status IN ('Loaded','Discharged')),
    notes TEXT,

    FOREIGN KEY (vessel_id) REFERENCES vessels(id),
    FOREIGN KEY (container_id) REFERENCES containers(id)
);
