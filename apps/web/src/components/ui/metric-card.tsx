import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  hint,
  className,
}: {
  label: string;
  value: string | number;
  hint?: string;
  className?: string;
}) {
  return (
    <Card className={cn("p-4", className)}>
      <CardHeader className="mb-1">
        <CardDescription>{label}</CardDescription>
      </CardHeader>
      <CardTitle className="text-2xl font-semibold tracking-tight">{value}</CardTitle>
      {hint ? <p className="mt-1 text-xs text-[var(--muted-foreground)]">{hint}</p> : null}
    </Card>
  );
}
