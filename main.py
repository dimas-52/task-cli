#!/usr/bin/env python3
import argparse
import sqlite3
import time
import os

def db_init():
    db_path = os.path.expanduser("~/.local/share/tas/tas.db")
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    db = sqlite3.connect(db_path)
    c = db.cursor()

    c.execute("PRAGMA foreign_keys = ON")

    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, created_at INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("""
    CREATE TABLE IF NOT EXISTS main (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        category_id INTEGER,
        content TEXT,
        remind_at INTEGER,
        is_done BOOLEAN,
        created_at INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        current_user_id INTEGER,
        FOREIGN KEY (current_user_id) REFERENCES users(id)
    )
    """)

    # c.execute("INSERT OR IGNORE INTO categories (id, name) VALUES (1, 'idea'), (2, 'task'), (3, 'remind')")
    c.execute("INSERT OR IGNORE INTO categories (id, name) VALUES (1, 'idea')")

    db.commit()
    return db, c

def create_user(username):
    if username:
        check = input(f"Ім'я користувача {username} [Y/n] ")
        if check == "" or check == "y":
            user_data = (username, int(time.time()))
            c.execute("INSERT INTO users (username, created_at) VALUES (?, ?)", user_data)
        else:
            return create_user(None)
    else:
        username = str(input("Введіть імя користувача: "))
        user_data = (username, int(time.time()))
        c.execute("INSERT INTO users (username, created_at) VALUES (?, ?)", user_data)

    db.commit()


def default_user():
    c.execute("SELECT id, username, created_at FROM users")

    users = c.fetchall()

    if not users:
        print("Користувачів ще немає. Використайте --create_user для створення користувача")
        return

    print(f"{'ID':<4} | {'Ім\'я':<15} | {'Дата створення'}")
    print("-" * 40)

    for user in users:
        uid, name, date = user
        print(f"{uid:<4} | {name:<15} | {date}")

    c.execute("SELECT id FROM users")
    users_id = c.fetchall()
    print("Стандартний користувач[", end = "")
    for i in users_id:
        print(i[0], end=", " if i != users_id[-1] else "")
    default_user_id = input("]: ")

    c.execute("INSERT OR REPLACE INTO settings (id, current_user_id) VALUES (1, ?)", (default_user_id,))
    db.commit()


def get_category(cat_name):
    c.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
    result = c.fetchone()

    if result:
        return result[0]
    else:
        print(f"Категорії '{cat_name}' не існує!")
        return None

def add(content, category_text = None):

    c.execute("SELECT current_user_id FROM settings")
    user_id = c.fetchone()
    if user_id is None:
        print("Використайте --default_user для встановлення стандартного користувача")
        return
    user_id = user_id[0]

    if category_text is None:
        category_id = 1 # idea
    else:
        category_id = get_category(category_text)

    is_done = 0

    created_at = int(time.time())

    data = (user_id, category_id, content, is_done, created_at)
    c.execute("INSERT INTO main (user_id, category_id, content, is_done, created_at) VALUES (?, ?, ?, ?, ?)", data)
    db.commit()

def view():
    c.execute("""
        SELECT main.id, users.username, categories.name, main.content
        FROM main
        JOIN users ON main.user_id = users.id
        JOIN categories ON main.category_id = categories.id
        WHERE main.is_done = 0
    """)

    table_view = c.fetchall()

    print(f"{'ID':<4} | {'User':<8} | {'Category':<8} | {'Content':<40}")
    print("-" * 50)

    for row in table_view:
        t_id, user, cat, txt = row
        print(f"{t_id:<4} | {user:<8} | {cat:<8} | {txt:<40}")

def delete():
    view()
    try:
        user_input = int(input("Введіть номер рядку: "))
    except ValueError:
        print("Помилка: введіть число!")
        return
    c.execute("SELECT 0 FROM main WHERE id = ?", (user_input,))
    if c.fetchone() is None:
        print(f"Рядка {user_input} не існує")
    else:
        c.execute("UPDATE main SET is_done = 1 WHERE id = ?", (user_input,))
        print("Видалено")

    db.commit()


if __name__ == "__main__":

    db, c = db_init()

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", nargs="?")
    # parser.add_argument("-r", "--remind", nargs=2)
    parser.add_argument("--create_user", nargs="?", const="UNSET", default=False)
    # parser.add_argument("-u", "--user", nargs=1)
    parser.add_argument("--default_user", action="store_true")
    parser.add_argument("-v", "--view", action="store_true")
    parser.add_argument("-d", "--delete", action="store_true")


    args = parser.parse_args()

    if args.add:
        data = args.add
        print(data)
        add(data)
    # if args.remind:
    #     pass
    if args.create_user is not False:
        print("create")
        if args.create_user == "UNSET":
            create_user(None)
        else:
            create_user(args.create_user)
    # if args.user:
    #     pass
    if args.default_user:
        default_user()

    if args.view:
        view()

    if args.delete:
        delete()

    db.close()
