"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Confetti, makeBurst, type ConfettiPiece } from "@/components/Confetti";
import { RequireAuth } from "@/components/RequireAuth";
import { EmptyPanel, ErrorPanel, ScreenState, Winding } from "@/components/ScreenState";
import { Sidebar } from "@/components/academy/Sidebar";
import { Topbar } from "@/components/academy/Topbar";
import { Dashboard } from "@/components/academy/screens/Dashboard";
import { QuestMap } from "@/components/academy/screens/QuestMap";
import { ProblemView } from "@/components/academy/screens/ProblemView";
import { BossBattle } from "@/components/academy/screens/BossBattle";
import { Achievements } from "@/components/academy/screens/Achievements";
import { Analytics } from "@/components/academy/screens/Analytics";
import { Leaderboard } from "@/components/academy/screens/Leaderboard";
import { Profile, type AccountValues } from "@/components/academy/screens/Profile";
import { TITLES, fmtTime, streakColors, type ScreenKey } from "@/components/academy/data";
import { api, errorMessage, patch, post } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/lib/useResource";
import type {
  AchievementsSummary,
  AnalyticsSummary,
  BossAction,
  BossSession,
  ChestTier,
  ChestUnlockResult,
  DashboardData,
  LeaderboardSummary,
  PlanOption,
  Problem,
  ProblemDetail,
  StreakSummary,
  SubmissionResult,
  User,
  Zone,
} from "@/lib/types";

const BOSS_FALLBACK_SECONDS = 900;
const EMPTY_STREAK = Array<number>(36).fill(0);

export default function AcademyPage() {
  return (
    <RequireAuth>
      <Academy />
    </RequireAuth>
  );
}

function Academy() {
  const router = useRouter();
  const { user, setUser, logout } = useAuth();

  const [screen, setScreen] = useState<ScreenKey>("dashboard");
  const [confetti, setConfetti] = useState<ConfettiPiece[]>([]);
  // Sprocket's line: the last thing that actually happened, falling back to the server's.
  const [sprocketSaid, setSprocketSaid] = useState<string | null>(null);

  const confettiTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---- server state -------------------------------------------------------
  const dashboard = useResource<DashboardData>("/dashboard");
  const streak = useResource<StreakSummary>("/analytics/streak");
  const zones = useResource<Zone[]>("/zones", screen === "quests");
  const achievements = useResource<AchievementsSummary>("/achievements", screen === "achievements");
  const analytics = useResource<AnalyticsSummary>("/analytics", screen === "analytics");
  const leaderboard = useResource<LeaderboardSummary>("/leaderboard", screen === "leaderboard");
  const plans = useResource<PlanOption[]>("/plans", screen === "workshop");

  const [openZone, setOpenZone] = useState<string | null>(null);
  const zoneProblems = useResource<Problem[]>(
    `/zones/${openZone ?? ""}/problems`,
    screen === "quests" && openZone !== null
  );

  useEffect(() => {
    return () => {
      if (confettiTimer.current) clearTimeout(confettiTimer.current);
    };
  }, []);

  function burst(n: number) {
    if (n <= 0) return;
    setConfetti(makeBurst(n));
    if (confettiTimer.current) clearTimeout(confettiTimer.current);
    confettiTimer.current = setTimeout(() => setConfetti([]), 2400);
  }

  function go(next: ScreenKey) {
    setScreen(next);
    if (typeof window !== "undefined") window.scrollTo(0, 0);
  }

  // ---- wind-up key --------------------------------------------------------
  const [winding, setWinding] = useState(false);

  async function windUp() {
    setWinding(true);
    try {
      const next = await post<DashboardData>("/me/wind-up");
      dashboard.set(next);
      streak.reload();
      setSprocketSaid("Wound up tight — that's +40 charge on the meter!");
      burst(24);
    } catch (err) {
      setSprocketSaid(errorMessage(err));
    } finally {
      setWinding(false);
    }
  }

  // ---- problem workbench --------------------------------------------------
  const [pickedSlug, setPickedSlug] = useState<string | null>(null);
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [loadError, setLoadError] = useState<{ slug: string; message: string } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [unlocking, setUnlocking] = useState<ChestTier | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [problemNonce, setProblemNonce] = useState(0);

  // Landing on the workbench with nothing picked? Take the first of today's quests.
  const activeSlug = pickedSlug ?? dashboard.data?.quests[0]?.slug ?? null;

  useEffect(() => {
    if (activeSlug === null) return;
    let cancelled = false;
    api<ProblemDetail>(`/problems/${activeSlug}`)
      .then((detail) => {
        if (cancelled) return;
        setProblem(detail);
        setCode(detail.starter_code);
      })
      .catch((err) => {
        if (!cancelled) setLoadError({ slug: activeSlug, message: errorMessage(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [activeSlug, problemNonce]);

  function openProblem(slug: string) {
    setPickedSlug(slug);
    setActionError(null);
    go("problem");
  }

  function reloadProblem() {
    setLoadError(null);
    setProblemNonce((n) => n + 1);
  }

  async function unlockChest(tier: ChestTier) {
    if (problem === null) return;
    setUnlocking(tier);
    setActionError(null);
    try {
      const opened = await post<ChestUnlockResult>(`/problems/${problem.slug}/chests/${tier}`);
      setProblem((p) =>
        p === null
          ? p
          : {
              ...p,
              chests: opened.chests,
              unaided: opened.unaided,
              help_shelf: { ...p.help_shelf, [tier]: opened.content },
            }
      );
      setSprocketSaid(opened.message);
      burst(18);
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setUnlocking(null);
    }
  }

  async function submitProblem() {
    if (problem === null) return;
    setSubmitting(true);
    setActionError(null);
    try {
      const result = await post<SubmissionResult>(`/problems/${problem.slug}/submit`, {
        code,
        language: problem.language,
        status: "passed",
        // Tagging the submission is what lets a boss round actually clear.
        boss_session_id: boss?.status === "running" ? boss.id : null,
      });
      setSprocketSaid(result.sprocket_message);
      burst(result.confetti);
      setProblem((p) => (p === null ? p : { ...p, solved: true }));
      dashboard.reload();
      streak.reload();
      if (boss !== null) refreshBoss();
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  // ---- boss battle --------------------------------------------------------
  const [boss, setBoss] = useState<BossSession | null>(null);
  const [bossReady, setBossReady] = useState(false);
  const [bossPending, setBossPending] = useState(false);
  const [bossError, setBossError] = useState<string | null>(null);
  // Ticked down locally between requests; every server response re-syncs it.
  const [remaining, setRemaining] = useState(BOSS_FALLBACK_SECONDS);

  function adopt(session: BossSession | null) {
    setBoss(session);
    setRemaining(session?.remaining_seconds ?? BOSS_FALLBACK_SECONDS);
  }

  async function refreshBoss() {
    try {
      adopt(await api<BossSession | null>("/boss/current"));
    } catch (err) {
      setBossError(errorMessage(err));
    }
  }

  useEffect(() => {
    if (screen !== "boss") return;
    let cancelled = false;
    api<BossSession | null>("/boss/current")
      .then((session) => {
        if (cancelled) return;
        setBoss(session);
        setRemaining(session?.remaining_seconds ?? BOSS_FALLBACK_SECONDS);
        setBossReady(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setBossError(errorMessage(err));
        setBossReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [screen]);

  // The on-screen countdown is cosmetic. The server computes the real remaining time
  // from when the fight was last resumed, so a refresh or a second tab can't stretch it.
  useEffect(() => {
    if (boss?.status !== "running") return;
    const id = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(id);
  }, [boss?.status]);

  // Out of time on screen: let the server settle the session and tell us the verdict.
  useEffect(() => {
    if (boss?.status !== "running" || remaining > 0) return;
    let cancelled = false;
    api<BossSession | null>("/boss/current")
      .then((session) => {
        if (cancelled) return;
        setBoss(session);
        setRemaining(session?.remaining_seconds ?? 0);
      })
      .catch(() => {
        // The clock already reads zero on screen; a failed poll changes nothing.
      });
    return () => {
      cancelled = true;
    };
  }, [boss?.status, remaining]);

  async function bossAct(action: BossAction) {
    if (boss === null) return;
    setBossPending(true);
    setBossError(null);
    try {
      const next = await post<BossSession>(`/boss/sessions/${boss.id}`, { action });
      adopt(next);
      if (action === "complete" && next.status === "completed") {
        setSprocketSaid(`Boss down! +${next.xp_awarded} charge for beating the clock.`);
        burst(80);
        dashboard.reload();
        streak.reload();
      }
    } catch (err) {
      setBossError(errorMessage(err));
    } finally {
      setBossPending(false);
    }
  }

  async function startBoss() {
    setBossPending(true);
    setBossError(null);
    try {
      adopt(await post<BossSession>("/boss/sessions"));
      setSprocketSaid("The Jack-in-the-Box is winding up. Fix the rounds before it springs!");
    } catch (err) {
      setBossError(errorMessage(err));
    } finally {
      setBossPending(false);
    }
  }

  const bossSpent =
    boss === null || remaining <= 0 || boss.status === "completed" || boss.status === "expired";

  // Derived from the same fields the server labels with, so the button always says what
  // clicking it will do — the server's own label reads "Begin battle" for a fight paused
  // on its first second, which would then resume rather than start.
  const bossLabel = bossSpent
    ? boss === null
      ? "Begin battle"
      : "Rematch"
    : boss.status === "running"
      ? "Pause fight"
      : "Resume fight";

  function toggleBoss() {
    if (bossSpent) return startBoss();
    return bossAct(boss.status === "running" ? "pause" : "resume");
  }

  // ---- account ------------------------------------------------------------
  const [saving, setSaving] = useState(false);
  const [acctFlash, setAcctFlash] = useState<string | null>(null);
  const [acctError, setAcctError] = useState<string | null>(null);

  async function saveAccount(values: AccountValues): Promise<boolean> {
    if (user === null) return false;
    setSaving(true);
    setAcctFlash(null);
    setAcctError(null);
    try {
      const wantsEmail = values.email.trim().toLowerCase() !== user.email;
      const wantsPassword = values.newPassword.length > 0;
      if ((wantsEmail || wantsPassword) && values.currentPassword.length === 0) {
        throw new Error("Pop in your current password to change your email or password.");
      }

      // Display preferences, then credentials — each is its own re-authenticated call.
      let saved = await patch<User>("/me", {
        toy_name: values.toyName.trim(),
        notifications: values.notif,
      });
      if (wantsPassword) {
        await post("/me/password", {
          current_password: values.currentPassword,
          new_password: values.newPassword,
        });
      }
      if (wantsEmail) {
        saved = await post<User>("/me/email", {
          current_password: values.currentPassword,
          new_email: values.email.trim(),
        });
      }

      setUser(saved);
      setAcctFlash("✓ Account saved!");
      dashboard.reload();
      burst(24);
      return true;
    } catch (err) {
      setAcctError(errorMessage(err));
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    setAcctFlash("Winding down… see you soon!");
    await logout();
    router.replace("/");
  }

  // ---- render -------------------------------------------------------------
  const progress = dashboard.data?.progress ?? null;
  const sprocketMsg =
    sprocketSaid ?? dashboard.data?.sprocket_message ?? "Sprocket is oiling the gears…";
  const problemReady = problem !== null && problem.slug === activeSlug;
  const problemFailed = loadError !== null && loadError.slug === activeSlug;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "repeating-linear-gradient(96deg,#E9D2A6 0px,#E9D2A6 46px,#E4CB9C 46px,#E4CB9C 48px)" }} className="acad-shell">
      <Sidebar active={screen} onNavigate={go} sprocketMsg={sprocketMsg} />

      <main style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: "#FCF6E9" }}>
        <Topbar
          title={TITLES[screen]}
          level={progress?.level ?? 1}
          levelName={progress?.level_name ?? "Freshly Unboxed"}
          xp={progress?.xp ?? 0}
          xpMax={progress?.xp_max ?? 500}
          xpPct={progress?.xp_pct ?? 0}
          streak={progress?.streak ?? 0}
          coins={progress?.coins ?? 0}
          streakCells={streakColors(streak.data?.cells ?? EMPTY_STREAK)}
          windAvailable={dashboard.data?.wind_up_available ?? false}
          winding={winding}
          onWind={windUp}
        />

        <div style={{ padding: "26px 30px 60px", flex: 1 }}>
          {screen === "dashboard" &&
            (dashboard.data === null ? (
              <ScreenState loading={dashboard.loading} error={dashboard.error} onRetry={dashboard.reload} label="Opening the playroom…" />
            ) : (
              <Dashboard
                toyName={dashboard.data.toy_name}
                traineeNo={dashboard.data.trainee_no}
                avBody={dashboard.data.avatar_body}
                avHead={dashboard.data.avatar_head}
                avAccent={dashboard.data.avatar_accent}
                ready={dashboard.data.progress.interview_ready}
                level={dashboard.data.progress.level}
                solved={dashboard.data.progress.solved_count}
                unaidedRate={dashboard.data.progress.unaided_rate}
                badgesLabel={dashboard.data.badges_label}
                rank={dashboard.data.rank}
                sprocketMessage={dashboard.data.sprocket_message}
                quests={dashboard.data.quests}
                questsDone={dashboard.data.quests_done}
                onOpenProblem={openProblem}
              />
            ))}

          {screen === "quests" &&
            (zones.data === null ? (
              <ScreenState loading={zones.loading} error={zones.error} onRetry={zones.reload} label="Unrolling the map…" />
            ) : (
              <QuestMap
                zones={zones.data}
                openZone={openZone}
                problems={zoneProblems.data ?? []}
                problemsLoading={zoneProblems.loading}
                problemsError={zoneProblems.error}
                onSelectZone={(slug) => setOpenZone((current) => (current === slug ? null : slug))}
                onOpenProblem={openProblem}
              />
            ))}

          {screen === "problem" &&
            (problemReady && problem !== null ? (
              <ProblemView
                problem={problem}
                code={code}
                onCodeChange={setCode}
                unlocking={unlocking}
                submitting={submitting}
                error={actionError}
                onUnlock={unlockChest}
                onSubmit={submitProblem}
              />
            ) : problemFailed && loadError !== null ? (
              <ErrorPanel message={loadError.message} onRetry={reloadProblem} />
            ) : activeSlug !== null || dashboard.loading ? (
              <Winding label="Fetching the toy…" />
            ) : (
              <EmptyPanel
                title="An empty workbench"
                message="Nothing is clamped in the vice yet. Pick a toy corner and choose something to fix."
                actionLabel="Open the Quest Map"
                onAction={() => go("quests")}
              />
            ))}

          {screen === "boss" &&
            (!bossReady ? (
              <Winding label="Waking the boss…" />
            ) : (
              <BossBattle
                session={boss}
                timeFmt={fmtTime(remaining)}
                pct={boss === null ? 100 : Math.round((remaining / boss.total_seconds) * 100)}
                running={boss?.status === "running"}
                label={bossLabel}
                pending={bossPending}
                error={bossError}
                onToggle={toggleBoss}
                onComplete={() => bossAct("complete")}
                onAbandon={() => bossAct("abandon")}
              />
            ))}

          {screen === "achievements" &&
            (achievements.data === null ? (
              <ScreenState loading={achievements.loading} error={achievements.error} onRetry={achievements.reload} label="Polishing badges…" />
            ) : (
              <Achievements toyName={user?.toy_name ?? "Your"} data={achievements.data} />
            ))}

          {screen === "analytics" &&
            (analytics.data === null ? (
              <ScreenState loading={analytics.loading} error={analytics.error} onRetry={analytics.reload} label="Counting the charge…" />
            ) : (
              <Analytics data={analytics.data} />
            ))}

          {screen === "leaderboard" &&
            (leaderboard.data === null ? (
              <ScreenState loading={leaderboard.loading} error={leaderboard.error} onRetry={leaderboard.reload} label="Dusting the shelf…" />
            ) : (
              <Leaderboard data={leaderboard.data} />
            ))}

          {screen === "workshop" &&
            (user === null ? (
              <Winding label="Finding your toy…" />
            ) : (
              <Profile
                user={user}
                plans={plans.data ?? []}
                saving={saving}
                flash={acctFlash}
                error={acctError}
                onSave={saveAccount}
                onLogout={handleLogout}
                onEdit={() => {
                  setAcctFlash(null);
                  setAcctError(null);
                }}
              />
            ))}
        </div>
      </main>

      <Confetti pieces={confetti} />
    </div>
  );
}
