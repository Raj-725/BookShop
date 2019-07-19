from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import unittest

class TestMethods(unittest.TestCase):

    def test_displayCategory(self):
        categoryId = '5'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = " + categoryId)
            data = connectionCursor.fetchall()
        conn.close()
        categoryName = data[0][4]
        self.assertEqual('Computer Science ',categoryName)

  
    def test_search(self):
        response = 'Computer Science'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute('SELECT productId, name, price, description, image, stock FROM products where description LIKE  ?', ('%'+response+'%',))
            itemData = connectionCursor.fetchall()  
        self.assertEqual(1,len(itemData))
    
    def test_productDescription(self):
        productId = '1'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ' + productId)
            productData = connectionCursor.fetchall()
        conn.close()
        self.assertEqual(1,len(productData))
    def test_addToCart(self):
        productId = '1'
        userId = '1'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT userId FROM users WHERE userId = "+userId)
            userId = connectionCursor.fetchone()[0]
            try:
                connectionCursor.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                response = "Request is completed successfully."
            except:
                conn.rollback()
                response = "Request is failed."
        conn.close()
        self.assertEqual(response,"Request is completed successfully.")
		
    def test_removeFromCart(self):
        productId = '1'
        userId = '1'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT userId FROM users WHERE userId = '" + userId + "'")
            userId = connectionCursor.fetchone()[0]
            try:
                connectionCursor.execute("DELETE FROM kart WHERE userId = " + str(userId) + " AND productId = " + str(productId))
                conn.commit()
                response = "Request is completed successfully."
            except:
                conn.rollback()
                response = "Request is failed."
        conn.close()
        self.assertEqual(response,"Request is completed successfully.")
		
    def test_viewProfile(self):
        userId = '1'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE userId = '" + userId + "'")
            profileData = connectionCursor.fetchall()
        conn.close()
        self.assertEqual(1,len(profileData))
		
    def test_invoicenum(self):
        invoice = '1563018123'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT invoicenum FROM orders WHERE invoicenum = '" + invoice + "'")
            inv = connectionCursor.fetchall()
        conn.close()
        self.assertEqual(1,len(inv))
		
    def test_feedback(self):
        name = 'saif'
        with sqlite3.connect('app.db') as conn:
            connectionCursor = conn.cursor()
            connectionCursor.execute("SELECT name FROM feedback WHERE name = '" + name + "'")
            d = connectionCursor.fetchall()
        conn.close()
        self.assertEqual(1,len(d))

       
if __name__ == '__main__':
    unittest.main()