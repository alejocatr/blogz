from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from utility import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100))
    body = db.Column(db.String(5000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)




@app.before_request
def require_login():
    # requires user be logged in before being allowed to create a new blog post
    allowed_routes = ['login', 'list_blogs', 'index', 'signup', 'static', 'logout']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')




# to handle signup.html post
@app.route('/signup', methods=["POST", "GET"])
def signup():
    # render signup template
    if request.method == "GET":
        return render_template('signup.html', page_title="signup")

    # define variables using form entries and database query
    username = request.form["username"]
    password = request.form["password"]
    verify = request.form["verify"]
    user = User.query.filter_by(username=username).first()

    # verification that username is filled in, is at least 3 characters long, and does not match a username in the database
    if username == "":
        username_error = "Name field cannot be blank"
    elif len(username) < 3:
        username_error = "Name must be at least three characters long"
    elif user: 
        username_error = "That username already exists.  Enter a different username."
    else:
        username_error = ""

    # verification that password is filled in and is at least 3 characters long
    if password == "" and not user: 
        password_error = "Password field cannot be blank"
    elif len(password) < 3 and not user: 
        password_error = "Password must be at least three characters long"
    else:
        password_error = ""

    # verification that verify password field is filled in and matches password
    if verify == "" and not user: 
        verify_error = "Verify Password field cannot be blank"
    elif verify != password and not user: 
        verify_error = "Passwords do not match"
    else:
        verify_error = ""

    # if there are no errors, adds new user to the database, creates a new session, and redirects user to newpost template
    if not username_error and not password_error and not verify_error:
        if request.method == "POST":
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
    else:
        # re-renders signup template with appropriate error messages if errors exist
        return render_template('signup.html', username = username, username_error = username_error, 
            password_error = password_error, verify_error = verify_error)

@app.route('/login', methods=["POST", "GET"])
def login(): 
    # render login template
    if request.method == "GET":
        return render_template('login.html', page_title="login")

    # define variables using form entries and database queries
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()

    # verification that username is filled in and matches a username in the database
    if username == "":
        username_error = "name field cannot be blank"
    elif not user: 
        username_error = "user name not registered"
    else:        
        username_error = ""

    # verification that password is filled in and matches the password for the given user in the database
    if password == "" and user: 
        password_error = "password cannot be blank" 
    elif user: 
        if not check_pw_hash(password, user.pw_hash):
            password_error = "incorrect password"
        else:
            password_error = ""
    elif not user: 
        password_error = ""
    
    # if there are no errors, creates new session and redirects user to newpost template
    if username_error == "" and  password_error == "":
        if request.method == 'POST':
            if user and check_pw_hash(password, user.pw_hash):
                session['username'] = username
                flash("logged in")
                return redirect('/newpost') 

    # re-renders login template with appropriate error messages if login errors exist
    else:
        return render_template('login.html', username = username, 
            username_error = username_error, password_error = password_error)    

# to handle index.html
@app.route('/', methods=["POST", "GET"])
def index():
    # main page shows list of all bloggers
    users = User.query.all()
    return render_template('index.html', users = users)

@app.route('/logout')
def logout():
    # redirects the user to /blog after deleting the user name from the session.
    if session:
        del session['username']
        flash("logged out")
    return redirect('/blog')


@app.route('/blog', methods=["POST", "GET"])
def list_blogs():
    # define variable using database query
    entries = Blog.query.all()
    
    # redirects to single blog entry when blog title is clicked
    if "id" in request.args:
        id = request.args.get('id')
        entry = Blog.query.get(id)
        
        return render_template('entries.html', page_title="blog-post", title = entry.title, body = entry.body, owner = entry.owner)

    # redirects to page showing all blog entries for a specific user when user name is clicked
    if "user" in request.args:
        owner_id = request.args.get('user')
        userEntries = Blog.query.filter_by(owner_id=owner_id)
        username = User.query.get(owner_id)

        return render_template('singleUser.html', page_title = "user contributions", userEntries = userEntries, user = username)

    # displays template posts which displays all entries in descending order
    return render_template('allposts.html', entries = entries)

@app.route('/newpost', methods=["POST", "GET"])
def add_entry():
    
    # render newpost template
    if request.method == "GET":
        return render_template('newpost.html', page_title="blog")

    # define variables using form entries
    title = request.form["title"]
    body = request.form["body"]

    # verification that title is filled in
    if title == "":
        title_error = "Blog entry must have a title."
    else:
        title_error = "" 

    # verification that body is filled in
    if body == "":
        body_error = "Blog entry must have content."
    elif len(body) > 5000:
        body_error = "Blog entry cannot be more than 5000 characters long."
    else:
        body_error = ""
    
    # if there are no errors, adds new entry to the database and redirects user to entries template
    if not title_error and not body_error:
        if request.method == "POST":
            owner = User.query.filter_by(username =session['username']).first()
            new_entry = Blog(title, body, owner) 
            db.session.add(new_entry)
            db.session.commit()
        
        return render_template('entries.html', page_title = "confirmation", title = title, body = body, owner = owner)
    else:
        # re-renders newpost template with appropriate error messages if errors exist
        return render_template('newpost.html', page_title = "blog", title = title, 
            title_error = title_error, body = body, body_error = body_error)




if __name__ == '__main__':
    app.run()