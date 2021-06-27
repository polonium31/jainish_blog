from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
import smtplib
import os

my_email = "jenu318190@gmail.com"
my_password = "jenu3191@"
personal_email = "jenu3181@gmail.com"




app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ehpbzpsmpjtqbm:37725e0ff3ad3f58fd6aff1be95544e729ebfaf07e805d78ce25836785622729@ec2-52-4-111-46.compute-1.amazonaws.com:5432/ddfn10oe4eofee'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os
db = SQLAlchemy(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=["GET", "POST"])
def register():
    if User.query.filter_by(email=request.form.get('email')).first():
        flash("You've already signed up with that email, log in instead!")
        return redirect(url_for('login'))
    if request.method == "POST":
        password_form = request.form.get('password')
        password_hash = generate_password_hash(password_form, method='pbkdf2:sha256', salt_length=8)

        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=password_hash
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/")
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html")


@app.route('/forgot-password', methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get('email')).first()
        password = request.form.get("password")
        if check_password_hash(user.password, password):
            flash("Your password is same as before")
            return redirect(url_for('login'))
        else:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            user.password = password_hash
            db.session.commit()
            flash("Your password is change now")
            return redirect(url_for('login'))

    return render_template('forgot.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/home')
def home():
    blogs = db.session.query(BlogPost).all()
    return render_template("index.html", blogs=blogs)


@app.route('/post/<int:blog_id>', methods=["GET", "POST"])
def post(blog_id):
    blogs = BlogPost.query.get(blog_id)
    image = blogs.img_url
    users = User.query.get(blog_id)

    if request.method == "POST":
        new_comment = Comment(
            text=request.form.get("comment"),
            comment_author=current_user,
            parent_post=blogs
        )
        print(new_comment)
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", blog=blogs, image=image, current_user=current_user)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route("/contribute", methods=["GET", "POST"])
def contribute():
    today_date = date.today()
    if request.method == "POST":
        new_blog = BlogPost(
            title=request.form["title"],
            subtitle=request.form["subtitle"],
            body=request.form["body"],
            img_url=request.form["image"],
            author=current_user,
            date=today_date
        )

        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("contribute.html", msg_sent=False)


@admin_only
@app.route("/edit-post/<blog_id>", methods=["GET", "POST"])
def edit_post(blog_id):
    blog = BlogPost.query.get(blog_id)
    db.session.delete(blog)
    db.session.commit()
    today_date = date.today()
    if request.method == "POST":
        new_blog = BlogPost(
            title=request.form["title"],
            subtitle=request.form["subtitle"],
            body=request.form["body"],
            image_url=request.form["image"],
            date=today_date
        )

        db.session.add(new_blog)

        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", blog=blog)


@admin_only
@app.route("/delete/<int:blog_id>")
def delete_post(blog_id):
    post_to_delete = BlogPost.query.get(blog_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        send_email(data["name"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)


def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=my_email, password=my_password)
        connection.sendmail(from_addr=my_email, to_addrs=personal_email, msg=email_message)
        print("send")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
