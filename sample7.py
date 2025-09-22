import streamlit as st
import sqlite3
import os

# ---------------- DATABASE ----------------
conn = sqlite3.connect("student_connectivity.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                college TEXT,
                skills TEXT,
                bio TEXT,
                profile_pic TEXT
            )''')

# Other tables
c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                content TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                course_name TEXT,
                description TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                file_path TEXT,
                rating INTEGER DEFAULT 0
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS forum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                question TEXT,
                answer TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS podcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                title TEXT,
                file_path TEXT
            )''')

# New: Projects and Hackathons
c.execute('''CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                owner TEXT,
                members TEXT
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS hackathons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                start_date TEXT,
                end_date TEXT,
                participants TEXT
            )''')

conn.commit()

# ---------------- HELPERS ----------------
def create_user(username, password, college):
    try:
        c.execute("INSERT INTO users (username, password, college, skills, bio, profile_pic) VALUES (?, ?, ?, ?, ?, ?)", 
                  (username, password, college, "", "", ""))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

def get_user(username):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    return c.fetchone()

def add_post(username, content):
    c.execute("INSERT INTO posts (username, content) VALUES (?, ?)", (username, content))
    conn.commit()

def get_posts():
    c.execute("SELECT * FROM posts ORDER BY id DESC")
    return c.fetchall()

def add_course(username, name, desc):
    c.execute("INSERT INTO courses (username, course_name, description) VALUES (?, ?, ?)", (username, name, desc))
    conn.commit()

def get_courses():
    c.execute("SELECT * FROM courses ORDER BY id DESC")
    return c.fetchall()

def add_notes(username, title, file_path):
    c.execute("INSERT INTO notes (username, title, file_path) VALUES (?, ?, ?)", (username, title, file_path))
    conn.commit()

def get_notes():
    c.execute("SELECT * FROM notes ORDER BY id DESC")
    return c.fetchall()

def rate_note(note_id, rating):
    c.execute("UPDATE notes SET rating = rating + ? WHERE id=?", (rating, note_id))
    conn.commit()

def add_question(username, question):
    c.execute("INSERT INTO forum (username, question, answer) VALUES (?, ?, ?)", (username, question, ""))
    conn.commit()

def get_questions():
    c.execute("SELECT * FROM forum ORDER BY id DESC")
    return c.fetchall()

def answer_question(q_id, answer):
    c.execute("UPDATE forum SET answer=? WHERE id=?", (answer, q_id))
    conn.commit()

def add_podcast(username, title, file_path):
    c.execute("INSERT INTO podcasts (username, title, file_path) VALUES (?, ?, ?)", (username, title, file_path))
    conn.commit()

def get_podcasts():
    c.execute("SELECT * FROM podcasts ORDER BY id DESC")
    return c.fetchall()

# ---------------- PROJECTS ----------------
def add_project(owner, title, desc):
    c.execute("INSERT INTO projects (title, description, owner, members) VALUES (?, ?, ?, ?)",
              (title, desc, owner, owner))
    conn.commit()

def get_projects():
    c.execute("SELECT * FROM projects ORDER BY id DESC")
    return c.fetchall()

def join_project(project_id, username):
    c.execute("SELECT members FROM projects WHERE id=?", (project_id,))
    members = c.fetchone()[0]
    member_list = members.split(",") if members else []
    if username not in member_list:
        member_list.append(username)
        c.execute("UPDATE projects SET members=? WHERE id=?", (",".join(member_list), project_id))
        conn.commit()

# ---------------- HACKATHONS ----------------
def add_hackathon(title, desc, start_date, end_date):
    c.execute("INSERT INTO hackathons (title, description, start_date, end_date, participants) VALUES (?, ?, ?, ?, ?)",
              (title, desc, start_date, end_date, ""))
    conn.commit()

def get_hackathons():
    c.execute("SELECT * FROM hackathons ORDER BY id DESC")
    return c.fetchall()

def join_hackathon(hackathon_id, username):
    c.execute("SELECT participants FROM hackathons WHERE id=?", (hackathon_id,))
    participants = c.fetchone()[0]
    participant_list = participants.split(",") if participants else []
    if username not in participant_list:
        participant_list.append(username)
        c.execute("UPDATE hackathons SET participants=? WHERE id=?", (",".join(participant_list), hackathon_id))
        conn.commit()

# ---------------- LEADERBOARD ----------------
def get_leaderboard():
    # Count posts
    c.execute("SELECT username, COUNT(*) FROM posts GROUP BY username")
    posts = dict(c.fetchall())

    # Count notes + sum of ratings
    c.execute("SELECT username, COUNT(*), SUM(rating) FROM notes GROUP BY username")
    notes_data = c.fetchall()
    notes = {u: (cnt, r if r else 0) for u, cnt, r in notes_data}

    # Count courses
    c.execute("SELECT username, COUNT(*) FROM courses GROUP BY username")
    courses = dict(c.fetchall())

    # Count answered forum questions
    c.execute("SELECT username, COUNT(*) FROM forum WHERE answer != '' GROUP BY username")
    answers = dict(c.fetchall())

    # Count projects joined
    c.execute("SELECT members FROM projects")
    projects_members = c.fetchall()
    project_points = {}
    for row in projects_members:
        for user in row[0].split(","):
            project_points[user] = project_points.get(user, 0) + 3

    # Count hackathons joined
    c.execute("SELECT participants FROM hackathons")
    hackathons_participants = c.fetchall()
    hack_points = {}
    for row in hackathons_participants:
        for user in row[0].split(","):
            hack_points[user] = hack_points.get(user, 0) + 5

    # Aggregate scores
    scores = {}
    all_users = set(posts.keys()) | set(notes.keys()) | set(courses.keys()) | set(answers.keys()) | set(project_points.keys()) | set(hack_points.keys())
    for u in all_users:
        score = 0
        score += posts.get(u, 0) * 2
        score += notes.get(u, (0,0))[0] * 3
        score += notes.get(u, (0,0))[1] * 1
        score += courses.get(u,0) *2
        score += answers.get(u,0) *4
        score += project_points.get(u,0)
        score += hack_points.get(u,0)
        scores[u] = score

    leaderboard = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return leaderboard

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ---------------- MAIN APP ----------------
st.set_page_config(page_title="SkillSync", layout="wide")
st.title("🎓 SkillSync")
st.image("image.jpg", width=500)

menu = ["Home", "Login", "SignUp"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- HOME ----------------
if choice == "Home":
    st.subheader("The Student Powered Connectivity Platform")
    st.write("Connect, share, and grow with students across campuses.")

# ---------------- SIGNUP ----------------
elif choice == "SignUp":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    college = st.text_input("College Name")
    if st.button("SignUp"):
        if create_user(new_user, new_pass, college):
            st.success("Account created successfully! Go to Login.")
        else:
            st.error("Username already exists.")

# ---------------- LOGIN ----------------
elif choice == "Login":
    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            result = login_user(username, password)
            if result:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid username or password")
    else:
        username = st.session_state.username
        st.success(f"Welcome back {username}! ✅")

        st.sidebar.subheader("Account")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.success("You have been logged out. Please log in again.")
            st.rerun()

        section = st.sidebar.radio("Sections", ["Profile", "Posts", "Courses", "Notes", "Forum", "Podcasts", "Projects", "Hackathons", "Leaderboard"])

        # ---------------- SECTIONS ----------------

        # PROFILE
        if section == "Profile":
            user = get_user(username)
            st.subheader("👤 Your Profile")
            pic_path = f"profile_pics/{username}.png"
            if os.path.exists(pic_path):
                st.image(pic_path, width=120)
            else:
                st.info("No profile picture uploaded.")
            st.write(f"**Username:** {user[1]}")
            st.write(f"**College:** {user[3]}")
            st.write("**Skills:**")
            if user[4]:
                for skill in user[4].split(","):
                    st.markdown(f"- 🟢 {skill.strip()}")
            else:
                st.write("No skills listed")
            st.write(f"**Bio:** {user[5]}")
            st.markdown("---")
            st.subheader("✏️ Edit Profile")
            new_college = st.text_input("Update College", value=user[3])
            new_skills = st.text_input("Update Skills (comma separated)", value=user[4])
            new_bio = st.text_area("Update Bio", value=user[5])
            profile_pic = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
            if st.button("Save Changes"):
                c.execute("UPDATE users SET college=?, skills=?, bio=? WHERE username=?", 
                          (new_college, new_skills, new_bio, username))
                conn.commit()
                if profile_pic:
                    os.makedirs("profile_pics", exist_ok=True)
                    with open(pic_path, "wb") as f:
                        f.write(profile_pic.getbuffer())
                st.success("✅ Profile updated! Please refresh to see changes.")

        # POSTS
        elif section == "Posts":
            st.subheader("📝 Share a Post")
            content = st.text_area("Write something...")
            if st.button("Post"):
                add_post(username, content)
                st.success("Post added!")
            st.subheader("📢 All Posts")
            posts = get_posts()
            for p in posts:
                st.write(f"**{p[1]}:** {p[2]}")

        # COURSES
        elif section == "Courses":
            st.subheader("📚 Share a Course")
            name = st.text_input("Course Name")
            desc = st.text_area("Course Description")
            if st.button("Add Course"):
                add_course(username, name, desc)
                st.success("Course shared!")
            st.subheader("🎓 Available Courses")
            courses = get_courses()
            for c_ in courses:
                st.write(f"**{c_[2]}** by {c_[1]}")
                st.write(c_[3])

        # NOTES
        elif section == "Notes":
            st.subheader("📂 Upload Notes")
            title = st.text_input("Title")
            file = st.file_uploader("Upload File", type=["pdf", "docx", "txt"])
            if st.button("Upload Notes"):
                if file:
                    os.makedirs("notes", exist_ok=True)
                    path = f"notes/{file.name}"
                    with open(path, "wb") as f:
                        f.write(file.getbuffer())
                    add_notes(username, title, path)
                    st.success("Notes uploaded!")
            st.subheader("📑 All Notes")
            notes = get_notes()
            for n in notes:
                st.write(f"**{n[2]}** by {n[1]}")
                st.write(f"⭐ {n[4]} likes")
                with open(n[3], "rb") as f:
                    st.download_button("Download", f, file_name=os.path.basename(n[3]))
                if st.button("👍 Like", key=f"like{n[0]}"):
                    rate_note(n[0], 1)
                    st.success("You liked this note!")

        # FORUM
        elif section == "Forum":
            st.subheader("❓ Ask a Question")
            question = st.text_input("Your Question")
            if st.button("Ask"):
                add_question(username, question)
                st.success("Question posted!")
            st.subheader("💬 Forum Q&A")
            qs = get_questions()
            for q in qs:
                st.write(f"**Q: {q[2]}** (by {q[1]})")
                if q[3]:
                    st.write(f"👉 Answer: {q[3]}")
                else:
                    ans = st.text_input("Your Answer", key=f"ans{q[0]}")
                    if st.button("Submit Answer", key=f"btn{q[0]}"):
                        answer_question(q[0], ans)
                        st.success("Answer submitted!")

        # PODCASTS
        elif section == "Podcasts":
            st.subheader("🎙️ Upload Podcast")
            title = st.text_input("Title")
            audio = st.file_uploader("Upload Audio", type=["mp3", "wav"])
            if st.button("Upload"):
                if audio:
                    os.makedirs("podcasts", exist_ok=True)
                    path = f"podcasts/{audio.name}"
                    with open(path, "wb") as f:
                        f.write(audio.getbuffer())
                    add_podcast(username, title, path)
                    st.success("Podcast uploaded!")
            st.subheader("🎧 Available Podcasts")
            podcasts = get_podcasts()
            for p in podcasts:
                st.write(f"**{p[2]}** by {p[1]}")
                st.audio(p[3])

        # PROJECTS
        elif section == "Projects":
            st.subheader("💡 Create a Project")
            title = st.text_input("Project Title")
            desc = st.text_area("Project Description")
            if st.button("Create Project"):
                add_project(username, title, desc)
                st.success("Project created!")
            st.subheader("🚀 Available Projects")
            projects = get_projects()
            for p in projects:
                st.write(f"**{p[1]}** by {p[3]}")
                st.write(p[2])
                st.write(f"Members: {p[4]}")
                if username not in p[4].split(","):
                    if st.button(f"Join Project", key=f"join_proj{p[0]}"):
                        join_project(p[0], username)
                        st.success("You joined the project!")

        # HACKATHONS
        elif section == "Hackathons":
            st.subheader("🏁 Create a Hackathon")
            title = st.text_input("Hackathon Title")
            desc = st.text_area("Description")
            start = st.date_input("Start Date")
            end = st.date_input("End Date")
            if st.button("Create Hackathon"):
                add_hackathon(title, desc, str(start), str(end))
                st.success("Hackathon created!")
            st.subheader("🎉 Upcoming Hackathons")
            hackathons = get_hackathons()
            for h in hackathons:
                st.write(f"**{h[1]}** from {h[3]} to {h[4]}")
                st.write(h[2])
                st.write(f"Participants: {h[5] if h[5] else 'None'}")
                if username not in (h[5] or "").split(","):
                    if st.button(f"Join Hackathon", key=f"join_hack{h[0]}"):
                        join_hackathon(h[0], username)
                        st.success("You joined the hackathon!")

        # LEADERBOARD
        elif section == "Leaderboard":
            st.subheader("🏆 Leaderboard")
            leaderboard = get_leaderboard()
            if not leaderboard:
                st.info("No contributions yet. Start posting, sharing, and answering to climb the leaderboard!")
            else:
                for rank, (user, score) in enumerate(leaderboard, start=1):
                    medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉" if rank==3 else "⭐"
                    st.write(f"{medal} **{user}** — {score} points")
                user_scores = dict(leaderboard)
                if username in user_scores:
                    user_rank = [u for u,_ in leaderboard].index(username)+1
                    st.markdown(f"---\n### 👤 Your Rank: **#{user_rank}** with **{user_scores[username]} points**")
