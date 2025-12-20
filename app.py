from flask import Flask, request

web = Flask(__name__)
users_db = {}
User_registration = """
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
    </body>
    </html>
"""

@web.route('/')
def home():
    return User_registration

@web.route('/register', methods=['POST'])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if username in users_db:
        return f"<h3>Error: User {username} already exists!</h3><a href='/'>Try again</a>"
    
    users_db[username] = {"email": email, "password": password}
    return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Success</title></head>
        <body>
            <h2 style="color: green;">Registration Successful!</h2>
            <p>Welcome, <strong>{username}</strong>. Your account with {email} has been created.</p>
            <br>
            <a href="/">Back to Register</a>
        </body>
        </html>
    """

if __name__ == "__main__":
    web.run(debug=True)