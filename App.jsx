import { useEffect, useState } from "react";

export default function App() {
  const [cities, setCities] = useState([]);
  const [city, setCity] = useState("Delhi");
  const [days, setDays] = useState(2);
  const [budget, setBudget] = useState(1500);

  const options = ["temple", "beach", "heritage", "museum", "nature", "food", "shopping", "park", "fort"];

  const [interests, setInterests] = useState(["temple"]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // Fetch city list from backend
  useEffect(() => {
    const loadCities = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/cities");
        const data = await res.json();
        setCities(data.cities || []);
        if (data.cities && data.cities.length > 0) {
          setCity(data.cities[0]); // set first city
        }
      } catch (e) {
        setError("Backend not running. Start Flask: python app.py");
      }
    };
    loadCities();
  }, []);

  const toggleInterest = (item) => {
    setInterests((prev) =>
      prev.includes(item) ? prev.filter((x) => x !== item) : [...prev, item]
    );
  };

  const generatePlan = async () => {
    setError("");
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:5000/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, days, budget, interests }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Something went wrong");
        return;
      }
      setResult(data);
    } catch (e) {
      setError("Backend not running. Start Flask: python app.py");
    }
  };

  return (
    <div style={{ fontFamily: "Arial", padding: 20, maxWidth: 1000, margin: "auto" }}>
      <h1>AI Travel Planner (Kaggle Dataset) ✨</h1>
      <p style={{ color: "#666" }}>
        Select city → choose interests → generate day-wise itinerary + budget breakup.
      </p>

      <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 12 }}>
        <h3>Trip Details</h3>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          <div>
            <label>City</label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              style={{ width: "100%", padding: 10, marginTop: 6 }}
            >
              {cities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label>Days</label>
            <input
              type="number"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              min={1}
              style={{ width: "100%", padding: 10, marginTop: 6 }}
            />
          </div>

          <div>
            <label>Budget (₹)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              min={200}
              style={{ width: "100%", padding: 10, marginTop: 6 }}
            />
          </div>
        </div>

        <div style={{ marginTop: 14 }}>
          <label><b>Interests</b></label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
            {options.map((item) => (
              <button
                key={item}
                onClick={() => toggleInterest(item)}
                style={{
                  padding: "8px 12px",
                  borderRadius: 20,
                  border: "1px solid #ccc",
                  cursor: "pointer",
                  background: interests.includes(item) ? "#111" : "#fff",
                  color: interests.includes(item) ? "#fff" : "#111",
                }}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={generatePlan}
          style={{
            marginTop: 16,
            padding: "10px 16px",
            borderRadius: 10,
            border: "none",
            background: "#2563eb",
            color: "white",
            cursor: "pointer",
            fontSize: 16,
          }}
        >
          Generate Plan
        </button>

        {error && <p style={{ color: "red", marginTop: 10 }}>{error}</p>}
      </div>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h2>Trip Plan for {result.city}</h2>
          <p>{result.ai_summary}</p>

          <div style={{ border: "1px solid #ddd", padding: 12, borderRadius: 10 }}>
            <h3>Cost Breakdown</h3>
            <ul>
              <li>Places: ₹{result.cost_breakup.places}</li>
              <li>Food: ₹{result.cost_breakup.food}</li>
              <li>Local Travel: ₹{result.cost_breakup.local_travel}</li>
              <li>Stay: ₹{result.cost_breakup.stay}</li>
              <li>Misc: ₹{result.cost_breakup.misc}</li>
              <li><b>Total Estimated: ₹{result.cost_breakup.total_estimated}</b></li>
            </ul>
          </div>

          {result.itinerary.map((day) => (
            <div key={day.day} style={{ border: "1px solid #ddd", padding: 12, borderRadius: 10, marginTop: 12 }}>
              <h3>Day {day.day}</h3>
              <ul>
                {day.places.map((p) => (
                  <li key={p.name}>
                    <b>{p.name}</b> ({p.category}) — ₹{p.avg_cost} — Rating: {p.rating}
                    {" "}
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                        p.name + " " + result.city
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ marginLeft: 8 }}
                    >
                      Map
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
