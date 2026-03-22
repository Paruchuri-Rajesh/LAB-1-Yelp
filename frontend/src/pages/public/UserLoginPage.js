import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../../api/authApi";
import { useAuth } from "../../context/AuthContext";

export default function UserLoginPage() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login({ email: form.email, password: form.password });
      loginUser(res.data.access_token, res.data.user);
      if (res.data.user.role === "owner") {
        navigate("/owner/dashboard");
      } else {
        navigate("/");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-3xl font-bold text-center mb-2" style={{ color: "#d32323" }}>
          Log In
        </h2>
        <p className="text-center text-gray-600 mb-6">
          Welcome back! Log in to your account
        </p>

        {error && (
          <div className="bg-red-100 text-red-700 px-4 py-3 rounded mb-4">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email" name="email" value={form.email} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password" name="password" value={form.password} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
          <button
            type="submit" disabled={loading}
            className="w-full py-3 text-white rounded-md font-semibold hover:opacity-90 disabled:opacity-50 border-none cursor-pointer"
            style={{ backgroundColor: "#d32323" }}
          >
            {loading ? "Logging in..." : "Log In"}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-4">
          New to Yelp Prototype?{" "}
          <Link to="/signup" style={{ color: "#d32323" }}>Sign Up</Link>
        </p>
        <p className="text-center text-gray-600 mt-2">
          Restaurant owner?{" "}
          <Link to="/owner/login" style={{ color: "#d32323" }}>Owner Login</Link>
        </p>
      </div>
    </div>
  );
}
