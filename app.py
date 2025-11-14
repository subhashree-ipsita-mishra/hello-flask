from flask import Flask, jsonify, request
from scapy.all import IP, ICMP, sr1
import requests

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
def http_ping(target):
    """HTTP-based "ping" that works on typical hosted environments.

    It tries an HTTPS GET to the given host (e.g. /ping/google.com) and reports
    whether it was reachable and how long it took.
    """
    # Build a URL; if the user already includes a scheme, respect it.
    if target.startswith("http://") or target.startswith("https://"):
        url = target
    else:
        url = f"https://{target}"

    try:
        resp = requests.get(url, timeout=3)
        return jsonify(
            {
                "target": target,
                "url": url,
                "reachable": True,
                "status_code": resp.status_code,
                "rtt_ms": resp.elapsed.total_seconds() * 1000,
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                "target": target,
                "url": url,
                "reachable": False,
                "error": str(e),
            }
        ), 200


@app.route("/scapy-ping/<target>", methods=["GET"])
def scapy_ping(target):
    """Use Scapy to send a single ICMP echo request to the target.

    NOTE: This usually requires raw-socket privileges and will *not* work on
    most serverless/hosted environments like Vercel. Intended for local use.
    """
    try:
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
