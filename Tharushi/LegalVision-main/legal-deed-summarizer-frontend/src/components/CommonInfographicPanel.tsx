import { useMemo, useRef, useState } from "react";
import {
  BadgeCheck,
  Users,
  MapPinned,
  Coins,
  Landmark,
  ChevronDown,
  ChevronUp,
  Download,
  Gavel,
  Home,
  UserCircle2,
  Stamp,
} from "lucide-react";
import { toPng } from "html-to-image";

import notarySeal from "../assets/notary-seal.png";

type Props = { infographic: any };

function safeStr(x: any) {
  if (x === null || x === undefined) return "";
  return String(x);
}
function pickFirstNonEmpty(...vals: any[]) {
  for (const v of vals) {
    if (v !== null && v !== undefined && String(v).trim() !== "") return v;
  }
  return null;
}

function Chip({ children }: { children: any }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs text-white">
      {children}
    </span>
  );
}

function KV({ k, v }: { k: string; v: any }) {
  const val = pickFirstNonEmpty(v);
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-neutral-500">{k}</div>
      <div className="text-sm font-semibold text-neutral-900">{val ?? "—"}</div>
    </div>
  );
}

function CardShell({
  title,
  icon,
  badgeIcon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  badgeIcon: React.ReactNode;
  children: any;
}) {
  return (
    <div className="relative rounded-3xl border border-neutral-300 bg-neutral-50 shadow-sm">
      {/* header */}
      <div className="flex items-center justify-between gap-3 border-b border-neutral-200 px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="text-neutral-800">{icon}</div>
          <div className="text-sm font-semibold text-neutral-900">{title}</div>
        </div>

        {/* stamp circle */}
        <div className="grid h-12 w-12 place-items-center rounded-full border border-neutral-300 bg-white shadow-sm">
          {badgeIcon}
        </div>
      </div>

      {/* body */}
      <div className="px-5 py-5">{children}</div>
    </div>
  );
}

function PartyItem({ role, name, nic, address }: any) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-semibold text-neutral-700">{role || "Role"}</div>
          <div className="mt-1 text-sm font-extrabold text-neutral-900">{name || "—"}</div>
          {address ? (
            <div className="mt-1 text-xs text-neutral-600">{address}</div>
          ) : null}
        </div>
        {nic ? (
          <span className="rounded-full border border-neutral-200 bg-neutral-100 px-3 py-1 text-[11px] font-semibold text-neutral-700">
            NIC: {nic}
          </span>
        ) : null}
      </div>
    </div>
  );
}

export default function CommonInfographicPanel({ infographic }: Props) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [showTrace, setShowTrace] = useState(false);

  const view = useMemo(() => {
    if (!infographic) return null;

    const h = infographic.header || {};
    const money = infographic.money || {};
    const prop = infographic.property || {};
    const notary = infographic.notary || {};
    const highlights = infographic.highlights || {};
    const parties = infographic.parties || [];
    const traceability = infographic.traceability || [];

    const badges: string[] = [];
    if (h.deed_type) badges.push(safeStr(h.deed_type));
    if (prop.district) badges.push(`District: ${safeStr(prop.district)}`);
    if (h.deed_number) badges.push(`No: ${safeStr(h.deed_number)}`);

    return { h, money, prop, notary, highlights, parties, traceability, badges };
  }, [infographic]);

  if (!view) return null;

  async function downloadPng() {
    if (!ref.current) return;
    setDownloading(true);
    try {
      const dataUrl = await toPng(ref.current, {
        cacheBust: true,
        pixelRatio: 2,
        backgroundColor: "#ffffff",
      });
      const a = document.createElement("a");
      a.href = dataUrl;
      a.download = `infographic_${safeStr(h.deed_number || "deed")}.png`;
      a.click();
    } finally {
      setDownloading(false);
    }
  }

  const { h, money, prop, notary, highlights, parties, traceability, badges } = view;

  return (
    <div className="space-y-4">
      {/* Download */}
      <div className="flex justify-end">
        <button
          onClick={downloadPng}
          disabled={downloading}
          className="inline-flex items-center gap-2 rounded-xl bg-neutral-900 px-4 py-2 text-sm text-white disabled:opacity-60"
        >
          <Download className="h-4 w-4" />
          {downloading ? "Generating…" : "Download PNG"}
        </button>
      </div>

      {/* CANVAS */}
<div ref={ref} className="rounded-3xl border border-[#b2bcc3] bg-[#d2dbe0] p-5 text-white shadow-sm">        <div className="rounded-3xl border border-neutral-700 bg-neutral-800 p-5 text-white shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            {/* left */}
            <div>
              <div className="text-xs uppercase tracking-wide text-white/75">
                LEGAL DEED INFOGRAPHIC
              </div>
              <div className="mt-1 text-3xl font-extrabold">
                {h.title || "LEGAL DEED"}
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {badges.slice(0, 3).map((b, i) => (
                  <Chip key={i}>{b}</Chip>
                ))}
              </div>
            </div>

            {/* right execution box */}
            <div className="min-w-[320px] max-w-[520px] flex-1 rounded-2xl border border-white/15 bg-white/10 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <BadgeCheck className="h-4 w-4" />
                Execution
              </div>

              <div className="mt-3 space-y-2 text-sm">
                <div>
                  <div className="text-xs text-white/70">Date</div>
                  <div className="font-semibold">{h.execution_date || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-white/70">Place</div>
                  <div className="font-semibold">{h.execution_place || "—"}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* MAIN GRID 2x2 */}
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          {/* Parties */}
          <CardShell
            title="Parties"
            icon={<Users className="h-5 w-5" />}
            badgeIcon={<UserCircle2 className="h-6 w-6 text-neutral-700" />}
          >
            <div className="space-y-3">
              {(parties || []).length ? (
                parties.slice(0, 6).map((p: any, i: number) => (
                  <PartyItem
                    key={i}
                    role={p.role}
                    name={p.name}
                    nic={p.nic}
                    address={p.address}
                  />
                ))
              ) : (
                <div className="text-sm text-neutral-600">No parties extracted.</div>
              )}
            </div>
          </CardShell>

          {/* Property */}
          <CardShell
            title="Property"
            icon={<MapPinned className="h-5 w-5" />}
            badgeIcon={<Home className="h-6 w-6 text-neutral-700" />}
          >
            <div className="space-y-4">
              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
                <div className="text-[11px] uppercase tracking-wide text-neutral-500">
                  Description
                </div>
                <div className="mt-2 text-sm text-neutral-900 whitespace-pre-wrap">
                  {prop.description || "—"}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <KV k="District" v={prop.district} />
                <KV k="Local Authority" v={prop.local_authority} />
              </div>

              <KV k="Extent" v={prop.extent} />
            </div>
          </CardShell>

          {/* Consideration */}
          <CardShell
            title="Consideration / Value"
            icon={<Coins className="h-5 w-5" />}
            badgeIcon={<Stamp className="h-6 w-6 text-neutral-700" />}
          >
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <KV k="Amount (text)" v={money.amount_text} />
                <KV k="Amount (numeric)" v={money.amount_numeric} />
              </div>

              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
                <div className="text-[11px] uppercase tracking-wide text-neutral-500">
                  Payment terms
                </div>
                <div className="mt-2 text-sm text-neutral-900 whitespace-pre-wrap">
                  {money.payment_terms || "—"}
                </div>
              </div>
            </div>
          </CardShell>

          {/* Notary */}
          <CardShell
            title="Notary"
            icon={<Landmark className="h-5 w-5" />}
            badgeIcon={<Gavel className="h-6 w-6 text-neutral-700" />}
          >
            <div className="space-y-4">
              <KV k="Notary" v={notary.name} />
              <KV k="Address" v={notary.address} />

              {/* Decorative seal */}
              {/* Notary seal image */}
<div className="mt-4 grid place-items-center">
  <img
    src={notarySeal}
    alt="Notary seal"
    className="h-32 w-32 rounded-full border border-neutral-300 bg-white shadow-sm"
  />
</div>
            </div>
          </CardShell>
        </div>

        {/* Bottom 2-column blocks */}
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <div className="rounded-3xl border border-neutral-300 bg-neutral-50 p-5 shadow-sm">
            <div className="text-sm font-semibold text-neutral-900">Key Obligations</div>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-neutral-800">
              {(highlights.key_obligations || []).length ? (
                (highlights.key_obligations || []).slice(0, 5).map((x: string, i: number) => (
                  <li key={i}>{x}</li>
                ))
              ) : (
                <li className="text-neutral-500">—</li>
              )}
            </ul>
          </div>

          <div className="rounded-3xl border border-neutral-300 bg-neutral-50 p-5 shadow-sm">
            <div className="text-sm font-semibold text-neutral-900">Special Conditions</div>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-neutral-800">
              {(highlights.special_conditions || []).length ? (
                (highlights.special_conditions || []).slice(0, 5).map((x: string, i: number) => (
                  <li key={i}>{x}</li>
                ))
              ) : (
                <li className="text-neutral-500">—</li>
              )}
            </ul>
          </div>
        </div>

        {/* Traceability drawer */}
        <div className="mt-6 rounded-3xl border border-neutral-300 bg-neutral-50 p-4">
          <button
            onClick={() => setShowTrace((s) => !s)}
            className="flex w-full items-center justify-between gap-2"
          >
            <div className="text-sm font-semibold text-neutral-900">
              Traceability Quotes{" "}
              <span className="text-xs font-normal text-neutral-600">
                ({traceability?.length || 0})
              </span>
            </div>
            {showTrace ? (
              <ChevronUp className="h-5 w-5 text-neutral-700" />
            ) : (
              <ChevronDown className="h-5 w-5 text-neutral-700" />
            )}
          </button>

          {showTrace ? (
            <div className="mt-3 space-y-2">
              {(traceability || []).slice(0, 12).map((t: any, i: number) => (
                <div key={i} className="rounded-2xl border border-neutral-200 bg-white p-3">
                  <div className="text-xs text-neutral-500">Field</div>
                  <div className="text-sm font-semibold text-neutral-900">{t.field || "—"}</div>
                  <div className="mt-2 text-xs text-neutral-500">Quote</div>
                  <div className="text-sm text-neutral-800 whitespace-pre-wrap">
                    {t.source_quote || "—"}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}