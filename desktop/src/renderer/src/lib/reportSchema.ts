// desktop/src/renderer/src/lib/reportSchema.ts
// zod mirror of report.json (manual §0.8). The renderer validates every report with this (§4.9.3).
import { z } from "zod";

export const STATUSES = ["red", "amber", "green", "unavailable", "failed"] as const;
export const CATEGORY_IDS = ["backup", "patch", "software", "protection", "recovery"] as const;

export const StatusSchema = z.enum(STATUSES);
export type Status = z.infer<typeof StatusSchema>;

const EvidenceSchema = z.object({
  label: z.string(),
  value: z.string(),
  status: StatusSchema.optional(), // missing status = neutral row (§4.10)
});

const CategorySchema = z.object({
  id: z.enum(CATEGORY_IDS),
  title: z.string(),
  status: StatusSchema,
  explanation: z.string().max(200),
  evidence: z.array(EvidenceSchema).max(8), // may be empty when a category "failed"
  fix_ids: z.array(z.string()),
});

const FixSchema = z.object({
  id: z.string(),
  category: z.enum(CATEGORY_IDS),
  severity: z.enum(["red", "amber"]),
  title: z.string(),
  why: z.string(),
  steps: z.array(z.string()).min(1).max(5),
  effort_minutes: z.number(),
  needs_admin: z.boolean(),
});

export const reportSchema = z
  .object({
    schema_version: z.string().regex(/^1\./, "Unsupported report major version"),
    run_id: z.string(),
    generated_at: z.string(),
    engine_version: z.string(),
    baseline_version: z.string(),
    evidence_id: z.string().optional(), // "AG-…" (§2.14.1), shown in the footer
    overall: z.enum(["red", "amber", "green"]),
    summary: z.string(),
    categories: z.array(CategorySchema).length(5),
    fixes: z.array(FixSchema),
    top_fixes: z.array(z.string()).max(3),
    scan: z.object({
      is_admin: z.boolean(),
      duration_ms: z.number(),
      os_caption: z.string(),
    }),
  })
  .superRefine((r, ctx) => {
    // Categories must be in the fixed order — the UI never sorts (§0.8).
    r.categories.forEach((c, i) => {
      if (c.id !== CATEGORY_IDS[i]) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["categories", i, "id"],
          message: `Expected category "${CATEGORY_IDS[i]}" at position ${i}`,
        });
      }
    });
    // Every referenced fix must exist.
    const ids = new Set(r.fixes.map((f) => f.id));
    const refs: [string, string[]][] = [
      ["top_fixes", r.top_fixes],
      ...r.categories.map((c, i): [string, string[]] => [`categories.${i}.fix_ids`, c.fix_ids]),
    ];
    for (const [where, list] of refs) {
      for (const id of list) {
        if (!ids.has(id)) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: where.split("."),
            message: `Unknown fix id "${id}"`,
          });
        }
      }
    }
  });

export type Report = z.infer<typeof reportSchema>;
export type Category = Report["categories"][number];
export type Fix = Report["fixes"][number];
