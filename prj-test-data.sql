-- test users
INSERT INTO users VALUES 
    ('1', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'customer'),
    ('2', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'customer'),
    ('3', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'customer'),
    ('100', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'sales');

--test customers
INSERT INTO customers VALUES 
    ('1', 'John Doe', 'john@example.com'),
    ('2', 'Jane Smith', 'jane@example.com'),
    ('3', 'Bob Johnson', 'bob@example.com');

-- Insert test products
INSERT INTO products VALUES 
    ('P001', 'Laptop Dell XPS 13', 'Electronics', 999.99, 10, 'High-performance ultrabook with 13-inch display'),
    ('P002', 'Laptop MacBook Pro', 'Electronics', 1499.99, 5, 'Apple laptop with M2 chip and retina display'),
    ('P003', 'Wireless Mouse Logitech', 'Accessories', 29.99, 50, 'Ergonomic wireless mouse with precision tracking'),
    ('P004', 'Keyboard Mechanical RGB', 'Accessories', 89.99, 25, 'Gaming keyboard with RGB lighting and mechanical switches'),
    ('P005', 'Monitor 27 inch 4K', 'Electronics', 399.99, 15, 'Ultra HD 4K monitor with IPS panel'),
    ('P006', 'USB-C Hub Adapter', 'Accessories', 39.99, 100, 'Multi-port USB-C hub with HDMI and USB 3.0'),
    ('P007', 'Laptop Bag Premium', 'Accessories', 49.99, 30, 'Premium padded laptop bag with multiple compartments'),
    ('P008', 'Wireless Headphones', 'Electronics', 149.99, 20, 'Noise-canceling wireless headphones with 30-hour battery'),
    ('P009', 'Webcam HD 1080p', 'Electronics', 79.99, 40, 'Full HD webcam with auto-focus and built-in microphone'),
    ('P010', 'External SSD 1TB', 'Electronics', 129.99, 35, 'Portable SSD with USB 3.1 and fast read speeds');
--past orders
--from the last 7 days
INSERT INTO orders VALUES 
    (1, '1', 1, date('now', '-2 days'), '123 Main St, Edmonton, AB'),
    (2, '2', 1, date('now', '-3 days'), '456 Oak Ave, Calgary, AB'),
    (3, '1', 2, date('now', '-5 days'), '123 Main St, Edmonton, AB'),
    (4, '3', 1, date('now', '-1 days'), '789 Pine Rd, Vancouver, BC');
-- Order lines
INSERT INTO orderlines VALUES 
    (1, 1, 'P001', 1, 999.99),
    (1, 2, 'P003', 2, 29.99),
    (2, 1, 'P002', 1, 1499.99),
    (2, 2, 'P004', 1, 89.99),
    (3, 1, 'P005', 1, 399.99),
    (3, 2, 'P006', 3, 39.99),
    (4, 1, 'P001', 1, 999.99),
    (4, 2, 'P008', 1, 149.99);
--some sessions
INSERT INTO sessions VALUES 
    ('1', 1, datetime('now', '-2 days', '-2 hours'), datetime('now', '-2 days', '-1 hours')),
    ('1', 2, datetime('now', '-5 days', '-3 hours'), datetime('now', '-5 days', '-2 hours')),
    ('2', 1, datetime('now', '-3 days', '-1 hours'), datetime('now', '-3 days', '-30 minutes')),
    ('3', 1, datetime('now', '-1 days', '-4 hours'), datetime('now', '-1 days', '-3 hours'));
--product views
INSERT INTO viewedProduct VALUES 
    ('1', 1, datetime('now', '-2 days', '-2 hours'), 'P001'),
    ('1', 1, datetime('now', '-2 days', '-2 hours', '+5 minutes'), 'P003'),
    ('1', 1, datetime('now', '-2 days', '-2 hours', '+10 minutes'), 'P005'),
    ('2', 1, datetime('now', '-3 days', '-1 hours'), 'P002'),
    ('2', 1, datetime('now', '-3 days', '-1 hours', '+5 minutes'), 'P004'),
    ('2', 1, datetime('now', '-3 days', '-1 hours', '+10 minutes'), 'P001'),
    ('3', 1, datetime('now', '-1 days', '-4 hours'), 'P001'),
    ('3', 1, datetime('now', '-1 days', '-4 hours', '+5 minutes'), 'P008'),
    ('1', 2, datetime('now', '-5 days', '-3 hours'), 'P005'),
    ('1', 2, datetime('now', '-5 days', '-3 hours', '+5 minutes'), 'P006');
--some searches
INSERT INTO search VALUES 
    ('1', 1, datetime('now', '-2 days', '-2 hours'), 'laptop'),
    ('2', 1, datetime('now', '-3 days', '-1 hours'), 'laptop macbook'),
    ('3', 1, datetime('now', '-1 days', '-4 hours'), 'wireless headphones');