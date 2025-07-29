import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Paths
PRODUCTS_FILE = 'products.json'
EXCEL_FILE = 'orders.xlsx'
IMAGE_FOLDER = 'static/product_images'

# Ensure Excel file exists with headers
if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=['Order ID', 'Name', 'Phone', 'Address', 'Pincode', 'Items', 'Total', 'Date'])
    df_init.to_excel(EXCEL_FILE, index=False)

@app.route('/')
def index():
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    return render_template('index.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    sku = request.form['sku']
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    product = next((p for p in products if p['sku'] == sku), None)
    if product:
        if 'cart' not in session:
            session['cart'] = []
        session['cart'].append(product)
        session.modified = True
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    return render_template('cart.html', cart=session.get('cart', []))

@app.route('/remove_item', methods=['POST'])
def remove_item():
    index = int(request.form['index'])
    if 'cart' in session:
        session['cart'].pop(index)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    pincode = request.form['pincode']
    cart = session.get('cart', [])
    if not cart:
        return redirect(url_for('index'))
    
    total = sum(p['price'] for p in cart)
    items = ', '.join([f"{p['name']} (₹{p['price']})" for p in cart])
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    date = datetime.now().strftime('%Y-%m-%d %H:%M')

    new_order = {
        'Order ID': order_id,
        'Name': name,
        'Phone': phone,
        'Address': address,
        'Pincode': pincode,
        'Items': items,
        'Total': total,
        'Date': date
    }

    df = pd.read_excel(EXCEL_FILE)
    df = df.append(new_order, ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)

    session.pop('cart', None)
    return render_template('thankyou.html', order_id=order_id, total=total)

@app.route('/download_orders')
def download_orders():
    return send_file(EXCEL_FILE, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)