from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, World from Flask!"


@app.route("/info", methods=["GET"])
def client_info():
    """Return some useful and interesting JSON about the client/request."""
    user_agent = request.headers.get("User-Agent", "unknown")
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    data = {
        "client_ip": client_ip,
        "user_agent": user_agent,
        "method": request.method,
        "path": request.path,
        "args": request.args.to_dict(),
        "interesting": {
            "is_mobile_like": any(x in user_agent.lower() for x in ["iphone", "android", "mobile"]),
            "request_id_hint": f"req-{abs(hash((client_ip, user_agent))) % 10_000}",
        },
    }

    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
