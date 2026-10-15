import os

from flask import Flask, abort, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError

TIME_SLOTS = [
    '8:00 - 9:00 AM',
    '9:00 - 10:00 AM',
    '10:00 - 11:00 AM',
    '11:00 AM - 12:00 PM',
    '12:00 - 1:00 PM',
    '1:00 - 2:00 PM',
    '2:00 - 3:00 PM',
    '3:00 - 4:00 PM',
    '6:00 - 7:00 PM',
    '7:00 - 8:00 PM',
    '8:00 - 9:00 PM',
    '9:00 - 10:00 PM',
]
BOOKING_HOURS_PER_DAY = 3
ADMIN_USERNAME = 'bashky'
CONSECUTIVE_SLOT_GROUPS = [
    TIME_SLOTS[:8],
    TIME_SLOTS[8:],
]

# Initialize Flask app
app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'sqlite:///laundry_booking.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize Database and Flask-Login
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Define Booking model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_slot = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('That username is already registered. Please choose another one.', 'error')
            return render_template('register.html')

        user = User(username=username, password=password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('That username is already registered. Please choose another one.', 'error')
            return render_template('register.html')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Booking Route
@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        selected_slots = request.form.getlist('time_slots')
        date = request.form.get('date')

        if not selected_slots or len(selected_slots) > BOOKING_HOURS_PER_DAY:
            flash('Choose between 1 and 3 hours.', 'error')
            return render_template('book.html', time_slots=TIME_SLOTS)

        selected_indexes = []
        for selected_slot in selected_slots:
            slot_group = next(
                (group for group in CONSECUTIVE_SLOT_GROUPS if selected_slot in group),
                None,
            )
            if slot_group is None:
                flash('Please choose valid time slots.', 'error')
                return render_template('book.html', time_slots=TIME_SLOTS)
            selected_indexes.append((slot_group, slot_group.index(selected_slot)))

        groups = {id(group) for group, _ in selected_indexes}
        indexes = sorted(index for _, index in selected_indexes)
        if len(groups) != 1 or indexes != list(range(indexes[0], indexes[0] + len(indexes))):
            flash('Choose consecutive time slots.', 'error')
            return render_template('book.html', time_slots=TIME_SLOTS)

        existing_hours = Booking.query.filter_by(
            user_id=current_user.id,
            date=date,
        ).count()
        if existing_hours + len(selected_slots) > BOOKING_HOURS_PER_DAY:
            flash('You can book a maximum of 3 hours per day.', 'error')
            return render_template('book.html', time_slots=TIME_SLOTS)

        for selected_slot in selected_slots:
            db.session.add(Booking(
                user_id=current_user.id,
                time_slot=selected_slot,
                date=date,
            ))
        db.session.commit()
        return redirect(url_for('view_bookings'))
    return render_template(
        'book.html',
        time_slots=TIME_SLOTS,
    )

# View Bookings Route
@app.route('/view_bookings')
@login_required
def view_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
        Booking.date,
        Booking.id,
    ).all()
    return render_template('view_bookings.html', bookings=bookings)

# Cancel Booking Route
@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id,
    ).first()
    if booking is None:
        flash('That booking could not be found.', 'error')
        return redirect(url_for('view_bookings'))

    db.session.delete(booking)
    db.session.commit()
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('view_bookings'))

# Admin Dashboard Route
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != ADMIN_USERNAME:
        abort(403)

    users = User.query.order_by(User.username).all()
    bookings = Booking.query.order_by(Booking.date, Booking.id).all()
    usernames = {user.id: user.username for user in users}
    booking_counts = {}
    for booking in bookings:
        booking_counts[booking.user_id] = booking_counts.get(booking.user_id, 0) + 1
    return render_template(
        'admin_dashboard.html',
        users=users,
        bookings=bookings,
        usernames=usernames,
        booking_counts=booking_counts,
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates all the tables in the database
    app.run(debug=True)
