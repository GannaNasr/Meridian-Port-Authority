INSERT INTO vessels (vessel_name, imo_number, arrival_date, departure_date, status)
VALUES
('Ever Glory', 'IMO1234567', '2026-07-20', NULL, 'Arrived'),
('Ocean Star', 'IMO2345678', '2026-07-18', '2026-07-22', 'Departed');

INSERT INTO consignees (consignee_name, company_name, contact_phone, email, address)
VALUES
('Ahmed Ali', 'ABC Imports', '01011111111', 'ahmed@abc.com', 'Alexandria'),
('Sara Hassan', 'Global Trade', '01022222222', 'sara@global.com', 'Cairo');

INSERT INTO trucking_companies (company_name, license_number, status, contact_phone)
VALUES
('Fast Logistics', 'LIC001', 'Active', '01033333333'),
('Safe Transport', 'LIC002', 'Suspended', '01044444444');

INSERT INTO containers
(container_number, vessel_id, consignee_id, carrier_id, container_type, hazmat, status, arrival_date)
VALUES
('MSKU100001', 1, 1, 1, '40FT', 0, 'In Yard', '2026-07-20'),

('MSKU100002', 1, 2, 1, '20FT', 1, 'In Yard', '2026-07-20'),

('MSKU100003', 1, 1, 1, '40FT', 0, 'On Hold', '2026-07-20'),

('MSKU100004', 1, 2, 2, '20FT', 1, 'On Hold', '2026-07-20');

INSERT INTO customs_holds
(container_id, hold_reason, hold_status, officer_name)
VALUES
(3, 'Missing customs documents', 'Active', 'Officer Omar'),

(4, 'Hazardous materials inspection', 'Active', 'Officer Ali');

INSERT INTO release_orders
(container_id, requested_by, approved_by, release_status, release_reason)
VALUES
(1, 'Dispatcher', 'Supervisor', 'Approved', 'Documents verified'),

(3, 'Dispatcher', NULL, 'Pending', 'Waiting customs approval');

INSERT INTO gate_transactions
(container_id, carrier_id, transaction_type, processed_by)
VALUES
(1, 1, 'OUT', 'Gate Officer'),

(2, 1, 'IN', 'Gate Officer');

INSERT INTO vessel_manifest_items
(vessel_id, container_id, manifest_status, notes)
VALUES
(1, 1, 'Loaded', 'Normal cargo'),

(1, 2, 'Loaded', 'Hazardous cargo'),

(1, 3, 'Loaded', 'Under customs inspection'),

(1, 4, 'Loaded', 'Hazmat + Customs Hold');
