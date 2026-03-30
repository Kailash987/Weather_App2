(function () {
  const form = document.getElementById("search-form");
  const cityInput = document.getElementById("city");
  const submitBtn = document.getElementById("submit-btn");
  const errorMsg = document.getElementById("error-msg");
  const loadingMsg = document.getElementById("loading-msg");
  const result = document.getElementById("result");
  const place = document.getElementById("place");
  const coords = document.getElementById("coords");
  const weatherIcon = document.getElementById("weather-icon");
  const description = document.getElementById("description");
  const temp = document.getElementById("temp");
  const feels = document.getElementById("feels");
  const stats = document.getElementById("stats");

  function hideError() {
    errorMsg.hidden = true;
    errorMsg.textContent = "";
  }

  function showError(text) {
    errorMsg.textContent = text;
    errorMsg.hidden = false;
  }

  function setLoading(on) {
    loadingMsg.hidden = !on;
    submitBtn.disabled = on;
    cityInput.disabled = on;
  }

  function renderWeather(data) {
    const country = data.country ? `, ${data.country}` : "";
    place.textContent = `${data.city || "—"}${country}`;

    if (data.lat != null && data.lon != null) {
      coords.textContent = `${Number(data.lat).toFixed(2)}°, ${Number(data.lon).toFixed(2)}°`;
    } else {
      coords.textContent = "";
    }

    if (data.icon) {
      weatherIcon.src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
      weatherIcon.alt = data.description || "Weather";
    } else {
      weatherIcon.removeAttribute("src");
      weatherIcon.alt = "";
    }

    description.textContent = data.description || "";
    temp.textContent =
      data.temp != null ? Math.round(Number(data.temp)) : "—";
    feels.textContent =
      data.feels_like != null
        ? `Feels like ${Math.round(Number(data.feels_like))} °C`
        : "";

    stats.innerHTML = "";
    const rows = [
      { label: "Humidity", value: data.humidity != null ? `${data.humidity} %` : "—" },
      { label: "Pressure", value: data.pressure != null ? `${data.pressure} hPa` : "—" },
      {
        label: "Wind",
        value:
          data.wind_speed != null
            ? `${Number(data.wind_speed).toFixed(1)} m/s`
            : "—",
      },
    ];
    rows.forEach((row) => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="label">${row.label}</span><span class="value">${row.value}</span>`;
      stats.appendChild(li);
    });

    result.hidden = false;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();
    result.hidden = true;

    const city = cityInput.value.trim();
    if (!city) {
      showError("Enter a city name.");
      return;
    }

    const url = new URL("/api/weather", window.location.origin);
    url.searchParams.set("city", city);

    setLoading(true);
    try {
      const res = await fetch(url.toString(), {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      const body = await res.json().catch(() => ({}));

      if (!res.ok) {
        showError(body.error || "Something went wrong.");
        return;
      }

      renderWeather(body);
    } catch {
      showError("Network error. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  });
})();
