-- ============================================================
-- Silver Screen Palace - Database Schema + Seed Data
-- CSI 3450 Database Design Project
-- ============================================================

DROP DATABASE IF EXISTS silver_screen;
CREATE DATABASE silver_screen;
USE silver_screen;

-- ---------------------------
-- MOVIE
-- ---------------------------
CREATE TABLE MOVIE (
    MOVIE_ID           INT AUTO_INCREMENT PRIMARY KEY,
    MOVIE_ACTIVE       BOOLEAN NOT NULL DEFAULT 1,
    MOVIE_TITLE        VARCHAR(100) NOT NULL,
    MOVIE_RATING       VARCHAR(5)   NOT NULL,
    MOVIE_RUNTIME      INT          NOT NULL,
    MOVIE_POSTER       VARCHAR(500) NULL,
    MOVIE_DESCRIPTION  TEXT         NULL
);

-- ---------------------------
-- THEATER
-- ---------------------------
CREATE TABLE THEATER (
    THEATER_ID        INT AUTO_INCREMENT PRIMARY KEY,
    THEATER_CAPACITY  INT          NOT NULL,
    THEATER_OPHOURS   VARCHAR(45)  NOT NULL
);

-- ---------------------------
-- EMPLOYEE (supertype with role discriminator)
-- ---------------------------
CREATE TABLE EMPLOYEE (
    EMPLOYEE_ID        INT AUTO_INCREMENT PRIMARY KEY,
    EMPLOYEE_NAME      VARCHAR(45) NOT NULL,
    EMPLOYEE_HIRE_DATE DATETIME    NOT NULL,
    EMPLOYEE_ROLE      VARCHAR(10) NOT NULL  -- 'MANAGER','CASHIER'
);

-- ---------------------------
-- Employee subtypes
-- ---------------------------
CREATE TABLE MANAGER (
    EMPLOYEE_ID    INT PRIMARY KEY,
    MANAGER_LEVEL  VARCHAR(45) NOT NULL,
    FOREIGN KEY (EMPLOYEE_ID) REFERENCES EMPLOYEE(EMPLOYEE_ID)
);

CREATE TABLE CASHIER (
    EMPLOYEE_ID        INT PRIMARY KEY,
    CASHIER_REGISTER   VARCHAR(45) NOT NULL,
    FOREIGN KEY (EMPLOYEE_ID) REFERENCES EMPLOYEE(EMPLOYEE_ID)
);

-- ---------------------------
-- SCREENING
-- ---------------------------
CREATE TABLE SCREENING (
    SCREENING_ID          INT AUTO_INCREMENT PRIMARY KEY,
    SCREENING_DATE        DATE NOT NULL,
    SCREENING_START_TIME  TIME NOT NULL,
    MOVIE_ID              INT  NOT NULL,
    THEATER_ID            INT  NOT NULL,
    FOREIGN KEY (MOVIE_ID)   REFERENCES MOVIE(MOVIE_ID),
    FOREIGN KEY (THEATER_ID) REFERENCES THEATER(THEATER_ID)
);

-- ---------------------------
-- TICKET
-- ---------------------------
CREATE TABLE TICKET (
    TICKET_ID          INT AUTO_INCREMENT PRIMARY KEY,
    TICKET_TYPE        VARCHAR(45)   NOT NULL,
    TICKET_SALEPRICE   DECIMAL(6,2)  NOT NULL,
    TICKET_STATUS      VARCHAR(45)   NOT NULL DEFAULT 'ACTIVE',
    SCREENING_ID       INT NOT NULL,
    EMPLOYEE_ID        INT NOT NULL,
    FOREIGN KEY (SCREENING_ID) REFERENCES SCREENING(SCREENING_ID),
    FOREIGN KEY (EMPLOYEE_ID)  REFERENCES EMPLOYEE(EMPLOYEE_ID)
);

-- ============================================================
-- Seed Data
-- ============================================================

-- Movies (posters/descriptions auto-fetched via TMDB on first add)
INSERT INTO MOVIE (MOVIE_TITLE, MOVIE_RATING, MOVIE_RUNTIME) VALUES
('Dune: Part Two',           'PG-13', 166),
('Inside Out 2',             'PG',    96),
('Deadpool & Wolverine',     'R',     127),
('The Wild Robot',           'PG',    102),
('Oppenheimer',              'R',     180);

-- Theaters
INSERT INTO THEATER (THEATER_CAPACITY, THEATER_OPHOURS) VALUES
(80,  '10:00-23:00'),
(120, '10:00-23:00'),
(50,  '12:00-22:00');

-- Employees with role discriminator (4 total: 2 managers, 2 cashiers)
INSERT INTO EMPLOYEE (EMPLOYEE_NAME, EMPLOYEE_HIRE_DATE, EMPLOYEE_ROLE) VALUES
('Jonathan Khami',    '2023-01-15 09:00:00', 'MANAGER'),
('Sameer Alshamiri',  '2023-05-20 09:00:00', 'CASHIER'),
('Connor Wellington', '2024-02-10 09:00:00', 'CASHIER'),
('Areeb Akhtar',      '2024-08-01 09:00:00', 'MANAGER');

INSERT INTO MANAGER (EMPLOYEE_ID, MANAGER_LEVEL) VALUES
(1, 'SENIOR'),
(4, 'JUNIOR');

INSERT INTO CASHIER (EMPLOYEE_ID, CASHIER_REGISTER) VALUES
(2, 'REG-01'),
(3, 'REG-02');

-- Screenings
INSERT INTO SCREENING (SCREENING_DATE, SCREENING_START_TIME, MOVIE_ID, THEATER_ID) VALUES
('2026-04-20', '18:00:00', 1, 2),
('2026-04-20', '20:30:00', 2, 1),
('2026-04-20', '21:00:00', 3, 3),
('2026-04-21', '19:00:00', 4, 1),
('2026-04-21', '21:30:00', 5, 2);

-- Sample tickets
INSERT INTO TICKET (TICKET_TYPE, TICKET_SALEPRICE, TICKET_STATUS, SCREENING_ID, EMPLOYEE_ID) VALUES
('ADULT',  14.50, 'ACTIVE', 1, 2),
('CHILD',   9.00, 'ACTIVE', 1, 2),
('SENIOR', 11.00, 'ACTIVE', 2, 3);