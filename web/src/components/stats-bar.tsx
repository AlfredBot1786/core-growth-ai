import { Card } from "@/components/ui/card";
import { TrendingUp, Flame, Sun, Archive, Activity } from "lucide-react";

interface StatsBarProps {
  total: number;
  t1Count: number;
  t2Count: number;
  t3Count: number;
  lastRunAt: string | null;
}

export function StatsBar({
  total,
  t1Count,
  t2Count,
  t3Count,
  lastRunAt,
}: StatsBarProps) {
  const stats = [
    {
      label: "Total Leads",
      value: total,
      icon: TrendingUp,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      label: "Hot (T1)",
      value: t1Count,
      icon: Flame,
      color: "text-red-400",
      bg: "bg-red-500/10",
    },
    {
      label: "Warm (T2)",
      value: t2Count,
      icon: Sun,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      label: "Stored (T3)",
      value: t3Count,
      icon: Archive,
      color: "text-zinc-400",
      bg: "bg-zinc-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map((stat) => (
        <Card key={stat.label} className="flex items-center gap-3 p-4">
          <div
            className={`flex items-center justify-center w-10 h-10 rounded-xl ${stat.bg}`}
          >
            <stat.icon className={`w-5 h-5 ${stat.color}`} />
          </div>
          <div>
            <p className="text-2xl font-bold text-zinc-100">{stat.value}</p>
            <p className="text-xs text-zinc-500">{stat.label}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}
