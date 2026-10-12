from backend.database.db_manager import connect

def initialize_database() -> None:
    con = connect(read_only=False)
    con.execute("""
    CREATE TABLE IF NOT EXISTS customers(customer_id INTEGER PRIMARY KEY, customer_name VARCHAR NOT NULL, email VARCHAR, city VARCHAR, country VARCHAR, signup_date DATE);
    CREATE TABLE IF NOT EXISTS products(product_id INTEGER PRIMARY KEY, product_name VARCHAR NOT NULL, category VARCHAR, price DECIMAL(10,2), stock_quantity INTEGER);
    CREATE TABLE IF NOT EXISTS orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(customer_id), order_date DATE, status VARCHAR, total_amount DECIMAL(12,2));
    CREATE TABLE IF NOT EXISTS order_items(order_item_id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(order_id), product_id INTEGER REFERENCES products(product_id), quantity INTEGER, unit_price DECIMAL(10,2));
    """)
    if con.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        con.execute("""INSERT INTO customers VALUES
        (1,'Aarav Sharma','aarav@example.test','Bengaluru','India','2023-01-12'),(2,'Maya Patel','maya@example.test','Mumbai','India','2023-02-20'),(3,'Noah Wilson','noah@example.test','London','UK','2023-03-05'),(4,'Ananya Rao','ananya@example.test','Bengaluru','India','2023-04-15'),(5,'Liam Chen','liam@example.test','Singapore','Singapore','2023-05-09'),(6,'Sofia Garcia','sofia@example.test','Madrid','Spain','2023-06-18'),(7,'Ishaan Mehta','ishaan@example.test','Delhi','India','2023-07-21'),(8,'Emma Brown','emma@example.test','London','UK','2023-08-11'),(9,'Kabir Joshi','kabir@example.test','Pune','India','2023-09-02'),(10,'Olivia Martin','olivia@example.test','Paris','France','2023-10-14')""")
    if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        con.execute("""INSERT INTO products VALUES (1,'Wireless Headphones','Electronics',79.99,120),(2,'Desk Lamp','Home',34.50,80),(3,'Running Shoes','Sports',89.00,45),(4,'Coffee Maker','Home',119.00,32),(5,'Smart Watch','Electronics',199.99,60),(6,'Yoga Mat','Sports',29.99,150),(7,'Travel Backpack','Accessories',64.00,75),(8,'Bluetooth Speaker','Electronics',54.99,90)""")
    if con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        con.execute("INSERT INTO orders SELECT i, ((i-1)%10)+1, DATE '2024-01-01' + CAST(((i*11)%300) AS INTEGER), CASE WHEN i%9=0 THEN 'cancelled' WHEN i%7=0 THEN 'pending' ELSE 'completed' END, (i%4+1)*45.5 FROM range(1,41) t(i)")
    if con.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 0:
        con.execute("INSERT INTO order_items SELECT i, ((i-1)%40)+1, ((i-1)%8)+1, (i%3)+1, (i%4+1)*18.25 FROM range(1,81) t(i)")
    con.close()

if __name__ == "__main__":
    initialize_database()
    print("QueryPilot sample database initialized.")
