import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Label } from "./ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { DownloadLinkInfo } from "@/lib/api";

interface LanguageQualitySelectorProps {
  episodes: Record<number, DownloadLinkInfo[]>;
  onSelect: (language: string, quality: number) => void;
  selectedLanguage?: string;
  selectedQuality?: number;
}

export function LanguageQualitySelector({
  episodes,
  onSelect,
  selectedLanguage,
  selectedQuality,
}: LanguageQualitySelectorProps) {
  // Get available languages and qualities from the first episode
  const firstEpisodeKey = Object.keys(episodes)[0];
  if (!firstEpisodeKey) return null;

  const firstEpisodeLinks = episodes[Number(firstEpisodeKey)];

  // Organize links by language and quality
  const organizedLinks: Record<string, Record<number, DownloadLinkInfo[]>> = {};

  firstEpisodeLinks.forEach((linkInfo) => {
    // linkInfo is a tuple: [link, size, lang]
    const [, sizeStr, langStr] = linkInfo;
    const lang = langStr || "jpn";
    const size = parseInt(sizeStr.replace("p", ""));

    if (!organizedLinks[lang]) {
      organizedLinks[lang] = {};
    }
    if (!organizedLinks[lang][size]) {
      organizedLinks[lang][size] = [];
    }
    organizedLinks[lang][size].push(linkInfo);
  });

  const languages = Object.keys(organizedLinks);
  const qualities = selectedLanguage
    ? Object.keys(organizedLinks[selectedLanguage])
        .map(Number)
        .sort((a, b) => b - a)
    : [];

  const handleLanguageChange = (lang: string) => {
    const availableQualities = Object.keys(organizedLinks[lang])
      .map(Number)
      .sort((a, b) => b - a);
    onSelect(lang, availableQualities[0]);
  };

  const handleQualityChange = (quality: string) => {
    if (selectedLanguage) {
      onSelect(selectedLanguage, parseInt(quality));
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Select Language & Quality</CardTitle>
        <CardDescription>
          Choose your preferred language and video quality
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="language">Language</Label>
          <Select
            value={selectedLanguage || ""}
            onValueChange={handleLanguageChange}
          >
            <SelectTrigger id="language">
              <SelectValue placeholder="Select language" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang} value={lang}>
                  {lang.toUpperCase()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedLanguage && qualities.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="quality">Quality</Label>
            <Select
              value={selectedQuality?.toString() || ""}
              onValueChange={handleQualityChange}
            >
              <SelectTrigger id="quality">
                <SelectValue placeholder="Select quality" />
              </SelectTrigger>
              <SelectContent>
                {qualities.map((quality) => (
                  <SelectItem key={quality} value={quality.toString()}>
                    {quality}p
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
