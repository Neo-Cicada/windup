import { FREDOKA } from "./academy/data";

const panel = {
  background: "#fff",
  border: "4px solid #2E2620",
  borderRadius: 24,
  boxShadow: "0 8px 0 #E0CBA0",
  padding: "34px 28px",
  maxWidth: 520,
  margin: "40px auto",
  textAlign: "center",
} as const;

/** The wind-up key, spinning while we wait. */
export function Winding({ label = "Winding up…" }: { label?: string }) {
  return (
    <div style={panel}>
      <div
        style={{
          width: 44,
          height: 44,
          margin: "0 auto 14px",
          border: "4px solid #2E2620",
          borderRadius: "50%",
          background: "#F7C948",
          position: "relative",
          animation: "spin 1.4s linear infinite",
        }}
      >
        <span style={{ position: "absolute", top: -7, left: "50%", width: 8, height: 15, transform: "translateX(-50%)", background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 4 }} />
        <span style={{ position: "absolute", bottom: -7, left: "50%", width: 8, height: 15, transform: "translateX(-50%)", background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 4 }} />
      </div>
      <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 17 }}>{label}</div>
    </div>
  );
}

export function ErrorPanel({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div style={panel}>
      <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, marginBottom: 8 }}>
        The gears slipped
      </div>
      <p style={{ margin: "0 0 18px", fontSize: 14, fontWeight: 700, color: "#8B7358", lineHeight: 1.5 }}>
        {message}
      </p>
      {onRetry && (
        <button
          className="tap"
          onClick={onRetry}
          style={{ border: "3px solid #2E2620", borderRadius: 15, background: "#6FBF73", color: "#173d19", fontWeight: 700, fontSize: 15, padding: "11px 22px", boxShadow: "0 5px 0 #2E2620", fontFamily: FREDOKA }}
        >
          Try again
        </button>
      )}
    </div>
  );
}

type EmptyProps = {
  title: string;
  message: string;
  actionLabel: string;
  onAction: () => void;
};

/** Nothing to show yet, with a way out that says where it goes. */
export function EmptyPanel({ title, message, actionLabel, onAction }: EmptyProps) {
  return (
    <div style={panel}>
      <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, marginBottom: 8 }}>{title}</div>
      <p style={{ margin: "0 0 18px", fontSize: 14, fontWeight: 700, color: "#8B7358", lineHeight: 1.5 }}>
        {message}
      </p>
      <button
        className="tap"
        onClick={onAction}
        style={{ border: "3px solid #2E2620", borderRadius: 15, background: "#4FB0E5", color: "#fff", fontWeight: 700, fontSize: 15, padding: "11px 22px", boxShadow: "0 5px 0 #2E2620", fontFamily: FREDOKA }}
      >
        {actionLabel}
      </button>
    </div>
  );
}

type Props = {
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
  label?: string;
};

/** Renders the loading / error state for a screen, or null once data has arrived. */
export function ScreenState({ loading, error, onRetry, label }: Props) {
  if (error) return <ErrorPanel message={error} onRetry={onRetry} />;
  if (loading) return <Winding label={label} />;
  return null;
}
