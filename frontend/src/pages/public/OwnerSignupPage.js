import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { signup } from "../../api/authApi";
import { useAuth } from "../../context/AuthContext";

export default function OwnerSignupPage() {
  const [form, setForm] = useState({ name: "", email: "", password: "", confirmPassword: "", restaurant_location: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      const res = await signup({
        name: form.name, email: form.email, password: form.password,
        role: "owner", restaurant_location: form.restaurant_location,
      });
      loginUser(res.data.access_token, res.data.user);
      navigate("/owner/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-3xl font-bold text-center mb-2" style={{ color: "#d32323" }}>
          Owner Sign Up
        </h2>
        <p className="text-center text-gray-600 mb-6">Register as a restaurant owner</p>

        {error && <div className="bg-red-100 text-red-700 px-4 py-3 rounded mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input type="text" name="name" value={form.name} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" name="email" value={form.email} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Location</label>
            <input type="text" name="restaurant_location" value={form.restaurant_location} onChange={handleChange} required
              placeholder="e.g., San Jose, CA"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" name="password" value={form.password} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
            <input type="password" name="confirmPassword" value={form.confirmPassword} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" />
          </div>
          <button type="submit" disabled={loading}
            className="w-full py-3 text-white rounded-md font-semibold hover:opacity-90 disabled:opacity-50 border-none cursor-pointer"
            style={{ backgroundColor: "#d32323" }}>
            {loading ? "Signing up..." : "Sign Up as Owner"}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-4">
          Already have an account? <Link to="/owner/login" style={{ color: "#d32323" }}>Log in</Link>
        </p>
        <p className="text-center text-gray-600 mt-2">
          Not an owner? <Link to="/signup" style={{ color: "#d32323" }}>User Sign Up</Link>
        </p>
      </div>
    </div>
  );
}
