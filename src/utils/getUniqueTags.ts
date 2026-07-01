import type { CollectionEntry } from "astro:content";
import { postFilter } from "./postFilter";
import { slugifyStr } from "./slugify";

type Tag = {
  tag: string;
  tagName: string;
  count: number;
};

/**
 * Builds a de-duplicated, sorted tag list from posts.
 *
 * - Drafts and scheduled posts are excluded via `postFilter()`
 * - `tag` is the slug used in URLs; `tagName` is the original label for display
 * - Uniqueness is based on the slug (so differently-cased labels collapse)
 * - Sorted by article count descending, then alphabetically for ties
 */
export function getUniqueTags(posts: CollectionEntry<"posts">[]) {
  const tagMap = new Map<string, { tagName: string; count: number }>();

  posts
    .filter(postFilter)
    .flatMap(post => post.data.tags)
    .forEach(tag => {
      const key = slugifyStr(tag);
      const existing = tagMap.get(key);
      if (existing) {
        existing.count++;
      } else {
        tagMap.set(key, { tagName: tag, count: 1 });
      }
    });

  const tags: Tag[] = Array.from(tagMap.entries())
    .map(([tag, { tagName, count }]) => ({ tag, tagName, count }))
    .sort((a, b) => b.count - a.count || a.tag.localeCompare(b.tag));

  return tags;
}
