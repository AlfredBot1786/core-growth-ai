"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardTitle } from "@/components/ui/card";
import { Bell, User, Users, CheckCircle2 } from "lucide-react";

interface Profile {
  full_name: string;
  email: string;
  notification_prefs: {
    email_t1: boolean;
    email_t2: boolean;
    push_t1: boolean;
  };
}

export default function SettingsPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function fetchProfile() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;

      const { data } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", user.id)
        .single();

      if (data) {
        setProfile({
          full_name: data.full_name || "",
          email: data.email || user.email || "",
          notification_prefs: data.notification_prefs || {
            email_t1: true,
            email_t2: false,
            push_t1: true,
          },
        });
      }
      setLoading(false);
    }

    fetchProfile();
  }, []);

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    setSaved(false);

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) return;

    await supabase
      .from("profiles")
      .update({
        full_name: profile.full_name,
        notification_prefs: profile.notification_prefs,
      })
      .eq("id", user.id);

    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  function togglePref(key: keyof Profile["notification_prefs"]) {
    if (!profile) return;
    setProfile({
      ...profile,
      notification_prefs: {
        ...profile.notification_prefs,
        [key]: !profile.notification_prefs[key],
      },
    });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-zinc-500">
        Loading settings...
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>

      {/* Profile */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <User className="w-4 h-4 text-blue-400" />
          <CardTitle>Profile</CardTitle>
        </div>
        <div className="space-y-4">
          <Input
            id="fullName"
            label="Full name"
            value={profile?.full_name || ""}
            onChange={(e) =>
              setProfile((p) => (p ? { ...p, full_name: e.target.value } : p))
            }
          />
          <Input
            id="email"
            label="Email"
            value={profile?.email || ""}
            disabled
            className="opacity-50"
          />
        </div>
      </Card>

      {/* Notifications */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-4 h-4 text-amber-400" />
          <CardTitle>Notifications</CardTitle>
        </div>
        <div className="space-y-3">
          <ToggleRow
            label="Email alerts for Hot (T1) leads"
            description="Get notified immediately when a high-value lead is detected"
            checked={profile?.notification_prefs.email_t1 ?? true}
            onChange={() => togglePref("email_t1")}
          />
          <ToggleRow
            label="Email alerts for Warm (T2) leads"
            description="Get a daily digest of warm leads"
            checked={profile?.notification_prefs.email_t2 ?? false}
            onChange={() => togglePref("email_t2")}
          />
          <ToggleRow
            label="Push notifications for Hot (T1) leads"
            description="Receive push notifications on your device"
            checked={profile?.notification_prefs.push_t1 ?? true}
            onChange={() => togglePref("push_t1")}
          />
        </div>
      </Card>

      {/* Team */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-4 h-4 text-green-400" />
          <CardTitle>Team</CardTitle>
        </div>
        <p className="text-sm text-zinc-400">
          Team management is coming soon. You&apos;ll be able to invite advisors,
          assign lead territories, and share lead lists.
        </p>
      </Card>

      {/* Save */}
      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save changes"}
        </Button>
        {saved && (
          <span className="flex items-center gap-1.5 text-sm text-green-400 animate-fade-in">
            <CheckCircle2 className="w-4 h-4" />
            Saved
          </span>
        )}
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="text-sm font-medium text-zinc-200">{label}</p>
        <p className="text-xs text-zinc-500">{description}</p>
      </div>
      <button
        onClick={onChange}
        className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
          checked ? "bg-blue-600" : "bg-zinc-700"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}
