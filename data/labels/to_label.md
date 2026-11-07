# Regions to hand label

30 random dev regions that reach the model, each under 1500 characters, seed 20261108

## 1. apps/ui/src/components/app-sidebar.tsx

pr_key `theopenco/llmgateway#237`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
	const { data: session, isPending: isLoading } = useSession();

	if (!session && !isLoading) {
```

**OURS**
```
	const { data, isLoading } = $api.useSuspenseQuery("get", "/user/me");

	if (!data?.user && !isLoading) {
```

**THEIRS**
```
	if ((!user && !isLoading) || isError) {
```

## 2. src/App.tsx

pr_key `HuberAndreas1/Dashboard-V2#1`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import DashboardHome from "@/components/pages/Home.tsx";
```

**THEIRS**
```
import StopGroups from "@/components/pages/stopgroups.tsx";
```

## 3. src/cli.ts

pr_key `justiceo/spectest#4`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
  const tests = await discoverSuites(cfg);
```

**OURS**
```
  const suites = await discoverSuites(cfg);
  const tests = suites.flatMap((suite) =>
    suite.tests.map((t) => ({ ...t, suiteName: suite.name }))
  );

  tests.forEach((t) => {
    if (!t.operationId) t.operationId = t.name;
  });
```

**THEIRS**
```
  const suites = await discoverSuites(cfg);
  const tests = suites.flatMap((suite) =>
    suite.tests.map((t) => ({ ...t, suiteName: suite.name }))
  );
```

## 4. components/ConcentrationInputStep.tsx

pr_key `rodneyg/SafeDose#53`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import React from 'react';
```

**OURS**
```
import React, { useEffect } from 'react';
```

**THEIRS**
```
import React, { useEffect, useState } from 'react';
```

## 5. apps/web/app/(landing-page)/components/SubFeaturesSection/SubFeaturesSection.tsx

pr_key `xXValhallaCoderXx/sentiment-hound-v2#21`, conflict_index `7`, AST verdict `content_changed`

**BASE**
```
      "They’re popular, but they’re rare. Trainers who show them off recklessly may be targeted by thieves",
```

**OURS**
```
      "Deploy anywhere with our cloud-native architecture. Scale effortlessly as your data needs grow.",
```

**THEIRS**
```
      "Generate detailed reports with actionable insights and visualizations that help you understand sentiment trends at a glance.",
    color: "violet",
```

## 6. src/lib/api/error-handler.ts

pr_key `cognoco/User-Mgmt#520`, conflict_index `0`, AST verdict `identifier_rename_only`, renames `{"BILLING_ERROR_CODES": "SSO_ERROR_CODES"}`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  BILLING_ERROR_CODES,
```

**THEIRS**
```
  SSO_ERROR_CODES,
```

## 7. apps/web-app/src/routeTree.gen.ts

pr_key `AsyncStatus/asyncstatus#15`, conflict_index `3`, AST verdict `identifier_rename_only`, renames `{"OrganizationSlugLayoutOldRoute": "OrganizationSlugLayoutProfileRoute"}`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  OrganizationSlugLayoutOldRoute: typeof OrganizationSlugLayoutOldRoute
```

**THEIRS**
```
  OrganizationSlugLayoutProfileRoute: typeof OrganizationSlugLayoutProfileRoute
```

## 8. src/App.tsx

pr_key `champierre/chess#32`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
        console.error('Failed to save username to localStorage:', error);
```

**OURS**
```
        console.error('Failed to save Chess.com username to localStorage:', error);
```

**THEIRS**
```
        console.error('Failed to save usernames to localStorage:', error);
```

## 9. src/app/services/device.service.ts

pr_key `p4cm4n972/verstack-ihm#32`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
    if (isPlatformBrowser(this.platformId)) {
      return this.mobileRegex.test(navigator.userAgent);
    }
    return false;
```

**OURS**
```
    if (!this.isBrowser) {
      return false;
    }
    return this.mobileRegex.test(navigator.userAgent);

```

**THEIRS**
```
    return this.mobileRegex.test(navigator.userAgent);
```

## 10. src/app/features/administracion/administracion-routing.module.ts

pr_key `CarlosServin18/vending-manager#13`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { UsuariosModule } from './usuarios/usuarios.module';

```

**OURS**
```
import { Menu } from './menu/menu';
```

**THEIRS**
```
import { AdministracionMenu } from './pages/menu/menu';
```

## 11. src/pages/Register.tsx

pr_key `IskenderDev/Rental_bike#11`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
					<CardDescription className="font-inter">
						Enter your information below to create to your account!
					</CardDescription>
```

**OURS**
```
                                        <CardDescription className="font-inter">
                                                Заполните форму для создания аккаунта
                                        </CardDescription>
```

**THEIRS**
```
                                        <CardDescription className="font-inter">
                                                Введите свои данные, чтобы создать аккаунт
					</CardDescription>
```

## 12. src/bundle/partial.ts

pr_key `Cap-go/CLI#399`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
      const filePathUnixSafe = encodePathSegments(filePathUnix)
      const filename = `orgs/${orgId}/apps/${appId}/${name}/${filePathUnixSafe}`
```

**OURS**
```

      // Determine the upload path (with or without .br extension)
      let uploadPathUnix = filePathUnix
      // Only add .br extension if file was actually compressed with brotli
      if (isBrotli) {
        uploadPathUnix = `${filePathUnix}.br`
        brFilesCount++
      }

      const filePathUnixSafe = encodePathSegments(uploadPathUnix)
      const filename = `orgs/${orgId}/apps/${appId}/${name}/${filePathUnixSafe}`
```

**THEIRS**
```
      const filePathUnixSafe = encodePathSegments(filePathUnix)
      const filePathWithExtension = compressed ? `${filePathUnixSafe}.br` : filePathUnixSafe
      const filename = `orgs/${orgId}/apps/${appId}/${name}/${filePathWithExtension}`
```

## 13. lib/db/helpers/01-core-to-parts.ts

pr_key `skalingclouds/ai-chatbot#3`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
const client = postgres(process.env.POSTGRES_URL);
const db = drizzle(client);
```

**OURS**
```
// if (!process.env.POSTGRES_URL) {
//   throw new Error('POSTGRES_URL environment variable is not set');
// }
```

**THEIRS**
```
const client = postgres(DB_URL);
const db = drizzle(client);
```

## 14. src/encounters/EncounterManager.ts

pr_key `MisterFlask/PhaserCardGame#2`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import { ImperialAuditorWraith } from './monsters/act2_segment2/ImperialAuditorWraith';
```

**THEIRS**
```
import { ZeppelinGrenadier } from './monsters/act2_segment2/ZeppelinGrenadier';
```

## 15. src/ai/PerformanceAnalyzer.ts

pr_key `cgbarlow/sasi#54`, conflict_index `1`, AST verdict `identifier_rename_only`, renames `{"rerenderRisk": "renderingTime", "domManipulation": "repaints", "layoutThrashing": "reflows"}`

**BASE**
```
  private calculateRenderingMetrics(issues: PerformanceIssue[]): any {
```

**OURS**
```
  private calculateRenderingMetrics(issues: PerformanceIssue[]): { rerenderRisk: number; domManipulation: number; layoutThrashing: number } {
```

**THEIRS**
```
  private calculateRenderingMetrics(issues: PerformanceIssue[]): { renderingTime: number; repaints: number; reflows: number } {
```

## 16. apps/web/app/(landing-page)/components/FaqSection/FaqSection.tsx

pr_key `xXValhallaCoderXx/sentiment-hound-v2#21`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
    <Container size="sm" className={classes.wrapper}>
      <Title ta="center" className={classes.title}>
        Frequently Asked Questions
      </Title>
```

**OURS**
```
    <div className={classes.faqBackground}>
      <Container size="sm" className={classes.wrapper}>
        <Title ta="center" className={classes.title}>
          Frequently Asked Questions
        </Title>
```

**THEIRS**
```
    <Box className={classes.sectionWrapper}>
      <Container size="md" className={classes.wrapper}>
        <Title ta="center" className={classes.title}>
          Frequently Asked Questions
        </Title>
        
        <Text size="sm" c="dimmed" ta="center" mb="xl" className={classes.subtitle}>
          Get answers to common questions about our sentiment analysis platform.
        </Text>
```

## 17. store/chat/index.ts

pr_key `rakansens/tradechat-mvp#44`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
export const createChatSlice = (
  set: (fn: (state: ChatSliceState) => void) => void,
  get: () => ChatSliceState
): ChatSlice => {
  // アクションを作成
  const actions = createChatActions(set, get)

  // 状態とアクションを組み合わせたスライスを返す
  return {
    ...initialChatState,
    ...actions
```

**OURS**
```
export const createChatSlice = createSlice<ChatSliceState, ChatSliceActions>(
  (set, get) => {
    const actions = createChatActions(set, get)
    return {
      ...initialChatState,
      ...actions
    }
```

**THEIRS**
```
export const createChatSlice = (
  set: (fn: (state: ChatSliceState) => void) => void,
  get: () => ChatSliceState,
  deps: ChatActionDeps
): ChatSlice => {
  // アクションを作成
  const actions = createChatActions(set, get, deps)

  // 状態とアクションを組み合わせたスライスを返す
  return {
    ...initialChatState,
    ...actions
```

## 18. src/app/core/component/shop/shop.component.ts

pr_key `p4cm4n972/verstack-ihm#32`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
    this.products = this.productsService.getProducts();


    this.updatePagedProducts();

    if (isPlatformBrowser(this.platformId)) {
      setTimeout(() => {
        if (!this.isLoadingAll) {
          this.isLoadingAll = true;
        }
      }, 1000);
    }
```

**OURS**
```
    this.products = this.productsService.getProducts();

    
    this.updatePagedProducts();

```

**THEIRS**
```
  this.productsService.getProducts().subscribe({
    next: (products) => {
      this.products = products;
      this.filteredProducts = products;
      if (!this.isLoadingAll) {
        this.isLoadingAll = true;
      }// Notifier Angular que les données ont changé
      this.cdr.markForCheck(); 
      this.updatePagedProducts();
      if (this.isBrowser) {
        this.shopifyLoader.load().catch(() => {});
      }
    },
    error: (err) => {
      console.error('Erreur lors du chargement des produits:', err);
    }
  })


   
```

## 19. app/tokendetail/[symbol]/page.tsx

pr_key `0xFuckTheFeds/Dashcoin#222`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import { Navbar } from "@/components/navbar";
import Image from "next/image";
```

**THEIRS**
```
import { Navbar } from "@/components/navbar";
```

## 20. cli/tests/cli.test.ts

pr_key `OmniScriptOSF/omniscript-core#8`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```

// format
const fmt = execFileSync('node', [cli, 'format', file], { encoding: 'utf8' });
if (!fmt.includes('@doc')) {
  throw new Error('format failed');
}

// render html
const html = execFileSync('node', [cli, 'render', file, '--format', 'html'], { encoding: 'utf8' });
if (!html.includes('<html>')) {
  throw new Error('render failed');
}
```

**THEIRS**
```
const sheet = result.blocks.find(b => b.type === 'sheet');
if (!Array.isArray(sheet.cols)) {
  throw new Error('sheet cols not parsed');
}
if (!sheet.formulas || sheet.formulas[0].expr !== '=A1') {
  throw new Error('sheet formula missing');
}
const slide = result.blocks.find(b => b.type === 'slide');
if (!slide || slide.bullets[1] !== 'Second') {
  throw new Error('slide bullets missing');
}
```

## 21. src/pages/Register.tsx

pr_key `IskenderDev/Rental_bike#11`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
											placeholder="example@gmail.com"
```

**OURS**
```
                                                                               placeholder="primer@gmail.com"
```

**THEIRS**
```
                                                                               placeholder="пример@gmail.com"
```

## 22. web/src/stores/__tests__/GlobalChatStore.test.ts

pr_key `nodetool-ai/nodetool#96`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
    (supabase.auth.getSession as jest.Mock).mockResolvedValue({ data: { session: null } });
```

**OURS**
```
    (supabase.auth.getSession as jest.Mock).mockResolvedValue({
      data: { session: null }
    });

    // Ensure any existing connections are cleaned up
    const currentSocket = (store.getState() as any).socket;
    if (currentSocket) {
      currentSocket.close();
    }
    const currentManager = (store.getState() as any).wsManager;
    if (currentManager) {
      currentManager.destroy();
    }

```

**THEIRS**
```
    (supabase.auth.getSession as jest.Mock).mockResolvedValue({
      data: { session: null }
    });

    // Create a new mock server for each test - this automatically mocks global WebSocket
    mockServer = new Server("ws://test/chat");

    // Ensure any existing socket is closed
    const currentSocket = store.getState().socket;
    if (currentSocket) {
      currentSocket.close();
    }

```

## 23. apps/web/app/(landing-page)/components/Footer/Footer.tsx

pr_key `xXValhallaCoderXx/sentiment-hound-v2#21`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
          © 2020 mantine.dev. All rights reserved.
```

**OURS**
```
          © {currentYear} Sentiment Hound. All rights reserved.
```

**THEIRS**
```
          © {new Date().getFullYear()} Sentiment Hound. All rights reserved.
```

## 24. web/app/routes/home.tsx

pr_key `sethjuarez/sustineo#30`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
        <Actions>
          <Tool
            icon={<TbClearAll size={18} />}
            onClick={() => {
              effort?.clearEfforts();
              output?.reset();
            }}
          />
          <Tool icon={<TbArticle size={18} />} onClick={() => addOutpuItem()} />
          <VoiceTool onClick={() => handleVoice()} />
        </Actions>
        <Settings>
          <Setting
            id={"voice-settings"}
            icon={<TbSettingsCog size={18} />}
            className={styles.voice}
          >
            <VoiceSettings />
          </Setting>
          <Setting
            id={"voice-agent-settings"}
            icon={<TbArticle size={18} />}
            className={styles.editor}
          >
            <AgentEditor />
          </Setting>
        </Settings>
      </main>
    </QueryClientProvider>
```

**OURS**
```
        <a href="/app">
          <div className={styles.micContainer}>
            <MicIcon 
              className={styles.micIcon}
              role="button"
              aria-label="Start recording"
              tabIndex={0}
            />
          </div>
        </a>
      </div>
    </div>
```

**THEIRS**
```
      </div>
    </div>
```

## 25. src/ai/PerformanceAnalyzer.ts

pr_key `cgbarlow/sasi#54`, conflict_index `0`, AST verdict `identifier_rename_only`, renames `{"bundleImpact": "bundleSize", "cacheability": "latencyRisk"}`

**BASE**
```
  private calculateNetworkMetrics(issues: PerformanceIssue[]): any {
```

**OURS**
```
  private calculateNetworkMetrics(issues: PerformanceIssue[]): { requestCount: number; bundleImpact: number; cacheability: number } {
```

**THEIRS**
```
  private calculateNetworkMetrics(issues: PerformanceIssue[]): { requestCount: number; bundleSize: number; latencyRisk: number } {
```

## 26. app/api/company/addresses/route.ts

pr_key `cognoco/User-Mgmt#670`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { type RouteAuthContext } from "@/middleware/auth";
```

**OURS**
```
import { type AuthContext } from "@/core/config/interfaces";
```

**THEIRS**
```
import type { AuthContext } from "@/core/config/interfaces";
```

## 27. packages/tokens-studio-for-figma/src/app/components/ManageThemesModal/CreateOrEditThemeForm.tsx

pr_key `tokens-studio/figma-plugin#3447`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
```

**THEIRS**
```
  const [searchQuery, setSearchQuery] = useState('');
```

## 28. src/World.ts

pr_key `elixr-games/elics#40`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
		this.queryManager = new QueryManager(deferredEntityUpdates);
```

**OURS**
```
		this.queryManager = new QueryManager(this.componentManager);
```

**THEIRS**
```
		this.queryManager = new QueryManager();
```

## 29. app/api/compliance/wipe.ts

pr_key `DigitalRoninCo/vanity-addy-generator#14`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
  if (req.method === 'DELETE') {
    // Verify JWT and initiate wipe
    const { txSignature } = await 
    (req.body.userId);
    res.status(202).json({ txSignature });
```

**OURS**
```
  if (req.method !== 'DELETE') {
    res.setHeader('Allow', 'DELETE');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const authHeader = req.headers['authorization'] || '';
  const token = Array.isArray(authHeader)
    ? authHeader[0]
    : authHeader.replace(/^Bearer\s+/i, '');

  if (!token) {
    return res.status(401).json({ error: 'Missing token' });
  }

  try {
    const secret = process.env.JWT_SECRET || 'secret';
    const payload = jwt.verify(token, secret) as { userId?: string };

    const userId = payload.userId || req.body?.userId;

    if (!userId) {
      return res.status(400).json({ error: 'Missing userId' });
    }

    const { txSignature } = await initiateWipe(userId);
    return res.status(202).json({ txSignature });
  } catch (err) {
    console.error(err);
    return res.status(401).json({ error: 'Invalid token' });
```

**THEIRS**
```
  if (req.method !== 'DELETE') {
    res.setHeader('Allow', 'DELETE')
    return res.status(405).end('Method Not Allowed')
  }

  try {
    const { userId } = typeof req.body === 'string' ? JSON.parse(req.body) : req.body
    const txSignature = await initiateWipe(userId)
    res.status(202).json({ txSignature })
  } catch (err) {
    res.status(400).json({ error: 'Invalid request' })
```

## 30. tura-wallet/src/lib/wallet.ts

pr_key `xiayuhkust/TuraAgent_Web3_New#22`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```

    // Initialize with HTTP provider first
    let provider = new Web3.providers.HttpProvider(CHAIN_CONFIG.rpcUrl);
    this.web3 = new Web3(provider);
```

**OURS**
```
<<<<<<< Updated upstream
```

**THEIRS**
```

    // Initialize with CustomProvider by default for consistent chain configuration
    const customProvider = new CustomProvider();
    this.web3 = new Web3(customProvider as any);
    console.log('CustomProvider initialized with chain config');
```

