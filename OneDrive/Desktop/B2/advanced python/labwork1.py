students = []
courses = []
marks = {}

# ------------------------------
# 1. Input functions
# ------------------------------

def input_students():
    n = int(input("Enter number of students: "))
    for _ in range(n):
        sid = input("Student ID: ")
        name = input("Student name: ")
        dob = input("Student DoB: ")
        students.append({"id": sid, "name": name, "dob": dob})
    print("\n✔ Students added!\n")

def input_courses():
    n = int(input("Enter number of courses: "))
    for _ in range(n):
        cid = input("Course ID: ")
        name = input("Course name: ")
        courses.append({"id": cid, "name": name})
    print("\n✔ Courses added!\n")

def input_marks():
    course_id = input("Enter course ID to input marks: ")
    # Check valid ID
    if course_id not in [c["id"] for c in courses]:
        print("❌ Course not found!")
        return
    
    if course_id not in marks:
        marks[course_id] = {}

    for stu in students:
        m = float(input(f"Mark for {stu['name']} (ID: {stu['id']}): "))
        marks[course_id][stu['id']] = m
    
    print("\n✔ Marks added!\n")

# ------------------------------
# 2. Display functions
# ------------------------------

def list_students():
    print("\n--- Student List ---")
    for s in students:
        print(f"{s['id']} - {s['name']} - {s['dob']}")

def list_courses():
    print("\n--- Course List ---")
    for c in courses:
        print(f"{c['id']} - {c['name']}")

def show_marks():
    course_id = input("Enter course ID to show marks: ")
    if course_id not in marks:
        print("❌ No marks for this course yet!")
        return
    
    print(f"\n--- Marks for course {course_id} ---")
    for stu in students:
        sid = stu["id"]
        print(f"{stu['name']}: {marks[course_id].get(sid, 'N/A')}")

# ------------------------------
# 3. Menu system
# ------------------------------

def menu():
    while True:
        print("\n======================")
        print(" Student Mark System ")
        print("======================")
        print("1. Input students")
        print("2. Input courses")
        print("3. Input marks")
        print("4. List students")
        print("5. List courses")
        print("6. Show marks")
        print("0. Exit")
        print("======================")

        choice = input("Choose an option: ")

        if choice == "1":
            input_students()
        elif choice == "2":
            input_courses()
        elif choice == "3":
            input_marks()
        elif choice == "4":
            list_students()
        elif choice == "5":
            list_courses()
        elif choice == "6":
            show_marks()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option!")

# Run the menu
menu()
