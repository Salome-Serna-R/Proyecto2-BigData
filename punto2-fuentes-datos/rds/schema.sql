CREATE DATABASE IF NOT EXISTS medellin_places;
USE medellin_places;

CREATE TABLE places (
    place_id     VARCHAR(100) PRIMARY KEY,
    name         VARCHAR(255),
    address      TEXT,
    neighborhood VARCHAR(100),
    lat          DECIMAL(10,7),
    lng          DECIMAL(10,7),
    rating       DECIMAL(2,1),
    price_level  TINYINT,
    review_count INT
);

CREATE TABLE place_hours (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    place_id    VARCHAR(100),
    day_es      VARCHAR(20),
    day_en      VARCHAR(20),
    is_open     BOOLEAN,
    open_time   VARCHAR(10),
    close_time  VARCHAR(10),
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);

CREATE TABLE place_types (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    place_id  VARCHAR(100),
    type      VARCHAR(100),
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);