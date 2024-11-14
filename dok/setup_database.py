import psycopg2
from faker import Faker
import random

# Налаштування з'єднання з PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="university",
    user="user",
    password="password"
)
cursor = conn.cursor()

# Створення таблиць
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id SERIAL PRIMARY KEY,
        last_name VARCHAR(50) NOT NULL,
        first_name VARCHAR(50) NOT NULL,
        address VARCHAR(100),
        phone VARCHAR(15) CHECK (phone ~ '^\\d{10}$'),
        course INT CHECK (course BETWEEN 1 AND 4),
        faculty VARCHAR(50) CHECK (faculty IN ('аграрного менеджменту', 'економіки', 'інформаційних технологій')),
        group_name VARCHAR(10),
        is_leader BOOLEAN DEFAULT FALSE
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        hours_per_semester INT,
        semesters INT
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS exams (
        exam_id SERIAL PRIMARY KEY,
        exam_date DATE,
        student_id INT REFERENCES students(student_id),
        subject_id INT REFERENCES subjects(subject_id),
        grade INT CHECK (grade BETWEEN 2 AND 5)
    );
''')

# Додавання даних
fake = Faker()

# Генерація студентів
for _ in range(11):  # 11 студентів
    phone_number = ''.join([str(fake.random_int(0, 9)) for _ in range(10)])
    cursor.execute('''
        INSERT INTO students (last_name, first_name, address, phone, course, faculty, group_name, is_leader)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        fake.last_name(),
        fake.first_name(),
        fake.address(),
        phone_number,
        fake.random_int(min=1, max=4),
        fake.random_element(elements=("аграрного менеджменту", "економіки", "інформаційних технологій")),
        fake.bothify(text="???-###"),
        fake.boolean()
    ))

# Генерація предметів
for i in range(3):  # 3 предмета
    cursor.execute('''
        INSERT INTO subjects (name, hours_per_semester, semesters)
        VALUES (%s, %s, %s)
    ''', (
        f"Subject {i+1}",
        random.randint(20, 100),
        random.randint(1, 2)
    ))

# Генерація іспитів
for student_id in range(1, 12):  # Для кожного студента
    for subject_id in range(1, 4):  # Для кожного предмета
        grade = random.randint(2, 5)
        cursor.execute('''
            INSERT INTO exams (exam_date, student_id, subject_id, grade)
            VALUES (CURRENT_DATE, %s, %s, %s)
        ''', (student_id, subject_id, grade))

conn.commit()
print("Дані успішно додано до бази.")

# Функція для отримання старостів
def get_leaders():
    cursor.execute('''
        SELECT last_name, first_name
        FROM students
        WHERE is_leader = TRUE
        ORDER BY last_name ASC;
    ''')
    for row in cursor.fetchall():
        print(row)

# Функція для отримання середнього балу для кожного студента
def get_average_grades():
    cursor.execute('''
        SELECT students.last_name, students.first_name, AVG(exams.grade) as average_grade
        FROM students
        JOIN exams ON students.student_id = exams.student_id
        GROUP BY students.student_id
    ''')
    for row in cursor.fetchall():
        print(f"{row[0]} {row[1]}: {row[2]:.2f}")

# Функція для підрахунку кількості годин для кожного предмета
def get_total_hours_per_subject():
    cursor.execute('''
        SELECT subjects.name, SUM(subjects.hours_per_semester * subjects.semesters) as total_hours
        FROM subjects
        GROUP BY subjects.subject_id
    ''')
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} hours")

# Функція для відображення успішності студентів по предмету
def get_success_by_subject(subject_id):
    cursor.execute('''
        SELECT students.last_name, students.first_name, exams.grade
        FROM exams
        JOIN students ON exams.student_id = students.student_id
        WHERE exams.subject_id = %s
    ''', (subject_id,))
    for row in cursor.fetchall():
        print(f"{row[0]} {row[1]}: {row[2]}")

# Функція для підрахунку кількості студентів на кожному факультеті
def count_students_per_faculty():
    cursor.execute('''
        SELECT faculty, COUNT(*) as student_count
        FROM students
        GROUP BY faculty
    ''')
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} students")

# Функція для відображення оцінок кожного студента по кожному предмету (перехресний запит)
def cross_tab_grades():
    cursor.execute('''
        SELECT students.last_name, students.first_name,
               MAX(CASE WHEN subjects.name = 'Subject 1' THEN exams.grade END) AS "Subject 1",
               MAX(CASE WHEN subjects.name = 'Subject 2' THEN exams.grade END) AS "Subject 2",
               MAX(CASE WHEN subjects.name = 'Subject 3' THEN exams.grade END) AS "Subject 3"
        FROM students
        JOIN exams ON students.student_id = exams.student_id
        JOIN subjects ON exams.subject_id = subjects.subject_id
        GROUP BY students.student_id
    ''')
    for row in cursor.fetchall():
        print(f"{row[0]} {row[1]} - Subject 1: {row[2]}, Subject 2: {row[3]}, Subject 3: {row[4]}")

# Виклик функцій для виконання запитів
print("Старости:")
get_leaders()

print("\nСередні бали студентів:")
get_average_grades()

print("\nЗагальна кількість годин для кожного предмета:")
get_total_hours_per_subject()

print("\nУспішність студентів по предмету (Subject 1):")
get_success_by_subject(1)

print("\nКількість студентів на кожному факультеті:")
count_students_per_faculty()

print("\nОцінки студентів по кожному предмету (перехресний запит):")
cross_tab_grades()

# Закриття з'єднання
cursor.close()
conn.close()
