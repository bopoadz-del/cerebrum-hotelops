import { useEffect, useState } from "react";
import { api } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

export default function ActionsPage() {
  const [actions, setActions] = useState<{ action_id: string; description: string }[]>([]);
  const [runs, setRuns] = useState<unknown[]>([]);
  const [out, setOut] = useState<unknown>(null);

  useEffect(() => {
    api<{ actions: { action_id: string; description: string }[] }>("/actions").then((d) => setActions(d.actions));
    api<{ runs: unknown[] }>("/actions/runs/recent").then((d) => setRuns(d.runs));
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardTitle>Action registry</CardTitle>
        <ul className="space-y-2 text-sm">
          {actions.map((a) => (
            <li key={a.action_id} className="flex items-center justify-between gap-2">
              <span>
                <strong>{a.action_id}</strong> — {a.description}
              </span>
              <Button
                onClick={async () => {
                  const payload =
                    a.action_id === "ppm.resolve"
                      ? { market: "uae", asset_type: "fire_pump", operator_sop: "Monthly flow test SOP." }
                      : a.action_id === "licensing.evaluate"
                        ? { market: "uae" }
                        : a.action_id === "engineering.classify"
                          ? { asset_type: "grms", room_map_complete: true }
                          : { slips: { M13: 5 } };
                  setOut(await api(`/actions/${a.action_id}`, { method: "POST", body: JSON.stringify(payload) }));
                  const r = await api<{ runs: unknown[] }>("/actions/runs/recent");
                  setRuns(r.runs);
                }}
              >
                Run
              </Button>
            </li>
          ))}
        </ul>
        {out != null && <pre className="mono mt-3 overflow-auto text-xs">{JSON.stringify(out, null, 2)}</pre>}
      </Card>
      <Card>
        <CardTitle>action_runs audit</CardTitle>
        {runs.length === 0 && <p className="text-sm text-ink/70">No runs yet.</p>}
        <pre className="mono overflow-auto text-xs">{JSON.stringify(runs, null, 2)}</pre>
      </Card>
    </div>
  );
}
