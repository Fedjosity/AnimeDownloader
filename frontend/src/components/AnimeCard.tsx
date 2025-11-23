import { AnimeInfo } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Film, Calendar, Star, Play } from "lucide-react";

interface AnimeCardProps {
  anime: AnimeInfo;
  onSelect: (anime: AnimeInfo) => void;
}

export function AnimeCard({ anime, onSelect }: AnimeCardProps) {
  return (
    <Card className="hover:border-primary/50 transition-colors cursor-pointer">
      <CardHeader>
        <CardTitle className="line-clamp-2">{anime.title}</CardTitle>
        <CardDescription className="flex items-center gap-4 flex-wrap">
          <span className="flex items-center gap-1">
            <Film className="h-4 w-4" />
            {anime.type}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            {anime.year}
          </span>
          <span className="flex items-center gap-1">
            <Star className="h-4 w-4" />
            {anime.score.toFixed(1)}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Episodes:</span>
            <span className="font-medium">{anime.episodes}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Status:</span>
            <span className="font-medium capitalize">{anime.status}</span>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button
          onClick={() => onSelect(anime)}
          className="w-full"
          variant="outline"
        >
          <Play className="mr-2 h-4 w-4" />
          Select Anime
        </Button>
      </CardFooter>
    </Card>
  );
}
