import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

PRODUCTS_FILE = 'products.json'
EXCEL_FILE = 'orders.xlsx'
DELIVERY = 59  # fixed delivery charge

if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(columns=[
        'Order ID', 'Name', 'Phone', 'Address', 'Pincode',
        'Items', 'Subtotal', 'Delivery', 'Total', 'Date', 'Payment Screenshot'
    ])
    df_init.to_excel(EXCEL_FILE, index=False)

@app.route('/')
def index():
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    return render_template('index.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    sku = request.form['sku']
    quantity = int(request.form.get('quantity', 1))
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    product = next((p for p in products if p['sku'] == sku), None)
    if product:
        cart = session.setdefault('cart', [])
        existing = next((item for item in cart if item['sku'] == sku), None)
        if existing:
            existing['quantity'] += quantity
        else:
            product['quantity'] = quantity
            cart.append(product)
        session.modified = True
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    subtotal = sum(p['price'] * p.get('quantity', 1) for p in cart)
    total = subtotal + DELIVERY if cart else 0
    return render_template('cart.html', cart=cart, subtotal=subtotal, delivery=DELIVERY if cart else 0, total=total)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    sku = request.form['sku']
    quantity = int(request.form['quantity'])
    for item in session.get('cart', []):
        if item['sku'] == sku:
            item['quantity'] = quantity
            break
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_item', methods=['POST'])
def remove_item():
    idx = int(request.form['index'])
    session['cart'].pop(idx)
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        session['order_info'] = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'address': request.form['address'],
            'pincode': request.form['pincode'],
        }
        return redirect(url_for('payment'))
    return render_template('checkout.html')
@app.route('/add_to_cart_restore', methods=['POST'])
def add_to_cart_restore():
    data = request.get_json()
    cart_data = data.get('cart', [])
    session['cart'] = []

    with open(PRODUCTS_FILE) as f:
        products = json.load(f)

    for item in cart_data:
        p = next((prod for prod in products if prod['sku'] == item['sku']), None)
        if p:
            p['quantity'] = item.get('quantity', 1)
            session['cart'].append(p)

    session.modified = True
    return '', 204

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    cart = session.get('cart', [])
    order_info = session.get('order_info')

    if not cart or not order_info:
        if request.method == 'POST':
            name = request.form.get('name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            pincode = request.form.get('pincode')

            if not all([name, phone, address, pincode]):
                return "<h3>Session expired. Please go back and fill the checkout form again.</h3>"

            order_info = {
                'name': name,
                'phone': phone,
                'address': address,
                'pincode': pincode
            }

            cart = session.get('cart', [])
            if not cart:
                return "<h3>Cart is empty. Please add products again.</h3>"

        else:
            return redirect(url_for('checkout'))

    subtotal = sum(p['price'] * p.get('quantity', 1) for p in cart)
    total = subtotal + DELIVERY

    if request.method == 'POST':
        screenshot = request.files.get('screenshot')
        if not screenshot or screenshot.filename == '':
            return "<h3>Please upload a screenshot before proceeding.</h3><a href='/payment'>Go back</a>"

        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ext = os.path.splitext(screenshot.filename)[1]
        screenshot_filename = f"{order_id}{ext}"
        screenshot_folder = os.path.join('static', 'payments')
        os.makedirs(screenshot_folder, exist_ok=True)
        screenshot_path = os.path.join(screenshot_folder, screenshot_filename)
        screenshot.save(screenshot_path)

        payment_proof_path = f"static/payments/{screenshot_filename}"
        items = ', '.join(f"{p['name']} (₹{p['price']} x {p.get('quantity', 1)})" for p in cart)
        date = datetime.now().strftime('%Y-%m-%d %H:%M')

        record = {
            'Order ID': order_id,
            'Name': order_info['name'],
            'Phone': order_info['phone'],
            'Address': order_info['address'],
            'Pincode': order_info['pincode'],
            'Items': items,
            'Subtotal': subtotal,
            'Delivery': DELIVERY,
            'Total': total,
            'Date': date,
            'Payment Screenshot': payment_proof_path
        }

        df = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)

        session.pop('cart', None)
        session.pop('order_info', None)

        return render_template('thankyou.html', order_id=order_id, total=total)

    return render_template('payment.html', total=total)

@app.route('/download_orders')
def download_orders():
    return send_file(EXCEL_FILE, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)