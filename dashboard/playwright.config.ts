import { defineConfig } from "@playwright/test";
import fs from "node:fs";
export default defineConfig({
  testDir: "./tests/browser",
  timeout: 45_000,
  workers: 2,
  use: {
    baseURL: process.env.DASHBOARD_URL ?? "http://127.0.0.1:3000",
    launchOptions: {
      executablePath:
        process.env.CHROME_PATH ??
        (fs.existsSync("/usr/bin/google-chrome")
          ? "/usr/bin/google-chrome"
          : undefined),
      args: ["--no-sandbox"],
    },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
});
