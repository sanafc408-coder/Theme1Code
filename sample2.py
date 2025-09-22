import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("student_connect.db", check_same_thread=False)
c = conn.cursor()

# Users Table
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                college TEXT,
                skills TEXT,
                bio TEXT)''')

# Posts Table
c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

# Courses Table
c.execute('''CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                created_by INTEGER,
                timestamp TEXT,
                FOREIGN KEY(created_by) REFERENCES users(id))''')

# Enrollments Table
c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(course_id) REFERENCES courses(id))''')

# Forums Table
c.execute('''CREATE TABLE IF NOT EXISTS forums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                message TEXT,
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

# Courses
def add_course(title, description, created_by):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO courses (title, description, created_by, timestamp) VALUES (?,?,?,?)",
              (title, description, created_by, timestamp))
    conn.commit()

def get_all_courses():
    c.execute("""SELECT courses.id, courses.title, courses.description, users.username, courses.timestamp
                 FROM courses JOIN users ON courses.created_by = users.id 
                 ORDER BY courses.id DESC""")
    return c.fetchall()

def enroll_in_course(user_id, course_id):
    c.execute("INSERT INTO enrollments (user_id, course_id) VALUES (?,?)", (user_id, course_id))
    conn.commit()

def get_user_courses(user_id):
    c.execute("""SELECT courses.title, courses.description 
                 FROM enrollments JOIN courses 
                 ON enrollments.course_id = courses.id 
                 WHERE enrollments.user_id=?""", (user_id,))
    return c.fetchall()

# Forums
def add_forum_post(user_id, topic, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO forums (user_id, topic, message, timestamp) VALUES (?,?,?,?)",
              (user_id, topic, message, timestamp))
    conn.commit()

def get_all_forum_posts():
    c.execute("""SELECT forums.topic, forums.message, forums.timestamp, users.username
                 FROM forums JOIN users ON forums.user_id = users.id
                 ORDER BY forums.id DESC""")
    return c.fetchall()

# ---------------------------
# Session State Setup
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("🎓 SkillSync")
st.subheader("The Student Powered Connectivity Platform")

menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------------------
# Signup
# ---------------------------
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

# ---------------------------
# Login
# ---------------------------
elif choice == "Login":
    if not st.session_state.logged_in:
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid username or password")
    else:
        user = st.session_state.user
        st.success(f"Welcome back {user[1]}!")

        section = st.sidebar.radio("Choose Section", 
                                   ["Profile", "Posts", "Courses", "Forum", "Logout"])

        # ---------------- Profile ----------------
        if section == "Profile":
            st.subheader("👤 Your Profile")
            st.write(f"**College:** {user[3]}")
            st.write(f"**Skills:** {user[4]}")
            st.write(f"**Bio:** {user[5]}")

        # ---------------- Posts ----------------
        elif section == "Posts":
            st.subheader("✍️ Create a Post")
            content = st.text_area("What's on your mind?")
            if st.button("Post"):
                add_post(user[0], content)
                st.success("Post added successfully!")

            st.subheader("📢 Student Feed")
            posts = get_all_posts()
            for post in posts:
                st.write(f"**{post[2]}** ({post[1]}):")
                st.write(post[0])
                st.markdown("---")

        # ---------------- Courses ----------------
        elif section == "Courses":
            st.subheader("📚 Courses")
            course_option = st.radio("Choose Option", ["Create Course", "View Courses", "My Courses"])

            if course_option == "Create Course":
                title = st.text_input("Course Title")
                description = st.text_area("Course Description")
                if st.button("Create"):
                    add_course(title, description, user[0])
                    st.success("Course created successfully!")

            elif course_option == "View Courses":
                courses = get_all_courses()
                for c_id, title, desc, creator, time in courses:
                    st.write(f"**{title}** (by {creator} at {time})")
                    st.write(desc)
                    if st.button(f"Enroll in {title}", key=f"enroll_{c_id}"):
                        enroll_in_course(user[0], c_id)
                        st.success(f"Enrolled in {title}!")
                    st.markdown("---")

            elif course_option == "My Courses":
                my_courses = get_user_courses(user[0])
                if my_courses:
                    for title, desc in my_courses:
                        st.write(f"**{title}**")
                        st.write(desc)
                        st.markdown("---")
                else:
                    st.info("You are not enrolled in any courses yet.")

        # ---------------- Forum ----------------
        elif section == "Forum":
            st.subheader("💬 Discussion Forum")
            topic = st.text_input("Topic")
            message = st.text_area("Message")
            if st.button("Post Message"):
                add_forum_post(user[0], topic, message)
                st.success("Message posted!")

            st.subheader("🌍 Forum Messages")
            forum_posts = get_all_forum_posts()
            for topic, message, time, author in forum_posts:
                st.write(f"**{topic}** by {author} ({time})")
                st.write(message)
                st.markdown("---")

        # ---------------- Logout ----------------
        elif section == "Logout":
            st.session_state.logged_in = False
            st.session_state.user = None
            st.info("You have been logged out.")
