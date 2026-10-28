import {
  CircleAlert,
  CircleCheck,
  CircleX,
  CloudOff,
  Download,
  Eye,
  KeyRound,
  Lock,
  Package,
  ShieldCheck,
  Timer,
  Trash2,
  TriangleAlert,
  type LucideIcon
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { DOWNLOAD_URL, EVENT, TEAM, downloadIsPlaceholder } from '@/config'

type Status = 'red' | 'amber' | 'green' | 'failed'

const STATUS_UI: Record<Status, { label: string; tone: 'red' | 'amber' | 'green' | 'grey'; Icon: LucideIcon }> = {
  red: { label: 'Act now', tone: 'red', Icon: CircleAlert },
  amber: { label: 'Needs attention', tone: 'amber', Icon: TriangleAlert },
  green: { label: 'Looks good', tone: 'green', Icon: CircleCheck },
  failed: { label: 'Check failed', tone: 'grey', Icon: CircleX }
}

function StatusPill({ status }: { status: Status }) {
  const { label, tone, Icon } = STATUS_UI[status]
  return (
    <Badge status={tone}>
      <Icon aria-hidden="true" />
      {label}
    </Badge>
  )
}

/* The five checks, in the app's fixed order (manual 0.8). Statuses here are the all-states sample. */
const CHECKS: { id: string; title: string; line: string; sample: Status }[] = [
  { id: 'backup', title: 'Backup evidence', line: 'Is there a recent backup you could restore from?', sample: 'green' },
  { id: 'patch', title: 'Windows updates', line: 'Is Windows up to date with the latest security fixes?', sample: 'amber' },
  { id: 'software', title: 'Outdated software', line: 'Are everyday apps, like your browser, out of date?', sample: 'red' },
  {
    id: 'protection',
    title: 'Ransomware protections',
    line: 'Are Microsoft Defender and the other built-in shields switched on?',
    sample: 'red'
  },
  {
    id: 'recovery',
    title: 'Recovery readiness',
    line: 'If the worst happened, could you get back to a working PC?',
    sample: 'failed'
  }
]

const SAMPLE_FIXES = [
  'Turn Microsoft Defender back on',
  'Update Google Chrome',
  'Install Windows updates and restart'
]

function DownloadButton({ size = 'lg' as 'lg' | 'default' }) {
  return (
    <Button asChild size={size}>
      <a href={downloadIsPlaceholder ? '#get-a-key' : DOWNLOAD_URL}>
        <Download aria-hidden="true" />
        Download for Windows
      </a>
    </Button>
  )
}

/* Styled stand-in for the Results screen. Swap for a real PNG in public/ once you have one. */
function ResultsMock() {
  return (
    <figure aria-label="Sample Antigravity results screen" className="w-full">
      <div className="overflow-hidden rounded-xl border border-border bg-background shadow-xl shadow-black/10">
        <div className="flex items-center gap-2 bg-rag-grey px-4 py-2 text-xs font-medium text-white">
          <ShieldCheck className="size-3.5" aria-hidden="true" />
          Antigravity
        </div>
        <div className="space-y-5 p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-lg font-semibold leading-snug">2 urgent issues need attention this week.</p>
              <p className="mt-1 text-sm text-muted-foreground">Sample result for a small-office PC</p>
            </div>
            <StatusPill status="red" />
          </div>

          <div>
            <p className="mb-2 text-sm font-semibold">Fix these first</p>
            <ol className="space-y-2">
              {SAMPLE_FIXES.map((fix, i) => (
                <li key={fix} className="flex items-center gap-3 rounded-lg border border-border px-3 py-2 text-sm">
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-semibold">
                    {i + 1}
                  </span>
                  {fix}
                </li>
              ))}
            </ol>
          </div>

          <ul className="divide-y divide-border rounded-lg border border-border">
            {CHECKS.map((c) => (
              <li key={c.id} className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm">
                <span>{c.title}</span>
                <StatusPill status={c.sample} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </figure>
  )
}

const STEPS: { n: number; title: string; body: string; Icon: LucideIcon }[] = [
  {
    n: 1,
    title: 'Enter your key',
    body: 'Paste the licence key you were given. It is checked on your PC, so it works without internet.',
    Icon: KeyRound
  },
  {
    n: 2,
    title: 'Run a 1-minute scan',
    body: 'Antigravity reads your settings and nothing else. It never changes anything on your PC.',
    Icon: Timer
  },
  {
    n: 3,
    title: 'Follow your action plan',
    body: 'Get a clear result, up to three ranked fixes, and a one-page PDF you can hand to whoever looks after your IT.',
    Icon: Package
  }
]

const PRIVACY: { title: string; body: string; Icon: LucideIcon }[] = [
  { title: 'Runs on your PC', body: 'The whole check happens on your computer.', Icon: Lock },
  { title: 'Reads settings only', body: 'No names, files, emails or IP addresses are collected.', Icon: Eye },
  { title: 'Uploads nothing', body: 'Nothing leaves your PC. Uninstalling removes what it saved.', Icon: CloudOff }
]

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <a href="#top" className="flex items-center gap-2 font-semibold">
            <ShieldCheck className="size-5" aria-hidden="true" />
            Antigravity
          </a>
          <nav className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
              <a href="#get-a-key">Get a demo key</a>
            </Button>
            <DownloadButton size="default" />
          </nav>
        </div>
      </header>

      <main id="top">
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-14 sm:py-20 lg:grid-cols-[1.05fr_1fr]">
          <div>
            <h1 className="text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl">
              Is your PC ready for ransomware? Find out in one minute.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground">
              A 1-minute, read-only check of this PC&apos;s ransomware readiness. It tells you what is weak in plain
              English and gives you the three fixes that matter most.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <DownloadButton />
              <Button asChild variant="outline" size="lg">
                <a href="#get-a-key">
                  <KeyRound aria-hidden="true" />
                  Get a demo key
                </a>
              </Button>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">
              For Windows 10 and 11. Your data stays on this PC. Nothing is uploaded.
            </p>
          </div>
          <ResultsMock />
        </section>

        {/* How it works */}
        <section id="how-it-works" className="border-t border-border bg-secondary/60">
          <div className="mx-auto max-w-6xl px-5 py-16">
            <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
            <ol className="mt-10 grid gap-8 md:grid-cols-3">
              {STEPS.map(({ n, title, body, Icon }) => (
                <li key={n} className="flex gap-4">
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                    {n}
                  </span>
                  <div>
                    <h3 className="flex items-center gap-2 text-lg font-semibold">
                      {title}
                      <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
                    </h3>
                    <p className="mt-1.5 leading-relaxed text-muted-foreground">{body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* The 5 checks */}
        <section id="checks" className="mx-auto max-w-6xl px-5 py-16">
          <div className="grid gap-10 lg:grid-cols-[1fr_1.6fr]">
            <div>
              <h2 className="text-3xl font-bold tracking-tight">The 5 checks</h2>
              <p className="mt-3 max-w-sm leading-relaxed text-muted-foreground">
                Every scan asks the same five questions, always in the same order, so results are easy to compare.
              </p>
            </div>
            <ul className="divide-y divide-border border-y border-border">
              {CHECKS.map((c) => (
                <li key={c.id} className="py-4">
                  <h3 className="font-semibold">{c.title}</h3>
                  <p className="mt-1 text-muted-foreground">{c.line}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Privacy */}
        <section id="privacy" className="bg-foreground text-background">
          <div className="mx-auto max-w-6xl px-5 py-16">
            <h2 className="text-3xl font-bold tracking-tight">Runs on your PC. Reads settings only. Uploads nothing.</h2>
            <ul className="mt-10 grid gap-8 md:grid-cols-3">
              {PRIVACY.map(({ title, body, Icon }) => (
                <li key={title} className="flex gap-3">
                  <Icon className="mt-1 size-5 shrink-0" aria-hidden="true" />
                  <div>
                    <h3 className="font-semibold">{title}</h3>
                    <p className="mt-1 leading-relaxed text-background/75">{body}</p>
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-10 flex items-center gap-2 text-sm text-background/75">
              <Trash2 className="size-4" aria-hidden="true" />
              Built to keep personal information off your report, in line with POPIA.
            </p>
          </div>
        </section>

        {/* Get a demo key */}
        <section id="get-a-key" className="mx-auto max-w-6xl px-5 py-16">
          <Card>
            <CardContent className="grid gap-8 p-6 sm:p-10 md:grid-cols-[1fr_1.2fr]">
              <div>
                <h2 className="text-3xl font-bold tracking-tight">Get a demo key</h2>
                <p className="mt-3 leading-relaxed text-muted-foreground">
                  Demo keys are handed out in person. Keys are checked on your PC, so they work offline.
                </p>
              </div>
              <ol className="space-y-5">
                <li className="flex gap-4">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold">
                    1
                  </span>
                  <p className="pt-1">Come to the Antigravity stand and ask the team for a demo key.</p>
                </li>
                <li className="flex gap-4">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold">
                    2
                  </span>
                  <p className="pt-1">Download and install Antigravity on a Windows PC.</p>
                </li>
                <li className="flex gap-4">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-secondary text-sm font-semibold">
                    3
                  </span>
                  <p className="pt-1">Paste your key, click Activate, then Start scan.</p>
                </li>
                <li className="pt-1">
                  <DownloadButton />
                </li>
              </ol>
            </CardContent>
          </Card>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-8 text-sm text-muted-foreground">
          <p>Antigravity by {TEAM.join(', ')}</p>
          <p>{EVENT}</p>
        </div>
      </footer>
    </div>
  )
}
