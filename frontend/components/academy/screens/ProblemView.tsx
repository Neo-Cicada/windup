import { FREDOKA, MONO } from "../data";

export type Chests = { hint: boolean; approach: boolean; solution: boolean };

type Props = {
  chests: Chests;
  unaided: boolean;
  onUnlock: (key: keyof Chests) => void;
  onSubmit: () => void;
};

const card = {
  background: "#fff",
  border: "4px solid #2E2620",
  borderRadius: 24,
  boxShadow: "0 8px 0 #E0CBA0",
} as const;

type ChestBtnProps = { color: string; lid: string; title: string; sub: string; onClick: () => void };

function LockedChest({ color, lid, title, sub, onClick }: ChestBtnProps) {
  return (
    <button
      className="tap"
      onClick={onClick}
      style={{ display: "flex", alignItems: "center", gap: 13, width: "100%", textAlign: "left", background: "#FCF6E9", border: "3px dashed #C9A96A", borderRadius: 16, padding: 14 }}
    >
      <span style={{ width: 44, height: 36, flex: "none", background: color, border: "3px solid #2E2620", borderRadius: "8px 8px 6px 6px", position: "relative" }}>
        <span style={{ position: "absolute", top: -6, left: 4, right: 4, height: 12, background: lid, border: "3px solid #2E2620", borderRadius: "8px 8px 0 0" }} />
        <span style={{ position: "absolute", top: 9, left: "50%", transform: "translateX(-50%)", width: 8, height: 8, background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%" }} />
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>{title}</div>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#9B7B5B" }}>{sub}</div>
      </div>
      <span style={{ fontSize: 11, fontWeight: 800, color: "#D8443D" }}>−bonus</span>
    </button>
  );
}

export function ProblemView({ chests, unaided, onUnlock, onSubmit }: Props) {
  return (
    <div data-screen-label="Problem View" style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 22, maxWidth: 1180, margin: "0 auto", alignItems: "start" }} className="acad-problem">
      {/* LEFT: problem + workspace */}
      <section style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        <div style={{ ...card, padding: 24 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 18 }}>
            <div style={{ flex: "none", textAlign: "center" }}>
              <div style={{ width: 70, height: 70, background: "#F7C948", border: "4px solid #2E2620", borderRadius: 18, boxShadow: "0 6px 0 #2E2620", position: "relative" }}>
                <span style={{ position: "absolute", inset: 14, border: "3px dashed #2E2620", borderRadius: 10 }} />
              </div>
              <div style={{ marginTop: 9, fontSize: 10, fontWeight: 800, color: "#B0794A" }}>MEDIUM WEIGHT</div>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <span style={{ background: "#EAF6FD", border: "2px solid #4FB0E5", color: "#2C6E9C", fontWeight: 800, fontSize: 11, padding: "3px 10px", borderRadius: 20 }}>MARBLE RUN</span>
                <span style={{ background: "#FDF3D6", border: "2px solid #E0A93C", color: "#A9761F", fontWeight: 800, fontSize: 11, padding: "3px 10px", borderRadius: 20 }}>Medium</span>
              </div>
              <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, margin: "0 0 8px" }}>Reverse Linked List</h1>
              <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.5, color: "#5C4A3C" }}>
                Sprocket&apos;s marble chute got tangled backwards! Given the <b>head</b> of a singly linked marble chute, reverse the run so the last marble drops first. Return the new head.
              </p>
            </div>
          </div>
          <div style={{ marginTop: 18, background: "#2E2620", borderRadius: 14, padding: "16px 18px", fontFamily: MONO, fontSize: 13, color: "#EAF7D9", lineHeight: 1.6 }}>
            <div style={{ color: "#F7C948" }}>Example</div>
            <div>Input:&nbsp;&nbsp;head = [1, 2, 3, 4, 5]</div>
            <div>Output: [5, 4, 3, 2, 1]</div>
          </div>
        </div>

        <div style={{ ...card, padding: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 17, margin: 0 }}>Your Workbench</h2>
            <span style={{ fontSize: 11, fontWeight: 800, color: "#9B7B5B" }}>Python</span>
          </div>
          <div style={{ background: "#FBF4E4", border: "3px solid #2E2620", borderRadius: 14, padding: 16, fontFamily: MONO, fontSize: 13, color: "#5C4A3C", lineHeight: 1.7, minHeight: 130 }}>
            def reverseList(head):<br />
            &nbsp;&nbsp;prev = None<br />
            &nbsp;&nbsp;while head:<br />
            &nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: "#B9A98C" }}>|</span> <span style={{ color: "#B9A98C" }}># your turn, little toy…</span>
          </div>
          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
            <button className="tap" onClick={onSubmit} style={{ border: "3px solid #2E2620", borderRadius: 15, background: "#6FBF73", color: "#173d19", fontWeight: 700, fontSize: 15, padding: "11px 22px", boxShadow: "0 5px 0 #2E2620", fontFamily: FREDOKA }}>
              Run &amp; Submit
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: "#9B7B5B" }}>Unaided bonus:</span>
              <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15, color: unaided ? "#4C7A2F" : "#B9A98C", textDecoration: unaided ? "none" : "line-through" }}>+60 charge</span>
            </div>
          </div>
        </div>
      </section>

      {/* RIGHT: tiered resource panel */}
      <section style={{ ...card, padding: 22 }}>
        <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: "0 0 4px" }}>Help Shelf</h2>
        <p style={{ margin: "0 0 18px", fontSize: 12, color: "#9B7B5B", fontWeight: 700 }}>Open a chest for help — but peeking past the explainer forfeits your unaided bonus.</p>

        {/* Tier 1 always open */}
        <div style={{ background: "#EAF7D9", border: "3px solid #2E2620", borderRadius: 16, padding: 15, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
            <span style={{ width: 24, height: 24, background: "#6FBF73", border: "3px solid #2E2620", borderRadius: 7 }} />
            <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>Tier 1 · Pattern Explainer</span>
            <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 800, color: "#4C7A2F" }}>FREE · OPEN</span>
          </div>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: "#4C5A3C" }}>
            <b>Two-pointer walk.</b> Keep a <i>prev</i> marble and a <i>current</i> marble. Each step, flip current&apos;s arrow to point at prev, then shuffle both forward one slot. When current runs off the end, prev is your new head.
          </p>
        </div>

        {/* Tier 2 hint (revealed) */}
        {chests.hint && (
          <div style={{ background: "#EAF6FD", border: "3px solid #2E2620", borderRadius: 16, padding: 15, marginBottom: 14, animation: "pop .35s ease both" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
              <span style={{ width: 24, height: 24, background: "#4FB0E5", border: "3px solid #2E2620", borderRadius: 7 }} />
              <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>Tier 2 · Hint</span>
              <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 800, color: "#2C6E9C" }}>OPENED</span>
            </div>
            <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: "#2C4A5C" }}>
              You only need <b>one pass</b> and <b>O(1)</b> extra space. Store <code>head.next</code> in a temp before you flip the arrow, or you&apos;ll lose the rest of the chute.
            </p>
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {!chests.hint && (
            <LockedChest color="#4FB0E5" lid="#63BCEC" title="Tier 2 · Hint" sub="A nudge in the right direction" onClick={() => onUnlock("hint")} />
          )}

          {!chests.approach ? (
            <LockedChest color="#E08A3C" lid="#EC9C54" title="Tier 3 · Full Approach" sub="Step-by-step walkthrough" onClick={() => onUnlock("approach")} />
          ) : (
            <div style={{ background: "#FDF3D6", border: "3px solid #2E2620", borderRadius: 16, padding: 15, animation: "pop .35s ease both" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
                <span style={{ width: 24, height: 24, background: "#E08A3C", border: "3px solid #2E2620", borderRadius: 7 }} />
                <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>Tier 3 · Full Approach</span>
              </div>
              <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: "#7A5A2C" }}>
                1) prev = None. 2) While head: save nxt = head.next. 3) head.next = prev. 4) prev = head. 5) head = nxt. 6) Return prev. That&apos;s the whole marble flip — O(n) time, O(1) space.
              </p>
            </div>
          )}

          {!chests.solution ? (
            <LockedChest color="#EF5B54" lid="#F26E68" title="Tier 4 · Full Solution" sub="The complete answer" onClick={() => onUnlock("solution")} />
          ) : (
            <div style={{ background: "#2E2620", borderRadius: 16, padding: 16, animation: "pop .35s ease both", fontFamily: MONO, fontSize: 12.5, color: "#EAF7D9", lineHeight: 1.65 }}>
              <div style={{ color: "#F7C948", fontFamily: FREDOKA, fontWeight: 700, marginBottom: 8 }}>Tier 4 · Full Solution</div>
              def reverseList(head):<br />
              &nbsp;&nbsp;prev = None<br />
              &nbsp;&nbsp;while head:<br />
              &nbsp;&nbsp;&nbsp;&nbsp;nxt = head.next<br />
              &nbsp;&nbsp;&nbsp;&nbsp;head.next = prev<br />
              &nbsp;&nbsp;&nbsp;&nbsp;prev = head<br />
              &nbsp;&nbsp;&nbsp;&nbsp;head = nxt<br />
              &nbsp;&nbsp;return prev
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
