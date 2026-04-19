-- ============================================================
-- Silver Screen Palace - Database Schema
-- CSI 3450 Database Design Project
-- ============================================================
-- Run this in MySQL to create the database and all tables.
-- Matches the EERD in the project doc.
-- ============================================================

DROP DATABASE IF EXISTS silver_screen;
CREATE DATABASE silver_screen;
USE silver_screen;

-- ---------------------------
-- MOVIE
-- ---------------------------
CREATE TABLE MOVIE (
    MOVIE_ID       INT AUTO_INCREMENT PRIMARY KEY,
    MOVIE_TITLE    VARCHAR(100) NOT NULL,
    MOVIE_RATING   VARCHAR(5)   NOT NULL,   -- 'G','PG','PG-13','R'
    MOVIE_RUNTIME  INT          NOT NULL    -- minutes
);

-- ---------------------------
-- THEATER (screening room)
-- ---------------------------
CREATE TABLE THEATER (
    THEATER_ID        INT AUTO_INCREMENT PRIMARY KEY,
    THEATER_CAPACITY  INT          NOT NULL,
    THEATER_OPHOURS   VARCHAR(45)  NOT NULL   -- e.g. '10:00-23:00'
);

-- ---------------------------
-- EMPLOYEE (supertype)
-- ---------------------------
CREATE TABLE EMPLOYEE (
    EMPLOYEE_ID        INT AUTO_INCREMENT PRIMARY KEY,
    EMPLOYEE_NAME      VARCHAR(45) NOT NULL,
    EMPLOYEE_HIRE_DATE DATETIME    NOT NULL
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

CREATE TABLE USHER (
    EMPLOYEE_ID              INT PRIMARY KEY,
    USHER_ISSUED_FLASHLIGHT  VARCHAR(45) NOT NULL,
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
    TICKET_TYPE        VARCHAR(45)   NOT NULL,  -- 'ADULT','CHILD','SENIOR'
    TICKET_SALEPRICE   DECIMAL(6,2)  NOT NULL,
    TICKET_STATUS      VARCHAR(45)   NOT NULL DEFAULT 'ACTIVE',  -- 'ACTIVE','CANCELLED'
    SCREENING_ID       INT NOT NULL,
    EMPLOYEE_ID        INT NOT NULL,
    FOREIGN KEY (SCREENING_ID) REFERENCES SCREENING(SCREENING_ID),
    FOREIGN KEY (EMPLOYEE_ID)  REFERENCES EMPLOYEE(EMPLOYEE_ID)
);
