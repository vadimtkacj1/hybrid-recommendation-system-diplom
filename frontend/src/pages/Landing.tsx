import { Button } from "@/components/ui/button"
import { useAuth } from "@/context/AuthContext"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Eye, EyeOff } from "lucide-react"


export default function Landing() {
  const { user, login, register, loading } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<"login" | "register">("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [name, setName] = useState("")
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [pointer, setPointer] = useState({ x: 50, y: 35 })

  useEffect(() => {
    if (user && !loading) {
      navigate(user.has_watch_history ? "/dashboard" : "/onboarding", { replace: true })
    }
  }, [user, loading, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-stone-950">
        <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
      </div>
    )
  }

  const validate = () => {
    const e: Record<string, string> = {}
    if (mode === "register" && !name.trim()) e.name = "Enter your name"
    if (!email.trim()) e.email = "Enter your email"
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Invalid email address"
    if (!password) e.password = "Enter your password"
    else if (password.length < 6) e.password = "Password must be at least 6 characters"
    else if (new TextEncoder().encode(password).length > 72) e.password = "Password is too long"
    if (mode === "register" && !confirm) e.confirm = "Confirm your password"
    else if (mode === "register" && confirm !== password) e.confirm = "Passwords do not match"
    return e
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setServerError(null)
    const fieldErrors = validate()
    if (Object.keys(fieldErrors).length > 0) { setErrors(fieldErrors); return }
    setErrors({})
    setSubmitting(true)
    try {
      if (mode === "login") {
        await login(email, password)
      } else {
        await register(email, password, name.trim())
      }
      navigate("/dashboard", { replace: true })
    } catch (err) {
      setServerError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="min-h-screen bg-stone-950 text-stone-100 overflow-hidden relative"
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect()
        const x = ((e.clientX - rect.left) / rect.width) * 100
        const y = ((e.clientY - rect.top) / rect.height) * 100
        setPointer({ x, y })
      }}
      onTouchMove={(e) => {
        const touch = e.touches[0]
        const rect = e.currentTarget.getBoundingClientRect()
        const x = ((touch.clientX - rect.left) / rect.width) * 100
        const y = ((touch.clientY - rect.top) / rect.height) * 100
        setPointer({ x, y })
      }}
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-[800px] h-[500px] bg-amber-500/5 rounded-full blur-[120px]" />
      </div>
      <div
        className="absolute inset-0 opacity-[0.11]"
        style={{
          backgroundImage: `linear-gradient(to right, currentColor 1px, transparent 1px),
            linear-gradient(to bottom, currentColor 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
          backgroundPosition: `${50 + (pointer.x - 50) * 0.03}% ${50 + (pointer.y - 50) * 0.03}%`,
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-200"
        style={{
          background: `radial-gradient(circle 260px at ${pointer.x}% ${pointer.y}%, rgba(251,191,36,0.22), transparent 72%)`,
        }}
      />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: `linear-gradient(to right, rgba(251,191,36,0.22) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(251,191,36,0.22) 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
          maskImage: `radial-gradient(circle 300px at ${pointer.x}% ${pointer.y}%, black 35%, transparent 85%)`,
          WebkitMaskImage: `radial-gradient(circle 300px at ${pointer.x}% ${pointer.y}%, black 35%, transparent 85%)`,
          opacity: 0.55,
        }}
      />

      <header className="relative z-10 flex justify-between items-center px-6 py-5 md:px-12">
        <span className="font-semibold tracking-tight">LikeMind</span>
      </header>

      <main className="relative z-10 flex flex-col items-center px-6 pt-16 pb-32 md:pt-24">
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tight text-center max-w-3xl leading-[1.06] mb-4">
          Find people who{" "}
          <span className="text-amber-400/90">think like you</span>
        </h1>

        <div className="w-full max-w-sm bg-stone-900 border border-stone-800 rounded-2xl p-6">
          <div className="flex mb-6 rounded-xl bg-stone-800/50 p-1">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => { setMode(m); setErrors({}); setServerError(null); setConfirm("") }}
                className={`flex-1 py-1.5 text-sm rounded-lg font-medium transition-colors ${
                  mode === m
                    ? "bg-stone-700 text-stone-100"
                    : "text-stone-500 hover:text-stone-300"
                }`}
              >
                {m === "login" ? "Sign in" : "Sign up"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-2">
            {mode === "register" && (
              <div className="flex flex-col gap-1">
                <input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => { setName(e.target.value); setErrors((p) => ({ ...p, name: "" })) }}
                  className={`w-full px-3 py-2.5 rounded-xl bg-stone-800 border text-stone-100 placeholder-stone-500 text-sm focus:outline-none transition-colors ${
                    errors.name ? "border-red-500/70 focus:border-red-500" : "border-stone-700 focus:border-amber-500/50"
                  }`}
                />
                {errors.name && <p className="text-red-400 text-xs px-1">{errors.name}</p>}
              </div>
            )}
            <div className="flex flex-col gap-1">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: "" })) }}
                className={`w-full px-3 py-2.5 rounded-xl bg-stone-800 border text-stone-100 placeholder-stone-500 text-sm focus:outline-none transition-colors ${
                  errors.email ? "border-red-500/70 focus:border-red-500" : "border-stone-700 focus:border-amber-500/50"
                }`}
              />
              {errors.email && <p className="text-red-400 text-xs px-1">{errors.email}</p>}
            </div>
            <div className="flex flex-col gap-1">
              <div className={`flex items-center rounded-xl bg-stone-800 border transition-colors ${
                errors.password ? "border-red-500/70" : "border-stone-700 focus-within:border-amber-500/50"
              }`}>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: "" })) }}
                  className="flex-1 px-3 py-2.5 bg-transparent text-stone-100 placeholder-stone-500 text-sm focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="px-3 text-stone-500 hover:text-stone-300 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs px-1">{errors.password}</p>}
            </div>
            {mode === "register" && (
              <div className="flex flex-col gap-1">
                <div className={`flex items-center rounded-xl bg-stone-800 border transition-colors ${
                  errors.confirm ? "border-red-500/70" : "border-stone-700 focus-within:border-amber-500/50"
                }`}>
                  <input
                    type={showConfirm ? "text" : "password"}
                    placeholder="Confirm password"
                    value={confirm}
                    onChange={(e) => { setConfirm(e.target.value); setErrors((p) => ({ ...p, confirm: "" })) }}
                    className="flex-1 px-3 py-2.5 bg-transparent text-stone-100 placeholder-stone-500 text-sm focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm((v) => !v)}
                    className="px-3 text-stone-500 hover:text-stone-300 transition-colors"
                    tabIndex={-1}
                  >
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.confirm && <p className="text-red-400 text-xs px-1">{errors.confirm}</p>}
              </div>
            )}

            {serverError && (
              <p className="text-red-400 text-xs px-1 pt-1">{serverError}</p>
            )}

            <Button
              type="submit"
              disabled={submitting}
              className="w-full bg-amber-500 hover:bg-amber-400 text-stone-950 font-semibold h-10 rounded-xl mt-2"
            >
              {submitting ? "…" : mode === "login" ? "Sign in" : "Create account"}
            </Button>
          </form>
        </div>

      </main>
    </div>
  )
}
