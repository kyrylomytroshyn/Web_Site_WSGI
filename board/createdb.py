import sqlite3
from datetime import datetime


class BoardDataBase:

    def get_posts(self) -> list:
        conn = sqlite3.connect('post_storage.db')
        cur = conn.cursor()
        cur.execute("SELECT _id, text, title, datetime FROM boards ORDER BY datetime DESC")
        conn.commit()
        return cur.fetchall()

    def get_post_info(self, post_id: int) -> list:
        conn = sqlite3.connect('post_storage.db')
        cur = conn.cursor()
        cur.execute(f"SELECT text, author, title, datetime FROM boards WHERE _id = {post_id}")
        conn.commit()
        return cur.fetchone()

    def add_post(self, text: str, author: str, title: str, now_time: datetime) -> None:
        conn = sqlite3.connect('post_storage.db')
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO boards (text, author, title, datetime) "
                        f"VALUES ('{text}', '{author}', '{title}', '{now_time}')")
            conn.commit()
        except Exception as e:
            print(e)


    def get_comments(self, post_id: int) -> list:
        conn = sqlite3.connect('post_storage.db')
        cur = conn.cursor()
        cur.execute(f"SELECT text, author FROM comments WHERE board_id = {post_id}")
        conn.commit()
        return cur.fetchall()

    def add_comment(self, author: str, text: str, board_id: int) -> None:
        conn = sqlite3.connect('post_storage.db')
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO comments (text, author, board_id) "
                        f"VALUES ('{text}', '{author}', {board_id})")
            conn.commit()
        except Exception as e:
            print(e)
