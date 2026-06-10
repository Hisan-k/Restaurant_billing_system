import mysql.connector
from decimal import Decimal
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# ---------- DB CONNECTION ----------
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="",
    database="restaurant_db"
)
cursor = conn.cursor()

order_id_global = None


# ---------- SAFE IMAGE LOADER ----------
def set_background(win, image_path, fallback_color):
    try:
        img = Image.open(image_path)
        img = img.resize((1500, 800))
        bg = ImageTk.PhotoImage(img)

        label = tk.Label(win, image=bg)
        label.place(x=0, y=0, relwidth=1, relheight=1)
        label.image = bg
    except:
        win.configure(bg=fallback_color)


# ---------- RESET ----------
def new_customer(win):
    global order_id_global
    order_id_global = None
    win.destroy()
    customer_interface()


# ---------- INTERFACE 1 ----------
def open_order_window():
    global order_id_global

    name = entry_name.get()
    phone = entry_phone.get()

    if not name or not phone:
        messagebox.showerror("Error", "Enter all details!")
        return

    cursor.execute("INSERT INTO Customers (name, phone) VALUES (%s,%s)", (name, phone))
    conn.commit()
    cust_id = cursor.lastrowid

    cursor.execute("INSERT INTO Orders (customer_id, table_no) VALUES (%s,%s)", (cust_id, 1))
    conn.commit()
    order_id_global = cursor.lastrowid

    root.destroy()
    order_interface()


def customer_interface():
    global root, entry_name, entry_phone

    root = tk.Tk()
    root.title("Billing System")
    root.state("zoomed")

    # Background
    set_background(root, "restaurant_bg.png", "#f8e1e7")

    tk.Label(root, text="BILLING SYSTEM",
             font=("Arial", 28, "bold"),
             bg="#000000", fg="white").pack(pady=20)

    tk.Label(root, text="Customer Details",
             font=("Arial", 20),
             bg="#000000", fg="yellow").pack()

    frame = tk.Frame(root, bg="white", bd=3)
    frame.pack(pady=40)

    tk.Label(frame, text="Name", font=("Arial", 16)).grid(row=0, column=0, padx=20, pady=15)
    entry_name = tk.Entry(frame, font=("Arial", 16))
    entry_name.grid(row=0, column=1)

    tk.Label(frame, text="Phone No", font=("Arial", 16)).grid(row=1, column=0, padx=20, pady=15)
    entry_phone = tk.Entry(frame, font=("Arial", 16))
    entry_phone.grid(row=1, column=1)

    tk.Button(frame, text="Create Order", bg="#ffb3c6",
              command=open_order_window).grid(row=2, column=1, pady=20, sticky="e")

    root.mainloop()


# ---------- INTERFACE 2 ----------
def show_menu(text):
    cursor.execute("SELECT * FROM Menu")
    items = cursor.fetchall()

    text.delete("1.0", tk.END)
    text.insert(tk.END, "========= MENU =========\n\n")
    text.insert(tk.END, "ID   ITEM NAME        PRICE\n")
    text.insert(tk.END, "-------------------------------\n")

    for item in items:
        text.insert(tk.END, f"{item[0]:<4} {item[1]:<15} ₹{item[2]}\n")


def add_item(entry_item, entry_qty):
    try:
        item_id = int(entry_item.get())
        qty = int(entry_qty.get())
    except:
        messagebox.showerror("Error", "Invalid input!")
        return

    cursor.execute("SELECT price FROM Menu WHERE item_id=%s", (item_id,))
    price = cursor.fetchone()

    if not price:
        messagebox.showerror("Error", "Invalid Item!")
        return

    subtotal = Decimal(price[0]) * qty

    cursor.execute(
        "INSERT INTO Order_Items (order_id, item_id, quantity, subtotal) VALUES (%s,%s,%s,%s)",
        (order_id_global, item_id, qty, subtotal)
    )
    conn.commit()

    messagebox.showinfo("Success", "Item Added!")


def kitchen_view(text):
    cursor.execute("""
        SELECT m.item_name, oi.quantity
        FROM Order_Items oi
        JOIN Menu m ON oi.item_id = m.item_id
        WHERE oi.order_id=%s
    """, (order_id_global,))

    items = cursor.fetchall()

    text.delete("1.0", tk.END)
    text.insert(tk.END, "------ KITCHEN VIEW ------\n\n")

    for i in items:
        text.insert(tk.END, f"{i[0]:<15} x {i[1]}\n")


def proceed(win):
    win.destroy()
    payment_interface()


def order_interface():
    win = tk.Tk()
    win.title("Order")
    win.state("zoomed")

    # SAME BACKGROUND IMAGE
    set_background(win, "restaurant_bg.png", "#e6d6f5")

    tk.Label(win, text="ORDER DETAILS",
             font=("Arial", 26, "bold"),
             bg="#000000", fg="white").pack(pady=20)

    frame = tk.Frame(win, bg="white", bd=3)
    frame.pack(pady=20)

    tk.Label(frame, text="Item ID").grid(row=0, column=0, padx=20, pady=10)
    entry_item = tk.Entry(frame)
    entry_item.grid(row=0, column=1)

    tk.Label(frame, text="Quantity").grid(row=1, column=0, padx=20, pady=10)
    entry_qty = tk.Entry(frame)
    entry_qty.grid(row=1, column=1)

    tk.Button(frame, text="Add Item", bg="#cdb4db",
              command=lambda: add_item(entry_item, entry_qty)).grid(row=2, column=1, pady=10)

    text = tk.Text(win, height=15, width=80)
    text.pack(pady=20)

    tk.Button(win, text="Show Menu", command=lambda: show_menu(text)).pack()
    tk.Button(win, text="Kitchen View", command=lambda: kitchen_view(text)).pack()

    tk.Button(win, text="Proceed", bg="#a3f7bf",
              command=lambda: proceed(win)).pack(pady=20)

    win.mainloop()


# ---------- INTERFACE 3 ----------
def generate_bill():
    cursor.execute("""
        SELECT m.item_name, oi.quantity, m.price
        FROM Order_Items oi
        JOIN Menu m ON oi.item_id = m.item_id
        WHERE oi.order_id=%s
    """, (order_id_global,))

    items = cursor.fetchall()

    total = Decimal('0')
    for name, qty, price in items:
        total += Decimal(price) * qty

    gst = total * Decimal('0.05')
    final = total + gst

    cursor.execute(
        "INSERT INTO Bills (order_id, total_amount, gst, final_amount) VALUES (%s,%s,%s,%s)",
        (order_id_global, total, gst, final)
    )
    conn.commit()

    messagebox.showinfo("Bill", f"Final Amount = ₹{final}")


def view_bill(text, mode):
    cursor.execute("""
        SELECT c.name, c.phone
        FROM Customers c
        JOIN Orders o ON c.customer_id = o.customer_id
        WHERE o.order_id=%s
    """, (order_id_global,))
    cust = cursor.fetchone()

    cursor.execute("""
        SELECT m.item_name, oi.quantity, m.price
        FROM Order_Items oi
        JOIN Menu m ON oi.item_id = m.item_id
        WHERE oi.order_id=%s
    """, (order_id_global,))
    items = cursor.fetchall()

    text.delete("1.0", tk.END)
    text.insert(tk.END, "========== BILL ==========\n\n")
    text.insert(tk.END, f"Name: {cust[0]}\nPhone: {cust[1]}\n")
    text.insert(tk.END, f"Payment: {mode.get()}\n\n")

    total = Decimal('0')
    for i in items:
        subtotal = i[1] * Decimal(i[2])
        text.insert(tk.END, f"{i[0]:<15} x {i[1]} = ₹{subtotal}\n")
        total += subtotal

    gst = total * Decimal('0.05')
    final = total + gst

    text.insert(tk.END, f"\nTotal: ₹{total}\nGST: ₹{gst}\nFinal: ₹{final}")


def payment_interface():
    win = tk.Tk()
    win.title("Payment")
    win.state("zoomed")

    # DIFFERENT IMAGE
    set_background(win, "payment.png", "#d8f3dc")

    tk.Label(win, text="PAYMENT",
             font=("Arial", 26, "bold"),
             bg="#000000", fg="white").pack(pady=20)

    mode = tk.StringVar(value="Cash")

    frame = tk.Frame(win, bg="white", bd=3)
    frame.pack(pady=20)

    tk.Radiobutton(frame, text="Cash", variable=mode, value="Cash").grid(row=0, column=0)
    tk.Radiobutton(frame, text="UPI", variable=mode, value="UPI").grid(row=0, column=1)

    text = tk.Text(win, height=15, width=80)
    text.pack(pady=20)

    tk.Button(win, text="Generate Bill", command=generate_bill).pack()
    tk.Button(win, text="View Bill", command=lambda: view_bill(text, mode)).pack()

    tk.Button(win, text="New Customer", bg="#ffadad",
              command=lambda: new_customer(win)).pack(pady=20)

    win.mainloop()


# ---------- START ----------
customer_interface()