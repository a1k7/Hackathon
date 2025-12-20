from flask import Flask, request

app = Flask(__name__)


users_db = {}


register_page = """
<!DOCTYPE html>
<html>
<head><title>Register</title></head>
<body>
    <h2>Register Yourself</h2>
    <form method="POST" action="/register">
        <label>Username:</label><br>
        <input type="text" name="username" required><br><br>

        <label>Email:</label><br>
        <input type="email" name="email" required><br><br>

        <label>Password:</label><br>
        <input type="password" name="password" required><br><br>

        <button type="submit">Register</button>
    </form>
    <br>
    <a href="/login">Already have an account? Login</a>
</body>
</html>
"""


login_page = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <h2>Login</h2>
    <form method="POST">
        <label>Username:</label><br>
        <input type="text" name="username" required><br><br>

        <label>Password:</label><br>
        <input type="password" name="password" required><br><br>

        <button type="submit">Login</button>
    </form>
    <br>
    <a href="/">New user? Register</a>
</body>
</html>
"""
@app.route("/")
def home():
    return register_page


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if username in users_db:
        return "<h3>User already exists!</h3><a href='/'>Try again</a>"

    users_db[username] = {
        "email": email,
        "password": password
    }

    return f"""
    <h2 style="color:green;">Registration Successful!</h2>
    <p>Welcome {username}</p>
    <a href="/login">Go to Login</a>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users_db and users_db[username]["password"] == password:
            return f"<h2 style='color:green;'>Login Successful! Welcome {username}</h2>"
        else:
            return "<h3>Invalid Username or Password</h3><a href='/login'>Try again</a>"

    return login_page



if __name__ == "__main__":
    app.run(debug=True)
