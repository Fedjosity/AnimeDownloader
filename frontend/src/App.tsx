import { useState } from "react";
import { SearchBar } from "./components/SearchBar";
import { AnimeCard } from "./components/AnimeCard";
import { EpisodeSelector } from "./components/EpisodeSelector";
import { LanguageQualitySelector } from "./components/LanguageQualitySelector";
import { DownloadManager } from "./components/DownloadManager";
import { OSInstructions } from "./components/OSInstructions";
import { animeAPI, AnimeInfo, DownloadLinkInfo } from "./lib/api";
import { Card, CardContent } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { ArrowLeft, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./components/ui/dialog";

type Step = "search" | "select" | "episodes" | "quality" | "download";

function App() {
  const [step, setStep] = useState<Step>("search");
  const [, setSearchQuery] = useState("");
  const [animeList, setAnimeList] = useState<AnimeInfo[]>([]);
  const [selectedAnime, setSelectedAnime] = useState<AnimeInfo | null>(null);
  const [episodeCount, setEpisodeCount] = useState(0);
  const [episodeRange, setEpisodeRange] = useState<[number, number]>([1, 1]);
  const [episodeData, setEpisodeData] = useState<
    Record<number, DownloadLinkInfo[]>
  >({});
  const [selectedLanguage, setSelectedLanguage] = useState<string>("");
  const [selectedQuality, setSelectedQuality] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    setIsLoading(true);
    setError(null);
    try {
      const results = await animeAPI.search(query);
      setAnimeList(results);
      if (results.length > 0) {
        setStep("select");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search anime");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectAnime = async (anime: AnimeInfo) => {
    setSelectedAnime(anime);
    setIsLoading(true);
    setError(null);
    try {
      const count = await animeAPI.getEpisodeCount(anime.session_id);
      setEpisodeCount(count);
      setEpisodeRange([1, count]);
      setStep("episodes");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to get episode count"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleEpisodeRangeConfirm = async () => {
    if (!selectedAnime) return;
    setIsLoading(true);
    setError(null);
    try {
      const episodes = await animeAPI.getEpisodes(
        selectedAnime.session_id,
        episodeRange
      );
      const episodeIds = episodes.map((ep) => ep.session_id);
      const downloadLinks = await animeAPI.getDownloadLinks(
        selectedAnime.session_id,
        episodeIds
      );

      // Organize by episode number
      const organized: Record<number, DownloadLinkInfo[]> = {};
      episodes.forEach((ep, index) => {
        organized[ep.episode_number] = downloadLinks[index] || [];
      });

      setEpisodeData(organized);
      setStep("quality");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to get download links"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleQualityConfirm = () => {
    if (selectedLanguage && selectedQuality) {
      setStep("download");
    }
  };

  const handleReset = () => {
    setStep("search");
    setAnimeList([]);
    setSelectedAnime(null);
    setEpisodeCount(0);
    setEpisodeRange([1, 1]);
    setEpisodeData({});
    setSelectedLanguage("");
    setSelectedQuality(0);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">AnimeDownloader</h1>
          <p className="text-muted-foreground">
            Download your favorite anime episodes with ease
          </p>
        </div>

        {/* Instructions Dialog */}
        <div className="mb-6 flex justify-center">
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline">View Setup Instructions</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Setup Instructions</DialogTitle>
                <DialogDescription>
                  Follow these instructions to set up AnimeDownloader on your
                  system
                </DialogDescription>
              </DialogHeader>
              <OSInstructions />
            </DialogContent>
          </Dialog>
        </div>

        {/* Error Display */}
        {error && (
          <Card className="mb-6 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Step 1: Search */}
        {step === "search" && (
          <div className="space-y-6">
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            {isLoading && (
              <div className="flex justify-center">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            )}
          </div>
        )}

        {/* Step 2: Select Anime */}
        {step === "select" && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={handleReset}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Search
              </Button>
              <h2 className="text-2xl font-semibold">Select Anime</h2>
            </div>
            {animeList.length === 0 ? (
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-muted-foreground">
                    No anime found. Try a different search.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {animeList.map((anime) => (
                  <AnimeCard
                    key={anime.session_id}
                    anime={anime}
                    onSelect={handleSelectAnime}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Select Episodes */}
        {step === "episodes" && selectedAnime && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => setStep("select")}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <div>
                <h2 className="text-2xl font-semibold">
                  {selectedAnime.title}
                </h2>
                <p className="text-muted-foreground">
                  {selectedAnime.type} • {selectedAnime.year} • {episodeCount}{" "}
                  episodes
                </p>
              </div>
            </div>
            <EpisodeSelector
              totalEpisodes={episodeCount}
              episodeRange={episodeRange}
              onRangeChange={setEpisodeRange}
            />
            <Button
              onClick={handleEpisodeRangeConfirm}
              disabled={isLoading || episodeRange[0] > episodeRange[1]}
              className="w-full"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                "Continue"
              )}
            </Button>
          </div>
        )}

        {/* Step 4: Select Language & Quality */}
        {step === "quality" && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => setStep("episodes")}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <h2 className="text-2xl font-semibold">
                Select Language & Quality
              </h2>
            </div>
            <LanguageQualitySelector
              episodes={episodeData}
              onSelect={(lang, quality) => {
                setSelectedLanguage(lang);
                setSelectedQuality(quality);
              }}
              selectedLanguage={selectedLanguage}
              selectedQuality={selectedQuality}
            />
            <Button
              onClick={handleQualityConfirm}
              disabled={!selectedLanguage || !selectedQuality}
              className="w-full"
              size="lg"
            >
              Continue to Download
            </Button>
          </div>
        )}

        {/* Step 5: Download */}
        {step === "download" && selectedAnime && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => setStep("quality")}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
              <div>
                <h2 className="text-2xl font-semibold">Download Episodes</h2>
                <p className="text-muted-foreground">
                  {selectedAnime.title} • Episodes {episodeRange[0]}-
                  {episodeRange[1]} • {selectedLanguage.toUpperCase()} •{" "}
                  {selectedQuality}p
                </p>
              </div>
            </div>
            <DownloadManager
              animeId={selectedAnime.session_id}
              episodes={episodeData}
              selectedLanguage={selectedLanguage}
              selectedQuality={selectedQuality}
              episodeRange={episodeRange}
            />
            <Button onClick={handleReset} variant="outline" className="w-full">
              Start New Download
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
