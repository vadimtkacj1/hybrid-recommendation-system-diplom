import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function NotFound() {
  const { user } = useAuth();
  const home = user ? (user.has_watch_history ? "/dashboard" : "/onboarding") : "/";

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col items-center justify-center px-6">
      <p className="text-8xl font-bold text-amber-500/20 select-none mb-2">404</p>
      <h1 className="text-2xl font-semibold tracking-tight mb-2">Page not found</h1>
      <p className="text-stone-500 text-sm mb-8 text-center max-w-xs">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        to={home}
        className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-stone-950 font-semibold text-sm transition-colors"
      >
        Go home
      </Link>
    </div>
  );
}
