# Regions to hand label, batch 3

50 random dev regions that reach the model on the current rules, seed 20261110, none of them in batch 1 or batch 2. Each region is under 1500 characters of base, ours and theirs together, the same rule as batch 1, so batch 1 and batch 3 can be scored together.

Dev has 2131 regions that reach the model and 1430 of them pass the size rule and are not labeled yet. This is a random sample of short regions, not of all regions, so say so next to any accuracy number from it.

Fatima labels all 50 regions, by hand and without AI help, because this batch is the answer key for scoring. Regions 61 to 70 are shared: Aneeza also labels them on her own, and the two sets are compared to measure agreement and settle tie breaks. Neither person looks at the other's labels for 61 to 70 until both are done.

Do not use any of these regions as a few shot example, because this batch is for scoring.

The AST verdict shown is the one after the guards, the same one the model sees in a real run.

## 61. src/components/index.ts

pr_key `shchilkin/PopChoice#27`, conflict_index `0`, AST verdict `content_changed`, shared by both

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
export * from './QuestionsForm';
export * from './TopNavigation';
```

**THEIRS**
```
export * from './LocaleSwitcher';
```

## 62. src/app/app.component.ts

pr_key `rodmjay/ByteBistro#2`, conflict_index `0`, AST verdict `content_changed`, shared by both

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import { CacheHierarchySimulationComponent } from './cache-hierarchy-simulation/cache-hierarchy-simulation.component';
import { MemoryTlbSimulationComponent } from './memory-tlb-simulation/memory-tlb-simulation.component';
import { RxjsMergeSimulationComponent } from './rxjs-merge-simulation/rxjs-merge-simulation.component';
```

**THEIRS**
```
import { TcpSimulationComponent } from './tcp-simulation/tcp-simulation.component';
```

## 63. src/workers/otlpJsonParser.worker.ts

pr_key `deepaucksharma/otel-metrics-explorer#8`, conflict_index `0`, AST verdict `content_changed`, shared by both

**BASE**
```
        // Extract datapoints based on metric type
        const dataPoints = extractDataPoints(metric, metricType, options.includeZeroValues);
        
        // Collect all unique attribute keys from datapoints
```

**OURS**
```
        // Extract datapoints based on metric type
        const dataPoints = extractDataPoints(metric, metric.name, metricType, options.includeZeroValues);
        
        // Collect all unique attribute keys from datapoints
```

**THEIRS**
```
        // Extract datapoints while collecting attribute keys
```

## 64. src/client/hooks/useTimelineData.ts

pr_key `esnya/blobloom#409`, conflict_index `1`, AST verdict `content_changed`, shared by both

**BASE**
```
    (id: string, parent?: string) => {
```

**OURS**
```
    (ts: number, parent?: string) => {
      if (lastTimestampRef.current === ts) return;
```

**THEIRS**
```
    (id: string, parent?: string) => {
      if (lastIdRef.current === id) return;
```

## 65. src/mock/users.ts

pr_key `Typefacers/bug#65`, conflict_index `1`, AST verdict `content_changed`, shared by both

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
    survivor: false,
```

**THEIRS**
```
    badges: [],
```

## 66. web/components/voice/userealtime.tsx

pr_key `sethjuarez/sustineo#30`, conflict_index `1`, AST verdict `content_changed`, shared by both

**BASE**
```
      await voiceRef.current.send({
        id: user.key,
        type: "settings",
        settings: {
          user: user!.name,
          date: currentDate.toLocaleDateString(),
          time: currentDate.toLocaleTimeString(),
          threshold: settings.threshold,
          silence: settings.silence,
          prefix: settings.prefix,
        },
      });
```

**OURS**
```
      const values: SettingsUpdate = {
        id: user.key,
        type: "settings",
        settings: {
          user: user!.name,
          date: currentDate.toLocaleDateString(),
          time: currentDate.toLocaleTimeString(),
          detection_type: settings.detectionType,
          transcription_model: settings.transcriptionModel,
          threshold: settings.threshold,
          silence_duration: settings.silenceDuration,
          prefix_padding: settings.prefixPadding,
          eagerness: settings.eagerness,
          voice: settings.voice,
        },
      };

      console.log("Sending settings", values);

      await voiceRef.current.send(values);
```

**THEIRS**
```
      await voiceRef.current.sendUserMessage(JSON.stringify(message));
```

## 67. scripts/weekly-git-summary.ts

pr_key `yinzhenyu-su/weekly-git-summary#1`, conflict_index `2`, AST verdict `content_changed`, shared by both

**BASE**
```
    since: string;
    until: string;
  };
  searchDir: string;
  author?: string;
  repositories: RepoData[];
```

**OURS**
```
    since: string
    until: string
  }
  searchDir: string
  author?: string
  messagePattern?: string
  conventional?: boolean
  statistics?: CommitStatistics
  repositories: RepoData[]
```

**THEIRS**
```
    since: string;
    until: string;
  };
  searchDir: string;
  author?: string;
  messagePattern?: string;
  statistics: Statistics;
  repositories: RepoData[];
```

## 68. pages/index.tsx

pr_key `tosi29/app#122`, conflict_index `4`, AST verdict `content_changed`, shared by both

**BASE**
```
      content: <BroadcastsContent />
```

**OURS**
```
      content: <BroadcastsContent 
                pastBroadcasts={pastBroadcasts}
                isLoadingBroadcasts={isLoadingBroadcasts}
                visibleEmbeds={visibleEmbeds}
                toggleEmbedVisibility={toggleEmbedVisibility}
                router={router}
              />
```

**THEIRS**
```
      content: <BroadcastsContent 
                 pastBroadcasts={pastBroadcasts}
                 isLoadingBroadcasts={isLoadingBroadcasts}
                 onPlayBroadcast={handlePlayBroadcast}
                 router={router}
               />
```

## 69. app/(apis)/login/route.ts

pr_key `drivly/ai#718`, conflict_index `0`, AST verdict `content_changed`, shared by both

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

## 70. src/components/home/CategoryGrid.tsx

pr_key `escape-ship/ui_test#7`, conflict_index `0`, AST verdict `content_changed`, shared by both

**BASE**
```
        <div key={cat.title} className="text-center">
          <img src={cat.img} alt={cat.title} className="rounded-lg mb-2 h-32 w-full object-cover" />
          <h3 className="font-semibold">{cat.title}</h3>
```

**OURS**
```
        <div key={cat.title} className="text-center space-y-2">
          <img
            src={cat.img}
            alt={cat.title}
            className="h-40 w-full rounded-lg object-cover"
          />
          <h3 className="text-lg font-medium text-primary">{cat.title}</h3>
```

**THEIRS**
```
        <div key={cat.title} className="text-center">
          <img
            src={cat.img}
            srcSet={`${cat.img} 1x, ${cat.img.replace('w=400', 'w=800')} 2x`}
            sizes="(min-width: 768px) 200px, 50vw"
            loading="lazy"
            alt={cat.title}
            className="rounded-lg mb-2 h-32 w-full object-cover"
          />
          <h3 className="font-semibold">{cat.title}</h3>
```

## 71. src/services/MultiAgentService.ts

pr_key `tysongreenan/copy-canvas-capture#19`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
      const fallbackResponse = this.createFallbackResponse(message, error.message);
```

**OURS**
```
      const fallbackResponse = this.createFallbackResponse(message, error.message, contextSnippet);
```

**THEIRS**
```
      const fallbackResponse = this.createFallbackResponse(message, error.message, memoryContext);
```

## 72. components/model-info.tsx

pr_key `louistrue/ifc-classifier#77`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
        {copyValue !== undefined && (
          <button onClick={handleCopy} className="opacity-60 hover:opacity-100">
            <Copy className="w-3 h-3" />
          </button>
        )}
```

**THEIRS**
```
        {copyable && propValue !== null && propValue !== undefined && (
          <button onClick={handleCopy} title={t('buttons.copy')} className="ml-1 hover:text-primary">
            <Copy className="w-3 h-3" />
          </button>
        )}
```

## 73. src/services/MultiAgentService.ts

pr_key `tysongreenan/copy-canvas-capture#19`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
  private static createFallbackResponse(query: string, errorMessage: string): string {
```

**OURS**
```
  private static createFallbackResponse(
    query: string,
    errorMessage: string,
    contextText?: string
  ): string {
```

**THEIRS**
```
  private static createFallbackResponse(query: string, errorMessage: string, context?: string): string {
```

## 74. app/api/team/members/route.ts

pr_key `cognoco/User-Mgmt#558`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
  let params;
  
  if (data) {
    // New approach: validated data is passed from middleware
    params = data;
  } else {
    // Legacy approach: parse and validate query params manually
    const query = Object.fromEntries(new URL(req.url).searchParams.entries());
    params = querySchema.parse(query);
  }
```

**OURS**
```
  const params = data;
```

**THEIRS**
```

```

## 75. client/src/app.tsx

pr_key `darwin-xu/vocab-app#40`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
    note?: string;
```

**THEIRS**
```
    note?: string | null;
```

## 76. src/pages/VerhuurderDashboard.tsx

pr_key `Cristiansotogarcia/huurly_1.0#40`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { demoLandlordProfiles, demoTenantProfiles } from '@/data/demoData';
```

**OURS**
```
import { propertyService } from '@/services/PropertyService';
import { userService } from '@/services/UserService';
import { viewingService } from '@/services/ViewingService';
```

**THEIRS**
```

```

## 77. app/api/team/route.ts

pr_key `cognoco/User-Mgmt#558`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
async function handleGet(_req: NextRequest, auth: RouteAuthContext) {
  const service = getApiTeamService();
  const teams = await service.getUserTeams(auth.userId!);
  return NextResponse.json({ teams });
}
```

**OURS**
```
async function handleGet(
  _req: Request,
  auth: AuthContext,
  _data: unknown,
  services: ServiceContainer
) {
  const teams = await services.team.getUserTeams(auth.userId!);
  return createSuccessResponse({ teams });
}
```

**THEIRS**
```
export const GET = createApiHandler(
  emptySchema,
  async (_req, { userId }, _data, services) => {
    if (!services.team) {
      throw new ApiError(ERROR_CODES.NOT_IMPLEMENTED, 'Team service not available');
    }
    const teams = await services.team.getUserTeams(userId!);
    return createSuccessResponse({ teams });
  },
  { requireAuth: true }
);
```

## 78. frontend/src/router.tsx

pr_key `RobboC1980/AGF#2`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
  
  console.log('requireAuth: Token exists, allowing access')
```

**OURS**
```

  if (isDevelopment) console.log('requireAuth: Token exists, allowing access')
```

**THEIRS**
```

```

## 79. components/ShiftCalendar.tsx

pr_key `xXJV10Xx/SkiftApp#16`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
  const getShiftColor = (shiftCode: string) => {
    if (shiftCode === 'L') return '#E8E8E8'; // Ledig = grå
    
    const teamColor = company.colors[team];
    if (teamColor) return teamColor;
    
    // Standardfärger för skift
    const shiftColors: Record<string, string> = {
      'M': '#FF6B6B', // Morgon = röd
      'A': '#4ECDC4', // Kväll = turkos
      'N': '#45B7D1', // Natt = blå
      'F': '#96CEB4', // Förmiddag = grön
      'E': '#FFA502', // Eftermiddag = orange
      'D': '#9B59B6'  // Dag = lila
    };
    
    return shiftColors[shiftCode] || '#95A5A6';
```

**OURS**
```
  // Formatera månadsnamn på svenska
  const getMonthName = (date: Date) => {
    return date.toLocaleDateString('sv-SE', { month: 'long', year: 'numeric' });
```

**THEIRS**
```
  const getShiftColor = (shiftCode: string, teamName?: string) => {
    if (shiftCode === 'L') return '#E8E8E8'; // Ledig = grå
    
    if (teamName && company.colors[teamName]) {
      return company.colors[teamName];
    }
    
    const teamColor = company.colors[team];
    if (teamColor) return teamColor;
    
    // Standardfärger för skift
    const shiftColors: Record<string, string> = {
      'M': '#FF6B6B', // Morgon = röd
      'A': '#4ECDC4', // Kväll = turkos
      'N': '#45B7D1', // Natt = blå
      'F': '#96CEB4', // Förmiddag = grön
      'E': '#FFA502', // Eftermiddag = orange
      'D': '#9B59B6'  // Dag = lila
    };
    
    return shiftColors[shiftCode] || '#95A5A6';
```

## 80. client/src/lib/subscriber.ts

pr_key `kota-yata/moqtail#51`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  public warpCatalogManager: WarpCatalogManager = new WarpCatalogManager();
```

**THEIRS**
```
  private asciiElement?: HTMLElement;
  private asciiWidth = 80;
  private asciiHeight = 60;
```

## 81. app/layout.tsx

pr_key `RaptorLaunchPage/Module#135`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
            <AgreementProvider>
              <RequireAuth>
                <AgreementRouteGuard>
                  {children}
                </AgreementRouteGuard>
              </RequireAuth>
              <AgreementModal />
            </AgreementProvider>
```

**OURS**
```
            <AgreementProvider>
              <AgreementRouteGuard>
                {children}
              </AgreementRouteGuard>
              <AgreementModal />
            </AgreementProvider>
```

**THEIRS**
```
            <RouteGuard>
              {children}
            </RouteGuard>
```

## 82. src/app/features/administracion/administracion.module.ts

pr_key `CarlosServin18/vending-manager#13`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import { Menu } from './menu/menu';
```

**THEIRS**
```
import { AdministracionMenu } from './pages/menu/menu';
```

## 83. components/model-info.tsx

pr_key `louistrue/ifc-classifier#76`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
      <div
        className="text-xs truncate text-right font-medium"
        title={
          typeof propValue === "string" || typeof propValue === "number"
            ? String(propValue)
            : undefined
        }
      >
```

**OURS**
```
      <div
        className="text-xs truncate text-right font-medium flex items-center justify-end gap-1"
        title={
          typeof propValue === "string" || typeof propValue === "number"
            ? String(propValue)
            : undefined
        }
      >
```

**THEIRS**
```
      <div className="text-xs truncate text-right font-medium flex items-center justify-end" title={typeof propValue === 'string' || typeof propValue === 'number' ? String(propValue) : undefined}>
```

## 84. src/workers/otlpJsonParser.worker.ts

pr_key `deepaucksharma/otel-metrics-explorer#8`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
        dataPoints.forEach(dp => {
          if (dp.attributes) {
            Object.keys(dp.attributes).forEach(key => attributeKeysSet.add(key));
          }
        });
```

**OURS**
```
        const uniqueSeriesKeys = new Set<string>();
        dataPoints.forEach(dp => {
          if (dp.attributes) {
            Object.keys(dp.attributes).forEach(key => attributeKeysSet.add(key));
          }
          if (dp.seriesKey) uniqueSeriesKeys.add(dp.seriesKey);
        });
```

**THEIRS**
```
        const dataPoints = extractDataPoints(
          metric,
          metricType,
          options.includeZeroValues,
          attributeKeysSet
        );
```

## 85. src/__tests__/hooks/usePlayer.test.ts

pr_key `esnya/blobloom#386`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { usePlayer } from '../../client/hooks/usePlayer';
import { createPlayer } from '../../client/player';

jest.mock('../../client/player');
```

**OURS**
```
import { usePlayer } from '../../client/hooks/usePlayer';
```

**THEIRS**
```
import * as playerHook from '../../client/hooks/usePlayer';

const { usePlayer } = playerHook;

let createPlayer: jest.SpiedFunction<typeof playerHook.createPlayer>;
```

## 86. src/components/fantasy/FantasyMain.tsx

pr_key `toshiotawa/jazzify-lab#110`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  }, [isGuest, profile, currentStage]);
  
  // ステージ選択に戻る
  const handleBackToStageSelect = useCallback(() => {
    setCurrentStage(null);
    setGameResult(null);
    setShowResult(false);
    setPendingAutoStart(false); // pendingAutoStart もリセット
  }, []);
  
  // ★ 追加: 次のステージに待機画面で遷移
  const gotoNextStageWaiting = useCallback(() => {
    if (!currentStage) return;
    const [rank, num] = currentStage.stageNumber.split('-').map(Number);
    const nextStageNumber = `${rank}-${num + 1}`;
```

**OURS**
```

```

**THEIRS**
```
  }, [isGuest, profile, currentStage]);
  
  // ステージ選択に戻る
  const handleBackToStageSelect = useCallback(() => {
    setCurrentStage(null);
    setGameResult(null);
    setShowResult(false);
    setPendingAutoStart(false); // pendingAutoStart もリセット
  }, []);
  
  // ステージ番号計算用のヘルパー関数
  const COURSE_LENGTH = 5; // テスト用：5、本番用：10に変更

  const getNextStageNumber = useCallback((current: string): string => {
    const [rank, num] = current.split('-').map(Number);
    const nextNum = num >= COURSE_LENGTH ? 1 : num + 1;
    const nextRank = num >= COURSE_LENGTH ? rank + 1 : rank;
    return `${nextRank}-${nextNum}`;
  }, []);

  // ★ 追加: 次のステージに待機画面で遷移（データベースから実データを取得）
  const gotoNextStageWaiting = useCallback(async () => {
    if (!currentStage) return;
    
    const nextStageNumber = getNextStageNumber(currentStage.stageNumber);
```

## 87. src/app/(app)/patients/[id]/page.tsx

pr_key `brunenrique/studio#124`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  const { user } = useAuth();
```

**THEIRS**
```
  const { isLoading, hasRole } = useRequireRole('Psicólogo');
```

## 88. src/games/dungeon-rpg/DungeonView.ts

pr_key `dainei-makino/dungeon-survival-rpg#12`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
      `Keys: ${pressed}\nPos: ${this.player.x},${this.player.y}\nDir: ${this.player.dir}`
```

**OURS**
```
      `Keys: ${pressed}\n` +
        `Pos: ${this.player.x},${this.player.y}\n` +
        `Dir: ${this.player.dir}\n` +
        `HP: ${this.hero.hp}\n` +
        `STR: ${this.hero.strength}`
```

**THEIRS**
```
      `Keys: ${pressed}\nPos: ${this.player.x},${this.player.y},${this.player.z}\nDir: ${this.player.dir}`
```

## 89. hooks/useConnection.ts

pr_key `ilyavolodin/metatool-app#9`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
      const proxyHealthUrl = new URL(
        process.env.USE_DOCKER_HOST === 'true'
          ? `http://host.docker.internal:12007/health`
          : `http://localhost:12007/health`
      );
      logger.log('Checking proxy health', proxyHealthUrl.toString());
```

**OURS**
```
      const proxyHealthUrl = '/api/proxy-health';
      logger.log('Checking proxy health via', proxyHealthUrl);
```

**THEIRS**
```
      const baseUrl =
        process.env.NEXT_PUBLIC_MCP_PROXY_URL ||
        (process.env.USE_DOCKER_HOST === 'true'
          ? 'http://host.docker.internal:12007'
          : 'http://localhost:12007');
      const proxyHealthUrl = `${baseUrl}/health`;
      logger.log('Checking proxy health via', proxyHealthUrl);
```

## 90. app/src/pages/ContentItemPage.tsx

pr_key `Ziinc/yunokit#40`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
    currentWorkspace && contentItemData?.schema_id ? `schema-${contentItemData.schema_id}` : null,
    () => getSchema(contentItemData?.schema_id!, currentWorkspace!.id),
```

**OURS**
```
    currentWorkspace && (contentItemData?.schema_id || schemaIdNumber) ? 
      `schema-${contentItemData?.schema_id || schemaIdNumber}` : null,
    () => {
      const targetSchemaId = contentItemData?.schema_id || schemaIdNumber;
      if (targetSchemaId && currentWorkspace) {
        return getSchema(targetSchemaId, currentWorkspace.id);
      }
      return null;
    },
```

**THEIRS**
```
    currentWorkspace && contentItemData?.schema_id ? `schema-${contentItemData.schema_id}` : null,
    () => getSchema(contentItemData!.schema_id, currentWorkspace!.id),
```

## 91. src/infrastructure/openai/OpenAIEmbeddingService.ts

pr_key `chollak/finance-tracker-backend#25`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import OpenAI from 'openai';

export class OpenAIEmbeddingService {
    private readonly openai: OpenAI;

    constructor(apiKey: string) {
        this.openai = new OpenAI({ apiKey });
    }

    async embed(text: string): Promise<Float32Array> {
        const response = await this.openai.embeddings.create({
            model: 'text-embedding-3-small',
            input: text,
        });
        const embedding = response.data[0]?.embedding ?? [];
        return new Float32Array(embedding);
    }
}

```

**THEIRS**
```
import OpenAI from 'openai';

export class OpenAIEmbeddingService {
    private readonly openai: OpenAI;

    constructor(apiKey: string) {
        this.openai = new OpenAI({ apiKey });
    }

    async embed(text: string): Promise<number[]> {
        const response = await this.openai.embeddings.create({
            model: 'text-embedding-3-small',
            input: text,
        });
        const [first] = response.data;
        if (!first) {
            throw new Error('No embedding returned');
        }
        return first.embedding as unknown as number[];
    }
}
```

## 92. hooks/useConnectionMulti.ts

pr_key `ilyavolodin/metatool-app#9`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
      const proxyHealthUrl = new URL(
        process.env.USE_DOCKER_HOST === 'true'
          ? `http://host.docker.internal:12007/health`
          : `http://localhost:12007/health`
      );
```

**OURS**
```
      const proxyHealthUrl = '/api/proxy-health';
```

**THEIRS**
```
      const baseUrl =
        process.env.NEXT_PUBLIC_MCP_PROXY_URL ||
        (process.env.USE_DOCKER_HOST === 'true'
          ? 'http://host.docker.internal:12007'
          : 'http://localhost:12007');
      const proxyHealthUrl = `${baseUrl}/health`;
```

## 93. docs/src/app/layout.config.tsx

pr_key `onlook-dev/onlook#1859`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
        title: (
            <>
                Onlook Docs
            </>
        ),
```

**OURS**
```
        title: (
            <div className="flex items-center gap-2">
                <Icons.OnlookLogo className="w-4 h-4" />
                <span >Onlook Docs</span>
            </div>
        ),
```

**THEIRS**
```
        component: null, // Remove the default title and navigation
```

## 94. app/routes/sponsorship.tsx

pr_key `HackUCF/hackucf-remix#12`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  const turnstileRef = useRef<any>(null);

  useEffect(() => {
    if (actionData?.success) {
      setShowSuccessMessage(true);
      setFormData({
        firstName: '',
        lastName: '',
        email: '',
        message: '',
        company: '',
      });
      // Reset Turnstile if form submission was successful
      if (turnstileRef.current?.reset) {
        turnstileRef.current.reset();
      }
      const timer = setTimeout(() => setShowSuccessMessage(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [actionData]);

```

**OURS**
```
  const [turnstileToken, setTurnstileToken] = useState('');
  const turnstileRef = useRef<TurnstileInstance | null>(null);

```

**THEIRS**
```
  const [turnstileToken, setTurnstileToken] = useState('');
  const turnstileRef = useRef<any>(null);

```

## 95. app/components/ChatWelcome.tsx

pr_key `KLM-Solutions/dev-003#15`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
          src="/woodworking-illustration.png" 
          alt="Woodworking Illustration" 
```

**OURS**
```
          src="/bents-image.jpg" 
          alt="Woodworking Illustration" 
```

**THEIRS**
```
          src="/woodworking-animation.gif" 
          alt="Woodworking Animation" 
```

## 96. tests/rls/poster-boards.test.ts

pr_key `team-mirai-volunteer/action-board#843`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
          previous_status: "posted",
          new_status: "checked",
```

**OURS**
```
          previous_status: "reserved",
          new_status: "done",
```

**THEIRS**
```
          previous_status: "done",
          new_status: "done",
```

## 97. src/pages/database.tsx

pr_key `beriman/www.SensasiWangi.id#29`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
              Jelajahi koleksi lengkap brand, parfum, dan perfumer Indonesia
              dengan informasi detail dan ulasan dari komunitas
```

**OURS**
```
              {t('database.subtitle')}
```

**THEIRS**
```
              {t('database.headerSubtitle')}
```

## 98. src/pages/CommunityWallPage.tsx

pr_key `Geminitic/RCF_Website#120`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
                        <button className="flex items-center space-x-1 hover:text-blue-300 transition-colors">
```

**OURS**
```
                        <button
                          className="flex items-center space-x-1 hover:text-blue-300 transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedPhoto(photo);
                          }}
                        >
```

**THEIRS**
```
                        <button
                          onClick={() => alert('Feature coming soon!')}
                          className="flex items-center space-x-1 hover:text-blue-300 transition-colors"
                        >
```

## 99. src/components/MainPage.tsx

pr_key `LTplus-AG/NHMzh-plugin-cost#11`, conflict_index `24`, AST verdict `content_changed`

**BASE**
```
                <Typography
                  variant="h5"
                  component="p"
                  color="common.black"
                  fontWeight="bold"
                >
                  CHF{" "}
                  {displayTotalInSidebar.toLocaleString("de-CH", {
                    // Use displayTotalInSidebar
                    maximumFractionDigits: 0,
                  })}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Kostenschätzung (Berechnet{" "}
                  {processedCostData ? "aus IFC & Excel" : "aus Excel"})
```

**OURS**
```
                <Typography variant="h5" component="p" color="common.black" fontWeight="bold">
                  CHF {totalCost.toLocaleString("de-CH", { maximumFractionDigits: 0 })}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Kostenschätzung
```

**THEIRS**
```
                <Typography
                  variant="h5"
                  component="p"
                  color="common.black"
                  fontWeight="bold"
                >
                  CHF {totalCost.toLocaleString("de-CH", { maximumFractionDigits: 0 })}
```

## 100. instrumentation-client.ts

pr_key `drivly/ai#1931`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID) {
    window.dataLayer = window.dataLayer || []
    function gtag(...args: any[]) {
      window.dataLayer.push(args)
    }
    window.gtag = gtag
    gtag('js', new Date())
    gtag('config', process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID)

    const script = document.createElement('script')
    script.src = `https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID}`
    script.async = true
    document.head.appendChild(script)
  }
```

**OURS**
```

```

**THEIRS**
```
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID) {
    console.debug('Initializing Google Analytics with ID:', process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID);
    window.dataLayer = window.dataLayer || []
    function gtag(...args: any[]) {
      window.dataLayer.push(args)
    }
    window.gtag = gtag
    gtag('js', new Date())
    gtag('config', process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID)

    const script = document.createElement('script')
    script.src = `https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID}`
    script.async = true
    document.head.appendChild(script)
    script.onload = () => console.debug('Google Analytics script loaded successfully');
    script.onerror = (e) => console.error('Failed to load Google Analytics script:', e);
  }
```

## 101. components/party-form.tsx

pr_key `AbuAli85/extra-contracts-yy#13`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
        const { error } = await supabase.from("parties").update(partyData).eq("id", partyToEdit.id).select()
        if (error) throw error
```

**OURS**
```
        const { error } = await supabase
          .from("parties")
          .update(partyData)
          .eq("id", partyToEdit.id)
          .select()
        if (error) throw error
```

**THEIRS**
```
        await updateParty(partyToEdit.id, partyData)
```

## 102. src/apps/chats/components/ChatsAppComponent.tsx

pr_key `ryokun6/ryos#122`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import { CreateRoomDialog } from "./CreateRoomDialog";
```

**THEIRS**
```
import { PrivateRoomDialog } from "@/components/dialogs/PrivateRoomDialog";
```

## 103. components/leaderboard-section.tsx

pr_key `maxencefrenette/all-the-benchmarks#63`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
      <LeaderboardTable llmData={filtered} />
```

**OURS**
```
      <LeaderboardTable llmData={visible} />
```

**THEIRS**
```
      <LeaderboardTable llmData={tableData} />
```

## 104. src/store.ts

pr_key `Typefacers/bug#65`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
let stormTimer: ReturnType<typeof setInterval> | null = null
let stormBugIds: string[] = []
```

**THEIRS**
```
let apocalypseTimer: ReturnType<typeof setTimeout> | null = null
```

## 105. lib/api.ts

pr_key `drivly/ai#861`, conflict_index `8`, AST verdict `content_changed`

**BASE**
```
export const storeShareMapping = async (
  shareId: string, 
  requestId: string, 
  response: Record<string, any>,
  db: PayloadDB
): Promise<void> => {
```

**OURS**
```
export const storeShareMapping = async (shareId: string, requestId: string, response: Record<string, any>, db: PayloadDB): Promise<void> => {
```

**THEIRS**
```
const storeShareMapping = async (shareId: string, requestId: string) => {
```

## 106. src/pages/SchedulePage.tsx

pr_key `Markf1994/segretaria-digitale-frontend#274`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
      <ImportExcel />
```

**OURS**
```
      <ImportExcel onComplete={handleImportComplete} />
```

**THEIRS**
```
      <ImportExcel onImported={handleImport} />

      <label>Calendario</label>
      <select value={calendarId} onChange={e => setCalendarId(e.target.value)}>
        {CALENDAR_IDS.map(id => (
          <option key={id} value={id}>{id}</option>
        ))}
      </select>
```

## 107. portfolio/src/components/home/home.tsx

pr_key `kotama7/portfolio#75`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { useState, useEffect } from 'react';
```

**OURS**
```
import React, { useState, useEffect } from 'react';
```

**THEIRS**
```
import { useState, useEffect, useRef } from 'react';
```

## 108. src/index.ts

pr_key `darwin-xu/vocab-app#40`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
                    'SELECT * FROM vocab WHERE user_id = ? AND word LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?',
```

**OURS**
```
                    `
                    SELECT v.*, n.note 
                    FROM vocab v 
                    LEFT JOIN notes n ON v.user_id = n.user_id AND v.word = n.word 
                    WHERE v.user_id = ? AND v.word LIKE ? 
                    ORDER BY v.id DESC 
                    LIMIT ? OFFSET ?
                `,
```

**THEIRS**
```
                    'SELECT v.word, v.add_date, n.note FROM vocab v LEFT JOIN notes n ON v.user_id = n.user_id AND v.word = n.word WHERE v.user_id = ? AND v.word LIKE ? ORDER BY v.id DESC LIMIT ? OFFSET ?',
```

## 109. src/components/Dashboard/DashboardNavigation.tsx

pr_key `TotalTactiles/total-sales-ai#15`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
            const isActive = location.pathname === item.href || 
                           (item.href === '/sales-rep-dashboard' && location.pathname === '/');
```

**OURS**
```
            const isActive =
              location.pathname === item.href ||
              ((item.href === '/sales/dashboard' || item.href === '/manager/dashboard') &&
                location.pathname === '/');
```

**THEIRS**
```
            const isActive = location.pathname === item.href ||
                           (item.href === '/sales/dashboard' && location.pathname === '/');
```

## 110. src/map-generator/index.ts

pr_key `LarsDenBakker/larsworld#7`, conflict_index `6`, AST verdict `content_changed`

**BASE**
```
        y
```

**OURS**
```
        y,
        elevation,
        temperature,
        moisture
```

**THEIRS**
```
        y,
        elevation: Math.max(0, Math.min(1, elevation)),
        temperature: Math.max(0, Math.min(1, temperature)),
        rainfall: Math.max(0, Math.min(1, rainfall))
```
