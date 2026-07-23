"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Confetti, makeBurst, type ConfettiPiece } from "@/components/Confetti";
import { Sidebar } from "@/components/academy/Sidebar";
import { Topbar } from "@/components/academy/Topbar";
import { Dashboard } from "@/components/academy/screens/Dashboard";
import { QuestMap } from "@/components/academy/screens/QuestMap";
import { ProblemView, type Chests } from "@/components/academy/screens/ProblemView";
import { BossBattle } from "@/components/academy/screens/BossBattle";
import { Achievements } from "@/components/academy/screens/Achievements";
import { Analytics } from "@/components/academy/screens/Analytics";
import { Leaderboard } from "@/components/academy/screens/Leaderboard";
import { Profile } from "@/components/academy/screens/Profile";
import {
  TITLES,
  levelName,
  fmtTime,
  buildStreakCells,
  type ScreenKey,
  type NotifKey,
} from "@/components/academy/data";

const READY = 62;
const BOSS_TOTAL = 900;

export default function AcademyPage() {
  const router = useRouter();

  const [screen, setScreen] = useState<ScreenKey>("dashboard");
  const [xp, setXp] = useState(340);
  const [xpMax, setXpMax] = useState(500);
  const [level, setLevel] = useState(3);
  const [streak] = useState(12);
  const [coins, setCoins] = useState(1280);
  const [solved] = useState(87);
  const [sprocketMsg, setSprocketMsg] = useState(
    "You showed up today — that's the hardest part. Let's fix some toys!"
  );
  const [confetti, setConfetti] = useState<ConfettiPiece[]>([]);
  const [chests, setChests] = useState<Chests>({ hint: false, approach: false, solution: false });
  const [unaided, setUnaided] = useState(true);
  const [bossTime, setBossTime] = useState(BOSS_TOTAL);
  const [bossRunning, setBossRunning] = useState(false);

  const [toyName] = useState("Bramble");
  const avBody = "#6FBF73";
  const avHead = "#F7C948";
  const avAccent = "#EF5B54";

  const [acctEmail, setAcctEmail] = useState("bramble@playroom.com");
  const [acctPass, setAcctPass] = useState("windup123");
  const [plan, setPlan] = useState("pro");
  const [notif, setNotif] = useState<Record<NotifKey, boolean>>({ streak: true, weekly: true, bosses: false });
  const [acctFlash, setAcctFlash] = useState(false);
  const [acctFlashMsg, setAcctFlashMsg] = useState("");

  const confettiTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bossTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const acctTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const streakCells = useMemo(() => buildStreakCells(), []);

  useEffect(() => {
    return () => {
      if (confettiTimer.current) clearTimeout(confettiTimer.current);
      if (bossTimer.current) clearInterval(bossTimer.current);
      if (acctTimer.current) clearTimeout(acctTimer.current);
    };
  }, []);

  function go(next: ScreenKey) {
    setScreen(next);
    if (typeof window !== "undefined") window.scrollTo(0, 0);
  }

  function burst(n: number) {
    setConfetti(makeBurst(n));
    if (confettiTimer.current) clearTimeout(confettiTimer.current);
    confettiTimer.current = setTimeout(() => setConfetti([]), 2400);
  }

  function gainXp(amount: number, why?: string) {
    let nextXp = xp + amount;
    let nextLevel = level;
    let nextMax = xpMax;
    let leveled = false;
    while (nextXp >= nextMax) {
      nextXp -= nextMax;
      nextLevel++;
      nextMax = Math.round((nextMax * 1.12) / 10) * 10;
      leveled = true;
    }
    setXp(nextXp);
    setLevel(nextLevel);
    setXpMax(nextMax);
    setCoins((c) => c + Math.round(amount / 4));
    setSprocketMsg(
      leveled
        ? `LEVEL UP! You climbed onto the ${levelName(nextLevel)} shelf. Whirr-whirr-hooray!`
        : why || "Ka-ching! That's some fresh charge. Keep winding!"
    );
    burst(leveled ? 80 : 34);
  }

  function unlockChest(key: keyof Chests) {
    if (chests[key]) return;
    const labels: Record<keyof Chests, string> = { hint: "Hint", approach: "Approach", solution: "Solution" };
    setChests((c) => ({ ...c, [key]: true }));
    setUnaided(false);
    setSprocketMsg(`Opened the ${labels[key]} chest — no shame in a peek! You forfeit the unaided bonus this time.`);
    burst(18);
  }

  function submitProblem() {
    gainXp(
      unaided ? 120 : 60,
      unaided
        ? "Solved UNAIDED — full bonus! You clever little toy."
        : "Solved with help — still counts! +60 charge."
    );
  }

  function toggleBoss() {
    if (bossRunning) {
      if (bossTimer.current) clearInterval(bossTimer.current);
      setBossRunning(false);
      return;
    }
    if (bossTime <= 0) setBossTime(BOSS_TOTAL);
    setBossRunning(true);
    bossTimer.current = setInterval(() => {
      setBossTime((t) => {
        if (t <= 1) {
          if (bossTimer.current) clearInterval(bossTimer.current);
          setBossRunning(false);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
  }

  function saveAccount() {
    setAcctFlash(true);
    setAcctFlashMsg("✓ Account saved!");
    burst(24);
    if (acctTimer.current) clearTimeout(acctTimer.current);
    acctTimer.current = setTimeout(() => setAcctFlash(false), 2600);
  }

  function logout() {
    setAcctFlash(true);
    setAcctFlashMsg("Winding down… see you soon!");
    if (acctTimer.current) clearTimeout(acctTimer.current);
    acctTimer.current = setTimeout(() => router.push("/"), 800);
  }

  const bossLabel = bossRunning ? "Pause fight" : bossTime <= 0 ? "Rematch" : "Begin battle";
  const xpPct = Math.min(100, Math.round((xp / xpMax) * 100));

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "repeating-linear-gradient(96deg,#E9D2A6 0px,#E9D2A6 46px,#E4CB9C 46px,#E4CB9C 48px)" }} className="acad-shell">
      <Sidebar active={screen} onNavigate={go} sprocketMsg={sprocketMsg} />

      <main style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: "#FCF6E9" }}>
        <Topbar
          title={TITLES[screen]}
          level={level}
          levelName={levelName(level)}
          xp={xp}
          xpMax={xpMax}
          xpPct={xpPct}
          streak={streak}
          coins={coins}
          streakCells={streakCells}
          onWind={() => gainXp(40)}
        />

        <div style={{ padding: "26px 30px 60px", flex: 1 }}>
          {screen === "dashboard" && (
            <Dashboard
              toyName={toyName}
              avBody={avBody}
              avHead={avHead}
              avAccent={avAccent}
              ready={READY}
              level={level}
              solved={solved}
              unaidedRate={74}
              badgesLabel="14/32"
              rank={6}
              onOpenProblem={() => go("problem")}
            />
          )}
          {screen === "quests" && <QuestMap onOpenProblem={() => go("problem")} />}
          {screen === "problem" && (
            <ProblemView chests={chests} unaided={unaided} onUnlock={unlockChest} onSubmit={submitProblem} />
          )}
          {screen === "boss" && (
            <BossBattle
              timeFmt={fmtTime(bossTime)}
              pct={Math.round((bossTime / BOSS_TOTAL) * 100)}
              running={bossRunning}
              label={bossLabel}
              onToggle={toggleBoss}
            />
          )}
          {screen === "achievements" && <Achievements />}
          {screen === "analytics" && <Analytics />}
          {screen === "leaderboard" && <Leaderboard />}
          {screen === "workshop" && (
            <Profile
              toyName={toyName}
              avHead={avHead}
              email={acctEmail}
              pass={acctPass}
              plan={plan}
              notif={notif}
              flash={acctFlash}
              flashMsg={acctFlashMsg}
              onSetEmail={(v) => { setAcctEmail(v); setAcctFlash(false); }}
              onSetPass={(v) => { setAcctPass(v); setAcctFlash(false); }}
              onPickPlan={(k) => { setPlan(k); setAcctFlash(false); }}
              onFlipToggle={(k) => { setNotif((s) => ({ ...s, [k]: !s[k] })); setAcctFlash(false); }}
              onSave={saveAccount}
              onLogout={logout}
            />
          )}
        </div>
      </main>

      <Confetti pieces={confetti} />
    </div>
  );
}
