import { useEffect, useState } from "react";
import { api } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Cascade = {
  critical_path: string[];
  project_days: number;
  lrm_alerts: { id: string; detail: string; severity: string }[];
};

export default function OpsPage() {
  const [milestones, setMilestones] = useState<{ id: string; name: string }[]>([]);
  const [cascade, setCascade] = useState<Cascade | null>(null);
  const [evidence, setEvidence] = useState<Record<string, unknown> | null>(null);
  const [license, setLicense] = useState<Record<string, unknown> | null>(null);
  const [ppm, setPpm] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<{ milestones: { id: string; name: string }[] }>("/pre-opening/milestones")
      .then((d) => setMilestones(d.milestones))
      .catch((e) => setErr(e.message));
  }, []);

  async function simulate() {
    setLoading(true);
    setErr(null);
    try {
      const data = await api<Cascade>("/pre-opening/simulate", {
        method: "POST",
        body: JSON.stringify({ slips: { M07: 10 } }),
      });
      setCascade(data);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "simulate failed");
    } finally {
      setLoading(false);
    }
  }

  async function firePump() {
    const data = await api<Record<string, unknown>>("/engineering/classify", {
      method: "POST",
      body: JSON.stringify({
        asset_type: "fire_pump",
        documents: ["uncontrolled_photo_or_note"],
        photo_tags: ["cover_closed", "clip_obscuring_nameplate"],
        nameplate_readable: false,
      }),
    });
    setEvidence(data);
  }

  async function licenses() {
    setLicense(await api("/licensing/evaluate", { method: "POST", body: JSON.stringify({ market: "uae" }) }));
  }

  async function refusePpm() {
    setPpm(
      await api("/operational/ppm", {
        method: "POST",
        body: JSON.stringify({ market: "uae", asset_type: "fire_pump", operator_sop: "" }),
      }),
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {err && <p className="md:col-span-2 text-sm text-red-800">{err}</p>}
      <Card className="md:col-span-2">
        <CardTitle>Pre-opening (M01–M15)</CardTitle>
        <p className="mb-3 text-sm text-ink/70">
          {loading ? "Computing critical path…" : "Empty programme until you simulate a slip."}
        </p>
        <div className="mb-3 flex flex-wrap gap-2">
          {milestones.map((m) => (
            <Badge key={m.id}>{m.id}</Badge>
          ))}
        </div>
        <Button onClick={simulate}>Simulate M07 +10 days</Button>
        {cascade && (
          <div className="mt-3 text-sm">
            <p>Critical path: {cascade.critical_path.join(" → ")}</p>
            <p>Project days: {cascade.project_days}</p>
            <ul className="mt-2 list-disc pl-5">
              {cascade.lrm_alerts.map((a) => (
                <li key={a.id + a.detail}>
                  {a.id} ({a.severity}): {a.detail}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>
      <Card>
        <CardTitle>Engineering inheritance</CardTitle>
        <Button onClick={firePump}>Judge fire pump (covers/clips)</Button>
        {evidence && <pre className="mono mt-3 overflow-auto text-xs">{JSON.stringify(evidence, null, 2)}</pre>}
      </Card>
      <Card>
        <CardTitle>Licensing + PPM</CardTitle>
        <div className="flex flex-wrap gap-2">
          <Button onClick={licenses}>Evaluate UAE pack</Button>
          <Button className="bg-ink" onClick={refusePpm}>
            PPM without SOP
          </Button>
        </div>
        {license && <p className="mt-2 text-sm">Overall: {String(license.overall ?? license.status)}</p>}
        {ppm && <pre className="mono mt-3 overflow-auto text-xs">{JSON.stringify(ppm, null, 2)}</pre>}
      </Card>
    </div>
  );
}
