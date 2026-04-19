-- ============================================================
-- Silver Screen Palace - Seed Data
-- ============================================================
USE silver_screen;

-- Movies
INSERT INTO MOVIE (MOVIE_TITLE, MOVIE_RATING, MOVIE_RUNTIME) VALUES
('Dune: Part Two',           'PG-13', 166),
('Inside Out 2',             'PG',    96),
('Deadpool & Wolverine',     'R',     127),
('The Wild Robot',           'PG',    102),
('Oppenheimer',              'R',     180);

-- Theaters (rooms)
INSERT INTO THEATER (THEATER_CAPACITY, THEATER_OPHOURS) VALUES
(80,  '10:00-23:00'),
(120, '10:00-23:00'),
(50,  '12:00-22:00');

-- Employees (supertype) + subtypes
INSERT INTO EMPLOYEE (EMPLOYEE_NAME, EMPLOYEE_HIRE_DATE) VALUES
('Jonathan Khami',   '2023-01-15 09:00:00'),  -- 1 manager
('Sameer Alshamiri', '2023-05-20 09:00:00'),  -- 2 cashier
('Connor Wellington','2024-02-10 09:00:00'),  -- 3 cashier
('Areeb Akhtar',     '2024-08-01 09:00:00');  -- 4 usher

INSERT INTO MANAGER (EMPLOYEE_ID, MANAGER_LEVEL) VALUES (1, 'SENIOR');
INSERT INTO CASHIER (EMPLOYEE_ID, CASHIER_REGISTER) VALUES (2, 'REG-01'), (3, 'REG-02');
INSERT INTO USHER   (EMPLOYEE_ID, USHER_ISSUED_FLASHLIGHT) VALUES (4, 'FL-A7');

-- Screenings
INSERT INTO SCREENING (SCREENING_DATE, SCREENING_START_TIME, MOVIE_ID, THEATER_ID) VALUES
('2026-04-20', '18:00:00', 1, 2),
('2026-04-20', '20:30:00', 2, 1),
('2026-04-20', '21:00:00', 3, 3),
('2026-04-21', '19:00:00', 4, 1),
('2026-04-21', '21:30:00', 5, 2);

-- A few sample tickets
INSERT INTO TICKET (TICKET_TYPE, TICKET_SALEPRICE, TICKET_STATUS, SCREENING_ID, EMPLOYEE_ID) VALUES
('ADULT',  14.50, 'ACTIVE', 1, 2),
('CHILD',   9.00, 'ACTIVE', 1, 2),
('SENIOR', 11.00, 'ACTIVE', 2, 3);
