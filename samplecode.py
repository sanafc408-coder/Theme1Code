import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("student_connect.db", check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                college TEXT,
                skills TEXT,
                bio TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id))''')
conn.commit()

# ---------------------------
# Helper Functions
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, college, skills, bio):
    c.execute("INSERT INTO users (username, password, college, skills, bio) VALUES (?,?,?,?,?)",
              (username, hash_password(password), college, skills, bio))
    conn.commit()

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hash_password(password)))
    return c.fetchone()

def get_user(username):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()

def add_post(user_id, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO posts (user_id, content, timestamp) VALUES (?,?,?)",
              (user_id, content, timestamp))
    conn.commit()

def get_all_posts():
    c.execute("""SELECT posts.content, posts.timestamp, users.username 
                 FROM posts JOIN users ON posts.user_id = users.id 
                 ORDER BY posts.id DESC""")
    return c.fetchall()

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🎓 SkillSync")
st.subheader("The Student Powered Connectivity Platform")


menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Signup":
    st.subheader("Create a New Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    college = st.text_input("College")
    skills = st.text_input("Skills (comma separated)")
    bio = st.text_area("Short Bio")

    if st.button("Signup"):
        if username and password:
            try:
                add_user(username, password, college, skills, bio)
                st.success("Account created successfully! Go to Login.")
            except:
                st.error("Username already exists. Try a different one.")
        else:
            st.warning("Please enter a username and password.")

elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.success(f"Welcome {username}!")

            # Profile
            st.subheader("👤 Your Profile")
            st.write(f"**College:** {user[3]}")
            st.write(f"**Skills:** {user[4]}")
            st.write(f"**Bio:** {user[5]}")

            # Post Creation
            st.subheader("✍️ Create a Post")
            content = st.text_area("What's on your mind?")
            if st.button("Post"):
                add_post(user[0], content)
                st.success("Post added successfully!")

            # Feed
            st.subheader("📢 Student Feed")
            posts = get_all_posts()
            for post in posts:
                st.write(f"**{post[2]}** ({post[1]}):")
                st.write(post[0])
                st.markdown("---")

        else:
            st.error("Invalid username or password")
