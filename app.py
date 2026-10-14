from flask import Flask, render_template, request, redirect, url_for, flash
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
CONSECUTIVE_SLOT_GROUPS = [
    TIME_SLOTS[:8],
    TIME_SLOTS[8:],
]
BOOKABLE_START_SLOTS = [
    slot
    for group in CONSECUTIVE_SLOT_GROUPS
    for slot in group[:-BOOKING_HOURS_PER_DAY + 1]
]

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laundry_booking.db'
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
        time_slot = request.form.get('time_slot')
        date = request.form.get('date')
        selected_group = next(
            (group for group in CONSECUTIVE_SLOT_GROUPS if time_slot in group),
            None,
        )
        if selected_group is None or time_slot not in BOOKABLE_START_SLOTS:
            flash('Please choose a valid time slot.', 'error')
            return render_template(
                'book.html',
                time_slots=BOOKABLE_START_SLOTS,
            )

        start_index = selected_group.index(time_slot)
        selected_slots = selected_group[
            start_index:start_index + BOOKING_HOURS_PER_DAY
        ]
        if len(selected_slots) != BOOKING_HOURS_PER_DAY:
            flash('Choose a starting time with three consecutive available hours.', 'error')
            return render_template(
                'book.html',
                time_slots=BOOKABLE_START_SLOTS,
            )

        existing_hours = Booking.query.filter_by(
            user_id=current_user.id,
            date=date,
        ).count()
        if existing_hours + BOOKING_HOURS_PER_DAY > BOOKING_HOURS_PER_DAY:
            flash('You can book a maximum of 3 hours per day.', 'error')
            return render_template(
                'book.html',
                time_slots=BOOKABLE_START_SLOTS,
            )

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
        time_slots=BOOKABLE_START_SLOTS,
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates all the tables in the database
    app.run(debug=True)
