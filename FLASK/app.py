from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = 'your_secret_key'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/your_db_name'
mongo = PyMongo(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
        notes = list(mongo.db.notes.find({'username': username}))
        return render_template('home.html', username=username, notes=notes)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your credentials.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if mongo.db.users.find_one({'username': username}):
            flash('Username already exists.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            mongo.db.users.insert_one({'username': username, 'password': hashed_password})
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_note', methods=['POST'])
def add_note():
    if 'username' in session:
        username = session['username']
        title = request.form['title']
        content = request.form['content']
        mongo.db.notes.insert_one({'username': username, 'title': title, 'content': content})
        flash('Note added successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/edit_note/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if 'username' in session:
        note = mongo.db.notes.find_one({'_id': ObjectId(note_id)})
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            mongo.db.notes.update_one({'_id': ObjectId(note_id)}, {'$set': {'title': title, 'content': content}})
            flash('Note updated successfully!', 'success')
            return redirect(url_for('home'))
        return render_template('edit_note.html', note=note)
    return redirect(url_for('login'))

@app.route('/delete_note/<note_id>', methods=['POST'])
def delete_note(note_id):
    if 'username' in session:
        mongo.db.notes.delete_one({'_id': ObjectId(note_id)})
        flash('Note deleted successfully!', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Verify MongoDB connection before running the app
    try:
        db = mongo.cx['your_db_name']
        logging.debug("Connected to MongoDB, database: %s", db.name)
    except Exception as e:
        logging.error("Failed to connect to MongoDB: %s", e)
    
    app.run(debug=True)
