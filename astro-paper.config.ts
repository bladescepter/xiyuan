import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    url: "https://xiyuan.wiki",
    title: "西园",
    description: "陆西园的博客",
    author: "陆西园",
    profile: "https://xiyuan.wiki",
    lang: "zh",
    timezone: "Asia/Shanghai",
    dir: "ltr",
  },
  posts: {
    perPage: 10,
    perIndex: 10,
    scheduledPostMargin: 15 * 60 * 1000,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: true,
    showArchives: true,
    showBackButton: true,
    search: "pagefind",
  },
  socials: [
    { name: "x", url: "https://x.com/bladescepter" },
    { name: "telegram", url: "https://t.me/bladescepter" },
    { name: "mail", url: "mailto:bladescepter@gmail.com" },
  ],
  shareLinks: [],
});
