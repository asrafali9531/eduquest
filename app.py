from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os

from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "eduquest_secret_key_2026"

DATABASE = "eduquest.db"

ADMIN_EMAIL = "admin@eduquest.com"
ADMIN_PASSWORD = "admin123"


# =========================================================
# OPENAI CLIENT
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            score INTEGER DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # COURSES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            level TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # QUESTIONS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # BADGES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # USER BADGES
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL
        )
    """)

    # -----------------------------------------------------
    # COURSE PROGRESS
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            UNIQUE(user_id, course_id)
        )
    """)

    # -----------------------------------------------------
    # AI CHAT HISTORY
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # DEFAULT COURSES
    # =====================================================

    cursor.execute("SELECT COUNT(*) FROM courses")

    if cursor.fetchone()[0] == 0:

        courses_data = [
            (
                "Python Programming",
                "Learn Python from beginner to intermediate level.",
                "Beginner"
            ),
            (
                "C Programming",
                "Learn the fundamentals of C programming.",
                "Beginner"
            ),
            (
                "Web Development",
                "Learn HTML, CSS and basic JavaScript.",
                "Beginner"
            ),
            (
                "Data Structures",
                "Learn arrays, stacks, queues and linked lists.",
                "Intermediate"
            )
        ]

        cursor.executemany("""
            INSERT INTO courses
            (title, description, level)
            VALUES (?, ?, ?)
        """, courses_data)

    # =====================================================
    # DEFAULT QUESTIONS
    # =====================================================

    cursor.execute("SELECT COUNT(*) FROM questions")

    if cursor.fetchone()[0] == 0:

        questions_data = [
            (
                1,
                "Which keyword is used to define a function in Python?",
                "function",
                "def",
                "fun",
                "define",
                "def"
            ),
            (
                1,
                "Which symbol is used for comments in Python?",
                "//",
                "#",
                "/*",
                "--",
                "#"
            ),
            (
                1,
                "Which data type stores True or False?",
                "int",
                "string",
                "boolean",
                "float",
                "boolean"
            ),
            (
                1,
                "Which function is used to display output?",
                "print()",
                "display()",
                "show()",
                "output()",
                "print()"
            ),
            (
                2,
                "Which function is the starting point of a C program?",
                "start()",
                "main()",
                "begin()",
                "run()",
                "main()"
            ),
            (
                2,
                "Which symbol is used to end a C statement?",
                ".",
                ":",
                ";",
                ",",
                ";"
            ),
            (
                3,
                "Which language is used to structure a webpage?",
                "CSS",
                "HTML",
                "Python",
                "SQL",
                "HTML"
            ),
            (
                3,
                "Which language is used for webpage styling?",
                "HTML",
                "CSS",
                "Python",
                "C",
                "CSS"
            ),
            (
                4,
                "Which data structure follows FIFO?",
                "Stack",
                "Queue",
                "Tree",
                "Graph",
                "Queue"
            ),
            (
                4,
                "Which data structure follows LIFO?",
                "Queue",
                "Array",
                "Stack",
                "Graph",
                "Stack"
            )
        ]

        cursor.executemany("""
            INSERT INTO questions
            (
                course_id,
                question,
                option1,
                option2,
                option3,
                option4,
                answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, questions_data)

    # =====================================================
    # DEFAULT BADGES
    # =====================================================

    cursor.execute("SELECT COUNT(*) FROM badges")

    if cursor.fetchone()[0] == 0:

        badges_data = [
            (
                "First Step",
                "Complete your first quiz.",
                "🚀"
            ),
            (
                "Quiz Master",
                "Score 80% or more in a quiz.",
                "🏆"
            ),
            (
                "Learning Star",
                "Reach 100 points.",
                "⭐"
            ),
            (
                "Skill Explorer",
                "Explore different courses.",
                "🎯"
            )
        ]

        cursor.executemany("""
            INSERT INTO badges
            (name, description, icon)
            VALUES (?, ?, ?)
        """, badges_data)

    conn.commit()

    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    conn = get_db()

    courses = conn.execute("""
        SELECT
            id,
            title,
            title AS name,
            description,
            level
        FROM courses
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        courses=courses
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not email or not password:

            flash("Please fill all fields.")

            return redirect(
                url_for("register")
            )

        hashed_password = generate_password_hash(
            password
        )

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                hashed_password
            ))

            conn.commit()

            flash(
                "Registration successful! Please login."
            )

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            flash(
                "Email already registered."
            )

        finally:

            conn.close()

    return render_template(
        "register.html"
    )


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    return register()


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password."
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if user is None:

        conn.close()

        session.clear()

        return redirect(
            url_for("login")
        )

    badges = conn.execute("""
        SELECT badges.*
        FROM badges
        INNER JOIN user_badges
        ON badges.id = user_badges.badge_id
        WHERE user_badges.user_id = ?
        ORDER BY badges.id
    """, (
        session["user_id"],
    )).fetchall()

    progress = conn.execute("""
        SELECT
            courses.id,
            courses.title,
            courses.description,
            courses.level,
            COALESCE(
                course_progress.progress,
                0
            ) AS progress
        FROM courses
        LEFT JOIN course_progress
        ON courses.id = course_progress.course_id
        AND course_progress.user_id = ?
        ORDER BY courses.id
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        badges=badges,
        progress=progress
    )


# =========================================================
# AI CHAT PAGE
# =========================================================

@app.route("/ai-chat")
def ai_chat_page():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db()

    history = conn.execute("""
        SELECT
            role,
            message,
            created_at
        FROM ai_chat_history
        WHERE user_id = ?
        ORDER BY id ASC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "ai_chat.html",
        history=history
    )


# =========================================================
# AI CHAT API
# =========================================================

@app.route("/ai_chat", methods=["POST"])
def ai_chat():

    if "user_id" not in session:

        return jsonify({
            "reply": "Please login first."
        }), 401

    if client is None:

        return jsonify({
            "reply": "AI service is not configured yet. Please check your OPENAI_API_KEY in the .env file."
        }), 500

    data = request.get_json(
        silent=True
    ) or {}

    user_message = data.get(
        "message",
        ""
    ).strip()

    if not user_message:

        return jsonify({
            "reply": "Please type a question first."
        }), 400

    # -----------------------------------------------------
    # MESSAGE LENGTH LIMIT
    # -----------------------------------------------------

    if len(user_message) > 4000:

        return jsonify({
            "reply": "Please keep your question under 4000 characters."
        }), 400

    conn = get_db()

    # -----------------------------------------------------
    # SAVE USER MESSAGE
    # -----------------------------------------------------

    conn.execute("""
        INSERT INTO ai_chat_history
        (
            user_id,
            role,
            message
        )
        VALUES (?, ?, ?)
    """, (
        session["user_id"],
        "user",
        user_message
    ))

    conn.commit()

    try:

        # -------------------------------------------------
        # AI RESPONSE
        # -------------------------------------------------

        response = client.responses.create(

            model="gpt-5.6-luna",

            instructions=(
                "You are EduQuest AI, a friendly educational assistant. "
                "Help students understand programming, computer science, "
                "web development, mathematics, and general study topics. "
                "Explain concepts simply and clearly. "
                "When explaining code, use beginner-friendly examples. "
                "Use short sections and examples when helpful. "
                "Do not pretend to know information you are unsure about."
            ),

            input=user_message,

            max_output_tokens=800

        )

        reply = response.output_text

        if not reply:

            reply = "Sorry, I could not generate an answer."

        # -------------------------------------------------
        # SAVE AI RESPONSE
        # -------------------------------------------------

        conn.execute("""
            INSERT INTO ai_chat_history
            (
                user_id,
                role,
                message
            )
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            "assistant",
            reply
        ))

        conn.commit()

        conn.close()

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print("OPENAI ERROR:", e)

        conn.close()

        return jsonify({
            "reply": "Sorry, AI service is temporarily unavailable. Please try again."
        }), 500


# =========================================================
# CLEAR AI CHAT HISTORY
# =========================================================

@app.route(
    "/clear_ai_history",
    methods=["POST"]
)
def clear_ai_history():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = get_db()

    conn.execute("""
        DELETE FROM ai_chat_history
        WHERE user_id = ?
    """, (
        session["user_id"],
    ))

    conn.commit()

    conn.close()

    return jsonify({
        "success": True,
        "message": "Chat history cleared successfully."
    })


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if user is None:

        conn.close()

        session.clear()

        return redirect(
            url_for("login")
        )

    badges = conn.execute("""
        SELECT badges.*
        FROM badges
        INNER JOIN user_badges
        ON badges.id = user_badges.badge_id
        WHERE user_badges.user_id = ?
        ORDER BY badges.id
    """, (
        session["user_id"],
    )).fetchall()

    progress = conn.execute("""
        SELECT
            courses.title,
            courses.level,
            COALESCE(
                course_progress.progress,
                0
            ) AS progress
        FROM courses
        LEFT JOIN course_progress
        ON courses.id = course_progress.course_id
        AND course_progress.user_id = ?
        ORDER BY courses.id
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        badges=badges,
        progress=progress
    )


# =========================================================
# COURSES
# =========================================================

@app.route("/courses")
def courses():

    conn = get_db()

    courses = conn.execute("""
        SELECT
            id,
            title,
            title AS name,
            description,
            level
        FROM courses
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "courses.html",
        courses=courses
    )


# =========================================================
# QUIZ
# =========================================================

@app.route("/quiz/<int:course_id>")
def quiz(course_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db()

    course = conn.execute("""
        SELECT
            id,
            title,
            title AS name,
            description,
            level
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    if course is None:

        conn.close()

        flash(
            "Course not found."
        )

        return redirect(
            url_for("courses")
        )

    questions = conn.execute("""
        SELECT
            id,
            course_id,
            question,
            option1,
            option2,
            option3,
            option4,
            answer
        FROM questions
        WHERE course_id = ?
        ORDER BY id
    """, (
        course_id,
    )).fetchall()

    fixed_questions = []

    for q in questions:

        fixed_questions.append({

            "id": q["id"],

            "question": q["question"],

            "option_a": q["option1"],

            "option_b": q["option2"],

            "option_c": q["option3"],

            "option_d": q["option4"],

            "answer": q["answer"]

        })

    conn.close()

    return render_template(
        "quiz.html",
        course=course,
        questions=fixed_questions,
        course_id=course_id
    )


# =========================================================
# SUBMIT QUIZ
# =========================================================

@app.route(
    "/submit_quiz/<int:course_id>",
    methods=["POST"]
)
def submit_quiz(course_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db()

    questions = conn.execute("""
        SELECT *
        FROM questions
        WHERE course_id = ?
        ORDER BY id
    """, (
        course_id,
    )).fetchall()

    if not questions:

        conn.close()

        flash(
            "No questions available for this course."
        )

        return redirect(
            url_for("courses")
        )

    score = 0

    for question in questions:

        user_answer = request.form.get(
            f"question_{question['id']}",
            ""
        )

        if user_answer == "A":

            selected_answer = question["option1"]

        elif user_answer == "B":

            selected_answer = question["option2"]

        elif user_answer == "C":

            selected_answer = question["option3"]

        elif user_answer == "D":

            selected_answer = question["option4"]

        else:

            selected_answer = ""

        if selected_answer == question["answer"]:

            score += 10

    total_marks = len(questions) * 10

    percentage = 0

    if total_marks > 0:

        percentage = (
            score / total_marks
        ) * 100

    conn.execute("""
        UPDATE users
        SET score = score + ?
        WHERE id = ?
    """, (
        score,
        session["user_id"]
    ))

    progress_value = int(
        round(percentage)
    )

    old_progress = conn.execute("""
        SELECT progress
        FROM course_progress
        WHERE user_id = ?
        AND course_id = ?
    """, (
        session["user_id"],
        course_id
    )).fetchone()

    if old_progress is None:

        conn.execute("""
            INSERT INTO course_progress
            (
                user_id,
                course_id,
                progress
            )
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            course_id,
            progress_value
        ))

    else:

        if progress_value > old_progress["progress"]:

            conn.execute("""
                UPDATE course_progress
                SET progress = ?
                WHERE user_id = ?
                AND course_id = ?
            """, (
                progress_value,
                session["user_id"],
                course_id
            ))

    # -----------------------------------------------------
    # FIRST STEP BADGE
    # -----------------------------------------------------

    first_badge = conn.execute("""
        SELECT id
        FROM badges
        WHERE name = 'First Step'
    """).fetchone()

    if first_badge:

        conn.execute("""
            INSERT INTO user_badges
            (user_id, badge_id)
            SELECT ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM user_badges
                WHERE user_id = ?
                AND badge_id = ?
            )
        """, (
            session["user_id"],
            first_badge["id"],
            session["user_id"],
            first_badge["id"]
        ))

    # -----------------------------------------------------
    # QUIZ MASTER BADGE
    # -----------------------------------------------------

    if percentage >= 80:

        quiz_badge = conn.execute("""
            SELECT id
            FROM badges
            WHERE name = 'Quiz Master'
        """).fetchone()

        if quiz_badge:

            conn.execute("""
                INSERT INTO user_badges
                (user_id, badge_id)
                SELECT ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM user_badges
                    WHERE user_id = ?
                    AND badge_id = ?
                )
            """, (
                session["user_id"],
                quiz_badge["id"],
                session["user_id"],
                quiz_badge["id"]
            ))

    # -----------------------------------------------------
    # LEARNING STAR BADGE
    # -----------------------------------------------------

    updated_user = conn.execute("""
        SELECT score
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if updated_user and updated_user["score"] >= 100:

        star_badge = conn.execute("""
            SELECT id
            FROM badges
            WHERE name = 'Learning Star'
        """).fetchone()

        if star_badge:

            conn.execute("""
                INSERT INTO user_badges
                (user_id, badge_id)
                SELECT ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM user_badges
                    WHERE user_id = ?
                    AND badge_id = ?
            )
            """, (
                session["user_id"],
                star_badge["id"],
                session["user_id"],
                star_badge["id"]
            ))

    # -----------------------------------------------------
    # SKILL EXPLORER BADGE
    # -----------------------------------------------------

    explored_courses = conn.execute("""
        SELECT COUNT(*)
        FROM course_progress
        WHERE user_id = ?
        AND progress > 0
    """, (
        session["user_id"],
    )).fetchone()[0]

    if explored_courses >= 2:

        explorer_badge = conn.execute("""
            SELECT id
            FROM badges
            WHERE name = 'Skill Explorer'
        """).fetchone()

        if explorer_badge:

            conn.execute("""
                INSERT INTO user_badges
                (user_id, badge_id)
                SELECT ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM user_badges
                    WHERE user_id = ?
                    AND badge_id = ?
                )
            """, (
                session["user_id"],
                explorer_badge["id"],
                session["user_id"],
                explorer_badge["id"]
            ))

    conn.commit()

    conn.close()

    return render_template(
        "result.html",
        score=score,
        total=total_marks,
        percentage=percentage
    )


# =========================================================
# LEADERBOARD
# =========================================================

@app.route("/leaderboard")
def leaderboard():

    conn = get_db()

    users = conn.execute("""
        SELECT
            name,
            score
        FROM users
        ORDER BY score DESC, name ASC
        LIMIT 20
    """).fetchall()

    conn.close()

    return render_template(
        "leaderboard.html",
        users=users
    )


# =========================================================
# BADGES
# =========================================================

@app.route("/badges")
def badges():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db()

    badges = conn.execute("""
        SELECT
            badges.id,
            badges.name,
            badges.description,
            badges.icon,
            CASE
                WHEN user_badges.user_id IS NOT NULL
                THEN 1
                ELSE 0
            END AS unlocked
        FROM badges
        LEFT JOIN user_badges
        ON badges.id = user_badges.badge_id
        AND user_badges.user_id = ?
        ORDER BY badges.id
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "badges.html",
        badges=badges
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            email == ADMIN_EMAIL
            and password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "Invalid admin email or password."
        )

    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN PROTECTION
# =========================================================

def admin_required():

    return session.get("admin") is True


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    users_count = conn.execute("""
        SELECT COUNT(*) AS total
        FROM users
    """).fetchone()["total"]

    courses_count = conn.execute("""
        SELECT COUNT(*) AS total
        FROM courses
    """).fetchone()["total"]

    questions_count = conn.execute("""
        SELECT COUNT(*) AS total
        FROM questions
    """).fetchone()["total"]

    badges_count = conn.execute("""
        SELECT COUNT(*) AS total
        FROM badges
    """).fetchone()["total"]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        users_count=users_count,
        courses_count=courses_count,
        questions_count=questions_count,
        badges_count=badges_count
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for("index")
    )


# =========================================================
# ADMIN USERS
# =========================================================

@app.route("/admin/users")
def admin_users():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    users = conn.execute("""
        SELECT
            id,
            name,
            email,
            score
        FROM users
        ORDER BY score DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users
    )


# =========================================================
# ADMIN COURSES
# =========================================================

@app.route("/admin/courses")
def admin_courses():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    courses = conn.execute("""
        SELECT *
        FROM courses
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "admin_courses.html",
        courses=courses
    )


# =========================================================
# ADMIN ADD COURSE
# =========================================================

@app.route(
    "/admin/courses/add",
    methods=["GET", "POST"]
)
def admin_add_course():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        level = request.form.get(
            "level",
            ""
        ).strip()

        if not title or not description or not level:

            flash(
                "Please fill all fields."
            )

            return redirect(
                url_for("admin_add_course")
            )

        conn = get_db()

        conn.execute("""
            INSERT INTO courses
            (
                title,
                description,
                level
            )
            VALUES (?, ?, ?)
        """, (
            title,
            description,
            level
        ))

        conn.commit()

        conn.close()

        flash(
            "Course added successfully!"
        )

        return redirect(
            url_for("admin_courses")
        )

    return render_template(
        "admin_add_course.html"
    )


# =========================================================
# ADMIN EDIT COURSE
# =========================================================

@app.route(
    "/admin/courses/edit/<int:course_id>",
    methods=["GET", "POST"]
)
def admin_edit_course(course_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    course = conn.execute("""
        SELECT *
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    if course is None:

        conn.close()

        flash(
            f"Course ID {course_id} not found."
        )

        return redirect(
            url_for("admin_courses")
        )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        level = request.form.get(
            "level",
            ""
        ).strip()

        if not title or not description or not level:

            conn.close()

            flash(
                "Please fill all fields."
            )

            return redirect(
                url_for(
                    "admin_edit_course",
                    course_id=course_id
                )
            )

        conn.execute("""
            UPDATE courses
            SET
                title = ?,
                description = ?,
                level = ?
            WHERE id = ?
        """, (
            title,
            description,
            level,
            course_id
        ))

        conn.commit()

        conn.close()

        flash(
            "Course updated successfully!"
        )

        return redirect(
            url_for("admin_courses")
        )

    conn.close()

    return render_template(
        "admin_edit_course.html",
        course=course
    )


# =========================================================
# ADMIN DELETE COURSE
# =========================================================

@app.route(
    "/admin/courses/delete/<int:course_id>",
    methods=["POST"]
)
def admin_delete_course(course_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    course = conn.execute("""
        SELECT id
        FROM courses
        WHERE id = ?
    """, (
        course_id,
    )).fetchone()

    if course is None:

        conn.close()

        flash(
            "Course not found."
        )

        return redirect(
            url_for("admin_courses")
        )

    conn.execute("""
        DELETE FROM questions
        WHERE course_id = ?
    """, (
        course_id,
    ))

    conn.execute("""
        DELETE FROM course_progress
        WHERE course_id = ?
    """, (
        course_id,
    ))

    conn.execute("""
        DELETE FROM courses
        WHERE id = ?
    """, (
        course_id,
    ))

    conn.commit()

    conn.close()

    flash(
        "Course and its questions deleted successfully!"
    )

    return redirect(
        url_for("admin_courses")
    )


# =========================================================
# ADMIN QUESTIONS
# =========================================================

@app.route("/admin/questions")
def admin_questions():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    questions = conn.execute("""
        SELECT
            questions.*,
            courses.title AS course_title
        FROM questions
        LEFT JOIN courses
        ON questions.course_id = courses.id
        ORDER BY questions.id
    """).fetchall()

    conn.close()

    return render_template(
        "admin_questions.html",
        questions=questions
    )


# =========================================================
# ADMIN ADD QUESTION
# =========================================================

@app.route(
    "/admin/questions/add",
    methods=["GET", "POST"]
)
def admin_add_question():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    courses = conn.execute("""
        SELECT *
        FROM courses
        ORDER BY title
    """).fetchall()

    if request.method == "POST":

        course_id = request.form.get(
            "course_id",
            ""
        )

        question = request.form.get(
            "question",
            ""
        ).strip()

        option1 = request.form.get(
            "option1",
            ""
        ).strip()

        option2 = request.form.get(
            "option2",
            ""
        ).strip()

        option3 = request.form.get(
            "option3",
            ""
        ).strip()

        option4 = request.form.get(
            "option4",
            ""
        ).strip()

        selected_answer = request.form.get(
            "answer",
            ""
        ).strip()

        answer_map = {
            "Option 1": option1,
            "Option 2": option2,
            "Option 3": option3,
            "Option 4": option4,
            "A": option1,
            "B": option2,
            "C": option3,
            "D": option4
        }

        real_answer = answer_map.get(
            selected_answer,
            selected_answer
        )

        if not all([
            course_id,
            question,
            option1,
            option2,
            option3,
            option4,
            real_answer
        ]):

            conn.close()

            flash(
                "Please fill all fields."
            )

            return redirect(
                url_for("admin_add_question")
            )

        conn.execute("""
            INSERT INTO questions
            (
                course_id,
                question,
                option1,
                option2,
                option3,
                option4,
                answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            course_id,
            question,
            option1,
            option2,
            option3,
            option4,
            real_answer
        ))

        conn.commit()

        conn.close()

        flash(
            "Question added successfully!"
        )

        return redirect(
            url_for("admin_questions")
        )

    conn.close()

    return render_template(
        "admin_add_question.html",
        courses=courses
    )


# =========================================================
# ADMIN EDIT QUESTION
# =========================================================

@app.route(
    "/admin/questions/edit/<int:question_id>",
    methods=["GET", "POST"]
)
def admin_edit_question(question_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    question = conn.execute("""
        SELECT
            id,
            course_id,
            question,
            option1,
            option2,
            option3,
            option4,
            answer
        FROM questions
        WHERE id = ?
    """, (
        question_id,
    )).fetchone()

    if question is None:

        conn.close()

        flash(
            f"Question ID {question_id} not found."
        )

        return redirect(
            url_for("admin_questions")
        )

    courses = conn.execute("""
        SELECT
            id,
            title
        FROM courses
        ORDER BY title
    """).fetchall()

    if request.method == "POST":

        course_id = request.form.get(
            "course_id",
            ""
        ).strip()

        question_text = request.form.get(
            "question",
            ""
        ).strip()

        option1 = request.form.get(
            "option1",
            ""
        ).strip()

        option2 = request.form.get(
            "option2",
            ""
        ).strip()

        option3 = request.form.get(
            "option3",
            ""
        ).strip()

        option4 = request.form.get(
            "option4",
            ""
        ).strip()

        selected_answer = request.form.get(
            "answer",
            ""
        ).strip()

        answer_map = {
            "Option 1": option1,
            "Option 2": option2,
            "Option 3": option3,
            "Option 4": option4,
            "A": option1,
            "B": option2,
            "C": option3,
            "D": option4
        }

        answer = answer_map.get(
            selected_answer,
            ""
        )

        if not all([
            course_id,
            question_text,
            option1,
            option2,
            option3,
            option4,
            selected_answer,
            answer
        ]):

            conn.close()

            flash(
                "Please fill all fields."
            )

            return redirect(
                url_for(
                    "admin_edit_question",
                    question_id=question_id
                )
            )

        conn.execute("""
            UPDATE questions
            SET
                course_id = ?,
                question = ?,
                option1 = ?,
                option2 = ?,
                option3 = ?,
                option4 = ?,
                answer = ?
            WHERE id = ?
        """, (
            course_id,
            question_text,
            option1,
            option2,
            option3,
            option4,
            answer,
            question_id
        ))

        conn.commit()

        conn.close()

        flash(
            "Question updated successfully!"
        )

        return redirect(
            url_for("admin_questions")
        )

    conn.close()

    return render_template(
        "admin_edit_question.html",
        question=question,
        courses=courses
    )


# =========================================================
# ADMIN DELETE QUESTION
# =========================================================

@app.route(
    "/admin/questions/delete/<int:question_id>",
    methods=["POST"]
)
def admin_delete_question(question_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    question = conn.execute("""
        SELECT id
        FROM questions
        WHERE id = ?
    """, (
        question_id,
    )).fetchone()

    if question is None:

        conn.close()

        flash(
            "Question not found."
        )

        return redirect(
            url_for("admin_questions")
        )

    conn.execute("""
        DELETE FROM questions
        WHERE id = ?
    """, (
        question_id,
    ))

    conn.commit()

    conn.close()

    flash(
        "Question deleted successfully!"
    )

    return redirect(
        url_for("admin_questions")
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )
