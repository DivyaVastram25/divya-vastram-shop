import os
import json
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

PRODUCTS_FILE = 'products.json'
DELIVERY = 59  # delivery charge

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
        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']
        existing = next((item for item in cart if item['sku'] == sku), None)
        if existing:
            existing['quantity'] += quantity
        else:
            cart.append({
                'sku': product['sku'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'quantity': quantity
            })
        session.modified = True

    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    total = subtotal + (DELIVERY if cart else 0)
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
    sku = request.form['sku']
    session['cart'] = [item for item in session.get('cart', []) if item['sku'] != sku]
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)
