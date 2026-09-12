import { useEffect, useState } from "react";
import { api } from "@/lib/utils";
import { Card, CardTitle } from "@/components/ui/card";

export default function AuditPage() {
  const [events, setEvents] = useState<unknown[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<{ events: unknown[] }>("/audit")
      .then((d) => setEvents(d.events))
      .catch((e) => setErr(e.message));
  }, []);

  return (
    <Card>
      <CardTitle>HTTP audit log</CardTitle>
      {err && <p className="text-sm text-red-800">{err}</p>}
      {events.length === 0 && !err && <p className="text-sm text-ink/70">No audited requests yet.</p>}
      <pre className="mono overflow-auto text-xs">{JSON.stringify(events, null, 2)}</pre>
    </Card>
  );
}
