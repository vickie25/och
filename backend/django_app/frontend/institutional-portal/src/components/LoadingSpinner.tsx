import clsx from "clsx";

export default function LoadingSpinner({
  size = "md",
  className,
}: {
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const dim =
    size === "sm" ? "h-4 w-4" : size === "lg" ? "h-12 w-12" : "h-8 w-8";
  return (
    <div
      className={clsx(
        "animate-spin rounded-full border-2 border-primary-500 border-t-transparent",
        dim,
        className
      )}
      role="status"
      aria-label="Loading"
    />
  );
}
