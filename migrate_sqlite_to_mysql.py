import os
import sqlite3
import sys

from sqlalchemy import create_engine, text


SOURCE_DB = os.path.join(os.path.dirname(__file__), 'pythonanywhere_laundry_backup.db')


def main():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print('Greška: DATABASE_URL nije postavljen.')
        sys.exit(1)

    if not os.path.isfile(SOURCE_DB):
        print(f'Greška: Ne postoji fajl {SOURCE_DB}')
        sys.exit(1)

    source = sqlite3.connect(SOURCE_DB)
    source.row_factory = sqlite3.Row
    try:
        users = source.execute(
            'SELECT id, username, password FROM "user" ORDER BY id'
        ).fetchall()
        bookings = source.execute(
            'SELECT id, user_id, time_slot, date FROM booking ORDER BY id'
        ).fetchall()
    finally:
        source.close()

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text('''
            CREATE TABLE IF NOT EXISTS `user` (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(150) NOT NULL
            )
        '''))
        connection.execute(text('''
            CREATE TABLE IF NOT EXISTS booking (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                user_id INTEGER NOT NULL,
                time_slot VARCHAR(50) NOT NULL,
                date VARCHAR(50) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES `user` (id)
            )
        '''))

        existing_users = connection.execute(
            text('SELECT COUNT(*) FROM `user`')
        ).scalar_one()
        existing_bookings = connection.execute(
            text('SELECT COUNT(*) FROM booking')
        ).scalar_one()
        if existing_users or existing_bookings:
            raise RuntimeError(
                'MySQL baza već sadrži podatke; migracija je zaustavljena.'
            )

        for user in users:
            connection.execute(
                text(
                    'INSERT INTO `user` (id, username, password) '
                    'VALUES (:id, :username, :password)'
                ),
                {key: user[key] for key in user.keys()},
            )
        for booking in bookings:
            connection.execute(
                text(
                    'INSERT INTO booking (id, user_id, time_slot, date) '
                    'VALUES (:id, :user_id, :time_slot, :date)'
                ),
                {key: booking[key] for key in booking.keys()},
            )

    print(f'Migracija uspešna: {len(users)} korisnika i {len(bookings)} bookinga.')


if __name__ == '__main__':
    main()
