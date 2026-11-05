import os

from flask import Flask, abort, render_template, request, redirect, url_for, flash, session
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

# Initialize Flask app
app = Flask(__name__)

database_path = os.path.join(app.root_path, 'pythonanywhere_laundry_backup.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path.replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'local-development-key')

TRANSLATIONS = {
    'da': {
        'Laundry Booking System': 'Vaskeribestillingssystem',
        'Dark mode': 'MÃ¸rk tilstand',
        'Light mode': 'Lys tilstand',
        'Switch to dark mode': 'Skift til mÃ¸rk tilstand',
        'Switch to light mode': 'Skift til lys tilstand',
        'Dansk': 'Dansk',
        'English': 'Engelsk',
        'Home': 'Hjem',
        'Admin': 'Admin',
        'My bookings': 'Mine bookinger',
        'Book a slot': 'Book en tid',
        'Log in': 'Log ind',
        'Log out': 'Log ud',
        'Get started': 'Kom i gang',
        'Welcome back': 'Velkommen tilbage',
        'Log in to Thomas Laubs Gade 25 - 29': 'Log ind pÃ¥ Thomas Laubs Gade 25 - 29',
        'Your next easy laundry day is waiting.': 'Din nÃ¦ste nemme vaskedag venter.',
        'Username': 'Brugernavn',
        'Password': 'Adgangskode',
        'New here?': 'Ny her?',
        'Create an account': 'Opret en konto',
        'Start fresh': 'Start her',
        'Create your account': 'Opret din konto',
        'Save your slots and make laundry part of the plan.': 'Gem dine tider og gÃ¸r vaskedagen til en del af planen.',
        'Choose a username': 'VÃ¦lg et brugernavn',
        'Create a password': 'Opret en adgangskode',
        'Already registered?': 'Allerede registreret?',
        'Your laundry, on your schedule': 'Dit vasketÃ¸j, efter din tidsplan',
        'More time for life. Less time at the laundromat.': 'Mere tid til livet. Mindre tid i vaskeriet.',
        'Reserve a machine in seconds and keep your day moving.': 'ReservÃ©r en maskine pÃ¥ fÃ¥ sekunder, og fÃ¥ dagen til at fungere.',
        'Reserve a slot': 'ReservÃ©r en tid',
        'View my bookings': 'Se mine bookinger',
        'I already have an account': 'Jeg har allerede en konto',
        'Laundry booking overview': 'Oversigt over vaskeribestillinger',
        'UP NEXT': 'NÃ†STE',
        'Wash day, sorted.': 'Vaskedagen er planlagt.',
        'Choose a time that works for you.': 'VÃ¦lg et tidspunkt, der passer dig.',
        'Book in seconds': 'Book pÃ¥ fÃ¥ sekunder',
        'Pick a date and time without the back-and-forth.': 'VÃ¦lg dato og tid uden besvÃ¦r.',
        'Always in control': 'Altid overblik',
        'Keep every upcoming laundry slot in one clear place.': 'Hold styr pÃ¥ alle dine kommende vasketider Ã©t sted.',
        'Made for shared spaces': 'Skabt til fÃ¦lles omrÃ¥der',
        'Less waiting, fewer surprises, and a smoother routine.': 'Mindre ventetid, fÃ¦rre overraskelser og en nemmere hverdag.',
        'Simple. Clean. On time.': 'Enkelt. Rent. Til tiden.',
        'Your schedule': 'Din tidsplan',
        'Everything you have planned, at a glance.': 'Alt, hvad du har planlagt, samlet Ã©t sted.',
        'Book another slot': 'Book endnu en tid',
        'Confirmed': 'BekrÃ¦ftet',
        'Cancel': 'Annuller',
        'No bookings yet': 'Ingen bookinger endnu',
        'When you reserve a slot, it will show up here.': 'NÃ¥r du reserverer en tid, vises den her.',
        'Make your first booking': 'Lav din fÃ¸rste booking',
        'Plan ahead': 'PlanlÃ¦g i god tid',
        'Book your laundry slot': 'Book din vasketid',
        'Choose a day and a time that fits your routine.': 'VÃ¦lg en dag og et tidspunkt, der passer til din hverdag.',
        'Date': 'Dato',
        'Choose your hours': 'VÃ¦lg dine timer',
        'Select 1, 2 or 3 consecutive hours in one booking.': 'VÃ¦lg 1, 2 eller 3 sammenhÃ¦ngende timer i Ã©n booking.',
        'Confirm booking': 'BekrÃ¦ft booking',
        'Administration': 'Administration',
        'Admin dashboard': 'Admin-dashboard',
        'Registered users and their booking activity.': 'Registrerede brugere og deres bookingaktivitet.',
        'Registered users': 'Registrerede brugere',
        'registered user(s)': 'registreret(e) bruger(e)',
        'Bookings': 'Bookinger',
        'No users have registered yet.': 'Ingen brugere er registreret endnu.',
        'All bookings': 'Alle bookinger',
        'booking slot(s)': 'bookingtid(er)',
        'User': 'Bruger',
        'Time slot': 'Tidsrum',
        'Unknown user': 'Ukendt bruger',
        'No bookings have been made yet.': 'Der er ikke foretaget nogen bookinger endnu.',
        'That username is already registered. Please choose another one.': 'Dette brugernavn er allerede registreret. VÃ¦lg et andet.',
        'Choose between 1 and 3 hours.': 'VÃ¦lg mellem 1 og 3 timer.',
        'Please choose valid time slots.': 'VÃ¦lg gyldige tidsrum.',
        'Choose consecutive time slots.': 'VÃ¦lg sammenhÃ¦ngende tidsrum.',
        'You can book a maximum of 3 hours per day.': 'Du kan hÃ¸jst booke 3 timer om dagen.',
        'That booking could not be found.': 'Bookingen blev ikke fundet.',
        'Booking cancelled successfully.': 'Bookingen blev annulleret.',
    },
}

def translate_text(text):
    language = session.get('language', 'en')
    return TRANSLATIONS.get(language, {}).get(text, text)

@app.context_processor
def inject_translation():
    return {'_': translate_text, 'language': session.get('language', 'en')}

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

@app.route('/set-language/<language>', methods=['POST'])
def set_language(language):
    if language not in {'en', 'da'}:
        abort(400)

    session['language'] = language
    next_url = request.form.get('next') or url_for('home')
    if not next_url.startswith('/') or next_url.startswith('//'):
        next_url = url_for('home')
    return redirect(next_url)

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash(translate_text('That username is already registered. Please choose another one.'), 'error')
            return render_template('register.html')

        user = User(username=username, password=password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(translate_text('That username is already registered. Please choose another one.'), 'error')
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
            flash(translate_text('Choose between 1 and 3 hours.'), 'error')
            return render_template('book.html', time_slots=TIME_SLOTS)

        selected_indexes = []
        for selected_slot in selected_slots:
            slot_group = next(
                (group for group in CONSECUTIVE_SLOT_GROUPS if selected_slot in group),
                None,
            )
            if slot_group is None:
                flash(translate_text('Please choose valid time slots.'), 'error')
                return render_template('book.html', time_slots=TIME_SLOTS)
            selected_indexes.append((slot_group, slot_group.index(selected_slot)))

        groups = {id(group) for group, _ in selected_indexes}
        indexes = sorted(index for _, index in selected_indexes)
        if len(groups) != 1 or indexes != list(range(indexes[0], indexes[0] + len(indexes))):
            flash(translate_text('Choose consecutive time slots.'), 'error')
            return render_template('book.html', time_slots=TIME_SLOTS)

        existing_hours = Booking.query.filter_by(
            user_id=current_user.id,
            date=date,
        ).count()
        if existing_hours + len(selected_slots) > BOOKING_HOURS_PER_DAY:
            flash(translate_text('You can book a maximum of 3 hours per day.'), 'error')
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
        flash(translate_text('That booking could not be found.'), 'error')
        return redirect(url_for('view_bookings'))

    db.session.delete(booking)
    db.session.commit()
    flash(translate_text('Booking cancelled successfully.'), 'success')
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
