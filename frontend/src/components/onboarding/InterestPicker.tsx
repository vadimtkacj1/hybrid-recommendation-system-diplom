import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { CATEGORIES } from "@/constants/interests";
import type { InterestPickerProps } from "@/types";

export function InterestPicker({ onSave, loading, initialCategories }: InterestPickerProps) {
  const [selected, setSelected] = useState<Set<string>>(
    () => new Set(initialCategories ?? [])
  );

  const MAX = 5;

  const toggle = (name: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else if (next.size < MAX) {
        next.add(name);
      }
      return next;
    });
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <p className="text-sm text-stone-500 text-center mb-5 leading-relaxed">
        Choose topics you care about. Pick 1–5.
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-6">
        {CATEGORIES.map(({ name, icon: Icon }) => {
          const active = selected.has(name);
          return (
            <button
              key={name}
              type="button"
              onClick={() => toggle(name)}
              className={[
                "flex items-center gap-2.5 px-3 py-2.5 rounded-xl border text-sm font-medium transition-all",
                active
                  ? "border-amber-500/60 bg-amber-500/10 text-amber-400"
                  : "border-stone-700 bg-stone-900/40 text-stone-400 hover:border-stone-600 hover:text-stone-300",
              ].join(" ")}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="text-left leading-tight">{name}</span>
            </button>
          );
        })}
      </div>

      <Button
        type="button"
        disabled={selected.size < 1 || loading}
        onClick={() => onSave(Array.from(selected))}
        className="w-full bg-amber-500 hover:bg-amber-400 text-stone-950 font-semibold rounded-xl gap-2 disabled:opacity-40"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Saving…
          </>
        ) : (
          <>Continue ({selected.size}/{MAX} selected)</>
        )}
      </Button>
    </div>
  );
}
