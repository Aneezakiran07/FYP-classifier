# Regions to hand label, batch 2

30 dev regions that reach the model, seed 20261109, none of them in batch 1. Every side is at most 500 characters, so nothing is cut off in the prompt.

This batch is filtered to find few shot examples for null-safety-conflict, type-incompatibility and execution-perturbation. The "picked because" line names the text filter that found the region. It is not a label, and many regions will turn out to be something else. Because of the filter this is not a random sample, so do not use it for accuracy numbers.

The AST verdict shown is the one after the guards, the same one the model sees in a real run.

## 31. packages/frontend/app/sindi/[conversationId].tsx

pr_key `OxyHQ/Homiio#27`, conflict_index `2`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
                    key={index}
                    style={styles.quickActionButton}
                    onPress={() => handleQuickAction(action.prompt)}
```

**OURS**
```
                    style={styles.emptyStateButton}
                    onPress={createNewConversation}
```

**THEIRS**
```
                    key={index}
                    style={styles.quickActionButton}
                    onPress={() => handleQuickAction(action.prompt, action.requiresInput)}
```

## 32. apps/frontend/src/app/api/attribute-values/[id]/route.ts

pr_key `Parketsense/erp-review#1`, conflict_index `0`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
export async function GET(request: Request, { params }: { params: { id: string } }) {
  try {
    const response = await fetch(`http://localhost:4003/api/attribute-values/${params.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
```

**OURS**
```
export async function GET(request: Request, { params }: { params: { id: string } }) {
  try {
    const response = await fetch(`http://localhost:4000/api/attribute-values/${params.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
```

**THEIRS**
```
import { NextRequest, NextResponse } from 'next/server';
```

## 33. packages/blac/src/Blac.ts

pr_key `jsnanigans/blac#18`, conflict_index `5`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
    // Fix: Find the specific bloc by ID within the isolated array
    const found = blocs.find((b) => b._id === id) as InstanceType<B> | undefined;
    return found;
```

**OURS**
```
    // Find the specific bloc by ID within the isolated array
    const found = blocs.find((b) => b._id === id && !(b as any).isDisposed) as
      | InstanceType<B>
      | undefined;
    return found;
```

**THEIRS**
```
    return blocMap.get(id) as InstanceType<B> | undefined;
```

## 34. packages/frontend/src/pages/dashboard/BusinessPage.tsx

pr_key `SunnyHillF/Miliare#20`, conflict_index `4`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
            <select className="py-1 px-3 border border-gray-300 rounded-md text-sm">
```

**OURS**
```
            <select
              className="py-1 px-3 border border-gray-300 rounded-md text-sm"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
```

**THEIRS**
```
            <select
              className="py-1 px-3 border border-gray-300 rounded-md text-sm"
              value={period}
              onChange={e => setPeriod(e.target.value)}
            >
```

## 35. src/lib/mock-data.ts

pr_key `brunenrique/studio#124`, conflict_index `3`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
  return {
    ...patient,
    name: decryptMock(patient.name),
    contact: decryptMock(patient.contact),
    dateOfBirth: decryptMock(patient.dateOfBirth),
  };
```

**OURS**
```
  return decryptPatient(patient);
```

**THEIRS**
```
  return {
    ...patient,
    name: decryptField(patient.name),
    contact: decryptField(patient.contact),
    dateOfBirth: decryptField(patient.dateOfBirth),
    sessionNotes: patient.sessionNotes.map(n => ({
      ...n,
      notes: decryptField(n.notes),
      patientHistorySummaryForAI: n.patientHistorySummaryForAI
        ? decryptField(n.patientHistorySummaryForAI)
        : undefined,
    })),
  };
```

## 36. app/(apis)/signin/route.ts

pr_key `drivly/ai#718`, conflict_index `0`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
  return NextResponse.redirect(new URL('/api/auth/signin/github?callbackUrl=/admin', getCurrentURL(request.headers)))
```

**OURS**
```
  const currentURL = getCurrentURL(request.headers)
  const hostname = request.headers.get('host') || ''
  const callbackUrl = hostname.endsWith('.do') && !hostname.includes('apis.do') ? 
    `/admin/collections/${hostname.replace('.do', '')}` : 
    '/admin'
  
  return NextResponse.redirect(new URL(`/api/auth/signin/github?callbackUrl=${callbackUrl}`, currentURL))
```

**THEIRS**
```
  const url = getCurrentURL(request.headers)
  const domain = new URL(url).hostname
  return NextResponse.redirect(new URL(`/api/auth/signin/github?callbackUrl=${encodeURIComponent(`/${domain}`)}`, url))
```

## 37. web/src/stores/__tests__/GlobalChatStore.test.ts

pr_key `nodetool-ai/nodetool#96`, conflict_index `39`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
    it('sends stop signal and resets state', () => {
      store.setState({ status: 'loading', progress: { current: 5, total: 10 }, statusMessage: 'Processing...' });
      
```

**OURS**
```
    afterEach(() => {
      if (mockServer) mockServer.stop(); // Clean up server
    });

    it("sends stop signal and resets state", async () => {
      store.setState({
        status: "loading" as any,
        progress: { current: 5, total: 10 },
        statusMessage: "Processing..."
      });

```

**THEIRS**
```
    it("sends stop signal and resets state", async () => {
      store.setState({
        status: "loading",
        progress: { current: 5, total: 10 },
        statusMessage: "Processing..."
      });

```

## 38. apps/ui/src/routes/signup.tsx

pr_key `theopenco/llmgateway#237`, conflict_index `2`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
	useEffect(() => {
		if (session.data?.user) {
			navigate({ to: "/dashboard" });
		}
	}, [session.data, navigate]);
```

**OURS**
```
	useEffect(() => {
		if (data?.user) {
			navigate({ to: "/dashboard" });
		}
	}, [data?.user, navigate]);
```

**THEIRS**
```
	useUser({ redirect: "authenticated" });
```

## 39. packages/backend/tests/unit/importer/stubs/stub_import_report_repository.ts

pr_key `eliemoriceau/HBManager#77`, conflict_index `0`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import { ImportReportRepository } from '#importer/secondary/ports/import_report_repository'
import { CsvImportReport } from '#importer/domain/import_report'

export class StubImportReportRepository extends ImportReportRepository {
  public saved: CsvImportReport | null = null

  async save(report: CsvImportReport): Promise<void> {
    this.saved = report
  }
}
```

**THEIRS**
```
import { ImportReportRepository } from '#importer/secondary/ports/import_report_repository'
import { CsvImportReport } from '#importer/domain/import_report'

export class StubImportReportRepository implements ImportReportRepository {
  public saved: CsvImportReport[] = []

  async save(report: CsvImportReport): Promise<void> {
    this.saved.push(report)
  }
}
```

## 40. src/pages/Home/index.tsx

pr_key `DCMHopper/bookclub-client#2`, conflict_index `0`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
  const calendar = new Calendar("#calendar", {
    defaultView: "month",
    usageStatistics: "false",
    calendars: [
```

**OURS**
```
  const calendarRef = useRef(null);

  useEffect(() => {
    if (!calendarRef.current) return;

    const calendar = new Calendar(calendarRef.current, {
      defaultView: "month",
      usageStatistics: false,
      calendars: [
        {
          id: "1",
          name: "Events",
          color: "#ffffff",
          bgColor: "#00a9ff",
          dragBgColor: "#00a9ff",
          borderColor: "#00a9ff",
        },
      ],
    });

    // sample events
    calendar.createEvents([
```

**THEIRS**
```
  const calendar = new Calendar("#calendar", {
    defaultView: "month",
    usageStatistics: false,
    calendars: [
```

## 41. src/modules/overlay.ts

pr_key `samdowrickstr/zotero-reading-list#1`, conflict_index `3`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
					};
				}),
			),
```

**OURS**
```
					}),
				),
				{
					tag: "menuitem" as const,
					label: getString("reading-tasks-menu"),
					commandListener: () => showReadingTasks(),
				} as MenuitemOptions,
				{
					tag: "menuitem" as const,
					label: getString("add-reading-task-menu"),
					commandListener: () => promptAddReadingTask(),
				} as MenuitemOptions,
			] as MenuitemOptions[],
```

**THEIRS**
```
					};
				}),
				{
					tag: "menuitem",
					label: getString("reading-tasks-menu"),
					commandListener: () => showReadingTasks(),
				},
			],
```

## 42. src/server/auth.ts

pr_key `mykcryptodev/log-a-dog#129`, conflict_index `2`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
          // Mark that we've attempted to fetch FID to prevent repeated queries
          token.fidFetched = true;
```

**THEIRS**
```
          if (dbUser?.neynarScore !== undefined && dbUser.neynarScore !== null) {
            token.neynarScore = dbUser.neynarScore;
          }
```

## 43. lib/db/helpers/01-core-to-parts.ts

pr_key `skalingclouds/ai-chatbot#3`, conflict_index `0`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
if (!process.env.POSTGRES_URL) {
  throw new Error('POSTGRES_URL environment variable is not set');
}
```

**OURS**
```
// config({
//   path: '.env.local',
// });
```

**THEIRS**
```
const DB_URL = process.env.POSTGRES_URL || process.env.DATABASE_URL;
if (!DB_URL) {
  throw new Error('POSTGRES_URL or DATABASE_URL environment variable is not set');
}
```

## 44. app/generate-contract/loading.tsx

pr_key `AbuAli85/extra-contracts-yy#12`, conflict_index `0`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import Loading from "../loading"
export default Loading
```

**THEIRS**
```
import { Loader2 } from "lucide-react"

export default function Loading() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
      <p className="ml-2 text-sm">Preparing form...</p>
    </div>
  )
}
```

## 45. apps/ui/src/routes/dashboard/_layout.tsx

pr_key `theopenco/llmgateway#237`, conflict_index `1`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
	const navigate = useNavigate();
	const session = useSession();

	useEffect(() => {
		if (!session.isPending && !session.data?.user) {
			navigate({ to: "/login" });
		}
	}, [session.data, session.isPending, navigate]);
```

**OURS**
```
	const navigate = useNavigate();
	const { data, isLoading } = $api.useSuspenseQuery("get", "/user/me");

	useEffect(() => {
		if (!isLoading && !data?.user) {
			navigate({ to: "/login" });
		}
	}, [data?.user, isLoading, navigate]);
```

**THEIRS**
```
	useUser({ redirect: "unauthenticated" });
```

## 46. app/manage-parties/loading.tsx

pr_key `AbuAli85/extra-contracts-yy#12`, conflict_index `0`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import Loading from "../loading"
export default Loading
```

**THEIRS**
```
import { Loader2 } from "lucide-react"

export default function Loading() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
      <p className="ml-2 text-sm">Loading parties...</p>
    </div>
  )
}
```

## 47. frontend/tests/e2e/chat.spec.ts

pr_key `miladyboy/wingman#10`, conflict_index `2`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
  test("user can delete a single conversation", async ({
    page,
  }: {
    page: any;
  }) => {
    const { chatTitle: chatToDeleteTitle } = await createNewChat(page, 1);
    const { chatTitle: chatToKeepTitle } = await createNewChat(page, 2);
    const chatItemToDelete = page.getByTestId("chat-item").filter({
      has: page
        .getByTestId("chat-item-name")
        .filter({ hasText: chatToDeleteTitle }),
    });
```

**OURS**
```
  test("user can delete a single conversation", async ({
    subscribedUserPage: page,
  }) => {
    const { chatTitle: chatToDeleteTitle, threadId: chatToDeleteThreadId } =
      await createNewChat(page, 1);
    const { chatTitle: chatToKeepTitle, threadId: chatToKeepThreadId } =
      await createNewChat(page, 2);
    const chatItemToDelete = page.locator(
      `[data-testid="chat-item"][data-thread-id="${chatToDeleteThreadId}"]`
    );
```

**THEIRS**
```
  test("user can delete a single conversation", async ({ subscribedUserPage: page }: { subscribedUserPage: Page }) => {
    const { chatTitle: chatToDeleteTitle } = await createNewChat(page, 1);
    const { chatTitle: chatToKeepTitle } = await createNewChat(page, 2);
    const chatItemToDelete = page.getByTestId("chat-item").filter({
      has: page
        .getByTestId("chat-item-name")
        .filter({ hasText: chatToDeleteTitle }),
    });
```

## 48. server/db/cache.ts

pr_key `Geminitic/RCF_Website#139`, conflict_index `0`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
// eslint-disable-next-line @typescript-eslint/no-var-requires
const MockRedis = process.env.NODE_ENV === 'test' ? require('ioredis-mock') : null;
```

**OURS**
```

const RedisMock = process.env.NODE_ENV === 'test' ? MockRedis : null;
```

**THEIRS**
```
 
// eslint-disable-next-line @typescript-eslint/no-require-imports
const MockRedis = process.env.NODE_ENV === 'test' ? require('ioredis-mock') : null;
```

## 49. src/components/fantasy/FantasyGameEngine.tsx

pr_key `toshiotawa/jazzify-lab#114`, conflict_index `0`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  // ★ 追加: Ready フェーズ中フラグ
  isReady?: boolean;
```

**THEIRS**
```
  fantasyPixiInstance?: any; // PIXIインスタンスへの参照
}

// 戻り値の型定義
interface FantasyGameEngineReturn {
  gameState: FantasyGameState;
  handleNoteInput: (note: number, isPress: boolean) => void;
  initializeGame: (stage: FantasyStage) => void;
  stopGame: () => void;
  proceedToNextEnemy: () => void;
  calculateDamage: (baseValue: number, isSpecial: boolean) => number;
  ENEMY_LIST: typeof ENEMY_LIST;
```

## 50. tura-wallet/src/lib/wallet_manager.ts

pr_key `xiayuhkust/TuraAgent_Web3_New#22`, conflict_index `1`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
        createdAt: new Date().toISOString()
```

**OURS**
```
        privateKey: account.privateKey,
        mnemonic: mnemonic,
        createdAt: new Date().toISOString()
```

**THEIRS**
```
        createdAt: new Date().toISOString(),
        mnemonic: wallet.mnemonic?.phrase
```

## 51. src/i18n.ts

pr_key `beriman/www.SensasiWangi.id#29`, conflict_index `0`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import id from './locales/id.json';

const savedLang = typeof window !== 'undefined' ? localStorage.getItem('lang') : null;

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    id: { translation: id },
  },
  lng: savedLang || 'id',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
```

**THEIRS**
```
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import id from './locales/id.json';

const resources = {
  en: { translation: en },
  id: { translation: id },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('lng') || 'id',
    fallbackLng: 'id',
    interpolation: { escapeValue: false },
  });

export default i18n;
```

## 52. WeedGrowApp/app/add-plant/step1.tsx

pr_key `Supergoku109/WeedGrow#29`, conflict_index `0`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
  const { name, strain, growthStage, setField } = usePlantForm();
  const theme = useColorScheme() ?? 'dark';
```

**OURS**
```
  const { name, strain, growthStage, ageDays, setField } = usePlantForm();
  type Theme = keyof typeof Colors;
  const theme = (useColorScheme() ?? 'dark') as Theme;
```

**THEIRS**
```
  const { name, strain, growthStage, setField } = usePlantForm();
  const theme: Theme = useColorScheme() ?? 'dark';
```

## 53. src/core/comparator.ts

pr_key `logickal/sitediff#3`, conflict_index `0`, AST verdict `content_changed`, picked because signature lines differ between the sides

**BASE**
```
  for (const pathKey of Object.keys(prodPages)) {
```

**OURS**
```
  const concurrency = options.concurrency ?? os.cpus().length;
  const limit = pLimit(concurrency);

  const paths = allPaths ?? [...new Set([...Object.keys(prodPages), ...Object.keys(testPages)])];

  await Promise.all(paths.map(pathKey => limit(async () => {
```

**THEIRS**
```
  const keys = Object.keys(prodPages);

  await Promise.all(keys.map(async pathKey => {
```

## 54. src/games/dungeon-rpg/DungeonView.ts

pr_key `dainei-makino/dungeon-survival-rpg#12`, conflict_index `6`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
      return (currentY - pos.y + (1 - stepY) / 2) / (rayDirY === 0 ? 1e-6 : rayDirY)
```

**OURS**
```
      dist =
        (currentY - pos.y + (1 - stepY) / 2) / (rayDirY === 0 ? 1e-6 : rayDirY)
```

**THEIRS**
```
      return {
        dist: (currentY - pos.y + (1 - stepY) / 2) / (rayDirY === 0 ? 1e-6 : rayDirY),
        hitX: currentX,
        hitY: currentY,
      }
```

## 55. backend/src/routes/tickets.ts

pr_key `CamileALTEN/CAF_Trainer_JSON#21`, conflict_index `0`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
router.get('/', (_req, res) => {
  res.json(load());
```

**OURS**
```
router.get('/', (req, res) => {
  const q = (req.query.search as string)?.toLowerCase();
  const list = load().filter(t => !t.archived);
  if (q) {
    return res.json(
      list.filter(
        t =>
          t.title.toLowerCase().includes(q) ||
          t.message.toLowerCase().includes(q) ||
          t.replies.some(r => r.message.toLowerCase().includes(q))
      )
    );
  }
  res.json(list);
```

**THEIRS**
```
router.get('/', (req, res) => {
  const { username, role, managerId } = req.query as {
    username?: string;
    role?: 'admin' | 'manager' | 'caf';
    managerId?: string;
  };
  let list = load();
  if (role === 'caf' && username) {
    list = list.filter(t => t.username === username);
  } else if (role === 'manager') {
    list = list.filter(t => t.username === username || t.managerId === managerId);
  }
  res.json(list);
```

## 56. packages/server/src/app.ts

pr_key `vskrch/AIOStreams#4`, conflict_index `1`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
apiRouter.use('/rpdb', rpdbApi);
apiRouter.use('/top-poster', topPosterApi);
apiRouter.use('/oauth/exchange/gdrive', gdriveApi);
apiRouter.use('/debrid', debridApi);
if (Env.ENABLE_SEARCH_API) {
  apiRouter.use('/search', searchApi);
}
apiRouter.use('/anime', animeApi);
apiRouter.use('/proxy', proxyApi);
apiRouter.use('/templates', templatesApi);
```

**THEIRS**
```
apiRouter.use('/cache', cacheApi);
```

## 57. apps/frontend/src/services/projectsApi.ts

pr_key `Parketsense/erp-review#1`, conflict_index `1`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
    return response.json();
```

**OURS**
```
    const result = await response.json();
    // Backend returns { success, data, pagination }
    return {
      data: result.data || [],
      meta: {
        total: result.pagination?.total || 0,
        page: result.pagination?.page || 1,
        limit: result.pagination?.limit || 50,
        totalPages: result.pagination?.totalPages || 1,
      },
    };
```

**THEIRS**
```
    const result = await response.json();
    return result; // Backend returns { success, data, pagination }
```

## 58. packages/core/src/utils/env.ts

pr_key `vskrch/AIOStreams#4`, conflict_index `0`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  STREAM_CACHE_MAX_SIZE: num({
    default: undefined,
    desc: 'Max number of stream items to cache',
  }),
```

**THEIRS**
```
  STREAM_CACHE_REFRESH_COUNT: num({
    default: 0,
    desc: 'Number of times to refresh stream cache when it expires',
  }),
```

## 59. components/token-table.tsx

pr_key `0xFuckTheFeds/Dashcoin#91`, conflict_index `2`, AST verdict `content_changed`, picked because null markers differ between the sides

**BASE**
```
                        const val = raw !== undefined && raw !== '' ? parseInt(raw) : null
                        const display = val === 2 ? 'Yes' : val === 1 ? 'No' : '-'
```

**OURS**
```
                        const display = raw !== undefined && raw !== '' ? raw : '-'
```

**THEIRS**
```
                        const val = raw !== undefined && raw !== '' ? valueToScore(raw, (gradeMaps as any)[label]) : null
                        const display = val === 2 ? 'Yes' : val === 1 ? 'No' : '-'
```

## 60. scripts/weekly-git-summary.ts

pr_key `yinzhenyu-su/weekly-git-summary#1`, conflict_index `5`, AST verdict `content_changed`, picked because control flow lines differ between the sides

**BASE**
```
      // 添加当前提交
      dateCommits!.commits.push({
        message: message,
        author: author,
        hash: hash,
      });
```

**OURS**
```
      // 添加当前提交
      dateCommits!.commits.push(commitData)
```

**THEIRS**
```
    // 转换为所需格式，按日期排序
    const sortedDates = Array.from(commitsByDate.keys()).sort().reverse();
    for (const date of sortedDates) {
      const dateCommits = commitsByDate.get(date)!;
      repoData.commits.push({
        date,
        commits: dateCommits,
      });
```

