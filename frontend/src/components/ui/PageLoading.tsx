import { Skeleton } from "./Skeleton";

export function PageLoading() {
  return (
    <div className="flex flex-col gap-6 w-full animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-32 rounded-full" />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full rounded-xl" />
        ))}
      </div>
      
      <div className="space-y-4">
        <Skeleton className="h-6 w-1/4" />
        <div className="rounded-xl border border-border overflow-hidden">
          <div className="p-4 border-b border-border bg-neutral/30">
            <Skeleton className="h-4 w-full" />
          </div>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-4 border-b border-border last:border-0">
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}