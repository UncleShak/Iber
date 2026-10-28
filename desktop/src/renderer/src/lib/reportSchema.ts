import { z } from "zod";
export const reportSchema = z.object({
  schema_version: z.string(),
  run_id: z.string(),
  generated_at: z.string(),
  engine_version: z.string(),
  baseline_version: z.string(),
  evidence_id: z.string().optional(),
  overall: z.enum(["red", "amber", "green"]),
  summary: z.string(),
  scan: z.object({ is_admin: z.boolean(), os_caption: z.string() }),
  categories: z.array(z.object({
    id: z.string(), title: z.string(),
    status: z.enum(["red", "amber", "green", "unavailable", "failed"]),
    explanation: z.string(),
    evidence: z.array(z.object({ label: z.string(), value: z.string(), status: z.string().optional() })),
    fix_ids: z.array(z.string())
  })).length(5),
  fixes: z.array(z.object({
    id: z.string(), title: z.string(), why: z.string(),
    steps: z.array(z.string()), effort_minutes: z.number(), needs_admin: z.boolean()
  })),
  top_fixes: z.array(z.string()).max(3)
});