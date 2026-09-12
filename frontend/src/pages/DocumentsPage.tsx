import { useEffect, useState } from "react";
import { api } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<{ id: number; title: string; doc_type: string }[]>([]);
  const [hits, setHits] = useState<unknown[]>([]);
  const [q, setQ] = useState("fire pump");
  const [title, setTitle] = useState("Civil Defense pack note");
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    const data = await api<{ documents: { id: number; title: string; doc_type: string }[] }>("/documents");
    setDocs(data.documents);
  }

  useEffect(() => {
    refresh().catch((e) => setErr(e.message));
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {err && <p className="md:col-span-2 text-sm text-red-800">{err}</p>}
      <Card>
        <CardTitle>Indexed documents</CardTitle>
        {docs.length === 0 && <p className="text-sm text-ink/70">No documents yet — add a note to seed retrieval.</p>}
        <ul className="mb-3 list-disc pl-5 text-sm">
          {docs.map((d) => (
            <li key={d.id}>
              {d.title} ({d.doc_type})
            </li>
          ))}
        </ul>
        <Input className="mb-2" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Button
          onClick={async () => {
            await api("/documents", {
              method: "POST",
              body: JSON.stringify({
                title,
                doc_type: "note",
                body: "Fire pump nameplate must be unobstructed. CCTV and utility accounts precede Civil Defense.",
              }),
            });
            await refresh();
          }}
        >
          Add note
        </Button>
      </Card>
      <Card>
        <CardTitle>Hybrid retrieval</CardTitle>
        <div className="mb-2 flex gap-2">
          <Input value={q} onChange={(e) => setQ(e.target.value)} />
          <Button onClick={() => api<{ hits: unknown[] }>(`/documents/search?q=${encodeURIComponent(q)}`).then((d) => setHits(d.hits))}>
            Search
          </Button>
        </div>
        <pre className="mono overflow-auto text-xs">{JSON.stringify(hits, null, 2)}</pre>
      </Card>
    </div>
  );
}
