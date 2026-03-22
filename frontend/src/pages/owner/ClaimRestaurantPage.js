import { useState } from "react";
import { searchRestaurants } from "../../api/restaurantApi";
import { claimRestaurant } from "../../api/ownerApi";

export default function ClaimRestaurantPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      const res = await searchRestaurants({ name: query });
      setResults(res.data.filter((r) => !r.is_claimed));
    } catch {}
  };

  const handleClaim = async (id, name) => {
    if (!window.confirm(`Claim "${name}" as your restaurant?`)) return;
    try {
      await claimRestaurant(id);
      setResults(results.filter((r) => r.id !== id));
      setMessage(`Successfully claimed "${name}"!`);
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Failed to claim");
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Claim a Restaurant</h1>
      <p className="text-gray-600 mb-4">Search for your restaurant and claim ownership</p>

      {message && <div className="bg-green-100 text-green-700 px-4 py-3 rounded mb-4">{message}</div>}

      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by restaurant name..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md" />
        <button type="submit"
          className="px-6 py-2 text-white rounded-md font-semibold border-none cursor-pointer"
          style={{ backgroundColor: "#d32323" }}>
          Search
        </button>
      </form>

      {results.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No unclaimed restaurants found.</p>
      ) : (
        <div className="space-y-3">
          {results.map((r) => (
            <div key={r.id} className="bg-white rounded-lg shadow p-4 flex justify-between items-center">
              <div>
                <h3 className="font-bold">{r.name}</h3>
                <p className="text-sm text-gray-600">{r.cuisine_type} · {r.city}</p>
              </div>
              <button onClick={() => handleClaim(r.id, r.name)}
                className="px-4 py-2 bg-green-600 text-white rounded font-semibold border-none cursor-pointer hover:bg-green-700">
                Claim
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
