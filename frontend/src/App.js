import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

// Public pages
import HomePage from "./pages/public/HomePage";
import SearchResultsPage from "./pages/public/SearchResultsPage";
import RestaurantDetailPage from "./pages/public/RestaurantDetailPage";
import UserSignupPage from "./pages/public/UserSignupPage";
import UserLoginPage from "./pages/public/UserLoginPage";
import OwnerSignupPage from "./pages/public/OwnerSignupPage";
import OwnerLoginPage from "./pages/public/OwnerLoginPage";

// User pages
import ProfilePage from "./pages/user/ProfilePage";
import PreferencesPage from "./pages/user/PreferencesPage";
import AddRestaurantPage from "./pages/user/AddRestaurantPage";
import WriteReviewPage from "./pages/user/WriteReviewPage";

// Owner pages
import OwnerDashboardPage from "./pages/owner/OwnerDashboardPage";
import OwnerRestaurantsPage from "./pages/owner/OwnerRestaurantsPage";
import ClaimRestaurantPage from "./pages/owner/ClaimRestaurantPage";

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchResultsPage />} />
            <Route path="/restaurants/:id" element={<RestaurantDetailPage />} />
            <Route path="/signup" element={<UserSignupPage />} />
            <Route path="/login" element={<UserLoginPage />} />
            <Route path="/owner/signup" element={<OwnerSignupPage />} />
            <Route path="/owner/login" element={<OwnerLoginPage />} />

            {/* User Protected Routes */}
            <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
            <Route path="/preferences" element={<ProtectedRoute><PreferencesPage /></ProtectedRoute>} />
            <Route path="/restaurants/add" element={<ProtectedRoute><AddRestaurantPage /></ProtectedRoute>} />
            <Route path="/restaurants/:id/review" element={<ProtectedRoute><WriteReviewPage /></ProtectedRoute>} />
            <Route path="/restaurants/:id/review/:reviewId" element={<ProtectedRoute><WriteReviewPage /></ProtectedRoute>} />

            {/* Owner Protected Routes */}
            <Route path="/owner/dashboard" element={<ProtectedRoute requiredRole="owner"><OwnerDashboardPage /></ProtectedRoute>} />
            <Route path="/owner/restaurants" element={<ProtectedRoute requiredRole="owner"><OwnerRestaurantsPage /></ProtectedRoute>} />
            <Route path="/owner/claim" element={<ProtectedRoute requiredRole="owner"><ClaimRestaurantPage /></ProtectedRoute>} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
