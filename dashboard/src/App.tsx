import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';
import AppShell from './components/AppShell';

// Public pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Apply from './pages/Apply';
import Register from './pages/Register';

// Owner pages
import OwnerDashboard from './pages/OwnerDashboard';
import Analytics from './pages/Analytics';
import ManageUsers from './pages/ManageUsers';

// Shared authenticated pages
import Broadcasts from './pages/Broadcasts';

// Mentee pages
import MenteeDashboard from './pages/MenteeDashboard';
import Academy from './pages/Academy';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>

          {/* ── Public routes ─────────────────────────────────────── */}
          <Route path="/" element={
            <PublicRoute><Landing /></PublicRoute>
          } />
          <Route path="/login" element={
            <PublicRoute><Login /></PublicRoute>
          } />
          <Route path="/apply" element={
            <PublicRoute><Apply /></PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute><Register /></PublicRoute>
          } />

          {/* ── Owner routes ───────────────────────────────────────── */}
          <Route path="/monitor" element={
            <ProtectedRoute role="owner">
              <AppShell><OwnerDashboard /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute role="owner">
              <AppShell><Analytics /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/manage" element={
            <ProtectedRoute role="owner">
              <AppShell><ManageUsers /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/broadcasts" element={
            <ProtectedRoute role="owner">
              <AppShell><Broadcasts /></AppShell>
            </ProtectedRoute>
          } />

          {/* ── Mentee routes ──────────────────────────────────────── */}
          <Route path="/home" element={
            <ProtectedRoute role="mentee">
              <AppShell><MenteeDashboard /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/academy" element={
            <ProtectedRoute role="mentee">
              <AppShell><Academy /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/updates" element={
            <ProtectedRoute role="mentee">
              <AppShell><Broadcasts /></AppShell>
            </ProtectedRoute>
          } />

          {/* ── Fallback ───────────────────────────────────────────── */}
          <Route path="*" element={<Navigate to="/" replace />} />

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
