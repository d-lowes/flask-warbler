import os

from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFProtect

from forms import (UserAddForm, LoginForm, MessageForm,
                   CSRFProtectForm,
                   EditProfileForm)
from models import (db, connect_db, User, Message,
                    DEFAULT_HEADER_IMAGE_URL,
                    DEFAULT_IMAGE_URL)

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
csrf = CSRFProtect(app)
csrf.init_app(app)

# fix incorrect database URIs currently returned by Heroku's pg setup
database_url = os.environ['DATABASE_URL']
database_url = database_url.replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

toolbar = DebugToolbarExtension(app)


# Disable CSRF for live demo, comment this out to enable
app.config['WTF_CSRF_ENABLED'] = False

connect_db(app)


##############################################################################
# USER BEFORE/LOGIN/LOGOUT

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

@app.before_request
def add_CSRF_form_to_g():
    """Declare g variable for CSRF form validation"""

    g.csrf_form = CSRFProtectForm()

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

##############################################################################
# USER SIGNUP

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    form = UserAddForm()

    if g.user:
        return redirect("/")

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)

##############################################################################
# USER LOGIN/LOGOUT ROUTES

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if not form.validate_on_submit() or not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


##############################################################################
# USERS

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user)

##############################################################################
# FOLLOWING/FOLLOWERS

@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)

##############################################################################
# FOLLOW/STOP FOLLOWING

@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

##############################################################################
# USER PROFILE

@app.route('/users/profile', methods=["GET", "POST"])
def update_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = g.user
    form = EditProfileForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(
            user.username,
            form.password.data,
        ):
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data or DEFAULT_IMAGE_URL
            user.location = form.location.data
            user.bio = form.bio.data
            user.header_image_url = form.header_image_url.data or DEFAULT_HEADER_IMAGE_URL

            db.session.commit()

            flash("User updated!", "success")

            return redirect(f"/users/{user.id}")

        flash("Incorrect password.", "danger")

    return render_template("users/edit.html",
                               form=form)

##############################################################################
# USER DELETE

@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page.
    """

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# MESSAGES

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """
    msg = Message.query.get_or_404(message_id)

    if not g.user or not g.csrf_form.validate_on_submit() or g.user.id != msg.user_id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# HOMEPAGE AND ERROR PAGES


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        following_ids = [user.id for user in g.user.following]
        following_ids.append(g.user.id)

        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


##############################################################################
# LIKE/UNLIKE REQUESTS

@app.post('/like/<int:msg_id>')
def like_msg(msg_id):
    """Add LikeMessage Instance to DB for current user"""
    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    url = request.form["url"] or "/"
    message = Message.query.get(msg_id)
    g.user.liked_messages.append(message)

    db.session.commit()

    return redirect(url)

@app.post('/unlike/<int:msg_id>')
def unlike_msg(msg_id):
    """Add LikeMessage Instance to DB for current user"""

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")
    else:
        url = request.form["url"] or "/"
        message = Message.query.get(msg_id)
        g.user.liked_messages.remove(message)

        db.session.commit()

        return redirect(url)


@app.get("/users/<int:user_id>/likes")
def show_likes(user_id):
    """Show all messages current user liked"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    messages = user.liked_messages

    return render_template("likes.html",
                    messages=messages,
                    user=user)


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
