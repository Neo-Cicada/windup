import { FREDOKA } from "../data";
import type { DuelInvite as Invite } from "@/lib/types";

type Props = {
  invite: Invite;
  pending: boolean;
  error: string | null;
  onAccept: () => void;
  onBack: () => void;
};

/** The card an invite link lands on. It never shows the problems — it can't: the
 *  server's preview payload has nowhere to put them. */
export function DuelInvite({ invite, pending, error, onAccept, onBack }: Props) {
  const minutes = Math.round(invite.total_seconds / 60);

  return (
    <div data-screen-label="Duel" style={{ maxWidth: 560, margin: "0 auto" }}>
      <div style={{ background: "#FBF4E4", border: "4px solid #2E2620", borderRadius: 22, padding: 30, boxShadow: "0 8px 0 #2E2620", textAlign: "center" }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A", letterSpacing: 2 }}>
          A CHALLENGE
        </div>

        <div style={{ width: 66, height: 66, margin: "16px auto 12px", borderRadius: 20, background: invite.host_avatar, border: "4px solid #2E2620", boxShadow: "0 5px 0 #2E2620" }} />

        <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, margin: "0 0 6px", color: "#2E2620" }}>
          {invite.message}
        </h1>
        <p style={{ margin: "0 0 22px", color: "#7A6A57", fontSize: 13, fontWeight: 700, lineHeight: 1.5 }}>
          {invite.rounds_total} problems · {minutes} minutes · first to fix them all wins.
          Neither of you sees which problems until you accept.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
          <button
            className="tap"
            onClick={onAccept}
            disabled={pending || !invite.joinable}
            style={{ border: "4px solid #2E2620", borderRadius: 18, background: invite.joinable ? "#E0566B" : "#C9B79A", color: "#fff", fontWeight: 700, fontSize: 17, padding: "13px 32px", boxShadow: "0 5px 0 #A93a4b", fontFamily: FREDOKA, opacity: pending || !invite.joinable ? 0.65 : 1 }}
          >
            {pending ? "Winding…" : "Accept the duel"}
          </button>
          <button
            className="tap"
            onClick={onBack}
            style={{ border: "4px solid #C9B79A", borderRadius: 18, background: "transparent", color: "#7A6A57", fontWeight: 700, fontSize: 16, padding: "13px 22px", fontFamily: FREDOKA }}
          >
            Not now
          </button>
        </div>

        {error && (
          <div role="alert" style={{ margin: "20px auto 0", maxWidth: 460, background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 14, padding: "11px 14px", fontSize: 13, fontWeight: 700, color: "#B4342D" }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
