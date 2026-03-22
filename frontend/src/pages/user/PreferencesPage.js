import { useState, useEffect } from "react";
import { getPreferences, updatePreferences } from "../../api/userApi";
import { CUISINES, PRICE_TIERS, DIETARY_OPTIONS, AMBIANCE_OPTIONS, SORT_OPTIONS } from "../../utils/constants";
import { useNavigate } from "react-router-dom";

export default function PreferencesPage() {
  const navigate = useNavigate();
  const [prefs, setPrefs] = useState({
    cuisine_preferences: [],
    price_range: "",
    preferred_locations: [],
    dietary_needs: [],
    ambiance_preferences: [],
    sort_preference: "rating",
  });
  const [locationInput, setLocationInput] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getPreferences().then((res) => {
      setPrefs({
        cuisine_preferences: res.data.cuisine_preferences || [],
        price_range: res.data.price_range || "",
        preferred_locations: res.data.preferred_locations || [],
        dietary_needs: res.data.dietary_needs || [],
        ambiance_preferences: res.data.ambiance_preferences || [],
        sort_preference: res.data.sort_preference || "rating",
      });
    });
  }, []);

  const toggleArray = (field, value) => {
    const arr = prefs[field];
    if (arr.includes(value)) {
      setPrefs({ ...prefs, [field]: arr.filter((v) => v !== value) });
    } else {
      setPrefs({ ...prefs, [field]: [...arr, value] });
    }
  };

  const addLocation = () => {
    if (locationInput.trim() && !prefs.preferred_locations.includes(locationInput.trim())) {
      setPrefs({ ...prefs, preferred_locations: [...prefs.preferred_locations, locationInput.trim()] });
      setLocationInput("");
    }
  };

  const removeLocation = (loc) => {
    setPrefs({ ...prefs, preferred_locations: prefs.preferred_locations.filter((l) => l !== loc) });
  };

  const handleSave = async () => {
    try {
      await updatePreferences(prefs);
      setMessage("Preferences saved!");
      setTimeout(() => setMessage(""), 3000);
    } catch {}
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Dining Preferences</h1>
      <p className="text-gray-600 mb-8">Set your preferences for personalized AI recommendations</p>

      {message && <div className="bg-green-100 text-green-700 px-4 py-2 rounded mb-4">{message}</div>}

      <div className="space-y-8">
        {/* Cuisine Preferences */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Cuisine Preferences</h3>
          <div className="flex flex-wrap gap-2">
            {CUISINES.map((c) => (
              <button key={c} onClick={() => toggleArray("cuisine_preferences", c)}
                className={`px-4 py-2 rounded-full border cursor-pointer transition-colors ${prefs.cuisine_preferences.includes(c) ? "bg-red-600 text-white border-red-600" : "bg-white text-gray-700 border-gray-300 hover:border-red-400"}`}>
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* Price Range */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Price Range</h3>
          <div className="flex gap-3">
            {PRICE_TIERS.map((p) => (
              <button key={p} onClick={() => setPrefs({ ...prefs, price_range: p })}
                className={`px-6 py-2 rounded border cursor-pointer font-semibold ${prefs.price_range === p ? "bg-red-600 text-white border-red-600" : "bg-white text-gray-700 border-gray-300"}`}>
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Preferred Locations */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Preferred Locations</h3>
          <div className="flex gap-2 mb-2">
            <input type="text" value={locationInput} onChange={(e) => setLocationInput(e.target.value)}
              placeholder="Add a city or area..."
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addLocation())}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md" />
            <button onClick={addLocation}
              className="px-4 py-2 bg-gray-800 text-white rounded border-none cursor-pointer">Add</button>
          </div>
          <div className="flex flex-wrap gap-2">
            {prefs.preferred_locations.map((loc) => (
              <span key={loc} className="bg-gray-100 px-3 py-1 rounded-full text-sm flex items-center gap-1">
                {loc}
                <button onClick={() => removeLocation(loc)} className="text-red-500 bg-transparent border-none cursor-pointer font-bold">x</button>
              </span>
            ))}
          </div>
        </div>

        {/* Dietary Needs */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Dietary Needs</h3>
          <div className="flex flex-wrap gap-2">
            {DIETARY_OPTIONS.map((d) => (
              <button key={d} onClick={() => toggleArray("dietary_needs", d)}
                className={`px-4 py-2 rounded-full border cursor-pointer ${prefs.dietary_needs.includes(d) ? "bg-green-600 text-white border-green-600" : "bg-white text-gray-700 border-gray-300"}`}>
                {d}
              </button>
            ))}
          </div>
        </div>

        {/* Ambiance */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Ambiance Preferences</h3>
          <div className="flex flex-wrap gap-2">
            {AMBIANCE_OPTIONS.map((a) => (
              <button key={a} onClick={() => toggleArray("ambiance_preferences", a)}
                className={`px-4 py-2 rounded-full border cursor-pointer ${prefs.ambiance_preferences.includes(a) ? "bg-blue-600 text-white border-blue-600" : "bg-white text-gray-700 border-gray-300"}`}>
                {a}
              </button>
            ))}
          </div>
        </div>

        {/* Sort Preference */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Default Sort</h3>
          <select value={prefs.sort_preference} onChange={(e) => setPrefs({ ...prefs, sort_preference: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md">
            {SORT_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>

        {/* Save Button */}
        <div className="flex gap-3">
          <button onClick={handleSave}
            className="px-8 py-3 text-white rounded-md font-semibold border-none cursor-pointer"
            style={{ backgroundColor: "#d32323" }}>
            Save Preferences
          </button>
          <button onClick={() => navigate("/profile")}
            className="px-8 py-3 bg-gray-200 rounded-md font-semibold border-none cursor-pointer">
            Back to Profile
          </button>
        </div>
      </div>
    </div>
  );
}
