import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Progress } from "./ui/progress";
import { Button } from "./ui/button";
import { Download, CheckCircle2, XCircle } from "lucide-react";
import { animeAPI, DownloadLinkInfo } from "@/lib/api";

interface DownloadItem {
  episodeNumber: number;
  status:
    | "pending"
    | "processing"
    | "ready"
    | "downloading"
    | "completed"
    | "error";
  progress: number;
  downloadLink?: string;
  error?: string;
}

interface DownloadManagerProps {
  animeId: string;
  episodes: Record<number, DownloadLinkInfo[]>;
  selectedLanguage: string;
  selectedQuality: number;
  episodeRange: [number, number];
}

export function DownloadManager({
  animeId,
  episodes,
  selectedLanguage,
  selectedQuality,
  episodeRange,
}: DownloadManagerProps) {
  const [downloadItems, setDownloadItems] = useState<DownloadItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Initialize download items
    const items: DownloadItem[] = [];
    for (let ep = episodeRange[0]; ep <= episodeRange[1]; ep++) {
      items.push({
        episodeNumber: ep,
        status: "pending",
        progress: 0,
      });
    }
    setDownloadItems(items);
  }, [episodeRange]);

  const processEpisodes = async () => {
    setIsProcessing(true);
    const updatedItems = [...downloadItems];

    for (let i = 0; i < updatedItems.length; i++) {
      const item = updatedItems[i];
      const episodeNum = item.episodeNumber;

      try {
        // Update status to processing
        updatedItems[i] = { ...item, status: "processing", progress: 10 };
        setDownloadItems([...updatedItems]);

        // Get the download link for this episode
        const episodeLinks = episodes[episodeNum];
        if (!episodeLinks || episodeLinks.length === 0) {
          throw new Error("No links found for this episode");
        }

        // Find the link matching language and quality
        // episodeLinks is an array of [link, size, lang] tuples
        const matchingLink = episodeLinks.find((linkInfo) => {
          const [, size, lang] = linkInfo;
          const linkLang = lang || "jpn";
          const linkSize = parseInt(size.replace("p", ""));
          return linkLang === selectedLanguage && linkSize === selectedQuality;
        });

        if (!matchingLink) {
          throw new Error(
            "No matching link found for selected language/quality"
          );
        }

        // Extract the actual link URL (first element of tuple)
        const linkUrl = matchingLink[0];

        // Parse the link to get kwik.cx URL
        updatedItems[i] = { ...item, status: "processing", progress: 30 };
        setDownloadItems([...updatedItems]);

        const kwikUrl = await animeAPI.parseLink(linkUrl);
        updatedItems[i] = { ...item, status: "processing", progress: 50 };
        setDownloadItems([...updatedItems]);

        // Get the final download link
        const downloadLink = await animeAPI.getKwikLink(kwikUrl);
        updatedItems[i] = {
          ...item,
          status: "ready",
          progress: 100,
          downloadLink,
        };
        setDownloadItems([...updatedItems]);
      } catch (error) {
        updatedItems[i] = {
          ...item,
          status: "error",
          error: error instanceof Error ? error.message : "Unknown error",
        };
        setDownloadItems([...updatedItems]);
      }
    }

    setIsProcessing(false);
  };

  const downloadEpisode = (item: DownloadItem) => {
    if (item.downloadLink) {
      window.open(item.downloadLink, "_blank");
      const updatedItems = downloadItems.map((i) =>
        i.episodeNumber === item.episodeNumber
          ? { ...i, status: "downloading" as const }
          : i
      );
      setDownloadItems(updatedItems);
    }
  };

  const completedCount = downloadItems.filter(
    (i) => i.status === "ready"
  ).length;
  const errorCount = downloadItems.filter((i) => i.status === "error").length;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Download Manager</CardTitle>
        <CardDescription>
          Process and download episodes ({completedCount}/{downloadItems.length}{" "}
          ready
          {errorCount > 0 && `, ${errorCount} errors`})
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          onClick={processEpisodes}
          disabled={isProcessing}
          className="w-full"
          size="lg"
        >
          {isProcessing ? "Processing Episodes..." : "Process All Episodes"}
        </Button>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {downloadItems.map((item) => (
            <div
              key={item.episodeNumber}
              className="border rounded-lg p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">
                  Episode {item.episodeNumber}
                </span>
                <div className="flex items-center gap-2">
                  {item.status === "ready" && (
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                  )}
                  {item.status === "error" && (
                    <XCircle className="h-5 w-5 text-destructive" />
                  )}
                  {item.status === "ready" && (
                    <Button
                      size="sm"
                      onClick={() => downloadEpisode(item)}
                      variant="outline"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  )}
                </div>
              </div>

              {item.status === "processing" && (
                <Progress value={item.progress} className="h-2" />
              )}

              {item.status === "error" && (
                <p className="text-sm text-destructive">{item.error}</p>
              )}

              {item.status === "pending" && (
                <p className="text-sm text-muted-foreground">
                  Waiting to process...
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
