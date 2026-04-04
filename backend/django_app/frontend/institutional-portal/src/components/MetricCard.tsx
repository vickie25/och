import clsx from "clsx";
import type { ForwardRefExoticComponent, SVGProps } from "react";

type Icon = ForwardRefExoticComponent<
  Omit<SVGProps<SVGSVGElement>, "ref"> & { title?: string; titleId?: string }
>;

const colorMap = {
  primary: "bg-primary-50 text-primary-800 border-primary-200",
  success: "bg-success-50 text-success-800 border-success-200",
  warning: "bg-warning-50 text-warning-800 border-warning-200",
  danger: "bg-danger-50 text-danger-800 border-danger-200",
};

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: Icon;
  color: keyof typeof colorMap;
  trend?: "up" | "down";
}) {
  return (
    <div
      className={clsx(
        "rounded-lg border p-6 shadow-sm bg-white",
        colorMap[color]
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium opacity-90">{title}</p>
          <p className="mt-1 text-2xl font-semibold">{value}</p>
          <p className="mt-1 text-sm opacity-80">{subtitle}</p>
        </div>
        <Icon className="h-10 w-10 shrink-0 opacity-90" aria-hidden />
      </div>
      {trend ? (
        <p className="mt-2 text-xs uppercase tracking-wide opacity-70">
          {trend === "up" ? "Trending up" : "Trending down"}
        </p>
      ) : null}
    </div>
  );
}
