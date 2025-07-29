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
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    product = next((p for p in products if p['sku']==sku), None)
    if product:
        session.setdefault('cart', []).append(product)
        session.modified = True
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    subtotal = sum(p['price'] for p in cart)
    total = subtotal + DELIVERY if cart else 0
    return render_template('cart.html', cart=cart, subtotal=subtotal, delivery=DELIVERY if cart else 0, total=total)

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

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    cart = session.get('cart', [])
    if not cart or 'order_info' not in session:
        return redirect(url_for('index'))

    subtotal = sum(p['price'] for p in cart)
    total = subtotal + DELIVERY

    if request.method == 'POST':
        # Check screenshot upload
        screenshot = request.files.get('screenshot')
        if not screenshot or screenshot.filename == '':
            return "<h3>Please upload a screenshot before proceeding.</h3><a href='/payment'>Go back</a>"

        # Create order ID
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ext = os.path.splitext(screenshot.filename)[1]
        screenshot_filename = f"{order_id}{ext}"

        # Save screenshot to static/payments/
        screenshot_folder = os.path.join('static', 'payments')
        os.makedirs(screenshot_folder, exist_ok=True)
        screenshot_path = os.path.join(screenshot_folder, screenshot_filename)
        screenshot.save(screenshot_path)

        # Relative path or full URL
        payment_proof_path = f"static/payments/{screenshot_filename}"

        # Save order details
        info = session.pop('order_info')
        items = ', '.join(f"{p['name']} (₹{p['price']})" for p in cart)
        date = datetime.now().strftime('%Y-%m-%d %H:%M')
        record = {
            'Order ID': order_id,
            'Name': info['name'],
            'Phone': info['phone'],
            'Address': info['address'],
            'Pincode': info['pincode'],
            'Items': items,
            'Subtotal': subtotal,
            'Delivery': DELIVERY,
            'Total': total,
            'Date': date,
            'Payment Screenshot': payment_proof_path  # ✅ New column
        }

        # Write to Excel
        df = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)

        session.pop('cart', None)
        return render_template('thankyou.html', order_id=order_id, total=total)

    return render_template('payment.html', total=total)



@app.route('/download_orders')
def download_orders():
    return send_file(EXCEL_FILE, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
