import { detectOS, getOSInstructions } from "@/lib/os-utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Separator } from "./ui/separator";
import { CheckCircle2 } from "lucide-react";

export function OSInstructions() {
  const currentOS = detectOS();
  const currentInstructions = getOSInstructions(currentOS);

  const allInstructions = {
    windows: getOSInstructions("windows"),
    macos: getOSInstructions("macos"),
    linux: getOSInstructions("linux"),
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Setup Instructions</CardTitle>
        <CardDescription>
          Follow these steps to get started with AnimeDownloader
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue={currentOS} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="windows">Windows</TabsTrigger>
            <TabsTrigger value="macos">macOS</TabsTrigger>
            <TabsTrigger value="linux">Linux</TabsTrigger>
          </TabsList>

          {Object.entries(allInstructions).map(([os, instructions]) => (
            <TabsContent key={os} value={os} className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold mb-2">
                  {instructions.title}
                </h3>
                {instructions.note && (
                  <p className="text-sm text-muted-foreground mb-4">
                    {instructions.note}
                  </p>
                )}
              </div>
              <Separator />
              <ol className="space-y-3">
                {instructions.steps.map((step, index) => (
                  <li key={index} className="flex gap-3">
                    <div className="flex-shrink-0 mt-0.5">
                      <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                        <span className="text-xs font-semibold">
                          {index + 1}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm leading-relaxed">{step}</p>
                  </li>
                ))}
              </ol>
              {instructions.command && (
                <>
                  <Separator />
                  <div className="bg-muted p-4 rounded-md">
                    <p className="text-xs text-muted-foreground mb-2 font-medium">
                      Command to run:
                    </p>
                    <code className="text-sm font-mono bg-background px-2 py-1 rounded">
                      {instructions.command}
                    </code>
                  </div>
                </>
              )}
            </TabsContent>
          ))}
        </Tabs>

        <Separator className="my-6" />

        <div className="bg-muted/50 p-4 rounded-md space-y-2">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium">Quick Start</p>
              <p className="text-xs text-muted-foreground mt-1">
                Make sure both the API server (port 8000) and frontend (port
                3000) are running. The frontend will automatically connect to
                the backend API.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
