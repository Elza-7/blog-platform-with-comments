import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for, abort
from flask_login import (
    LoginManager, UserMixin, current_user, login_required,
    login_user, logout_user
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "blog.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
csrf = CSRFProtect(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    posts = db.relationship("Post", backref="author", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="author", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    comments = db.relationship(
        "Comment", backref="post", lazy=True, cascade="all, delete-orphan",
        order_by="Comment.created_at.asc()"
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def valid_email(email):
    return "@" in email and "." in email.rsplit("@", 1)[-1]


@app.context_processor
def inject_helpers():
    return {"current_year": datetime.utcnow().year}


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    posts_query = Post.query
    if query:
        pattern = f"%{query}%"
        posts_query = posts_query.join(User).filter(
            or_(Post.title.ilike(pattern), Post.content.ilike(pattern), User.username.ilike(pattern))
        )
    posts = posts_query.order_by(Post.created_at.desc()).all()
    return render_template("index.html", posts=posts, search_query=query)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not 3 <= len(username) <= 30:
            flash("Username must be between 3 and 30 characters.", "error")
        elif not valid_email(email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account is ready. Welcome!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(
            or_(User.username == identity, User.email == identity.lower())
        ).first()
        if user and user.check_password(password):
            login_user(user)
            flash("You are now logged in.", "success")
            next_page = request.args.get("next")
            # Only allow local relative redirects.
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))
        flash("Invalid username/email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template("dashboard.html", posts=posts)


@app.route("/posts/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("Both title and content are required.", "error")
        elif len(title) > 160:
            flash("Title must be 160 characters or fewer.", "error")
        else:
            post = Post(title=title, content=content, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash("Your blog post has been published.", "success")
            return redirect(url_for("post_detail", post_id=post.id))
    return render_template("post_form.html", page_title="Write a post", post=None)


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = db.get_or_404(Post, post_id)
    return render_template("post_detail.html", post=post)


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("Both title and content are required.", "error")
        elif len(title) > 160:
            flash("Title must be 160 characters or fewer.", "error")
        else:
            post.title = title
            post.content = content
            post.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Your post has been updated.", "success")
            return redirect(url_for("post_detail", post_id=post.id))
    return render_template("post_form.html", page_title="Edit post", post=post)


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.get_or_404(Post, post_id)
    content = request.form.get("content", "").strip()
    if not content:
        flash("Please write a comment first.", "error")
    elif len(content) > 1000:
        flash("Comment must be 1000 characters or fewer.", "error")
    else:
        comment = Comment(content=content, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been added.", "success")
    return redirect(url_for("post_detail", post_id=post.id) + "#comments")


@app.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    if comment.user_id != current_user.id and comment.post.user_id != current_user.id:
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("post_detail", post_id=post_id) + "#comments")


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="You don't have permission to do that."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="The page or post you're looking for doesn't exist."), 404


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
