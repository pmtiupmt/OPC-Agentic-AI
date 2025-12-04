class Student:
    def __init__(self, id = '', name = '', dob = ''):
        self._id = id
        self._name = name
        self._dob = dob
        self.mark = {}
    def input(self):
        self._id = input("ID: ")
        self._name = input("Name: ")
        self._dob = input("Date of birth: ")
    def get_id(self):
        return self._id
    def get_name(self):
        return self._name
    def get_dob(self):
        return self._dob
    def __str__(self):
        return f"ID: {self._id}, Name: {self._name}, DoB: {self._dob}"
class Course:
    def __init__(self, id = '', name = ''):
        self._id = id
        self._name = name
    def input(self):
        self._id = input("Course ID: ")
        self._name = input("Course name: ")
    def get_id(self):
        return self._id
    def get_name(self):
        return self._name
    def __str__(self):
        return f"ID: {self._id}, Name: {self._name}"
class Mark:
    def __init__(self):
        self.students = []
        self.courses = []
        self.mark = {}
    def input_student(self):
        n = int(input("Enter the number of students: "))
        for i in range(n):
            print(f'\nStudent {i + 1}: ')
            s = Student()
            s.input()
            self.students.append(s)
    def input_course(self):
        n = int(input("Enter the number of courses: "))
        for i in range(n):
            print(f'Course {i + 1}: ')
            c = Course()
            c.input()
            self.courses.append(c)
    def input_mark(self):
        c = input("Select a course: ")
        for s in self.students:
            mark = float(input(f'Enter mark for {s.get_name()}: '))
            self.mark[(s.get_id(), c)] = mark
    def list_student(self):
        print("List student:\n")
        for i in self.students:
            print(i)
    def list_course(self):
        print("List course:\n")
        for j in self.courses:
            print(j)
    def show_mark(self, course_id):
        print(f"Marks for course {course_id}:\n")
        for k in self.students:
            key = (k.get_id(), course_id)
            if key in self.mark:
                print(f"{k.get_name}: {self.mark[key]}\n")
            else:
                print(f"{k.get_name}: No mark\n")
    def menu(self):
        self.input_student()
        self.input_course()
        self.input_mark()
        self.list_student()
        self.list_course()
        c = input("Enter course ID to show mark: ")
        self.show_mark(c)
run = Mark()
run.menu()