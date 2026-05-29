import {
  Music2, Gamepad2, FlaskConical, BookOpen, Tv2, Newspaper,
  Laugh, Trophy, Clapperboard, Plane, Scissors, Users, PawPrint, Sword,
} from "lucide-react";
import type { Category } from "@/types";

export const CATEGORIES: Category[] = [
  { name: "Music",                icon: Music2 },
  { name: "Gaming",               icon: Gamepad2 },
  { name: "Science & Technology", icon: FlaskConical },
  { name: "Education",            icon: BookOpen },
  { name: "Entertainment",        icon: Tv2 },
  { name: "News & Politics",      icon: Newspaper },
  { name: "Comedy",               icon: Laugh },
  { name: "Sports",               icon: Trophy },
  { name: "Film & Animation",     icon: Clapperboard },
  { name: "Travel & Events",      icon: Plane },
  { name: "How-to & Style",       icon: Scissors },
  { name: "People & Blogs",       icon: Users },
  { name: "Pets & Animals",       icon: PawPrint },
  { name: "Anime/Animation",      icon: Sword },
];
