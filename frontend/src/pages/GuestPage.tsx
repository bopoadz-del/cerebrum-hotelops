import { useEffect, useState } from "react";
import { api } from "@/lib/utils";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type Profile = { guest_id: string; name: string; market: string; language: string };

export default function GuestPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [empty, setEmpty] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<{ profiles: Profile[] }>("/guest/profiles")
      .then((d) => {
        setProfiles(d.profiles);
        setEmpty(d.profiles.length === 0);
      })
      .catch((e) => setErr(e.message));
    api("/guest/report")
      .then(setReport)
      .catch(() => undefined);
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {err && <p className="md:col-span-2 text-sm text-red-800">{err}</p>}
      <Card>
        <CardTitle>Fixture guests (UAE + generic)</CardTitle>
        {empty && <p className="text-sm text-ink/70">No guest fixtures loaded.</p>}
        <ul className="space-y-2">
          {profiles.map((p) => (
            <li key={p.guest_id} className="flex items-center justify-between gap-2">
              <span>
                {p.name} <Badge>{p.market}</Badge>
              </span>
              <Button onClick={() => api(`/guest/profiles/${p.guest_id}`).then(setDetail)}>Open</Button>
            </li>
          ))}
        </ul>
      </Card>
      <Card>
        <CardTitle>Intelligence</CardTitle>
        {!detail && <p className="text-sm text-ink/70">Select a guest to see funnel, loyalty, and personalization.</p>}
        {detail && <pre className="mono overflow-auto text-xs">{JSON.stringify(detail, null, 2)}</pre>}
      </Card>
      <Card className="md:col-span-2">
        <CardTitle>Surface report</CardTitle>
        {report ? (
          <pre className="mono overflow-auto text-xs">{JSON.stringify(report, null, 2)}</pre>
        ) : (
          <p className="text-sm">Loading report…</p>
        )}
      </Card>
    </div>
  );
}
