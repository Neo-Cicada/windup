"use client";

import { useState, type CSSProperties } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV, FREDOKA, isNavActive } from "./data";

type Props = {
  sprocketMsg: string;
};

/**
 * The academy's nav. A column down the left on a desk; a bar across the top of a phone.
 *
 * Which one you get is decided in CSS (`globals.css`, the `.acad-sidebar` block) rather
 * than by measuring the window, so the first paint is already right and there's nothing
 * to mismatch on hydration. `open` only means anything in the narrow layout, where the
 * links are a drawer under the brand — from the breakpoint up they're always shown.
 */
export function Sidebar({ sprocketMsg }: Props) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <aside
      className="acad-sidebar"
      style={{
        width: 246,
        flex: "none",
        position: "sticky",
        top: 0,
        alignSelf: "flex-start",
        height: "100vh",
        background: "#FBF4E4",
        borderRight: "4px solid #2E2620",
        display: "flex",
        flexDirection: "column",
        padding: "22px 16px",
        gap: 6,
        boxShadow: "6px 0 0 rgba(46,38,32,.06)",
        zIndex: 60,
      }}
    >
      {/* brand */}
      <div className="acad-brand" style={{ display: "flex", alignItems: "center", gap: 11, padding: "2px 6px 18px" }}>
        <div style={{ width: 44, height: 44, flex: "none", background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 13, position: "relative", boxShadow: "0 4px 0 #2E2620" }}>
          <div style={{ position: "absolute", inset: 8, border: "3px solid #FBE7C6", borderRadius: 7 }} />
          <div style={{ position: "absolute", top: "50%", left: "50%", width: 10, height: 10, transform: "translate(-50%,-50%)", background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%" }} />
        </div>
        <div style={{ lineHeight: 1 }}>
          <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 16, letterSpacing: ".3px" }}>WINDUP</div>
          <div style={{ fontFamily: FREDOKA, fontWeight: 500, fontSize: 11, letterSpacing: 3, color: "#B0794A" }}>ACADEMY</div>
        </div>

        {/* Hidden by CSS in the wide layout, where the drawer it opens is always open. */}
        <button
          type="button"
          className="acad-nav-toggle tap"
          aria-expanded={open}
          aria-controls="acad-nav"
          aria-label={open ? "Close the toy box" : "Open the toy box"}
          onClick={() => setOpen(!open)}
          style={{
            marginLeft: "auto",
            alignItems: "center",
            gap: 9,
            background: open ? "#FDECEC" : "#fff",
            border: "3px solid #2E2620",
            borderRadius: 14,
            boxShadow: "0 4px 0 #2E2620",
            padding: "8px 13px",
            fontFamily: FREDOKA,
            fontWeight: 700,
            fontSize: 13.5,
            color: "#2E2620",
            cursor: "pointer",
          }}
        >
          <span aria-hidden style={{ display: "flex", flexDirection: "column", gap: 3, width: 16 }}>
            <span style={{ height: 3, borderRadius: 2, background: "#2E2620" }} />
            <span style={{ height: 3, borderRadius: 2, background: "#EF5B54" }} />
            <span style={{ height: 3, borderRadius: 2, background: "#2E2620" }} />
          </span>
          {open ? "Close" : "Menu"}
        </button>
      </div>

      {/* nav */}
      <nav
        id="acad-nav"
        className="acad-nav"
        data-open={open}
        style={{ display: "flex", flexDirection: "column", gap: 6 }}
      >
        {NAV.map((n) => {
          const isActive = isNavActive(pathname, n.href);
          // Anchors don't inherit colour or lose their underline, and they're inline by
          // default — the rest of this matches the button these used to be.
          const linkStyle: CSSProperties = {
            display: "flex",
            alignItems: "center",
            gap: 11,
            width: "100%",
            textAlign: "left",
            padding: "9px 11px",
            borderRadius: 14,
            cursor: "pointer",
            transition: ".12s",
            color: "inherit",
            textDecoration: "none",
            background: isActive ? "#FDECEC" : "transparent",
            border: isActive ? "3px solid #2E2620" : "3px solid transparent",
            boxShadow: isActive ? "0 4px 0 #2E2620" : "none",
          };
          return (
            // Tapping a link is also how the narrow drawer closes — the layout doesn't
            // unmount on navigation, so nothing else would put it away.
            <Link key={n.href} href={n.href} className="tap" style={linkStyle} onClick={() => setOpen(false)}>
              <span style={{ width: 24, height: 24, flex: "none", borderRadius: 8, border: "3px solid #2E2620", background: n.color, opacity: isActive ? 1 : 0.9 }} />
              <span style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", lineHeight: 1.15 }}>
                <span style={{ fontFamily: FREDOKA, fontWeight: 600, fontSize: 14.5 }}>{n.label}</span>
                <span style={{ fontSize: 10.5, color: "#9B7B5B", fontWeight: 700 }}>{n.sub}</span>
              </span>
            </Link>
          );
        })}
      </nav>

      {/* sprocket says */}
      <div className="acad-sprocket" style={{ marginTop: "auto", background: "#F2E6CC", border: "3px dashed #C9A96A", borderRadius: 16, padding: "12px 13px" }}>
        <div style={{ fontFamily: FREDOKA, fontWeight: 600, fontSize: 12, color: "#B0794A", marginBottom: 6 }}>SPROCKET SAYS</div>
        <div style={{ fontSize: 12, lineHeight: 1.4, color: "#5C4A3C" }}>{sprocketMsg}</div>
      </div>
    </aside>
  );
}
