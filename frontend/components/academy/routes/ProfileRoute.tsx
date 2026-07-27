"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Winding } from "@/components/ScreenState";
import { Profile, type AccountValues } from "@/components/academy/screens/Profile";
import { useAcademy } from "@/components/academy/AcademyProvider";
import { errorMessage, patch, post } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { User } from "@/lib/types";

export function ProfileRoute() {
  const router = useRouter();
  const { user, setUser, logout } = useAuth();
  const { dashboard, burst } = useAcademy();

  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function saveAccount(values: AccountValues): Promise<boolean> {
    if (user === null) return false;
    setSaving(true);
    setFlash(null);
    setError(null);
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
      setFlash("✓ Account saved!");
      dashboard.reload();
      burst(24);
      return true;
    } catch (err) {
      setError(errorMessage(err));
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    setFlash("Winding down… see you soon!");
    await logout();
    router.replace("/");
  }

  if (user === null) return <Winding label="Finding your toy…" />;

  return (
    <Profile
      user={user}
      saving={saving}
      flash={flash}
      error={error}
      onSave={saveAccount}
      onLogout={handleLogout}
      onEdit={() => {
        setFlash(null);
        setError(null);
      }}
    />
  );
}
