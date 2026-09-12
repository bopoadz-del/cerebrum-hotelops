import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "./lib/utils";
import OpsPage from "./pages/OpsPage";
import GuestPage from "./pages/GuestPage";
import DocumentsPage from "./pages/DocumentsPage";
import ActionsPage from "./pages/ActionsPage";
import AuditPage from "./pages/AuditPage";
import { Input } from "./components/ui/input";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";

const NAV = [
  { to: "/ops", label: "Ops" },
  { to: "/guest", label: "Guest" },
  { to: "/documents", label: "Documents" },
  { to: "/actions", label: "Actions" },
  { to: "/audit", label: "Audit" },
];

export default function App() {
  const [health, setHealth] = useState<{ status?: string; markets?: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tok, setTok] = useState(localStorage.getItem("hotelops_token") || "operator-pilot");

  useEffect(() => {
    api<{ status: string; markets: string[] }>("/health")
      .then(setHealth)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="min-h-screen">
      <header className="border-b border-ink/10 bg-ink text-sand">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-brass">Cerebrum</p>
            <h1 className="text-2xl">HotelOps</h1>
            <p className="text-sm text-sand/70">Ops reasoner + guest intelligence · UAE + generic</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {health?.markets?.map((m) => (
              <Badge key={m}>{m}</Badge>
            ))}
            <Input
              className="w-44 bg-white text-ink"
              value={tok}
              onChange={(e) => setTok(e.target.value)}
              aria-label="API token"
            />
            <Button
              onClick={() => {
                localStorage.setItem("hotelops_token", tok);
                window.location.reload();
              }}
            >
              Use token
            </Button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 px-4 pb-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-brass text-ink" : "text-sand/80 hover:bg-white/10"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
            API unreachable: {error}. Start uvicorn on port 43180.
          </div>
        )}
        <Routes>
          <Route path="/" element={<Navigate to="/ops" replace />} />
          <Route path="/ops" element={<OpsPage />} />
          <Route path="/guest" element={<GuestPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/actions" element={<ActionsPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Routes>
      </main>
    </div>
  );
}
