import streamlit as st
import mysql.connector
from streamlit import session_state
import random
from datetime import datetime


class User:
    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password
        self.logged_in = False


class Quiz:
    def __init__(self):
        self.questions = {
            "What is the output of the following code? \n\nx = 5\ny = 2\nprint(x ** y)": ["25", "10", "32", "7"],
            "What is the correct way to declare a tuple in Python?": ["my_tuple = (1, 2, 3)", "my_tuple = [1, 2, 3]", "my_tuple = {1, 2, 3}", "my_tuple = '1, 2, 3'"],
            "Which of the following data types is mutable?": ["List", "Tuple", "String", "Set"],
            "What does the len() function do in Python?": ["Returns the length of a list, tuple, or string", "Returns the largest element in a list or tuple", "Returns the smallest element in a list or tuple", "Returns the sum of all elements in a list or tuple"],
            "What will be the output of the following code? \n\nmy_list = [1, 2, 3, 4, 5]\nprint(my_list[2:4])": ["[3,4]", "[2, 3]", "[1,2]", "[4, 5]"],
            "What is the output of the following code? \n\ndef add(a, b=3):\n    return a + b\n\nprint(add(5))": ["8", "5", "3", "Error"],
            "How can you open a file named 'data.txt' in read mode in Python?": ["file = open('data.txt', 'r')", "file = open('data.txt', 'w')", "file = open('data.txt', 'a')", "file = open('data.txt', 'rb')"],
            "What is the correct way to import a module named 'math' in Python?": ["import math", "include math", "import Math", "from math import *"],
            "What will be the output of the following code? \n\nmy_dict = {'a': 1, 'b': 2, 'c': 3}\ndel my_dict['b']\nprint(my_dict)": ["{'a': 1, 'c': 3}", "{'a': 1, 'b': 2}", "{'b': 2, 'c': 3}", "Error"],
            "What is the result of the expression 5 == 5.0?": ["True", "False", "None", "Error"]
        }
        self.db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="userdata"
        )
        self.cursor = self.db_connection.cursor()

    def register(self, name, username, password):
        sql = "INSERT INTO user (name, username, password) VALUES (%s, %s, %s)"
        val = (name, username, password)
        try:
            self.cursor.execute(sql, val)
            self.db_connection.commit()
            st.success("Registration successful.")
        except mysql.connector.Error as err:
            st.error("Error during registration: {}".format(err))

    def login(self, username, password):
        sql = "SELECT * FROM user WHERE username = %s AND password = %s"
        val = (username, password)
        self.cursor.execute(sql, val)
        user = self.cursor.fetchone()
        if user:
            session_state.user = User(user[1], user[2], user[3])
            session_state.user.logged_in = True
            st.success("Login successful.")
        else:
            st.error("Invalid username or password.")

    def profile(self):
        if hasattr(session_state, "user") and session_state.user.logged_in:
            st.write("Name:", session_state.user.name)
            st.write("Username:", session_state.user.username)
            new_password = st.text_input(
                "Enter new password:", type="password")
            if st.button("Change Password"):
                sql = "UPDATE user SET password = %s WHERE username = %s"
                val = (new_password, session_state.user.username)
                try:
                    self.cursor.execute(sql, val)
                    self.db_connection.commit()
                    st.success("Password changed successfully.")
                except mysql.connector.Error as err:
                    st.error("Error changing password: {}".format(err))
        else:
            st.warning("Please log in to view profile.")

    def attempt_quiz(self):
        if hasattr(session_state, "user") and session_state.user.logged_in:
            correct_answers = 0
            user_answers = {}
            if not hasattr(session_state, "shuffled_questions"):
                session_state.shuffled_questions = list(self.questions.items())
                random.shuffle(session_state.shuffled_questions)
                session_state.correct_options = {}
                for question, options in session_state.shuffled_questions:
                    session_state.correct_options[question] = options[0]
                    random.shuffle(options)
            for i, (question, options) in enumerate(session_state.shuffled_questions, start=1):
                st.write(f"Question {i}: {question}")
                correct_option = session_state.correct_options[question]
                user_answer = st.radio(
                    f"Select an option for Question {i}", options=options, index=None, key=f"{question}_{i}")
                if user_answer is not None:
                    user_answers[question] = user_answer
                    if user_answer == correct_option:
                        st.success("Correct!")
                        correct_answers += 1
                    else:
                        st.error("Incorrect!")
            if user_answers:
                self.store_quiz_results(correct_answers, len(
                    session_state.shuffled_questions))
            else:
                st.warning("No answers selected. Quiz not completed.")
            return user_answers, correct_answers
        else:
            st.warning("Please log in to attempt the quiz.")

    def store_quiz_results(self, correct_answers, total_questions):
        if hasattr(session_state, "user") and session_state.user.logged_in:
            cursor = self.db_connection.cursor()
            sql = "INSERT INTO quiz_results (user_id, attempted_on, correct_answers, total_questions) VALUES (%s, %s, %s, %s)"
            val = (session_state.user.username, datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"), correct_answers, total_questions)
            try:
                cursor.execute(sql, val)
                self.db_connection.commit()
            except mysql.connector.Error as err:
                st.error("Error storing quiz results: {}".format(err))
        else:
            st.warning("Please log in to attempt the quiz.")

    def display_results(self):
        if hasattr(session_state, "user") and session_state.user.logged_in:
            st.write("Quiz results:")
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT * FROM quiz_results WHERE user_id = %s ORDER BY attempted_on DESC", (session_state.user.username,))
            quiz_attempt = cursor.fetchone()
            if quiz_attempt:
                st.write("Attempted on:", quiz_attempt[2])
                st.write("Correct answers: ", quiz_attempt[3])
                st.write("Total questions: ", quiz_attempt[4])
                st.write("Score: {}%".format(
                    (quiz_attempt[3] / quiz_attempt[4]) * 100))
            else:
                st.warning("You haven't attempted the quiz yet.")
        else:
            st.warning("Please log in to view results.")

    def logout(self):
        if hasattr(session_state, "user") and session_state.user.logged_in:
            session_state.user.logged_in = False
            st.success("Logged out successfully.")
        else:
            st.warning("You are not logged in.")


def main():
    st.title("Quiz Program with Streamlit")
    quiz = Quiz()
    menu = ["Register", "Login", "Profile",
            "Attempt Quiz", "Results", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        name = st.text_input("Enter your name:")
        username = st.text_input("Enter username:")
        password = st.text_input("Enter password:", type="password")
        if st.button("Register"):
            quiz.register(name, username, password)

    elif choice == "Login":
        if not hasattr(session_state, "user") or not session_state.user.logged_in:
            username = st.text_input("Enter username:")
            password = st.text_input("Enter password:", type="password")
            if st.button("Login"):
                quiz.login(username, password)
        else:
            st.warning("You are already logged in.")

    elif choice == "Profile":
        quiz.profile()

    elif choice == "Attempt Quiz":
        user_answers, correct_answers = quiz.attempt_quiz()

    elif choice == "Results":
        quiz.display_results()

    elif choice == "Logout":
        quiz.logout()


if __name__ == "__main__":
    main()