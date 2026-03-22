import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useState } from "react";

export default function Navbar() {
  const { isAuthenticated, user, role, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav style={{ backgroundColor: "#d32323" }} className="text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-2xl font-bold text-white no-underline">
            Yelp Prototype
          </Link>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-white text-2xl"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? "\u2715" : "\u2630"}
          </button>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center space-x-4">
            <Link to="/" className="text-white no-underline hover:opacity-80 px-3 py-2">
              Home
            </Link>
            <Link to="/search" className="text-white no-underline hover:opacity-80 px-3 py-2">
              Search
            </Link>

            {!isAuthenticated ? (
              <>
                <Link to="/login" className="text-white no-underline hover:opacity-80 px-3 py-2">
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="bg-white no-underline px-4 py-2 rounded font-semibold"
                  style={{ color: "#d32323" }}
                >
                  Sign Up
                </Link>
              </>
            ) : role === "owner" ? (
              <>
                <Link to="/owner/dashboard" className="text-white no-underline hover:opacity-80 px-3 py-2">
                  Dashboard
                </Link>
                <Link to="/owner/restaurants" className="text-white no-underline hover:opacity-80 px-3 py-2">
                  My Restaurants
                </Link>
                <Link to="/profile" className="text-white no-underline hover:opacity-80 px-3 py-2">
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="bg-white px-4 py-2 rounded font-semibold border-none cursor-pointer"
                  style={{ color: "#d32323" }}
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/restaurants/add" className="text-white no-underline hover:opacity-80 px-3 py-2">
                  Add Restaurant
                </Link>
                <Link to="/profile" className="text-white no-underline hover:opacity-80 px-3 py-2">
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="bg-white px-4 py-2 rounded font-semibold border-none cursor-pointer"
                  style={{ color: "#d32323" }}
                >
                  Logout
                </button>
              </>
            )}
          </div>
        </div>

        {/* Mobile nav */}
        {menuOpen && (
          <div className="md:hidden pb-4 space-y-2">
            <Link to="/" className="block text-white no-underline py-2" onClick={() => setMenuOpen(false)}>Home</Link>
            <Link to="/search" className="block text-white no-underline py-2" onClick={() => setMenuOpen(false)}>Search</Link>
            {!isAuthenticated ? (
              <>
                <Link to="/login" className="block text-white no-underline py-2" onClick={() => setMenuOpen(false)}>Login</Link>
                <Link to="/signup" className="block text-white no-underline py-2" onClick={() => setMenuOpen(false)}>Sign Up</Link>
              </>
            ) : (
              <>
                <Link to="/profile" className="block text-white no-underline py-2" onClick={() => setMenuOpen(false)}>Profile</Link>
                {role === "owner" && (
                  <Link to="/owner/dashboard" className="block text-white no-underline py-2" onClick={() => setMenuOpen(false)}>Dashboard</Link>
                )}
                <button onClick={() => { handleLogout(); setMenuOpen(false); }} className="block text-white bg-transparent border-none cursor-pointer py-2">Logout</button>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
