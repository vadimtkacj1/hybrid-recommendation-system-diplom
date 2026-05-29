import { Button } from "@/components/ui/button";
import { resolvePictureUrl } from "@/lib/media";
import { pickCover } from "@/lib/covers";
import type { UserFeedCardProps } from "@/types";

function displayName(name: string | null | undefined) {
  const n = name?.trim();
  if (!n) return "User";
  return n.split(/[\s–]/)[0];
}

export function UserFeedCard({ user: u, onMessage }: UserFeedCardProps) {
  const pic = resolvePictureUrl(u.picture);
  const cover = pic || pickCover(u.user_id);
  const name = displayName(u.name);
  const matchPct = Math.round(u.similarity * 100);

  return (
    <article
      className="group relative aspect-square rounded-2xl overflow-hidden bg-stone-900 border border-stone-800/80 shadow-md cursor-pointer transition duration-300 hover:-translate-y-0.5 hover:shadow-lg"
      onClick={() => onMessage({ id: u.user_id, name: u.name, picture: u.picture })}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onMessage({ id: u.user_id, name: u.name, picture: u.picture });
        }
      }}
    >
      <img
        src={cover}
        alt=""
        className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-[1.04] group-hover:brightness-[1.05]"
        loading="lazy"
      />
      <div className="hidden sm:block absolute inset-0 bg-gradient-to-t from-black/90 via-black/35 to-black/5 transition-opacity duration-300 group-hover:opacity-0" />

      <div className="absolute inset-0 flex flex-col justify-between p-3 bg-black/80 backdrop-blur-sm opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity duration-300">
        <div className="flex justify-between items-start">
          <p className="font-semibold text-white text-sm leading-tight">{name}</p>
          <span className="px-2.5 py-1 rounded-full bg-black/60 border border-white/20 text-[11px] font-semibold text-white shrink-0 ml-2">
            {matchPct}% match
          </span>
        </div>

        <div className="space-y-2">
          {u.top_topics.length > 0 && (
            <div>
              <p className="text-[10px] text-stone-400 font-medium mb-1 uppercase tracking-wide">Topics</p>
              <div className="flex flex-wrap gap-1">
                {u.top_topics.map((topic) => (
                  <span key={topic} className="text-[11px] px-2 py-0.5 rounded-full bg-black/50 text-white/90 border border-white/15">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="w-full h-9 rounded-xl bg-amber-500 text-stone-950 font-semibold hover:bg-amber-400 border-0 text-xs mt-1"
            onClick={(e) => {
              e.stopPropagation();
              onMessage({ id: u.user_id, name: u.name, picture: u.picture });
            }}
            aria-label={`Message ${name}`}
          >
            Message
          </Button>
        </div>
      </div>

      <div className="hidden sm:block group-hover:opacity-0 transition-opacity duration-300">
        <div className="absolute top-3 right-3 px-2.5 py-1.5 rounded-full bg-black/65 border border-white/20 text-[11px] font-semibold text-white backdrop-blur">
          {matchPct}% match
        </div>

        <div className="absolute inset-x-0 bottom-0 p-3 flex items-end justify-between gap-2">
          <div className="min-w-0 space-y-1">
            <p className="font-semibold text-white text-sm truncate drop-shadow-md">{name}</p>
            {u.top_topics.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {u.top_topics.slice(0, 3).map((topic) => (
                  <span key={topic} className="text-[11px] px-2 py-0.5 rounded-full bg-black/45 text-white/90 border border-white/10 backdrop-blur">
                    {topic}
                  </span>
                ))}
              </div>
            )}
          </div>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="h-9 shrink-0 rounded-full bg-white/15 border border-white/30 text-white hover:bg-amber-500 hover:text-stone-950 hover:border-amber-400 backdrop-blur px-3 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              onMessage({ id: u.user_id, name: u.name, picture: u.picture });
            }}
            aria-label={`Message ${name}`}
          >
            Message
          </Button>
        </div>
      </div>
    </article>
  );
}

function FeedSkeleton() {
  return <div className="aspect-square rounded-xl bg-stone-900/60 border border-stone-800 animate-pulse" />;
}

export function UserFeedSkeletonGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 sm:gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <FeedSkeleton key={i} />
      ))}
    </div>
  );
}
