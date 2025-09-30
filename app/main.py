# ---- Imports ----
from shipy.app import App, Response
from shipy.render import render_req, render_htmx, is_htmx_request
from shipy.sql import connect, query, one, exec, tx
from shipy.forms import Form
from shipy.auth import (
    current_user, login_required,
    hash_password, check_password,
    login, logout,
    too_many_login_attempts, record_login_failure, reset_login_failures
)
import os
import mimetypes

# ---- App Setup ----
app = App()
connect("data/app.db")

# ---- Utilities ----
def get_user_safely(req):
    """Get user from state or fetch directly if not available."""
    if hasattr(req.state, 'user'):
        return req.state.user
    user = current_user(req)
    req.state.user = user  # Cache for future use
    return user

def serve_static(req):
    """Serve static files from the public directory."""
    path = req.scope["path"]
    # Remove /public prefix
    file_path = path[7:] if path.startswith("/public/") else path[1:]
    
    # Security: prevent directory traversal
    if ".." in file_path or file_path.startswith("/"):
        return Response("Forbidden", status=403)
    
    # Construct full path
    full_path = os.path.join("public", file_path)
    
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return Response("Not Found", status=404)
    
    # Get MIME type
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    # Read file content
    try:
        with open(full_path, "rb") as f:
            content = f.read()
        return Response(content, headers={"Content-Type": mime_type})
    except Exception:
        return Response("Internal Server Error", status=500)

# ---- Middleware ----
@app.middleware("request")
def attach_user_to_state(req):
    user = current_user(req)
    req.state.user = user

# ---- Route Handlers ----
def home(req):
    user = get_user_safely(req)  # Reliable user access
    return render_htmx(req, "home/index.html", user=user)

def signup_form(req): return render_req(req, "users/new.html")

async def signup(req):
    await req.load_body()
    form = Form(req.form).require("email","password").min("password", 6).email("email")
    if not form.ok:
        return render_req(req, "users/new.html", form=form)
    if one("SELECT id FROM users WHERE email=?", form["email"]):
        form.errors.setdefault("email", []).append("already registered")
        return render_req(req, "users/new.html", form=form)
    with tx():
        exec("INSERT INTO users(email,password_hash) VALUES(?,?)", form["email"], hash_password(form['password']))
    u = one("SELECT id,email FROM users WHERE email=?", form["email"])
    resp = Response.redirect("/")
    login(req, resp, u["id"])
    return resp

def login_form(req): return render_req(req, "sessions/login.html")

async def login_post(req):
    await req.load_body()
    form = Form(req.form).require("email","password").email("email")
    ip = req.scope.get("client", ("",0))[0] or "unknown"
    if too_many_login_attempts(ip):
        form.errors.setdefault("email", []).append("too many attempts, try later")
        return render_req(req, "sessions/login.html", form=form)
    u = one("SELECT id,email,password_hash FROM users WHERE email=?", form["email"])
    if not u or not check_password(form["password"], u["password_hash"]):
        record_login_failure(ip)
        form.errors.setdefault("email", []).append("invalid email or password")
        return render_req(req, "sessions/login.html", form=form)
    reset_login_failures(ip)
    resp = Response.redirect("/")
    login(req, resp, u["id"])
    return resp

async def logout_post(req):
    resp = Response.redirect("/")
    logout(resp)
    return resp

@login_required()
def secret(req):
    # req.state.user is guaranteed to exist here
    user = get_user_safely(req)  # Reliable user access
    return render_req(req, "secret.html", user=user)

# ---- Docs & Tutorials ----
def docs_manifesto(req):
    return render_req(req, "docs/manifesto.html")

def tutorials_index(req):
    return render_req(req, "tutorials/index.html")

def tutorials_todo(req):
    return render_req(req, "tutorials/todo.html")

def docs_get_started(req):
    return render_req(req, "docs/get-started.html")

def docs_get_started_install(req):
    return render_req(req, "docs/get-started/install.html")

def docs_guides_htmx(req):
    return render_req(req, "docs/guides/htmx-patterns.html")

def docs_contributing(req):
    return render_req(req, "docs/contributing.html")

# ---- Routes ----
# Static files
app.get("/public/base.css", serve_static)
app.get("/public/docs.css", serve_static)
app.get("/public/favicon.svg", serve_static)

# Main routes
app.get("/", home)
app.get("/signup", signup_form)
app.post("/signup", signup)
app.get("/login", login_form)
app.post("/login", login_post)
app.post("/logout", logout_post)
app.get("/secret", secret)

# Documentation routes
app.get("/docs/manifesto", docs_manifesto)
app.get("/docs/manifesto/", docs_manifesto)
app.get("/docs/tutorials", tutorials_index)
app.get("/docs/tutorials/", tutorials_index)
app.get("/docs/tutorials/todo", tutorials_todo)
app.get("/docs/tutorials/todo/", tutorials_todo)
app.get("/docs/get-started", docs_get_started)
app.get("/docs/get-started/", docs_get_started)
app.get("/docs/get-started/install", docs_get_started_install)
app.get("/docs/get-started/install/", docs_get_started_install)
app.get("/docs/guides/htmx-patterns", docs_guides_htmx)
app.get("/docs/guides/htmx-patterns/", docs_guides_htmx)
app.get("/docs/contributing", docs_contributing)
app.get("/docs/contributing/", docs_contributing)
