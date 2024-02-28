"""
1. Đăng ký (Sign up):
    Chức năng này cần lấy dữ liệu từ form đăng ký và thêm thông tin người dùng vào bảng users.

2. Đăng nhập (Login):
    Cần lấy dữ liệu từ form đăng nhập và kiểm tra với thông tin người dùng trong bảng users.

3. Tìm kiếm bạn bè (Search for Friends):
    Sử dụng truy vấn SQL để tìm kiếm người dùng dựa trên username hoặc các tiêu chí khác.

4. Tạo nhóm chat (Create Group Chat):
    Chức năng này cần tạo một cuộc trò chuyện mới và thêm các thành viên vào bảng conversation_members.

5. Hiển thị cuộc trò chuyện (Display Conversations):
    Sử dụng truy vấn SQL để lấy danh sách các cuộc trò chuyện mà người dùng tham gia từ bảng conversations và conversation_members.

6. Chat Trực tuyến (Real-time Chat):
    Sử dụng Flask-SocketIO để tạo chức năng chat trực tuyến giữa các người dùng. Cần cập nhật tin nhắn mới vào bảng messages và trạng thái tin nhắn của từng người dùng trong bảng message_status.

7. Đăng xuất (Logout):
    Cần cung cấp một nút logout để người dùng có thể đăng xuất và quay lại trang đăng nhập.

Database Schema: 
-- Bảng Người dùng (Users)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT
);

-- Bảng Cuộc trò chuyện (Conversations)
CREATE TABLE conversations (
    conversation_id SERIAL PRIMARY KEY,
    conversation_name VARCHAR(255),
    conversation_type VARCHAR(20) NOT NULL
);

-- Bảng Thành viên cuộc trò chuyện (Conversation Members)
CREATE TABLE conversation_members (
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    user_id INTEGER REFERENCES users(user_id),
    PRIMARY KEY (conversation_id, user_id)
);

-- Bảng Tin nhắn (Messages)
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    sender_id INTEGER REFERENCES users(user_id),
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Trạng thái tin nhắn (Message Status)
CREATE TABLE message_status (
    message_id INTEGER REFERENCES messages(message_id),
    user_id INTEGER REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL,
    PRIMARY KEY (message_id, user_id)
);

-- Bảng Tệp đính kèm (Attachments)
CREATE TABLE attachments (
    attachment_id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(message_id),
    attachment_url TEXT NOT NULL,
    attachment_type VARCHAR(50) NOT NULL
);

"""

# Import các thư viện cần thiết
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

# Khởi tạo ứng dụng SocketIO
socketio = SocketIO(app)

# Kết nối đến cơ sở dữ liệu PostgreSQL
conn = psycopg2.connect(
    dbname="chatapptutorial",
    user="postgres",
    password="lunalevi",
    host="localhost",
    port="5435",
)


# Đăng ký (Sign up)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        password_hash = generate_password_hash(password)

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, full_name) VALUES (%s, %s, %s)",
                (username, password_hash, full_name),
            )
        conn.commit()
        return redirect(url_for("login"))
    return render_template("signup.html")


# Đăng nhập (Login)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, password_hash FROM users WHERE username = %s",
                (username,),
            )
            user = cur.fetchone()
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect(url_for("home"))
    return render_template("login.html")


# Tìm kiếm bạn bè (Search for Friends)
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get("query")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, full_name FROM users WHERE username LIKE %s",
                ("%" + query + "%",),
            )
            users = cur.fetchall()
        return render_template("search.html", users=users)
    return render_template("search.html")


# Tạo nhóm chat (Create Group Chat)
@app.route("/create_group", methods=["GET", "POST"])
def create_group():
    if request.method == "POST":
        conversation_name = request.form["conversation_name"]
        members = request.form.getlist("members")
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (conversation_name, conversation_type) VALUES (%s, %s) RETURNING conversation_id",
                (conversation_name, "group"),
            )
            conversation_id = cur.fetchone()[0]
            for member in members:
                cur.execute(
                    "INSERT INTO conversation_members (conversation_id, user_id) VALUES (%s, %s)",
                    (conversation_id, member),
                )
        conn.commit()
        return redirect(url_for("home"))
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, username, full_name FROM users")
        users = cur.fetchall()
    return render_template("create_group.html", users=users)


# Hiển thị cuộc trò chuyện (Display Conversations)
@app.route("/home")
def home():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login"))
    with conn.cursor() as cur:
        cur.execute(
            "SELECT c.conversation_id, c.conversation_name, c.conversation_type FROM conversations c JOIN conversation_members m ON c.conversation_id = m.conversation_id WHERE m.user_id = %s",
            (user_id,),
        )
        conversations = cur.fetchall()
    return render_template("home.html", conversations=conversations)


# Chat Trực tuyến (Real-time Chat)
@socketio.on("send_message")
def handle_send_message(data):
    conversation_id = data["conversation_id"]
    sender_id = data["sender_id"]
    message_text = data["message_text"]
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO messages (conversation_id, sender_id, message_text) VALUES (%s, %s, %s) RETURNING message_id, sent_at",
            (conversation_id, sender_id, message_text),
        )
        message_id, sent_at = cur.fetchone()
        cur.execute(
            "SELECT user_id FROM conversation_members WHERE conversation_id = %s AND user_id != %s",
            (conversation_id, sender_id),
        )
        recipient_ids = [row[0] for row in cur.fetchall()]
        for recipient_id in recipient_ids:
            cur.execute(
                "INSERT INTO message_status (message_id, user_id, status) VALUES (%s, %s, %s)",
                (message_id, recipient_id, "received"),
            )
    conn.commit()
    emit(
        "receive_message",
        {
            "message_id": message_id,
            "sender_id": sender_id,
            "message_text": message_text,
            "sent_at": sent_at,
        },
        room=str(conversation_id),
    )


# Đăng xuất (Logout)
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


# Chạy ứng dụng
if __name__ == "__main__":
    socketio.run(app, debug=True)


# References:
# Flask-SocketIO Documentation: https://flask-socketio.readthedocs.io/en/latest/
# PostgreSQL Documentation: https://www.postgresql.org/docs/
# Flask Documentation: https://flask.palletsprojects.com/en/1.1.x/
# Python PostgreSQL Tutorial: https://www.postgresqltutorial.com/postgresql-python/
# Python Flask Tutorial: https://realpython.com/tutorials/flask/
