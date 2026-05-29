import { ArrowRight } from "lucide-react";
import type { MethodCardProps } from "@/types";

export function MethodCard({ icon: Icon, title, description, onClick }: MethodCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group w-full flex items-center gap-4 rounded-xl border border-stone-800 bg-stone-900/50 px-5 py-4 text-left transition-all hover:border-stone-700 hover:bg-stone-900"
    >
      <div className="shrink-0 w-10 h-10 rounded-lg bg-stone-800 border border-stone-700/60 flex items-center justify-center transition-all group-hover:bg-amber-500/10 group-hover:border-amber-500/25">
        <Icon className="h-5 w-5 text-stone-400 transition-colors group-hover:text-amber-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-stone-200 mb-0.5 transition-colors group-hover:text-white">
          {title}
        </p>
        <p className="text-xs text-stone-500 leading-relaxed">{description}</p>
      </div>
      <ArrowRight className="shrink-0 h-4 w-4 text-stone-600 transition-colors group-hover:text-stone-400" />
    </button>
  );
}
