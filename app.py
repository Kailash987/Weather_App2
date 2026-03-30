import os
import socket
import ssl

import requests
import truststore
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from requests.adapters import HTTPAdapter
from werkzeug.middleware.proxy_fix import ProxyFix

# Broken IPv6 routes often cause timeouts on Windows; prefer IPv4 for API calls.
try:
    import urllib3.util.connection as urllib3_connection

    def _force_ipv4():
        return socket.AF_INET

    urllib3_connection.allowed_gai_family = _force_ipv4
except (ImportError, AttributeError):
    pass

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="public/static",
    static_url_path="/static",
)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

OWM_BASE = "https://api.openweathermap.org/data/2.5/weather"
HTTP_TIMEOUT = 20
REQUEST_HEADERS = {
    "User-Agent": "WeatherApp/1.0 (Flask; +https://openweathermap.org/)",
}


class TruststoreHTTPAdapter(HTTPAdapter):
    """Use the OS trust store (Windows/macOS/Linux) so HTTPS verifies correctly."""

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        pool_kwargs["ssl_context"] = ctx
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)


def _http_session():
    s = requests.Session()
    s.mount("https://", TruststoreHTTPAdapter())
    return s


_http = _http_session()


def get_api_key():
    key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not key:
        return None
    return key


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/weather", methods=["GET"])
def weather():
    city = (request.args.get("city") or "").strip()
    if not city:
        return jsonify({"error": "Enter a city name."}), 400

    api_key = get_api_key()
    if not api_key:
        return jsonify(
            {"error": "Server is not configured with OPENWEATHER_API_KEY."}
        ), 503

    try:
        r = _http.get(
            OWM_BASE,
            params={
                "q": city,
                "appid": api_key,
                "units": "metric",
            },
            headers=REQUEST_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        app.logger.warning("OpenWeather request failed: %s", exc)
        return jsonify({"error": "Could not reach weather service. Try again."}), 502

    try:
        data = r.json()
    except ValueError:
        app.logger.warning("OpenWeather returned non-JSON (status %s)", r.status_code)
        return jsonify({"error": "Could not read weather service response."}), 502

    if r.status_code != 200:
        msg = data.get("message", "Weather lookup failed.")
        if r.status_code == 404:
            return jsonify({"error": "City not found. Check spelling or try another name."}), 404
        return jsonify({"error": str(msg).capitalize()}), r.status_code

    w = data.get("weather", [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})
    coord = data.get("coord", {})

    payload = {
        "city": data.get("name"),
        "country": (data.get("sys") or {}).get("country"),
        "description": w.get("description", "").capitalize(),
        "icon": w.get("icon"),
        "temp": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed"),
        "lat": coord.get("lat"),
        "lon": coord.get("lon"),
    }
    return jsonify(payload)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
