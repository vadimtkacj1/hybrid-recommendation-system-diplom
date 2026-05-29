import { useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ProfilePhotoPickerProps } from "@/types";

export function ProfilePhotoPicker({ token, onUploaded, children }: ProfilePhotoPickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  const open = () => inputRef.current?.click();

  const onChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    try {
      await api.users.uploadAvatar(token, file);
      onUploaded();
    } catch {
      // silent  could add a toast here
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/*"
        className="sr-only"
        aria-hidden
        onChange={onChange}
      />
      {children(open, busy)}
    </>
  );
}
