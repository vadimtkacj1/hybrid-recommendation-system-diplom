import { useState } from "react";
import { Link } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { EditNameModal } from "./EditNameModal";
import { ProfilePhotoPicker } from "@/components/profile/ProfilePhotoPicker";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { resolvePictureUrl } from "@/lib/media";
import { ImagePlus, LogOut, Pencil } from "lucide-react";

export function AppHeader() {
  const { user, token, logout, refreshUser } = useAuth();
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [nameBusy, setNameBusy] = useState(false);

  const openNameEdit = () => {
    setNameInput(user?.name ?? "");
    setEditingName(true);
  };

  const saveName = async () => {
    if (!token || !nameInput.trim()) return;
    setNameBusy(true);
    try {
      await api.users.updateProfile(token, nameInput.trim());
      await refreshUser();
      setEditingName(false);
    } finally {
      setNameBusy(false);
    }
  };

  return (
    <header className="border-b border-stone-800/50 sticky top-0 z-10 bg-stone-950/95 backdrop-blur-md">
      {editingName && (
        <EditNameModal
          value={nameInput}
          busy={nameBusy}
          onChange={setNameInput}
          onSave={saveName}
          onClose={() => setEditingName(false)}
        />
      )}

      <div className="flex justify-between items-center px-5 py-3 md:px-10 max-w-5xl mx-auto">
        <Link to="/" className="font-semibold tracking-tight text-stone-100 hover:text-amber-400 transition-colors">LikeMind</Link>

        {!user ? null : user && token ? (
          <ProfilePhotoPicker token={token} onUploaded={refreshUser}>
            {(openPhoto, photoBusy) => (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-stone-800/60 transition-colors">
                    <Avatar className="h-7 w-7 border border-stone-700/60">
                      <AvatarImage src={resolvePictureUrl(user.picture)} alt="" />
                      <AvatarFallback className="bg-stone-800 text-stone-300 text-xs">
                        {user.name?.[0] ?? "?"}
                      </AvatarFallback>
                    </Avatar>
                    <span className="text-sm text-stone-400 hidden sm:block pr-1">
                      {user.name?.split(" ")[0] ?? user.email}
                    </span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 border-stone-800 bg-stone-900">
                  <DropdownMenuItem
                    onSelect={(e) => { e.preventDefault(); openNameEdit(); }}
                    className="text-stone-200 cursor-pointer text-sm"
                  >
                    <Pencil className="mr-2 h-3.5 w-3.5 text-stone-400" />
                    Edit name
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onSelect={(e) => { e.preventDefault(); openPhoto(); }}
                    disabled={photoBusy}
                    className="text-stone-200 cursor-pointer text-sm"
                  >
                    <ImagePlus className="mr-2 h-3.5 w-3.5 text-amber-500/80" />
                    {photoBusy ? "Uploading..." : "Change photo"}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={logout}
                    className="text-red-400/90 focus:text-red-400 cursor-pointer text-sm"
                  >
                    <LogOut className="mr-2 h-3.5 w-3.5" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </ProfilePhotoPicker>
        ) : user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-stone-800/60 transition-colors">
                <Avatar className="h-7 w-7 border border-stone-700/60">
                  <AvatarImage src={resolvePictureUrl(user.picture)} alt="" />
                  <AvatarFallback className="bg-stone-800 text-stone-300 text-xs">
                    {user.name?.[0] ?? "?"}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm text-stone-400 hidden sm:block pr-1">
                  {user.name?.split(" ")[0] ?? user.email}
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40 border-stone-800 bg-stone-900">
              <DropdownMenuItem
                onClick={logout}
                className="text-red-400/90 focus:text-red-400 cursor-pointer text-sm"
              >
                <LogOut className="mr-2 h-3.5 w-3.5" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : null}
      </div>
    </header>
  );
}
