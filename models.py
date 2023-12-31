import psycopg2
from psycopg2 import pool
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

render = True
db = os.getenv('EXTERNAL_DB')

if render:
    db = os.getenv('INTERNAL_DB')

min_conn, max_conn = 1, 10
conn_pool = psycopg2.pool.SimpleConnectionPool(min_conn, max_conn, db)


def get_conn():
    return conn_pool.getconn()


def release_conn(conn):
    conn_pool.putconn(conn)


def sql_select(query, params):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchall()
    cur.close()
    release_conn(conn)
    return result


def sql_write(query, params):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    cur.close()
    release_conn(conn)


def log_message(username, message):
    query = 'INSERT INTO messages (username, message) VALUES (%s, %s)'
    params = (username, message)
    sql_write(query, params)


def render_messages():
    query = 'SELECT username, message FROM messages ORDER BY id DESC LIMIT 8'
    result = sql_select(query, ())
    return result


def chat_log():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT username, message FROM messages ORDER BY id DESC LIMIT 8')
    result = cur.fetchall()
    chat_messages = [{'username': row[0], 'msg': row[1]} for row in result]
    cur.close()
    release_conn(conn)
    return chat_messages


def clear_chat():
    query = 'DELETE FROM messages'
    params = []
    sql_write(query, params)


def user_signup(email, name, password, confirm_password):
    if password == confirm_password:

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        query = "INSERT INTO users (email, name, pw_hash) VALUES (%s, %s, %s)"
        params = (email, name, pw_hash,)

        sql_write(query, params)

        return True
    else:
        return False


def check_login(user_email, user_pw):
    result = sql_select("SELECT id, email, pw_hash, admin FROM users WHERE email = %s", (user_email,))

    if result and bcrypt.checkpw(user_pw.encode(), result[0][2].encode()):
        user_id = result[0][0]
        user_email = result[0][1]
        admin_status = result[0][3]

        return user_id, user_email, admin_status
    else:
        print("log-in error. try again.")


def get_user(user_id):
    query = "SELECT name FROM users WHERE id = %s"
    params = (user_id,)
    result = sql_select(query, params)
    username = result[0][0]
    return username


def log_post(data):
    query = "INSERT INTO posts (username, title, content) VALUES (%s, %s, %s)"
    username, title, content = data['username'], data['title'], data['content']
    params = (username, title, content)
    sql_write(query, params)
    print(f"logged a new post from {username}!")


def get_posts():
    query = "SELECT * FROM posts ORDER BY post_id DESC;"
    params = ()
    result = sql_select(query, params)
    return result


def get_post(post_id):
    query = "SELECT * FROM posts WHERE post_id = %s"
    params = (post_id,)
    result = sql_select(query, params)
    return result[0]


def get_recent_posts():
    query = "SELECT title, post_id FROM posts ORDER BY post_id DESC LIMIT 2"
    params = ()
    results = sql_select(query, params)
    latest_posts = []
    for result in results:
        latest_posts.append(result)
    return latest_posts


def delete_post(post_id):
    query = "DELETE FROM posts WHERE post_id = %s"
    params = (post_id,)
    sql_write(query, params)
    print(f"deleted post_id: {post_id}")


def log_comment(data):
    query = "INSERT INTO comments (post_id, user_id, comment) VALUES (%s, %s, %s)"
    post_id, user_id, comment = int(data['post_id']), data['user_id'], data['comment']
    params = (post_id, user_id, comment)
    sql_write(query, params)
    print(f"New comment from {user_id} on post {post_id}.")


def get_comments(post_id):
    query = "SELECT * FROM comments WHERE post_id = %s"
    params = (post_id,)
    result = sql_select(query, params)
    comments = []
    for comment in result:
        data = {
            'comment_id': comment[0],
            'post_id': comment[1],
            'user_id': comment[2],
            'comment': comment[3]
        }
        comments.append(data)
    return comments
