import { useState } from "react";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";

interface EpisodeSelectorProps {
  totalEpisodes: number;
  episodeRange: [number, number];
  onRangeChange: (range: [number, number]) => void;
}

export function EpisodeSelector({
  totalEpisodes,
  episodeRange,
  onRangeChange,
}: EpisodeSelectorProps) {
  const [start, setStart] = useState(episodeRange[0].toString());
  const [end, setEnd] = useState(episodeRange[1].toString());

  const handleStartChange = (value: string) => {
    const num = parseInt(value);
    if (!isNaN(num) && num >= 1 && num <= totalEpisodes) {
      setStart(value);
      onRangeChange([num, episodeRange[1]]);
    } else if (value === "") {
      setStart(value);
    }
  };

  const handleEndChange = (value: string) => {
    const num = parseInt(value);
    if (!isNaN(num) && num >= 1 && num <= totalEpisodes) {
      setEnd(value);
      onRangeChange([episodeRange[0], num]);
    } else if (value === "") {
      setEnd(value);
    }
  };

  const handleSelectAll = () => {
    setStart("1");
    setEnd(totalEpisodes.toString());
    onRangeChange([1, totalEpisodes]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Select Episode Range</CardTitle>
        <CardDescription>
          Choose which episodes to download (1-{totalEpisodes})
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="start-episode">Start Episode</Label>
            <Input
              id="start-episode"
              type="number"
              min={1}
              max={totalEpisodes}
              value={start}
              onChange={(e) => handleStartChange(e.target.value)}
              placeholder="1"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="end-episode">End Episode</Label>
            <Input
              id="end-episode"
              type="number"
              min={1}
              max={totalEpisodes}
              value={end}
              onChange={(e) => handleEndChange(e.target.value)}
              placeholder={totalEpisodes.toString()}
            />
          </div>
        </div>
        <Button onClick={handleSelectAll} variant="outline" className="w-full">
          Select All Episodes
        </Button>
        {episodeRange[0] > episodeRange[1] && (
          <p className="text-sm text-destructive">
            Start episode must be less than or equal to end episode
          </p>
        )}
      </CardContent>
    </Card>
  );
}
