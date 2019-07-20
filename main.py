from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import time
app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def makeSignin():
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            connectionCursor.execute("SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            userId, firstName = connectionCursor.fetchone()
            connectionCursor.execute("SELECT count(productId) FROM kart WHERE userId = " + str(userId))
            noOfItems = connectionCursor.fetchone()[0]
    conn.close()
    return (loggedIn, firstName, noOfItems)

@app.route("/")
def root():
    loggedIn, firstName, noOfItems = makeSignin()
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute('SELECT productId, name, price, description, image, stock FROM products')
        itemData = connectionCursor.fetchall()
        connectionCursor.execute('SELECT categoryId, name FROM categories')
        categoryData = connectionCursor.fetchall()
    itemData = parse(itemData)   
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)

@app.route("/add")
def admin():
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT categoryId, name FROM categories")
        categories = connectionCursor.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)

@app.route("/displayCategory")
def displayCategory():
        loggedIn, firstName, noOfItems = makeSignin()
        categoryId = request.args.get("categoryId")
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = " + categoryId)
            data = connectionCursor.fetchall()
        conn.close()
        categoryName = data[0][4]
        data = parse(data)
        return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryName=categoryName)

@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = '" + session['email'] + "'")
        profileData = connectionCursor.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/account/card_details/edit")
def edit_card_details():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    card_details=get_card_details()
    return render_template("editCardDetails.html", loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, card_details=card_details)

@app.route("/account/update_card_details", methods=['GET','POST'])
def update_card_details():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = makeSignin()
    title = request.form['title']
    card_number = request.form['cardnumber']
    card_expiry = request.form['cardExpiry']
    save_card_details(title, card_number, card_expiry)
    card_details=get_card_details()
    status="Request is completed successfully" if card_details else "Request Failed!"
    return render_template("editCardDetails.html", loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, card_details=card_details, status=status)

@app.route("/account/profile/view")
def viewProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = '" + session['email'] + "'")
        profileData = connectionCursor.fetchone()
    conn.close()
    return render_template("viewProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = makeSignin()
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT userId, password FROM users WHERE email = '" + session['email'] + "'")
            userId, password = connectionCursor.fetchone()
            if (password == oldPassword):
                try:
                    connectionCursor.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                    conn.commit()
                    response="Request is completed successfully."
                except:
                    conn.rollback()
                    response = "Request is failed."
                return render_template("changePassword.html", response=response, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
            else:
                response = "Password is not valid."
        conn.close()
        return render_template("changePassword.html", response=response, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
    else:
        return render_template("changePassword.html",loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == 'POST':
        response = request.form['searchBox']
        loggedIn, firstName, noOfItems = makeSignin()
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute('SELECT productId, name, price, description, image, stock FROM products where description LIKE ? OR name LIKE ?', ('%'+response+'%','%'+response+'%'))
            itemData = connectionCursor.fetchall()
            connectionCursor.execute('SELECT categoryId, name FROM categories')
            categoryData = connectionCursor.fetchall()
        itemData = parse(itemData)   
        return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)

		
@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('app.db') as con:
                try:
                    connectionCursor = con.cursor()
                    connectionCursor.execute('UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?', (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))
                    con.commit()
                    response = "Request is completed successfully."
                except:
                    con.rollback()
                    response = "Request is failed."
        con.close()
        #return redirect(url_for('editProfile'))
        if 'email' not in session:
            return redirect(url_for('root'))
        loggedIn, firstName, noOfItems = makeSignin()
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = '" + session['email'] + "'")
            profileData = connectionCursor.fetchone()
        conn.close()
        return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,error=response)

@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid Email or Password. Please try again.'
            return render_template('login.html', error=error)

@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = makeSignin()
    productId = request.args.get('productId')
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ' + productId)
        productData = connectionCursor.fetchone()
    conn.close()
    return render_template("productDescription.html", data=productData, loggedIn = loggedIn, firstName = firstName, noOfItems = noOfItems)

@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
            userId = connectionCursor.fetchone()[0]
            try:
                connectionCursor.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                response = "Request is completed successfully."
            except:
                conn.rollback()
                response = "Request is failed."
        conn.close()
        return redirect(url_for('root'))

@app.route("/account/order")
def order():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = makeSignin()
    email = session['email']
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = connectionCursor.fetchone()[0]
        connectionCursor.execute("SELECT products.productId, products.name, products.price, products.image, strftime('%d/%m/%Y',orders.orderdate) as orderdate, orders.invoicenum FROM products, orders WHERE products.productId = orders.productId AND orders.userId = " + str(userId))
        products = connectionCursor.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("order.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = makeSignin()
    email = session['email']
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = connectionCursor.fetchone()[0]
        connectionCursor.execute("SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(userId))
        products = connectionCursor.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("cart.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = connectionCursor.fetchone()[0]
        try:
            connectionCursor.execute("DELETE FROM kart WHERE userId = " + str(userId) + " AND productId = " + str(productId))
            conn.commit()
            response = "Request is completed successfully."
        except:
            conn.rollback()
            response = "Request is failed."
    conn.close()
    return redirect(url_for('root'))

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    con = sqlite3.connect('app.db')
    connectionCursor = con.cursor()
    connectionCursor.execute('SELECT email, password FROM users')
    data = connectionCursor.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/checkout", methods=['GET','POST'])
def payment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = makeSignin()
    email = session['email']

    title = request.form['title']
    card_number = request.form['cardnumber']
    card_expiry = request.form['cardExpiry']
    card_cvc = request.form['cardCVC']
    save_card_details(title, card_number, card_expiry)

    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = connectionCursor.fetchone()[0]
        connectionCursor.execute("SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(userId))
        products = connectionCursor.fetchall()
    totalPrice = 0
    invoicenum = int(time.time())
    for row in products:
        totalPrice += row[2]
        print(row)
        connectionCursor.execute("INSERT INTO Orders (invoicenum,userId, productId) VALUES (?, ?,?)", (invoicenum,userId, row[0]))
        connectionCursor.execute("UPDATE products SET stock = stock-1 WHERE productId = ? AND stock > 0",(row[0],))
    connectionCursor.execute("DELETE FROM kart WHERE userId = " + str(userId))
    conn.commit()
    return render_template("checkout.html", products = products, invoicenum = invoicenum, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/paymentDetails", methods=['GET','POST'])
def paymentDetails():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    card_details = get_card_details()
    return render_template("paymentDetails.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, card_details=card_details)

@app.route("/contactus", methods=['GET','POST'])
def contactus():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    return render_template("contactus.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/sendsupport", methods=['GET','POST'])
def sendsupport():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = makeSignin()
    if request.method == 'POST':
        message = request.form['message']
        email = request.form['email']
        name = request.form['name']
        with sqlite3.connect('app.db') as con:
            try:
                connectionCursor = con.cursor()
                connectionCursor.execute('INSERT INTO feedback (name,email,message) VALUES (?, ?, ?)', (name,email,message))
                con.commit()
                response = "Request is completed successfully."
            except:
                con.rollback()
                response = "Request is failed."
        con.close()
        return render_template("message.html",error=response)
	
def validate(email):
    userId = -1
    with sqlite3.connect('app.db') as conn:
        connectionCursor = conn.cursor()
        connectionCursor.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = connectionCursor.fetchone()
    conn.close()
    return userId
	
@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        if (validate(email)) != None:
            return render_template("login.html", error="Email already exist.")
        else:
            with sqlite3.connect('app.db') as con:
                try:
                    connectionCursor = con.cursor()
                    connectionCursor.execute('INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, address1, address2, zipcode, city, state, country, phone))
                    con.commit()
                    response = "Request is completed successfully."
                except:
                    con.rollback()
                    response = "Request is failed."
            con.close()
            return render_template("login.html", error=response)

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans


def get_user_id():
    email=session['email']
    with sqlite3.connect('app.db') as con:
        connectionCursor = con.cursor()
        connectionCursor.execute("SELECT userId FROM users where email='" + email + "'")
        data = connectionCursor.fetchone()
        return data[0] if data else None


def save_card_details(title, card_number, card_expiry):
    user_id = get_user_id()
    card_details=get_card_details()
    with sqlite3.connect('app.db') as con:
        try:
            connectionCursor = con.cursor()
            if card_details:
                connectionCursor.execute(
                    'UPDATE card_details SET title = ?, card_number = ?, card_expiry = ? WHERE userId = ?',
                    (title, card_number, card_expiry, user_id)
                )
            else:
                connectionCursor.execute(
                    'INSERT INTO card_details (title, card_number, card_expiry, userId) VALUES (?, ?, ?, ?)',
                    (title, card_number, card_expiry, user_id)
                )

            con.commit()
        except:
            con.rollback()

def get_card_details():
    user_id = get_user_id()
    with sqlite3.connect('app.db') as con:
        connectionCursor = con.cursor()
        connectionCursor.execute("SELECT title,card_number,card_expiry FROM card_details where userId='" + str(user_id) + "'")
        data = connectionCursor.fetchone()
        card_details = {'cardholder_name': data[0], 'card_number': data[1], 'card_expiry': data[2]} if data else None
        return card_details


if __name__ == '__main__':
    app.run(debug=True)
