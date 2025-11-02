DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS search;
DROP TABLE IF EXISTS viewedProduct;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS orderlines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS users;

CREATE TABLE users(
    uid TEXT PRIMARY KEY,
    pwd TEXT NOT NULL,
    role TEXT CHECK(role IN ('customer', 'sales'))
);
CREATE TABLE customers(
    cid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    FOREIGN KEY (cid) REFERENCES users(uid)
);

CREATE TABLE products(
    pid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL CHECK(price >= 0),
    stock_count INTEGER NOT NULL CHECK(stock_count >= 0),
    descr TEXT
);

CREATE TABLE orders(
    ono INTEGER PRIMARY KEY,
    cid TEXT NOT NULL,
    sessionNo INTEGER NOT NULL,
    odate DATE NOT NULL,
    shipping_address TEXT NOT NULL,
    FOREIGN KEY (cid) REFERENCES customers(cid)
);
CREATE TABLE orderlines(
    ono INTEGER,
    lineNo INTEGER,
    pid TEXT NOT NULL,
    qty INTEGER NOT NULL CHECK(qty > 0),
    uprice REAL NOT NULL CHECK(uprice >= 0),
    PRIMARY KEY (ono, lineNo),
    FOREIGN KEY (ono) REFERENCES orders(ono),
    FOREIGN KEY (pid) REFERENCES products(pid)
);

CREATE TABLE sessions(
    cid TEXT,
    sessionNo INTEGER,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    PRIMARY KEY (cid, sessionNo),
    FOREIGN KEY (cid) REFERENCES customers(cid)
);

CREATE TABLE viewedProduct(
    cid TEXT,
    sessionNo INTEGER,
    ts DATETIME,
    pid TEXT,
    PRIMARY KEY (cid, sessionNo, ts, pid),
    FOREIGN KEY (cid, sessionNo) REFERENCES sessions(cid, sessionNo),
    FOREIGN KEY (pid) REFERENCES products(pid)
);
CREATE TABLE search(
    cid TEXT,
    sessionNo INTEGER,
    ts DATETIME,
    query TEXT,
    PRIMARY KEY (cid, sessionNo, ts),
    FOREIGN KEY (cid, sessionNo) REFERENCES sessions(cid, sessionNo)
);
CREATE TABLE cart(
    cid TEXT,
    sessionNo INTEGER,
    pid TEXT,
    qty INTEGER NOT NULL CHECK(qty > 0),
    PRIMARY KEY (cid, sessionNo, pid),
    FOREIGN KEY (cid, sessionNo) REFERENCES sessions(cid, sessionNo),
    FOREIGN KEY (pid) REFERENCES products(pid)
);
