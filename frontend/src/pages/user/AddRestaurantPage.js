import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createRestaurant, uploadRestaurantPhotos } from "../../api/restaurantApi";
import { CUISINES, PRICE_TIERS } from "../../utils/constants";

export default function AddRestaurantPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "", cuisine_type: "", address: "", city: "", zip_code: "",
    contact_info: "", description: "", pricing_tier: "",
    amenities: "",
  });
  const [photos, setPhotos] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = {
        ...form,
        amenities: form.amenities ? form.amenities.split(",").map((a) => a.trim()).filter(Boolean) : [],
      };
      const res = await createRestaurant(data);

      if (photos.length > 0) {
        await uploadRestaurantPhotos(res.data.id, photos);
      }

      navigate(`/restaurants/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create restaurant");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Add a Restaurant</h1>

      {error && <div className="bg-red-100 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Name *</label>
            <input type="text" name="name" value={form.name} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cuisine Type *</label>
            <select name="cuisine_type" value={form.cuisine_type} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="">Select cuisine</option>
              {CUISINES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address *</label>
            <input type="text" name="address" value={form.address} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
            <input type="text" name="city" value={form.city} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Zip Code</label>
            <input type="text" name="zip_code" value={form.zip_code} onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contact Info</label>
            <input type="text" name="contact_info" value={form.contact_info} onChange={handleChange}
              placeholder="Phone number"
              className="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pricing Tier</label>
            <select name="pricing_tier" value={form.pricing_tier} onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option value="">Select</option>
              {PRICE_TIERS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amenities</label>
            <input type="text" name="amenities" value={form.amenities} onChange={handleChange}
              placeholder="wifi, outdoor seating, parking (comma-separated)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea name="description" value={form.description} onChange={handleChange} rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Photos</label>
          <input type="file" multiple accept="image/*" onChange={(e) => setPhotos([...e.target.files])}
            className="w-full" />
        </div>

        <button type="submit" disabled={loading}
          className="px-8 py-3 text-white rounded-md font-semibold hover:opacity-90 disabled:opacity-50 border-none cursor-pointer"
          style={{ backgroundColor: "#d32323" }}>
          {loading ? "Creating..." : "Add Restaurant"}
        </button>
      </form>
    </div>
  );
}
