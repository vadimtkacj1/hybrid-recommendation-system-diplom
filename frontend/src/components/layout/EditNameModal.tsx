import { Button } from "@/components/ui/button";

interface EditNameModalProps {
  value: string;
  busy: boolean;
  onChange: (v: string) => void;
  onSave: () => void;
  onClose: () => void;
}

export function EditNameModal({ value, busy, onChange, onSave, onClose }: EditNameModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-stone-900 border border-stone-700 rounded-2xl p-5 w-72 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-sm font-semibold text-stone-100 mb-3">Edit profile name</p>
        <input
          autoFocus
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSave();
            if (e.key === "Escape") onClose();
          }}
          maxLength={80}
          className="w-full bg-stone-800 border border-stone-700 rounded-xl px-3 py-2 text-sm text-stone-100 outline-none focus:border-stone-500 mb-3"
        />
        <div className="flex gap-2 justify-end">
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="text-stone-400 text-xs h-8"
          >
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={onSave}
            disabled={busy || !value.trim()}
            className="bg-amber-500 hover:bg-amber-400 text-stone-950 font-semibold text-xs h-8"
          >
            {busy ? "Saving..." : "Save"}
          </Button>
        </div>
      </div>
    </div>
  );
}
