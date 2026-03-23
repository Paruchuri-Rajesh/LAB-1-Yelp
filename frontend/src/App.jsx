import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import ProtectedRoute from './components/layout/ProtectedRoute'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import SearchPage from './pages/SearchPage'
import RestaurantPage from './pages/RestaurantPage'
import ProfilePage from './pages/ProfilePage'
import OwnerDashboardPage from './pages/OwnerDashboardPage'
import OwnerRestaurantPage from './pages/OwnerRestaurantPage'
import OwnerNewRestaurantPage from './pages/OwnerNewRestaurantPage'
import SuggestRestaurantPage from './pages/SuggestRestaurantPage'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/restaurants/:id" element={<RestaurantPage />} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/profile/:tab" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/owner" element={<ProtectedRoute><OwnerDashboardPage /></ProtectedRoute>} />
          <Route path="/owner/new" element={<ProtectedRoute><OwnerNewRestaurantPage /></ProtectedRoute>} />
          <Route path="/suggest" element={<ProtectedRoute><SuggestRestaurantPage /></ProtectedRoute>} />
          <Route path="/owner/restaurants/:id" element={<ProtectedRoute><OwnerRestaurantPage /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  )
}
