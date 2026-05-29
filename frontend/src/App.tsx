import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/layout";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import { Onboarding } from "./pages/Onboarding";
import NotFound from "./pages/NotFound";
import { useAuth } from "./context/AuthContext";

function GuestOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to={user.has_watch_history ? "/dashboard" : "/onboarding"} replace />;
  return <>{children}</>;
}

function RequireOnboarding({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/" replace />;
  if (!user.has_watch_history) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
}

function RequireNoOnboarding({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/" replace />;
  if (user.has_watch_history) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<GuestOnly><Landing /></GuestOnly>} />
        <Route
          path="dashboard"
          element={
            <RequireOnboarding>
              <Dashboard />
            </RequireOnboarding>
          }
        />
      </Route>
      <Route
        path="/onboarding"
        element={
          <RequireNoOnboarding>
            <Onboarding />
          </RequireNoOnboarding>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
