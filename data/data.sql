-- Insert sample data into Users
INSERT INTO Users (id, address_id, enrolled_clinic_id, nric, first_name, last_name, email, date_of_birth, gender, password)
VALUES
-- User for getting no vaccine recommendations (Female, 17 years old)
('d2e8d855-1c1a-4fe6-a8b8-ac823250a414', '0968e1e9-f766-4268-bd05-52a2795e8e99', NULL, 'S1111111J', 'Jane', 'Doe', 'jane.doe@example.com', '2008-01-01', 'F', '$2b$12$//InOGG5Oo6zeAVdyAth3.b7dwZSVAp8ovAXrdkY/GAccLe8B/hDq'),
-- User for getting vaccination records (Female, 20 years old)
('8045a3aa-e221-4d9c-89c5-822ab96d4885', '9d02493b-e55b-44fb-b4f5-2f530ffcef06', '225d024f-3d0e-427d-aef9-1fe9a2fc4e13', 'S1234567A', 'Test', 'User', 'test.user@example.com', '2005-01-01', 'F', '$2b$12$I4QqYcmEDKCFi0V3FodWWuFIi4IUKINf/DqvSmXlAdU/lEFjxZSRq'),
-- User for scheduling vaccination (Male, 25 years old)
('564b4728-9436-4e1a-8da1-c40dde49a0cc', 'fe68a41d-6ee2-449b-9b5a-68103a7f676f', NULL, 'T8815246X', 'Test_2', 'For_scheduling', 'test_2@example.com', '2000-04-02', 'M', '$2b$12$blZnIuQU1VYiVceIpxYRauEAZ20t3jE68tn45ezMSNzy0rxXrZIQe');


-- Insert sample data into Clinics
INSERT INTO Clinics (id, address_id, name, type)
VALUES
('225d024f-3d0e-427d-aef9-1fe9a2fc4e13', '9d02493b-e55b-44fb-b4f5-2f530ffcef06', 'Ang Mo Kio Polyclinic', 'polyclinic'),
('bd760847-db7e-439f-add8-3610167478ca', '7cb8712c-7824-49ef-88ce-b418a71e78f9', 'Yishun Polyclinic', 'polyclinic'),
('492f66d8-fd4b-4d61-a343-1c85898337f1', '0968e1e9-f766-4268-bd05-52a2795e8e99', 'Bartley Clinic', 'gp'),
('1be076b3-6452-4f2d-9f2d-cfa7544dc073', '51650b4e-48fb-4665-80f4-c27b8c7de411', 'Raffles Medical (Compass One)', 'gp');

-- Insert sample data into Addresses
INSERT INTO Addresses (id, postal_code, address, latitude, longitude)
VALUES
('9d02493b-e55b-44fb-b4f5-2f530ffcef06', '569666', '21 ANG MO KIO CENTRAL 2 ANG MO KIO POLYCLINIC SINGAPORE 569666', 1.3743245905856, 103.845677779279),
('7cb8712c-7824-49ef-88ce-b418a71e78f9', '768898', '2 YISHUN AVENUE 9 NATIONAL HEALTHCARE GROUP POLYCLINICS (YISHUN POLYCLINIC) SINGAPORE 768898', 1.43035851992416, 103.839190698939),
('0968e1e9-f766-4268-bd05-52a2795e8e99', '534869', '187 UPPER PAYA LEBAR ROAD SINGAPORE 534869', 1.34010826990085, 103.885032592997),
('51650b4e-48fb-4665-80f4-c27b8c7de411', '545078', '1 SENGKANG SQUARE COMPASS ONE SINGAPORE 545078', 1.39205314156706, 103.89507054384),
-- User Address for booking tests
('fe68a41d-6ee2-449b-9b5a-68103a7f676f', '618490', '123 CORPORATION WALK LAKESIDE GROVE SINGAPORE 618490', 1.339401, 103.718451);

-- Insert sample data into Vaccines
INSERT INTO Vaccines (id, name)
VALUES
('9004aab3-8993-4d37-81c3-78844191e5ec', 'Influenza (INF)'),
('a67ed08a-95f0-47d4-a97b-8153f1d7874a', 'Human papillomavirus (HPV2 or HPV4)'),
('599b1189-0687-4a38-8de5-95850cfa9ee7', 'Pneumococcal Conjugate (PCV13)');

INSERT INTO VaccineCriteria (id, vaccine_id, age_criteria, gender_criteria, health_condition_criteria, doses_required, frequency)
VALUES
-- Influenza (INF)
('d0dde26e-89bd-4366-878b-5e57117bab0e', '9004aab3-8993-4d37-81c3-78844191e5ec', '18-64 years', 'None', 'Specific medical conditions or indications', 1, 'Annually or per season'),
('617c7996-546a-4b6c-b5bb-3e2cdd3bf0a1', 'b79e4769-a79f-4142-96fc-da07d538cf9e', '65+ years', 'None', 'None', 1, 'Annually or per season'),
-- Human papillomavirus (HPV2 or HPV4)
('5696ee5b-761e-45bb-9df8-7bc440bf261e', 'a67ed08a-95f0-47d4-a97b-8153f1d7874a', '12-13 years', 'F', 'None', 1, 'Once'),
('bdbe6d75-5e9e-4dab-ac57-296d9a57613a', 'a67ed08a-95f0-47d4-a97b-8153f1d7874a', '13-14 years', 'F', 'None', 1, 'Once'),
('0e759716-b221-4ebd-abe2-4e4e7bd665c7', 'a67ed08a-95f0-47d4-a97b-8153f1d7874a', '18-26 years', 'F', 'Unvaccinated adults or uncertain history', 3, 'Once'),
-- Pneumococcal Conjugate (PCV13)
('255b7260-c7da-4f15-b772-64ec13dcf6a9', '599b1189-0687-4a38-8de5-95850cfa9ee7', '4 months', 'None', 'None', 1, 'Once'),
('cda2e4b1-27ae-4bb2-9ee1-da75cd4683d4', '599b1189-0687-4a38-8de5-95850cfa9ee7', '6 months', 'None', 'None', 1, 'Once'),
('d448048c-1d0e-4d3f-abd4-95919562d8bb', '599b1189-0687-4a38-8de5-95850cfa9ee7', '12 months', 'None', 'None', 1, 'Once');

-- Insert sample data into BookingSlots
INSERT INTO BookingSlots (id, polyclinic_id, vaccine_id, datetime)
VALUES
-- booked slot (see VaccineRecords):
('97ba51db-48d8-4873-b1ee-57a9b7f766f0', '225d024f-3d0e-427d-aef9-1fe9a2fc4e13', '9004aab3-8993-4d37-81c3-78844191e5ec', '2025-04-01 09:00:00'),
('3f7f75c0-b28c-4bb7-8c9a-991e5d150bc3', '225d024f-3d0e-427d-aef9-1fe9a2fc4e13', '599b1189-0687-4a38-8de5-95850cfa9ee7', '2025-04-01 10:00:00'),
-- completed slot (see VaccineRecords):
('21b89cd2-f99c-4113-bb46-5cc21d566b97', '225d024f-3d0e-427d-aef9-1fe9a2fc4e13', 'a67ed08a-95f0-47d4-a97b-8153f1d7874a', '2025-04-01 10:00:00'),
-- available slots, to be booked by a user during test:
('213fa5e7-abbb-4e55-bccc-318db42ace81', 'bd760847-db7e-439f-add8-3610167478ca', '599b1189-0687-4a38-8de5-95850cfa9ee7', '2025-04-02 14:00:00'),
('e7bbc307-ae75-4854-bd91-d6851ae085fd', 'bd760847-db7e-439f-add8-3610167478ca', '9004aab3-8993-4d37-81c3-78844191e5ec', '2025-04-03 11:00:00'),
-- available slots to test location
('5379aea8-3acd-4274-9cbc-acb3c4973b6c', '492f66d8-fd4b-4d61-a343-1c85898337f1', '9004aab3-8993-4d37-81c3-78844191e5ec', '2025-04-03 10:00:00');
-- Insert sample data into VaccinationRecords
INSERT INTO VaccineRecords (id, user_id, booking_slot_id, status)
VALUES
-- vaccine record to test for record
('b6732344-bc30-4401-9a69-b91e28273b8d', '8045a3aa-e221-4d9c-89c5-822ab96d4885', '97ba51db-48d8-4873-b1ee-57a9b7f766f0', 'booked'),
('7eb3a1a2-dd8c-4cd7-84d5-cd5621ab4fc1', '8045a3aa-e221-4d9c-89c5-822ab96d4885', '21b89cd2-f99c-4113-bb46-5cc21d566b97', 'completed'),
-- vaccine record to test for reschedule
('a6578d08-4e81-40ca-bc30-c9f2d01024aa', '564b4728-9436-4e1a-8da1-c40dde49a0cc', '3f7f75c0-b28c-4bb7-8c9a-991e5d150bc3', 'booked');
