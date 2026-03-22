import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { searchRestaurants } from "../../api/restaurantApi";
import RestaurantCard from "../../components/RestaurantCard";
import { CUISINES, PRICE_TIERS } from "../../utils/constants";

export default function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    keyword: searchParams.get("keyword") || "",
    city: searchParams.get("city") || "",
    cuisine_type: searchParams.get("cuisine_type") || "",
    pricing_tier: searchParams.get("pricing_tier") || "",
    name: searchParams.get("name") || "",
  });

  const fetchResults = async (params) => {
    setLoading(true);
    try {
      const cleanParams = {};
      Object.entries(params).forEach(([k, v]) => {
        if (v) cleanParams[k] = v;
      });
      const res = await searchRestaurants(cleanParams);
      setResults(res.data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults(filters);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });
    setSearchParams(params);
    fetchResults(filters);
  };

  const handleChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Search Filters */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <input
            type="text" name="keyword" placeholder="Keywords..."
            value={filters.keyword} onChange={handleChange}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <input
            type="text" name="name" placeholder="Restaurant name..."
            value={filters.name} onChange={handleChange}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <input
            type="text" name="city" placeholder="City or Zip..."
            value={filters.city} onChange={handleChange}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <select name="cuisine_type" value={filters.cuisine_type} onChange={handleChange}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500">
            <option value="">All Cuisines</option>
            {CUISINES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select name="pricing_tier" value={filters.pricing_tier} onChange={handleChange}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500">
            <option value="">All Prices</option>
            {PRICE_TIERS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <button type="submit"
          className="mt-4 px-8 py-2 text-white rounded-md font-semibold hover:opacity-90 border-none cursor-pointer"
          style={{ backgroundColor: "#d32323" }}>
          Search
        </button>
      </form>

      {/* Results */}
      {loading ? (
        <div className="text-center py-10">
          <div className="text-xl text-gray-500">Searching...</div>
        </div>
      ) : results.length === 0 ? (
        <div className="text-center py-10">
          <div className="text-xl text-gray-500">No restaurants found. Try different filters.</div>
        </div>
      ) : (
        <>
          <p className="text-gray-600 mb-4">{results.length} result(s) found</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((r) => (
              <RestaurantCard key={r.id} restaurant={r} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
