import sqlite3
import sys
import getpass
from datetime import datetime, timedelta
import hashlib

class ECommerceSystem:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.current_user = None
        self.current_role = None
        self.session_no = None
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
            print(f"Connected to database: {self.db_name}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            sys.exit(1)
    
    def close(self):
        """Close con"""
        if self.conn:
            self.conn.close()
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    def start_session(self, cid):
        try:
            #next session number
            self.cursor.execute("""
                SELECT COALESCE(MAX(sessionNo), 0) + 1 
                FROM sessions 
                WHERE cid = ?
            """, (cid,))
            session_no = self.cursor.fetchone()[0]
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("""
                INSERT INTO sessions (cid, sessionNo, start_time)
                VALUES (?, ?, ?)
            """, (cid, session_no, start_time))
            self.conn.commit()
            self.session_no = session_no
            return session_no
        except sqlite3.Error as e:
            print(f"Error starting session: {e}")
            return None
    
    def end_session(self):
        if self.current_user and self.session_no:
            try:
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute("""
                    UPDATE sessions 
                    SET end_time = ? 
                    WHERE cid = ? AND sessionNo = ?
                """, (end_time, self.current_user, self.session_no))
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"Error ending session: {e}")
    
    def login_screen(self):
        """login/register screen"""
        while True:
            print("\n" + "="*50)
            print("E-COMMERCE SYSTEM")
            print("="*50)
            print("1. Login")
            print("2. Sign Up")
            print("3. Exit")
            print("="*50)
            
            choice = input("Enter your choice: ").strip()
            if choice == '1':
                if self.login():
                    return True
            elif choice == '2':
                self.signup()
            elif choice == '3':
                print("Goodbye!")
                return False
            else:
                print("Invalid choice. Please try again.")
    
    def login(self):
        print("\n--- LOGIN ---")
        uid = input("User ID: ").strip()
        pwd = getpass.getpass("Password: ")
        
        pwd_hash = self.hash_password(pwd)
        
        try:
            self.cursor.execute("""
                SELECT uid, role FROM users 
                WHERE uid = ? AND pwd = ?
            """, (uid, pwd_hash))
            
            result = self.cursor.fetchone()
            
            if result:
                self.current_user = result[0]
                self.current_role = result[1]
                print(f"\nLogin successful! Welcome, {uid}")
                
                # Start session for customers
                if self.current_role == 'customer':
                    self.start_session(self.current_user)
                return True
            else:
                print("Invalid user ID or password.")
                return False
        except sqlite3.Error as e:
            print(f"Login error: {e}")
            return False
    
    def signup(self):
        """user registration"""
        print("\n--- SIGN UP ---")
        name = input("Name: ").strip()
        email = input("Email: ").strip()
        pwd = getpass.getpass("Password: ")
        pwd_confirm = getpass.getpass("Confirm Password: ")
        if pwd != pwd_confirm:
            print("Passwords do not match!")
            return
        #if email exists
        try:
            self.cursor.execute("""
                SELECT cid FROM customers WHERE email = ?
            """, (email,))
            if self.cursor.fetchone():
                print("Email already in use!")
                return
            #unique user ID
            self.cursor.execute("SELECT COALESCE(MAX(CAST(uid AS INTEGER)), 0) + 1 FROM users")
            new_uid = str(self.cursor.fetchone()[0])
            pwd_hash = self.hash_password(pwd)
            #add to users table
            self.cursor.execute("""
                INSERT INTO users (uid, pwd, role)
                VALUES (?, ?, 'customer')
            """, (new_uid, pwd_hash))
            
            #customers table
            self.cursor.execute("""
                INSERT INTO customers (cid, name, email)
                VALUES (?, ?, ?)
            """, (new_uid, name, email))
            self.conn.commit()
            print(f"\nRegistration successful! Your user ID is: {new_uid}")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Registration error: {e}")
    def customer_menu(self):
        """Display customer menu"""
        while True:
            print("\n" + "="*50)
            print("CUSTOMER MENU")
            print("="*50)
            print("1. Search for Products")
            print("2. View Cart")
            print("3. Checkout")
            print("4. My Orders")
            print("5. Logout")
            print("="*50)
            
            choice = input("Enter your choice: ").strip()
            if choice == '1':
                self.search_products()
            elif choice == '2':
                self.view_cart()
            elif choice == '3':
                self.checkout()
            elif choice == '4':
                self.view_orders()
            elif choice == '5':
                self.end_session()
                print("Logged out successfully.")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def search_products(self):
        """Search for products"""
        print("\n--- PRODUCT SEARCH ---")
        query = input("Enter search keyword(s): ").strip()
        
        if not query:
            print("Please enter at least one keyword.")
            return
        #Record search
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute("""
                INSERT INTO search (cid, sessionNo, ts, query)
                VALUES (?, ?, ?, ?)
            """, (self.current_user, self.session_no, ts, query))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error recording search: {e}")
        #Split keywords and build query
        keywords = query.lower().split()
        where_conditions = []
        params = []
        for keyword in keywords:
            where_conditions.append("(LOWER(name) LIKE ? OR LOWER(descr) LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        where_clause = " AND ".join(where_conditions)
        sql = f"""
            SELECT pid, name, category, price, stock_count
            FROM products
            WHERE {where_clause}
            ORDER BY name
        """
        
        try:
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            if not results:
                print("No products found.")
                return
            # Pagination
            self.paginate_results(results, self.display_product_row, 
                                self.product_detail_view)
        except sqlite3.Error as e:
            print(f"Search error: {e}")
    
    def display_product_row(self, product):
        """Display product row"""
        pid, name, category, price, stock = product
        print(f"  {pid:5} | {name:30} | {category:15} | ${price:8.2f} | Stock: {stock}")
    def product_detail_view(self, product):
        """Display product view"""
        pid = product[0]
        #product details
        self.cursor.execute("""
            SELECT pid, name, category, price, stock_count, descr
            FROM products WHERE pid = ?
        """, (pid,))
        details = self.cursor.fetchone()
        if not details:
            print("Product not found.")
            return
        
        pid, name, category, price, stock, descr = details
        # Record view
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute("""
                INSERT INTO viewedProduct (cid, sessionNo, ts, pid)
                VALUES (?, ?, ?, ?)
            """, (self.current_user, self.session_no, ts, pid))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error recording view: {e}")
        
        print("\n" + "="*60)
        print(f"Product ID: {pid}")
        print(f"Name: {name}")
        print(f"Category: {category}")
        print(f"Price: ${price:.2f}")
        print(f"Stock: {stock}")
        print(f"Description: {descr}")
        print("="*60)
        #add to cart
        if stock > 0:
            add = input("\nAdd to cart? (y/n): ").strip().lower()
            if add == 'y':
                self.add_to_cart(pid, stock)
        else:
            print("\nOut of stock!")
    
    def add_to_cart(self, pid, available_stock):
        try:
            #Check if in cart
            self.cursor.execute("""
                SELECT qty FROM cart
                WHERE cid = ? AND sessionNo = ? AND pid = ?
            """, (self.current_user, self.session_no, pid))
            
            existing = self.cursor.fetchone()
            if existing:
                new_qty = existing[0] + 1
                if new_qty > available_stock:
                    print("Cannot add more - insufficient stock!")
                    return
                self.cursor.execute("""
                    UPDATE cart SET qty = ?
                    WHERE cid = ? AND sessionNo = ? AND pid = ?
                """, (new_qty, self.current_user, self.session_no, pid))
            else:
                self.cursor.execute("""
                    INSERT INTO cart (cid, sessionNo, pid, qty)
                    VALUES (?, ?, ?, 1)
                """, (self.current_user, self.session_no, pid))
            
            self.conn.commit()
            print("Product added to cart!")
        except sqlite3.Error as e:
            print(f"Error adding to cart: {e}")
            self.conn.rollback()
    
    def view_cart(self):
        """View and manage cart"""
        print("\n--- SHOPPING CART ---")
        try:
            self.cursor.execute("""
                SELECT c.pid, p.name, p.price, c.qty, p.stock_count,
                       (p.price * c.qty) as total
                FROM cart c
                JOIN products p ON c.pid = p.pid
                WHERE c.cid = ? AND c.sessionNo = ?
            """, (self.current_user, self.session_no))
            
            cart_items = self.cursor.fetchall()
            if not cart_items:
                print("Your cart is empty.")
                return
            
            print(f"\n{'PID':<6} {'Name':<30} {'Price':<10} {'Qty':<5} {'Total':<10}")
            print("-" * 65)
            
            grand_total = 0
            for item in cart_items:
                pid, name, price, qty, stock, total = item
                print(f"{pid:<6} {name:<30} ${price:<9.2f} {qty:<5} ${total:<9.2f}")
                grand_total += total
            
            print("-" * 65)
            print(f"{'GRAND TOTAL:':<51} ${grand_total:.2f}")
            print("\n1. Update quantity")
            print("2. Remove item")
            print("3. Back to menu")
            
            choice = input("Enter choice: ").strip()
            if choice == '1':
                self.update_cart_quantity(cart_items)
            elif choice == '2':
                self.remove_from_cart(cart_items)
        except sqlite3.Error as e:
            print(f"Error viewing cart: {e}")
    
    def update_cart_quantity(self, cart_items):
        """Update quantity of cart item"""
        pid = input("Enter product ID: ").strip()
        #Find item in cart
        item = next((i for i in cart_items if i[0] == pid), None)
        if not item:
            print("Product not in cart.")
            return
        stock = item[4]
        try:
            new_qty = int(input(f"Enter new quantity (available: {stock}): ").strip())
            
            if new_qty <= 0:
                print("Quantity must be positive.")
                return
            if new_qty > stock:
                print("Insufficient stock!")
                return
            self.cursor.execute("""
                UPDATE cart SET qty = ?
                WHERE cid = ? AND sessionNo = ? AND pid = ?
            """, (new_qty, self.current_user, self.session_no, pid))
            self.conn.commit()
            print("Quantity updated!")
        except ValueError:
            print("Invalid quantity.")
        except sqlite3.Error as e:
            print(f"Error updating cart: {e}")
            self.conn.rollback()
    
    def remove_from_cart(self, cart_items):
        """Remove from cart"""
        pid = input("Enter product ID to remove: ").strip()
        try:
            self.cursor.execute("""
                DELETE FROM cart
                WHERE cid = ? AND sessionNo = ? AND pid = ?
            """, (self.current_user, self.session_no, pid))
            
            if self.cursor.rowcount > 0:
                self.conn.commit()
                print("Item removed from cart!")
            else:
                print("Product not in cart.")
                
        except sqlite3.Error as e:
            print(f"Error removing from cart: {e}")
            self.conn.rollback()
    def checkout(self):
        """Process checkout"""
        print("\n--- CHECKOUT ---")
        # Get items
        try:
            self.cursor.execute("""
                SELECT c.pid, p.name, p.price, c.qty, p.stock_count,
                       (p.price * c.qty) as total
                FROM cart c
                JOIN products p ON c.pid = p.pid
                WHERE c.cid = ? AND c.sessionNo = ?
            """, (self.current_user, self.session_no))
            
            cart_items = self.cursor.fetchall()
            if not cart_items:
                print("Your cart is empty.")
                return
            # Display order summary
            print(f"\n{'PID':<6} {'Name':<30} {'Price':<10} {'Qty':<5} {'Total':<10}")
            print("-" * 65)
            grand_total = 0
            for item in cart_items:
                pid, name, price, qty, stock, total = item
                print(f"{pid:<6} {name:<30} ${price:<9.2f} {qty:<5} ${total:<9.2f}")
                grand_total += total
            
            print("-" * 65)
            print(f"{'GRAND TOTAL:':<51} ${grand_total:.2f}")
            # Get shipping address
            shipping_address = input("\nEnter shipping address: ").strip()
            
            if not shipping_address:
                print("Shipping address is required.")
                return
            confirm = input("\nConfirm order? (y/n): ").strip().lower()
            
            if confirm != 'y':
                print("Order cancelled.")
                return
            self.create_order(cart_items, shipping_address)
            
        except sqlite3.Error as e:
            print(f"Checkout error: {e}")
    
    def create_order(self, cart_items, shipping_address):
        """new order"""
        try:
            #Generate order number
            self.cursor.execute("SELECT COALESCE(MAX(ono), 0) + 1 FROM orders")
            ono = self.cursor.fetchone()[0]
            
            odate = datetime.now().strftime("%Y-%m-%d")
            # Insert order
            self.cursor.execute("""
                INSERT INTO orders (ono, cid, sessionNo, odate, shipping_address)
                VALUES (?, ?, ?, ?, ?)
            """, (ono, self.current_user, self.session_no, odate, shipping_address))
            line_no = 1
            for item in cart_items:
                pid, name, price, qty, stock, total = item
                # Insert order line
                self.cursor.execute("""
                    INSERT INTO orderlines (ono, lineNo, pid, qty, uprice)
                    VALUES (?, ?, ?, ?, ?)
                """, (ono, line_no, pid, qty, price))
                #Update stock
                self.cursor.execute("""
                    UPDATE products
                    SET stock_count = stock_count - ?
                    WHERE pid = ?
                """, (qty, pid))
                line_no += 1
            
            #Clear cart
            self.cursor.execute("""
                DELETE FROM cart
                WHERE cid = ? AND sessionNo = ?
            """, (self.current_user, self.session_no))
            self.conn.commit()
            print(f"\nOrder placed successfully! Order number: {ono}")
            
        except sqlite3.Error as e:
            print(f"Error creating order: {e}")
            self.conn.rollback()
    
    def view_orders(self):
        """View past orders"""
        print("\n--- MY ORDERS ---")
        try:
            self.cursor.execute("""
                SELECT o.ono, o.odate, o.shipping_address,
                       SUM(ol.qty * ol.uprice) as total
                FROM orders o
                JOIN orderlines ol ON o.ono = ol.ono
                WHERE o.cid = ?
                GROUP BY o.ono, o.odate, o.shipping_address
                ORDER BY o.odate DESC, o.ono DESC
            """, (self.current_user,))
            
            orders = self.cursor.fetchall()
            
            if not orders:
                print("No orders found.")
                return
            self.paginate_results(orders, self.display_order_row, 
                                self.order_detail_view)
        except sqlite3.Error as e:
            print(f"Error viewing orders: {e}")
    
    def display_order_row(self, order):
        """Display order row"""
        ono, odate, address, total = order
        print(f"  Order #{ono} | {odate} | {address[:30]:30} | ${total:.2f}")
    def order_detail_view(self, order):
        """Display order view"""
        ono = order[0]
        try:
            #order header
            self.cursor.execute("""
                SELECT ono, odate, shipping_address
                FROM orders WHERE ono = ?
            """, (ono,))
            
            header = self.cursor.fetchone()
            if not header:
                print("Order not found.")
                return
            ono, odate, address = header            
            #order lines
            self.cursor.execute("""
                SELECT p.name, p.category, ol.qty, ol.uprice,
                       (ol.qty * ol.uprice) as line_total
                FROM orderlines ol
                JOIN products p ON ol.pid = p.pid
                WHERE ol.ono = ?
                ORDER BY ol.lineNo
            """, (ono,))
            
            lines = self.cursor.fetchall()
            #Display order
            print("\n" + "="*70)
            print(f"Order Number: {ono}")
            print(f"Order Date: {odate}")
            print(f"Shipping Address: {address}")
            print("="*70)
            
            print(f"\n{'Product':<30} {'Category':<15} {'Qty':<5} {'Price':<10} {'Total':<10}")
            print("-" * 70)
            grand_total = 0
            for line in lines:
                name, category, qty, uprice, line_total = line
                print(f"{name:<30} {category:<15} {qty:<5} ${uprice:<9.2f} ${line_total:<9.2f}")
                grand_total += line_total
            
            print("-" * 70)
            print(f"{'GRAND TOTAL:':<60} ${grand_total:.2f}")
            print("="*70)
            input("\nPress Enter to continue...")
            
        except sqlite3.Error as e:
            print(f"Error viewing order details: {e}")
    
    def sales_menu(self):
        """Display salesperson menu"""
        while True:
            print("\n" + "="*50)
            print("SALES MENU")
            print("="*50)
            print("1. Check/Update Products")
            print("2. Sales Report")
            print("3. Top Selling Products")
            print("4. Logout")
            print("="*50)
            
            choice = input("Enter your choice: ").strip()
            if choice == '1':
                self.manage_products()
            elif choice == '2':
                self.sales_report()
            elif choice == '3':
                self.top_products()
            elif choice == '4':
                print("Logged out successfully.")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def manage_products(self):
        """Check and update product information"""
        print("\n--- PRODUCT MANAGEMENT ---")
        pid = input("Enter product ID: ").strip()
        try:
            self.cursor.execute("""
                SELECT pid, name, category, price, stock_count, descr
                FROM products WHERE pid = ?
            """, (pid,))
            
            product = self.cursor.fetchone()
            if not product:
                print("Product not found.")
                return
            pid, name, category, price, stock, descr = product
            
            print("\n" + "="*60)
            print(f"Product ID: {pid}")
            print(f"Name: {name}")
            print(f"Category: {category}")
            print(f"Price: ${price:.2f}")
            print(f"Stock: {stock}")
            print(f"Description: {descr}")
            print("="*60)

            print("\n1. Update price")
            print("2. Update stock")
            print("3. Back")
            
            choice = input("Enter choice: ").strip()
            if choice == '1':
                try:
                    new_price = float(input("Enter new price: ").strip())
                    if new_price <= 0:
                        print("Price must be positive.")
                        return
                    
                    self.cursor.execute("""
                        UPDATE products SET price = ? WHERE pid = ?
                    """, (new_price, pid))
                    self.conn.commit()
                    print("Price updated successfully!")
                    
                except ValueError:
                    print("Invalid price.")
            elif choice == '2':
                try:
                    new_stock = int(input("Enter new stock count: ").strip())
                    if new_stock < 0:
                        print("Stock must be non-negative.")
                        return
                    
                    self.cursor.execute("""
                        UPDATE products SET stock_count = ? WHERE pid = ?
                    """, (new_stock, pid))
                    self.conn.commit()
                    print("Stock updated successfully!")
                except ValueError:
                    print("Invalid stock count.")
                    
        except sqlite3.Error as e:
            print(f"Error managing products: {e}")
            self.conn.rollback()
    
    def sales_report(self):
        """Generate weekly sales report"""
        print("\n--- WEEKLY SALES REPORT ---")
        print("Last 7 days")
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        try:
            # distinct orders
            self.cursor.execute("""
                SELECT COUNT(DISTINCT ono)
                FROM orders
                WHERE odate >= ?
            """, (seven_days_ago,))
            num_orders = self.cursor.fetchone()[0]
            
            #Number of distinct products sold
            self.cursor.execute("""
                SELECT COUNT(DISTINCT ol.pid)
                FROM orders o
                JOIN orderlines ol ON o.ono = ol.ono
                WHERE o.odate >= ?
            """, (seven_days_ago,))
            num_products = self.cursor.fetchone()[0]
            #distinct customers
            self.cursor.execute("""
                SELECT COUNT(DISTINCT cid)
                FROM orders
                WHERE odate >= ?
            """, (seven_days_ago,))
            num_customers = self.cursor.fetchone()[0]
            # sales amount
            self.cursor.execute("""
                SELECT COALESCE(SUM(ol.qty * ol.uprice), 0)
                FROM orders o
                JOIN orderlines ol ON o.ono = ol.ono
                WHERE o.odate >= ?
            """, (seven_days_ago,))
            total_sales = self.cursor.fetchone()[0]
            avg_per_customer = total_sales / num_customers if num_customers > 0 else 0
            
            print("\n" + "="*50)
            print(f"Number of Orders:       {num_orders}")
            print(f"Products Sold:          {num_products}")
            print(f"Customers:              {num_customers}")
            print(f"Total Sales:            ${total_sales:.2f}")
            print(f"Average per Customer:   ${avg_per_customer:.2f}")
            print("="*50)
            input("\nPress Enter to continue...")
            
        except sqlite3.Error as e:
            print(f"Error generating report: {e}")
    
    def top_products(self):
        """top-selling products"""
        print("\n--- TOP SELLING PRODUCTS ---")
        try:
            print("\nTop 3 Products by Orders:")
            print("-" * 60)
            
            self.cursor.execute("""
                SELECT p.pid, p.name, COUNT(DISTINCT ol.ono) as order_count
                FROM products p
                JOIN orderlines ol ON p.pid = ol.pid
                GROUP BY p.pid, p.name
                ORDER BY order_count DESC
                LIMIT 3
            """)
            top_by_orders = self.cursor.fetchall()
            if not top_by_orders:
                print("No data available.")
            else:
                #ties at position 3
                if len(top_by_orders) == 3:
                    third_count = top_by_orders[2][2]
                    # Get all products with same count as 3rd place
                    self.cursor.execute("""
                        SELECT p.pid, p.name, COUNT(DISTINCT ol.ono) as order_count
                        FROM products p
                        JOIN orderlines ol ON p.pid = ol.pid
                        GROUP BY p.pid, p.name
                        HAVING order_count >= ?
                        ORDER BY order_count DESC
                    """, (third_count,))
                    
                    top_by_orders = self.cursor.fetchall()
                rank = 1
                for pid, name, count in top_by_orders:
                    print(f"{rank}. {name} (PID: {pid}) - {count} orders")
                    rank += 1
            print("\nTop 3 Products by Views:")
            print("-" * 60)
            
            self.cursor.execute("""
                SELECT p.pid, p.name, COUNT(*) as view_count
                FROM products p
                JOIN viewedProduct v ON p.pid = v.pid
                GROUP BY p.pid, p.name
                ORDER BY view_count DESC
                LIMIT 3
            """)
            
            top_by_views = self.cursor.fetchall()
            
            if not top_by_views:
                print("No data available.")
            else:
                #ties at position 3
                if len(top_by_views) == 3:
                    third_count = top_by_views[2][2]
                    
                    self.cursor.execute("""
                        SELECT p.pid, p.name, COUNT(*) as view_count
                        FROM products p
                        JOIN viewedProduct v ON p.pid = v.pid
                        GROUP BY p.pid, p.name
                        HAVING view_count >= ?
                        ORDER BY view_count DESC
                    """, (third_count,))
                    
                    top_by_views = self.cursor.fetchall()
                
                rank = 1
                for pid, name, count in top_by_views:
                    print(f"{rank}. {name} (PID: {pid}) - {count} views")
                    rank += 1
            input("\nPress Enter to continue...")
            
        except sqlite3.Error as e:
            print(f"Error fetching top products: {e}")
    
    def paginate_results(self, results, display_func, detail_func):
        """Generic pagination for results"""
        page = 0
        page_size = 5
        total_pages = (len(results) + page_size - 1) // page_size
        while True:
            start = page * page_size
            end = min(start + page_size, len(results))
            
            print(f"\nPage {page + 1} of {total_pages}")
            print("-" * 70)
            
            for i, result in enumerate(results[start:end], start=1):
                print(f"{start + i}.", end=" ")
                display_func(result)
            
            print("-" * 70)
            print("n: Next | p: Previous | #: Select item | b: Back")
            
            choice = input("Enter choice: ").strip().lower()
            
            if choice == 'n' and page < total_pages - 1:
                page += 1
            elif choice == 'p' and page > 0:
                page -= 1
            elif choice == 'b':
                break
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    detail_func(results[idx])
                else:
                    print("Invalid selection.")
            else:
                print("Invalid choice.")
    
    def run(self):
        """Main application loop"""
        self.connect()
        try:
            while True:
                if not self.login_screen():
                    break
                
                if self.current_role == 'customer':
                    self.customer_menu()
                elif self.current_role == 'sales':
                    self.sales_menu()
                #Reset user
                self.current_user = None
                self.current_role = None
                self.session_no = None
                
        finally:
            self.close()
def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <database_file>")
        sys.exit(1)
    
    db_name = sys.argv[1]
    system = ECommerceSystem(db_name)
    system.run()
if __name__ == "__main__":
    main()
