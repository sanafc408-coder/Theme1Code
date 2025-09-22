import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("student_connect.db", check_same_thread=False)
c = conn.cursor()

# Users
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                college TEXT,
                skills TEXT,
                bio TEXT)''')

# Posts
c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id))''')

# Courses
c.execute('''CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Forum
c.execute('''CREATE TABLE IF NOT EXISTS forum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                question TEXT,
                answer TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Notes (PDF)
c.execute('''CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                file_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Note Ratings
c.execute('''CREATE TABLE IF NOT EXISTS note_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                username TEXT,
                rating INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(note_id) REFERENCES notes(id))''')

# Podcasts
c.execute('''CREATE TABLE IF NOT EXISTS podcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                language TEXT,
                file_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

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

# Courses
def add_course(username, title, description):
    c.execute("INSERT INTO courses (username, title, description) VALUES (?, ?, ?)", (username, title, description))
    conn.commit()

def get_courses():
    c.execute("SELECT username, title, description, timestamp FROM courses ORDER BY timestamp DESC")
    return c.fetchall()

# Forum
def add_forum_question(username, question):
    c.execute("INSERT INTO forum (username, question, answer) VALUES (?, ?, ?)", (username, question, None))
    conn.commit()

def add_forum_answer(q_id, answer):
    c.execute("UPDATE forum SET answer=? WHERE id=?", (answer, q_id))
    conn.commit()

def get_forum():
    c.execute("SELECT id, username, question, answer, timestamp FROM forum ORDER BY timestamp DESC")
    return c.fetchall()

# Notes
def add_note(username, title, file_path):
    c.execute("INSERT INTO notes (username, title, file_path) VALUES (?, ?, ?)", 
              (username, title, file_path))
    conn.commit()

def get_notes():
    c.execute("SELECT id, username, title, file_path, timestamp FROM notes ORDER BY timestamp DESC")
    return c.fetchall()

# Note Ratings
def rate_note(note_id, username, rating):
    c.execute("SELECT * FROM note_ratings WHERE note_id=? AND username=?", (note_id, username))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE note_ratings SET rating=?, timestamp=CURRENT_TIMESTAMP WHERE id=?", (rating, existing[0]))
    else:
        c.execute("INSERT INTO note_ratings (note_id, username, rating) VALUES (?, ?, ?)", (note_id, username, rating))
    conn.commit()

def get_avg_rating(note_id):
    c.execute("SELECT AVG(rating) FROM note_ratings WHERE note_id=?", (note_id,))
    avg = c.fetchone()[0]
    return round(avg,1) if avg else None

# Podcasts
def add_podcast(username, title, language, file_path):
    c.execute("INSERT INTO podcasts (username, title, language, file_path) VALUES (?, ?, ?, ?)",
              (username, title, language, file_path))
    conn.commit()

def get_podcasts(language=None):
    if language:
        c.execute("SELECT username, title, language, file_path, timestamp FROM podcasts WHERE language=? ORDER BY timestamp DESC", (language,))
    else:
        c.execute("SELECT username, title, language, file_path, timestamp FROM podcasts ORDER BY timestamp DESC")
    return c.fetchall()

# ---------------------------
# Session State
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_id = None

st.title("🎓 SkillSync")
st.subheader("The Student Powered Connectivity Platform")

# ---------------------------
# Login / Signup
# ---------------------------
if not st.session_state.logged_in:
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
                st.session_state.logged_in = True
                st.session_state.username = user[1]
                st.session_state.user_id = user[0]
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid username or password")

# ---------------------------
# Main App Sections
# ---------------------------
else:
    section = st.sidebar.radio("Choose Section", 
                               ["Profile", "Posts", "Courses", "Forum", "Notes", "Podcasts", "Logout"])
    username = st.session_state.username
    user_id = st.session_state.user_id

    # ---------------- Profile ----------------
    if section == "Profile":
        user = get_user(username)
        st.subheader("👤 Your Profile")
        st.write(f"**Username:** {user[1]}")
        st.write(f"**College:** {user[3]}")
        st.write(f"**Skills:** {user[4]}")
        st.write(f"**Bio:** {user[5]}")

    # ---------------- Posts ----------------
    elif section == "Posts":
        st.subheader("✍️ Create a Post")
        content = st.text_area("What's on your mind?")
        if st.button("Post"):
            add_post(user_id, content)
            st.success("Post added successfully!")

        st.subheader("📢 Student Feed")
        posts = get_all_posts()
        for post in posts:
            st.write(f"**{post[2]}** ({post[1]}):")
            st.write(post[0])
            st.markdown("---")

    # ---------------- Courses ----------------
    elif section == "Courses":
        st.subheader("📚 Share a Course")
        title = st.text_input("Course Title")
        desc = st.text_area("Course Description")
        if st.button("Add Course"):
            add_course(username, title, desc)
            st.success("Course added!")

        st.subheader("All Courses")
        courses = get_courses()
        for u, t, d, time in courses:
            st.markdown(f"**{t}** (by {u} at {time})")
            st.write(d)
            st.write("---")

    # ---------------- Forum ----------------
    elif section == "Forum":
        st.subheader("💬 Forum")
        question = st.text_area("Ask a question")
        if st.button("Post Question"):
            add_forum_question(username, question)
            st.success("Question posted!")

        st.subheader("All Questions")
        forum = get_forum()
        for q_id, u, q, a, time in forum:
            st.markdown(f"**{u}** asked ({time}): {q}")
            if a:
                st.write(f"💡 Answer: {a}")
            answer = st.text_input(f"Your Answer to Q{q_id}", key=f"ans_{q_id}")
            if st.button(f"Submit Answer to Q{q_id}"):
                add_forum_answer(q_id, answer)
                st.success("Answer submitted!")
            st.write("---")

    # ---------------- Notes ----------------
    elif section == "Notes":
        st.subheader("📚 Share PDF Notes")
        note_title = st.text_input("Note Title")
        note_file = st.file_uploader("Upload PDF File", type=["pdf"])

        if note_file is not None:
            os.makedirs("notes_uploads", exist_ok=True)
            file_path = f"notes_uploads/{note_file.name}"
            with open(file_path, "wb") as f:
                f.write(note_file.getbuffer())
            if st.button("Share Note"):
                add_note(username, note_title, file_path)
                st.success("✅ Note shared!")

        st.subheader("All Notes")
        notes = get_notes()
        for note in notes:
            note_id, u, t, path, time = note
            st.markdown(f"**{t}** (by {u} at {time})")
            with open(path, "rb") as pdf_file:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_file,
                    file_name=path.split("/")[-1],
                    mime="application/pdf"
                )

            avg_rating = get_avg_rating(note_id)
            st.write(f"⭐ Average Rating: {avg_rating if avg_rating else 'No ratings yet'}")
            user_rating = st.slider(f"Rate this note (1-5) - {t}", min_value=1, max_value=5, key=f"rate_{note_id}")
            if st.button(f"Submit Rating - {note_id}"):
                rate_note(note_id, username, user_rating)
                st.success("✅ Your rating has been submitted!")
            st.write("---")

    # ---------------- Podcasts ----------------
    elif section == "Podcasts":
        st.subheader("🎧 Short Podcasts")
        podcast_title = st.text_input("Podcast Title")
        podcast_language = st.selectbox("Language", ["English", "Tamil"])
        podcast_file = st.file_uploader("Upload Audio File", type=["mp3", "wav"])

        if podcast_file is not None:
            os.makedirs("uploads", exist_ok=True)
            file_path = f"uploads/{podcast_file.name}"
            with open(file_path, "wb") as f:
                f.write(podcast_file.getbuffer())
            if st.button("Upload Podcast"):
                add_podcast(username, podcast_title, podcast_language, file_path)
                st.success("✅ Podcast uploaded!")

        st.subheader("All Podcasts")
        filter_lang = st.radio("Filter by Language", ["All", "English", "Tamil"])
        podcasts = get_podcasts(None if filter_lang=="All" else filter_lang)
        for u, t, lang, path, time in podcasts:
            st.markdown(f"**{t}** ({lang}) by {u} at {time}")
            st.audio(path)
            st.write("---")

    # ---------------- Logout ----------------
    elif section == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.success("Logged out successfully!")
