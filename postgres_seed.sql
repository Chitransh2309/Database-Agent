-- Run in pgAdmin while connected to copilot_db.
-- WARNING: drops/recreates the five project tables.

BEGIN;

DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
 customer_id SERIAL PRIMARY KEY,
 name VARCHAR(120) NOT NULL,
 email VARCHAR(180) UNIQUE NOT NULL,
 phone VARCHAR(20),
 city VARCHAR(100), state VARCHAR(100), country VARCHAR(80) DEFAULT 'India',
 age INTEGER CHECK (age BETWEEN 18 AND 100),
 gender VARCHAR(20), registration_date DATE NOT NULL,
 customer_segment VARCHAR(30), loyalty_points INTEGER DEFAULT 0,
 is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE products (
 product_id SERIAL PRIMARY KEY,
 name VARCHAR(180) NOT NULL,
 category VARCHAR(100), subcategory VARCHAR(100), brand VARCHAR(100),
 price NUMERIC(12,2) NOT NULL, cost_price NUMERIC(12,2),
 stock INTEGER DEFAULT 0, supplier VARCHAR(150),
 rating NUMERIC(3,2), is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE orders (
 order_id SERIAL PRIMARY KEY,
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
 order_date DATE NOT NULL, status VARCHAR(30) NOT NULL,
 total_amount NUMERIC(12,2) NOT NULL, discount_amount NUMERIC(12,2) DEFAULT 0,
 shipping_city VARCHAR(100), payment_status VARCHAR(30)
);

CREATE TABLE order_items (
 order_item_id SERIAL PRIMARY KEY,
 order_id INTEGER NOT NULL REFERENCES orders(order_id),
 product_id INTEGER NOT NULL REFERENCES products(product_id),
 quantity INTEGER NOT NULL CHECK (quantity > 0),
 unit_price NUMERIC(12,2) NOT NULL,
 discount_percent NUMERIC(5,2) DEFAULT 0
);

CREATE TABLE payments (
 payment_id SERIAL PRIMARY KEY,
 order_id INTEGER NOT NULL REFERENCES orders(order_id),
 payment_date DATE NOT NULL, amount NUMERIC(12,2) NOT NULL,
 payment_method VARCHAR(40), status VARCHAR(30),
 transaction_reference VARCHAR(80) UNIQUE
);

INSERT INTO customers
(name,email,phone,city,state,country,age,gender,registration_date,customer_segment,loyalty_points,is_active)
VALUES
('Rahul Sharma','rahul.sharma@example.com','9876500001','Delhi','Delhi','India',28,'Male','2023-01-15','Premium',4250,TRUE),
('Priya Reddy','priya.reddy@example.com','9876500002','Hyderabad','Telangana','India',25,'Female','2023-02-10','Gold',3180,TRUE),
('Arjun Mehta','arjun.mehta@example.com','9876500003','Mumbai','Maharashtra','India',34,'Male','2022-11-20','Premium',5620,TRUE),
('Sneha Rao','sneha.rao@example.com','9876500004','Bengaluru','Karnataka','India',29,'Female','2023-03-12','Gold',2910,TRUE),
('Karan Singh','karan.singh@example.com','9876500005','Delhi','Delhi','India',41,'Male','2022-08-17','Premium',6040,TRUE),
('Ananya Iyer','ananya.iyer@example.com','9876500006','Chennai','Tamil Nadu','India',31,'Female','2023-05-22','Gold',2470,TRUE),
('Vikram Patel','vikram.patel@example.com','9876500007','Ahmedabad','Gujarat','India',38,'Male','2022-12-01','Premium',4780,TRUE),
('Neha Kapoor','neha.kapoor@example.com','9876500008','Pune','Maharashtra','India',27,'Female','2023-04-18','Silver',1850,TRUE),
('Rohan Verma','rohan.verma@example.com','9876500009','Hyderabad','Telangana','India',35,'Male','2022-09-25','Premium',5210,TRUE),
('Ishita Nair','ishita.nair@example.com','9876500010','Kochi','Kerala','India',24,'Female','2023-06-10','Silver',1320,TRUE),
('Aditya Kulkarni','aditya.k@example.com','9876500011','Pune','Maharashtra','India',32,'Male','2023-01-28','Gold',2740,TRUE),
('Meera Joshi','meera.j@example.com','9876500012','Jaipur','Rajasthan','India',30,'Female','2023-07-04','Silver',1560,TRUE),
('Siddharth Bose','siddharth.b@example.com','9876500013','Kolkata','West Bengal','India',37,'Male','2022-06-19','Premium',4930,TRUE),
('Kavya Menon','kavya.m@example.com','9876500014','Kochi','Kerala','India',26,'Female','2023-08-11','Silver',1190,TRUE),
('Nikhil Gupta','nikhil.g@example.com','9876500015','Noida','Uttar Pradesh','India',33,'Male','2022-10-14','Gold',3520,TRUE),
('Divya Shah','divya.sh@example.com','9876500016','Mumbai','Maharashtra','India',29,'Female','2023-09-03','Gold',3010,TRUE),
('Aman Khanna','aman.k@example.com','9876500017','Chandigarh','Chandigarh','India',40,'Male','2022-07-23','Premium',4480,TRUE),
('Pooja Desai','pooja.d@example.com','9876500018','Ahmedabad','Gujarat','India',36,'Female','2023-02-27','Gold',2670,TRUE),
('Harsh Agarwal','harsh.a@example.com','9876500019','Gurugram','Haryana','India',31,'Male','2023-10-08','Silver',1430,TRUE),
('Lakshmi Krishnan','lakshmi.k@example.com','9876500020','Chennai','Tamil Nadu','India',44,'Female','2022-05-12','Premium',5120,TRUE),
('Varun Bhat','varun.b@example.com','9876500021','Bengaluru','Karnataka','India',28,'Male','2024-01-09','Silver',980,TRUE),
('Nandini Rao','nandini.r@example.com','9876500022','Hyderabad','Telangana','India',33,'Female','2023-11-17','Gold',2240,TRUE),
('Yash Thakur','yash.t@example.com','9876500023','Shimla','Himachal Pradesh','India',26,'Male','2024-02-06','Silver',760,TRUE),
('Ayesha Khan','ayesha.k@example.com','9876500024','Lucknow','Uttar Pradesh','India',30,'Female','2023-12-22','Gold',1980,TRUE),
('Manish Sethi','manish.s@example.com','9876500025','Jaipur','Rajasthan','India',39,'Male','2022-04-30','Premium',5730,TRUE),
('Riya Das','riya.d@example.com','9876500026','Kolkata','West Bengal','India',27,'Female','2024-03-15','Silver',640,TRUE),
('Gaurav Jain','gaurav.j@example.com','9876500027','Indore','Madhya Pradesh','India',42,'Male','2022-09-02','Premium',4660,TRUE),
('Tanvi Deshmukh','tanvi.d@example.com','9876500028','Nagpur','Maharashtra','India',25,'Female','2024-04-19','Silver',520,TRUE),
('Suresh Rao','suresh.r@example.com','9876500029','Visakhapatnam','Andhra Pradesh','India',45,'Male','2022-03-11','Gold',3370,TRUE),
('Maya Thomas','maya.t@example.com','9876500030','Kochi','Kerala','India',34,'Female','2023-06-28','Gold',2860,TRUE);

INSERT INTO products
(name,category,subcategory,brand,price,cost_price,stock,supplier,rating,is_active)
VALUES
('Laptop Pro 14','Electronics','Laptops','TechNova',85000,68000,24,'TechNova Distribution',4.70,TRUE),
('Laptop Air 13','Electronics','Laptops','TechNova',68000,52000,31,'TechNova Distribution',4.50,TRUE),
('Smartphone X','Electronics','Smartphones','Orion',55000,42000,45,'Orion India',4.60,TRUE),
('Smartphone Lite','Electronics','Smartphones','Orion',28000,20500,62,'Orion India',4.20,TRUE),
('Monitor 27','Electronics','Monitors','ViewMax',28000,21000,28,'ViewMax India',4.40,TRUE),
('Monitor 24','Electronics','Monitors','ViewMax',18500,13500,35,'ViewMax India',4.30,TRUE),
('Mechanical Keyboard','Accessories','Keyboards','KeyCraft',4500,2700,85,'KeyCraft Supplies',4.60,TRUE),
('Wireless Mouse','Accessories','Mice','KeyCraft',1500,800,130,'KeyCraft Supplies',4.30,TRUE),
('USB-C Hub','Accessories','Adapters','ConnectX',2500,1300,95,'ConnectX India',4.10,TRUE),
('Noise Cancelling Headphones','Audio','Headphones','SonicWave',12000,7200,58,'SonicWave India',4.70,TRUE),
('Bluetooth Speaker','Audio','Speakers','SonicWave',6500,3800,72,'SonicWave India',4.40,TRUE),
('Smart Watch','Wearables','Smartwatches','PulseFit',18000,10500,49,'PulseFit India',4.50,TRUE),
('Fitness Band','Wearables','Fitness','PulseFit',6500,3600,75,'PulseFit India',4.10,TRUE),
('Tablet Air','Electronics','Tablets','Orion',42000,31000,38,'Orion India',4.60,TRUE),
('Tablet Mini','Electronics','Tablets','Orion',26000,19000,46,'Orion India',4.20,TRUE),
('Gaming Chair','Furniture','Chairs','ComfortPro',22000,14500,21,'ComfortPro India',4.30,TRUE),
('Office Chair','Furniture','Chairs','ComfortPro',12500,7900,34,'ComfortPro India',4.50,TRUE),
('Standing Desk','Furniture','Desks','WorkSpace',32000,21000,17,'WorkSpace India',4.40,TRUE),
('Backpack Pro','Accessories','Bags','TravelGear',4500,2400,80,'TravelGear India',4.20,TRUE),
('Webcam HD','Electronics','Cameras','VisionTech',7500,4500,43,'VisionTech India',4.00,TRUE),
('Portable SSD 1TB','Storage','SSDs','DataCore',9500,6200,52,'DataCore India',4.60,TRUE),
('External HDD 2TB','Storage','HDDs','DataCore',6500,4100,48,'DataCore India',4.20,TRUE),
('WiFi Router AX','Networking','Routers','NetSphere',8500,5100,39,'NetSphere India',4.30,TRUE),
('Power Bank 20000','Accessories','Power','VoltEdge',3200,1700,105,'VoltEdge India',4.10,TRUE),
('USB Microphone','Audio','Microphones','SonicWave',9000,5400,29,'SonicWave India',4.50,TRUE);

-- 80 orders.
INSERT INTO orders
(customer_id,order_date,status,total_amount,discount_amount,shipping_city,payment_status)
VALUES
(1,'2026-01-05','Completed',86500,1500,'Delhi','Paid'),
(2,'2026-01-09','Completed',55000,0,'Hyderabad','Paid'),
(3,'2026-01-14','Completed',98000,5000,'Mumbai','Paid'),
(4,'2026-01-21','Completed',42000,0,'Bengaluru','Paid'),
(5,'2026-01-28','Completed',125000,7500,'Delhi','Paid'),
(6,'2026-02-03','Completed',18000,0,'Chennai','Paid'),
(7,'2026-02-08','Completed',30000,2500,'Ahmedabad','Paid'),
(8,'2026-02-13','Completed',55000,3000,'Pune','Paid'),
(9,'2026-02-19','Completed',95000,5000,'Hyderabad','Paid'),
(10,'2026-02-25','Completed',18000,0,'Kochi','Paid'),
(11,'2026-03-02','Completed',73500,2500,'Pune','Paid'),
(12,'2026-03-07','Completed',26000,0,'Jaipur','Paid'),
(13,'2026-03-11','Completed',102000,7000,'Kolkata','Paid'),
(14,'2026-03-16','Completed',6500,0,'Kochi','Paid'),
(15,'2026-03-22','Completed',41000,2000,'Noida','Paid'),
(16,'2026-03-27','Completed',83000,4500,'Mumbai','Paid'),
(17,'2026-04-02','Completed',54000,3000,'Chandigarh','Paid'),
(18,'2026-04-06','Completed',38500,1500,'Ahmedabad','Paid'),
(19,'2026-04-12','Completed',22000,0,'Gurugram','Paid'),
(20,'2026-04-18','Completed',115000,5000,'Chennai','Paid'),
(21,'2026-04-23','Completed',7500,0,'Bengaluru','Paid'),
(22,'2026-05-01','Completed',73500,3500,'Hyderabad','Paid'),
(23,'2026-05-05','Completed',26000,0,'Shimla','Paid'),
(24,'2026-05-11','Completed',58000,2500,'Lucknow','Paid'),
(25,'2026-05-17','Completed',128000,8000,'Jaipur','Paid'),
(26,'2026-05-22','Completed',18500,0,'Kolkata','Paid'),
(27,'2026-05-28','Completed',95000,5000,'Indore','Paid'),
(28,'2026-06-03','Completed',32000,1500,'Nagpur','Paid'),
(29,'2026-06-08','Completed',72000,3000,'Visakhapatnam','Paid'),
(30,'2026-06-14','Completed',45000,2000,'Kochi','Paid'),
(1,'2026-06-19','Completed',12500,0,'Delhi','Paid'),
(2,'2026-06-24','Completed',68000,3000,'Hyderabad','Paid'),
(3,'2026-06-29','Completed',42000,0,'Mumbai','Paid'),
(4,'2026-07-03','Completed',93500,5500,'Bengaluru','Paid'),
(5,'2026-07-08','Completed',18000,0,'Delhi','Paid'),
(6,'2026-07-12','Completed',76000,4000,'Chennai','Paid'),
(7,'2026-07-16','Completed',28000,0,'Ahmedabad','Paid'),
(8,'2026-07-20','Completed',46500,2500,'Pune','Paid'),
(9,'2026-07-24','Completed',112000,8000,'Hyderabad','Paid'),
(10,'2026-07-28','Completed',32000,1000,'Kochi','Paid'),
(11,'2026-08-01','Completed',85000,5000,'Pune','Paid'),
(12,'2026-08-02','Completed',18500,0,'Jaipur','Paid'),
(13,'2026-08-03','Completed',68000,3000,'Kolkata','Paid'),
(14,'2026-08-04','Completed',4500,0,'Kochi','Paid'),
(15,'2026-08-05','Completed',95000,6000,'Noida','Paid'),
(16,'2026-08-06','Completed',55000,2500,'Mumbai','Paid'),
(17,'2026-08-07','Completed',32000,1500,'Chandigarh','Paid'),
(18,'2026-08-08','Completed',12500,0,'Ahmedabad','Paid'),
(19,'2026-08-09','Completed',22000,0,'Gurugram','Paid'),
(20,'2026-08-10','Completed',126000,9000,'Chennai','Paid'),
(21,'2026-08-11','Completed',9500,0,'Bengaluru','Paid'),
(22,'2026-08-12','Completed',73500,3500,'Hyderabad','Paid'),
(23,'2026-08-13','Completed',26000,0,'Shimla','Paid'),
(24,'2026-08-14','Completed',58500,2500,'Lucknow','Paid'),
(25,'2026-08-15','Completed',132000,8000,'Jaipur','Paid'),
(26,'2026-08-16','Completed',18500,0,'Kolkata','Paid'),
(27,'2026-08-17','Completed',98000,6000,'Indore','Paid'),
(28,'2026-08-18','Completed',32000,1500,'Nagpur','Paid'),
(29,'2026-08-19','Completed',74500,3500,'Visakhapatnam','Paid'),
(30,'2026-08-20','Completed',45000,2000,'Kochi','Paid'),
(1,'2026-08-21','Pending',28500,1000,'Delhi','Pending'),
(3,'2026-08-21','Completed',65000,2500,'Mumbai','Paid'),
(5,'2026-08-22','Cancelled',45000,0,'Delhi','Refunded'),
(9,'2026-08-22','Completed',88000,5000,'Hyderabad','Paid'),
(13,'2026-08-23','Completed',37500,1500,'Kolkata','Paid'),
(15,'2026-08-23','Pending',18000,0,'Noida','Pending'),
(20,'2026-08-24','Completed',72000,4000,'Chennai','Paid'),
(25,'2026-08-24','Completed',55000,2500,'Jaipur','Paid'),
(27,'2026-08-25','Completed',43000,1500,'Indore','Paid'),
(29,'2026-08-25','Completed',91000,4500,'Visakhapatnam','Paid'),
(2,'2026-08-25','Completed',28000,1000,'Hyderabad','Paid'),
(4,'2026-08-25','Returned',18500,0,'Bengaluru','Refunded'),
(6,'2026-08-25','Completed',65000,3000,'Chennai','Paid'),
(10,'2026-08-25','Completed',12500,0,'Kochi','Paid'),
(18,'2026-08-25','Completed',38500,1500,'Ahmedabad','Paid'),
(22,'2026-08-25','Completed',47000,2000,'Hyderabad','Paid'),
(24,'2026-08-25','Completed',68000,3000,'Lucknow','Paid'),
(30,'2026-08-25','Completed',54000,2500,'Kochi','Paid');

-- Two items per order => 160 rows.
INSERT INTO order_items(order_id,product_id,quantity,unit_price,discount_percent)
SELECT o.order_id,
       ((o.order_id * 7 + x.n * 3) % 25) + 1,
       ((o.order_id + x.n) % 3) + 1,
       p.price,
       CASE WHEN (o.order_id + x.n) % 5 = 0 THEN 10
            WHEN (o.order_id + x.n) % 3 = 0 THEN 5 ELSE 0 END
FROM orders o
CROSS JOIN LATERAL generate_series(1,2) x(n)
JOIN products p ON p.product_id = ((o.order_id * 7 + x.n * 3) % 25) + 1;

INSERT INTO payments(order_id,payment_date,amount,payment_method,status,transaction_reference)
SELECT order_id,order_date,
       CASE WHEN status='Cancelled' THEN 0 ELSE total_amount END,
       CASE WHEN order_id % 4=0 THEN 'UPI'
            WHEN order_id % 4=1 THEN 'Credit Card'
            WHEN order_id % 4=2 THEN 'Debit Card'
            ELSE 'Net Banking' END,
       CASE WHEN status='Completed' THEN 'Completed'
            WHEN status='Pending' THEN 'Pending'
            WHEN status IN ('Cancelled','Returned') THEN 'Refunded'
            ELSE 'Failed' END,
       'TXN-' || LPAD(order_id::text,6,'0')
FROM orders;

COMMIT;

SELECT 'customers' table_name, COUNT(*) row_count FROM customers
UNION ALL SELECT 'products',COUNT(*) FROM products
UNION ALL SELECT 'orders',COUNT(*) FROM orders
UNION ALL SELECT 'order_items',COUNT(*) FROM order_items
UNION ALL SELECT 'payments',COUNT(*) FROM payments;
