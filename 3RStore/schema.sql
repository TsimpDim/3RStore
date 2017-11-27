CREATE TABLE Users(
    email TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)

CREATE TABLE Links(
    url TEXT PRIMARY KEY,
    name TEXT
)

CREATE TABLE Stores(
    link_url TEXT,
    user_email TEXT,
    PRIMARY KEY (link_url, user_email),
    FOREIGN KEY (link_url) REFERENCES Links (url),
    FOREIGN KEY (user_email) REFERENCES Users (email)
);