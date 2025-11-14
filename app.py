from flask import Flask, jsonify, request
from scapy.all import IP, ICMP, sr1

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


@app.route("/ping/<target>", methods=["GET"])
def ping_host(target):
    """Use Scapy to send a single ICMP echo request to the target.

    Example: GET /ping/8.8.8.8
    """
    try:
        # Send one ICMP Echo Request (like ping)
        reply = sr1(
            IP(dst=target) / ICMP(),
            timeout=1,
            verbose=0,
        )

        if reply is None:
            return jsonify(
                {
                    "target": target,
                    "reachable": False,
                    "message": "No reply",
                }
            ), 200
        else:
            rtt_ms = None
            if hasattr(reply, "time") and hasattr(reply, "sent_time"):
                rtt_ms = (reply.time - reply.sent_time) * 1000

            return jsonify(
                {
                    "target": target,
                    "reachable": True,
                    "source": reply.src,
                    "rtt_ms": rtt_ms,
                }
            ), 200

    except Exception as e:
        return jsonify({"target": target, "reachable": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
