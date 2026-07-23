"use client";

import type { CSSProperties, ReactNode } from "react";

type PushStyle = Omit<CSSProperties, "boxShadow"> & {
  /** Rest drop-shadow depth in px (default 4). Press depth is derived from it. */
  boxShadowY?: number;
  /** Border width in px (default 3). */
  borderWidth?: number;
};

type Props = {
  children: ReactNode;
  onClick?: () => void;
  bg: string;
  color: string;
  /** Drop-shadow / border color. */
  shadow: string;
  style?: PushStyle;
  type?: "button" | "submit";
};

export function PushButton({
  children,
  onClick,
  bg,
  color,
  shadow,
  style = {},
  type = "button",
}: Props) {
  const { boxShadowY = 4, borderWidth = 3, ...rest } = style;
  const pressShadowY = (boxShadowY - 2) / 2;
  const pressTranslate = boxShadowY - pressShadowY;

  const cssVars = {
    "--sy": `${boxShadowY}px`,
    "--sc": shadow,
    "--psy": `${pressShadowY}px`,
    "--pt": `${pressTranslate}px`,
  } as CSSProperties;

  return (
    <button
      type={type}
      onClick={onClick}
      className="pushbtn"
      style={{
        border: `${borderWidth}px solid #2E2620`,
        borderRadius: 13,
        background: bg,
        color,
        fontWeight: 700,
        fontSize: 14,
        padding: "9px 18px",
        ...cssVars,
        ...rest,
      }}
    >
      {children}
    </button>
  );
}
