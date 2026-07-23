import Link from "next/link";

const FREDOKA = "var(--font-fredoka), system-ui, sans-serif";

// Placeholder for the post-auth destination. The full academy is a separate
// design file (Toybox Academy.dc.html) and out of scope for this landing build.
export default function AcademyPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 20,
        padding: 40,
        textAlign: "center",
        background:
          "radial-gradient(circle at 80% -5%,#FBEBD0,transparent 45%),radial-gradient(circle at 5% 20%,#F7E0C4,transparent 40%),#F3E3C3",
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          background: "#EF5B54",
          border: "4px solid #2E2620",
          borderRadius: 18,
          boxShadow: "0 6px 0 #2E2620",
          animation: "wob 2.4s ease-in-out infinite",
        }}
      />
      <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 40, margin: 0 }}>
        Welcome to the academy!
      </h1>
      <p style={{ fontSize: 16, fontWeight: 700, color: "#8B7358", maxWidth: 420, margin: 0 }}>
        Your toy is wound up and ready. The playroom is still being unboxed — this
        is where the training shelves will live.
      </p>
      <Link
        href="/"
        className="pushbtn"
        style={{
          border: "4px solid #2E2620",
          borderRadius: 16,
          background: "#6FBF73",
          color: "#173d19",
          fontWeight: 700,
          fontSize: 17,
          padding: "14px 28px",
          fontFamily: FREDOKA,
          // pushbtn CSS vars
          ["--sy" as string]: "6px",
          ["--sc" as string]: "#2E2620",
          ["--psy" as string]: "2px",
          ["--pt" as string]: "4px",
        }}
      >
        ← Back to the toybox
      </Link>
    </main>
  );
}
