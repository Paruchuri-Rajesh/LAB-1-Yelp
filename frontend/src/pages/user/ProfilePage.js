import { useState, useEffect } from "react";
import { getProfile, updateProfile, uploadProfilePicture, getUserReviews } from "../../api/userApi";
import { getFavorites } from "../../api/favoriteApi";
import { useAuth } from "../../context/AuthContext";
import { COUNTRIES, US_STATES } from "../../utils/constants";
import RestaurantCard from "../../components/RestaurantCard";
import ReviewCard from "../../components/ReviewCard";
import StarRating from "../../components/StarRating";
import { Link } from "react-router-dom";

export default function ProfilePage() {
  const { loginUser, token } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [favorites, setFavorites] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getProfile().then((res) => {
      setProfile(res.data);
      setForm(res.data);
    });
  }, []);

  useEffect(() => {
    if (activeTab === "favorites") {
      getFavorites().then((res) => setFavorites(res.data)).catch(() => {});
    }
    if (activeTab === "history") {
      getUserReviews().then((res) => setReviews(res.data)).catch(() => {});
    }
  }, [activeTab]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSave = async () => {
    try {
      const res = await updateProfile({
        name: form.name, email: form.email, phone: form.phone,
        about_me: form.about_me, city: form.city, state: form.state,
        country: form.country, languages: form.languages, gender: form.gender,
      });
      setProfile(res.data);
      loginUser(token, res.data);
      setEditing(false);
      setMessage("Profile updated!");
      setTimeout(() => setMessage(""), 3000);
    } catch {}
  };

  const handlePictureUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await uploadProfilePicture(file);
      setProfile(res.data);
      loginUser(token, res.data);
    } catch {}
  };

  if (!profile) return <div className="text-center py-10">Loading...</div>;

  const tabs = [
    { key: "profile", label: "Profile" },
    { key: "favorites", label: "Favorites" },
    { key: "history", label: "History" },
    { key: "preferences", label: "Preferences" },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-6 mb-8">
        <div className="relative">
          <img
            src={profile.profile_picture ? `http://localhost:8000${profile.profile_picture}` : "https://via.placeholder.com/120?text=User"}
            alt="Profile"
            className="w-24 h-24 rounded-full object-cover border-4 border-white shadow-md"
          />
          <label className="absolute bottom-0 right-0 bg-white rounded-full p-1 shadow cursor-pointer">
            <input type="file" accept="image/*" onChange={handlePictureUpload} className="hidden" />
            <span className="text-xs">Edit</span>
          </label>
        </div>
        <div>
          <h1 className="text-2xl font-bold">{profile.name}</h1>
          <p className="text-gray-600">{profile.email}</p>
          {profile.city && <p className="text-gray-500">{profile.city}{profile.state ? `, ${profile.state}` : ""}</p>}
        </div>
      </div>

      {message && <div className="bg-green-100 text-green-700 px-4 py-2 rounded mb-4">{message}</div>}

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-6 py-3 font-semibold border-b-2 bg-transparent cursor-pointer ${activeTab === tab.key ? "border-red-500 text-red-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <div className="bg-white rounded-lg shadow p-6">
          {!editing ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div><span className="text-gray-500 text-sm">Name</span><p className="font-medium">{profile.name}</p></div>
                <div><span className="text-gray-500 text-sm">Email</span><p className="font-medium">{profile.email}</p></div>
                <div><span className="text-gray-500 text-sm">Phone</span><p className="font-medium">{profile.phone || "—"}</p></div>
                <div><span className="text-gray-500 text-sm">Gender</span><p className="font-medium">{profile.gender || "—"}</p></div>
                <div><span className="text-gray-500 text-sm">City</span><p className="font-medium">{profile.city || "—"}</p></div>
                <div><span className="text-gray-500 text-sm">State</span><p className="font-medium">{profile.state || "—"}</p></div>
                <div><span className="text-gray-500 text-sm">Country</span><p className="font-medium">{profile.country || "—"}</p></div>
                <div><span className="text-gray-500 text-sm">Languages</span><p className="font-medium">{profile.languages || "—"}</p></div>
              </div>
              <div><span className="text-gray-500 text-sm">About Me</span><p className="font-medium">{profile.about_me || "—"}</p></div>
              <button onClick={() => setEditing(true)}
                className="mt-4 px-6 py-2 text-white rounded font-semibold border-none cursor-pointer"
                style={{ backgroundColor: "#d32323" }}>
                Edit Profile
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input type="text" name="name" value={form.name || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input type="email" name="email" value={form.email || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input type="tel" name="phone" value={form.phone || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                  <select name="gender" value={form.gender || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md">
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                  <input type="text" name="city" value={form.city || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                  <select name="state" value={form.state || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md">
                    <option value="">Select</option>
                    {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                  <select name="country" value={form.country || ""} onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md">
                    <option value="">Select</option>
                    {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Languages</label>
                  <input type="text" name="languages" value={form.languages || ""} onChange={handleChange}
                    placeholder="e.g., English, Spanish"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">About Me</label>
                <textarea name="about_me" value={form.about_me || ""} onChange={handleChange} rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md" />
              </div>
              <div className="flex gap-3">
                <button onClick={handleSave}
                  className="px-6 py-2 text-white rounded font-semibold border-none cursor-pointer"
                  style={{ backgroundColor: "#d32323" }}>
                  Save
                </button>
                <button onClick={() => { setEditing(false); setForm(profile); }}
                  className="px-6 py-2 bg-gray-200 rounded font-semibold border-none cursor-pointer">
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Favorites Tab */}
      {activeTab === "favorites" && (
        <div>
          {favorites.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No favorites yet.</p>
          ) : (
            <div className="space-y-3">
              {favorites.map((f) => (
                <Link key={f.id} to={`/restaurants/${f.restaurant_id}`} className="block no-underline">
                  <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
                    <h3 className="font-bold text-gray-800">{f.restaurant_name}</h3>
                    <p className="text-gray-600 text-sm">{f.restaurant_cuisine} · {f.restaurant_city}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <div>
          <h3 className="text-lg font-bold mb-4">My Reviews</h3>
          {reviews.length === 0 ? (
            <p className="text-gray-500 py-4">No reviews yet.</p>
          ) : (
            reviews.map((r) => (
              <div key={r.id} className="mb-4">
                <Link to={`/restaurants/${r.restaurant_id}`} className="text-blue-600 font-semibold hover:underline">
                  {r.restaurant_name}
                </Link>
                <div className="flex items-center gap-2 mt-1">
                  <StarRating rating={r.rating} size={14} />
                  <span className="text-sm text-gray-500">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}
                  </span>
                </div>
                <p className="text-gray-700 mt-1">{r.comment}</p>
                <hr className="mt-3" />
              </div>
            ))
          )}
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === "preferences" && (
        <div className="text-center py-4">
          <Link to="/preferences"
            className="px-6 py-3 text-white rounded-md font-semibold no-underline"
            style={{ backgroundColor: "#d32323" }}>
            Edit Preferences
          </Link>
        </div>
      )}
    </div>
  );
}
