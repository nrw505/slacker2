from . import app


@app.route("/")
def index() -> str:
    return "SLAAAAACK"
