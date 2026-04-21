from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            items TEXT,
            total INTEGER
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- DATA ----------------
restaurants = {
    "pizza": {
        "name": "Aminas palace",
        "menu": [
            {
                "name": "Margherita",
                "price": 8,
                "image": "https://images.unsplash.com/photo-1600891964599-f61ba0e24092"
            },
            {
                "name": "Pepperoni",
                "price": 10,
                "image": "https://images.unsplash.com/photo-1594007654729-407eedc4be65"
            },
        ]
    },
    "burger": {
        "name": "Royal Burgers",
        "menu": [
            {
                "name": "Cheeseburger",
                "price": 6,
                "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd"
            },
            {
                "name": "Fries",
                "price": 3,
                "image": "https://images.unsplash.com/photo-1576107232684-1279f390859f"
            },
        ]
    }
}

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template("home.html", restaurants=restaurants)


@app.route('/menu/<restaurant>')
def menu(restaurant):
    selected = restaurants.get(restaurant)

    cart = session.get('cart', [])
    total = sum(int(item['price']) * int(item.get('qty', 1)) for item in cart)

    cart_lookup = {item['name']: item.get('qty', 1) for item in cart}

    return render_template(
        "menu.html",
        restaurant=selected,
        total=total,
        cart_lookup=cart_lookup
    )


# ---------------- ADD TO CART (NORMAL) ----------------
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_name = request.form['name']
    item_price = int(request.form['price'])

    if 'cart' not in session:
        session['cart'] = []

    for item in session['cart']:
        if item['name'] == item_name:
            item['qty'] = item.get('qty', 1) + 1
            session.modified = True
            return redirect(request.referrer)

    session['cart'].append({
        'name': item_name,
        'price': item_price,
        'qty': 1
    })

    session.modified = True
    return redirect(request.referrer)


# ---------------- ADD TO CART (AJAX) ----------------
@app.route('/add_to_cart_ajax', methods=['POST'])
def add_to_cart_ajax():
    data = request.get_json()
    name = data['name']
    price = int(data['price'])

    cart = session.get('cart', [])

    found = False
    for item in cart:
        if item['name'] == name:
            item['qty'] = item.get('qty', 1) + 1
            found = True
            break

    if not found:
        cart.append({'name': name, 'price': price, 'qty': 1})

    session['cart'] = cart
    session.modified = True

    return jsonify({"status": "success",
                    "cart": session['cart']})


# ---------------- CART PAGE ----------------
@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    total = sum(int(item['price']) * int(item.get('qty', 1)) for item in cart)

    return render_template("cart.html", cart=cart, total=total)


# ---------------- REMOVE ITEM ----------------
@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):
    if 'cart' in session:
        session['cart'].pop(index)
        session.modified = True
    return redirect('/cart')


# ---------------- INCREASE (CART PAGE) ----------------
@app.route('/increase/<int:index>')
def increase(index):
    if 'cart' in session:
        session['cart'][index]['qty'] = session['cart'][index].get('qty', 1) + 1
        session.modified = True
    return redirect('/cart')


# ---------------- DECREASE (CART PAGE) ----------------
@app.route('/decrease/<int:index>')
def decrease(index):
    if 'cart' in session:
        if session['cart'][index]['qty'] > 1:
            session['cart'][index]['qty'] -= 1
        else:
            session['cart'].pop(index)
        session.modified = True
    return redirect('/cart')


# ---------------- INCREASE (MENU PAGE) ----------------
@app.route('/increase_item/<name>')
def increase_item(name):
    for item in session.get('cart', []):
        if item['name'] == name:
            item['qty'] = item.get('qty', 1) + 1
            session.modified = True
            break
    return redirect(request.referrer)


# ---------------- DECREASE (MENU PAGE) ----------------
@app.route('/decrease_item/<name>')
def decrease_item(name):
    for item in session.get('cart', []):
        if item['name'] == name:
            if item['qty'] > 1:
                item['qty'] -= 1
            else:
                session['cart'].remove(item)
            session.modified = True
            break
    return redirect(request.referrer)


# ---------------- CHECKOUT ----------------
@app.route('/checkout')
def checkout():
    cart = session.get('cart', [])
    total = sum(int(item['price']) * int(item.get('qty', 1)) for item in cart)

    return render_template("checkout.html", cart=cart, total=total)


# ---------------- PLACE ORDER ----------------
@app.route('/place_order', methods=['POST'])
def place_order():
    cart = session.get('cart', [])
    total = sum(int(item['price']) * int(item.get('qty', 1)) for item in cart)

    conn = sqlite3.connect('orders.db')
    c = conn.cursor()

    c.execute(
        "INSERT INTO orders (items, total) VALUES (?, ?)",
        (str(cart), total)
    )

    conn.commit()
    conn.close()

    session.pop('cart', None)

    return render_template("success.html")


# ---------------- VIEW ORDERS ----------------
@app.route('/orders')
def view_orders():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()

    c.execute("SELECT * FROM orders")
    orders = c.fetchall()

    conn.close()

    return str(orders)


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)