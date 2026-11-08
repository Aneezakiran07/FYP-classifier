# Regions to hand label, test split, regions that reach the model

50 random test regions that reach the model on the current rules, seed 20261109, each under 1500 characters of base, ours and theirs together, the same rule as batches 1 and 3.

The test split has 2137 regions that reach the model, and 1520 of them pass the size rule. Accuracy from this sheet describes short regions, so say so next to the number.

This sheet comes from the **test split**. It is used once, for the final numbers, after the full run and every fix are done. Nobody tunes a prompt, a rule or a validator after looking at these regions.

Label by hand, without AI. Write a label and a one line reason into `true_label` and `notes` of the jsonl file. Leave `test_answers` empty. Use `.claude/skills/label-guidelines/SKILL.md` and the label table in CLAUDE.md, and apply the stage order when two labels fit.

`scripts/evaluate.py` refuses these labels unless `--final` is given.

The AST verdict shown is the one after the guards, the same one the model sees in a real run.

## 201. packages/adapters/sqljs-adapter/src/index.ts

pr_key `elias-sundqvist/cypher-anywhere#149`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
          if (chain.pathVariable) {
            varsMap.set(chain.pathVariable, { nodes: [n1, n2], relationships: [rel] });
          }
```

**THEIRS**
```
          if (chain.pathVariable)
            varsMap.set(chain.pathVariable, {
              nodes: [n1, n2],
              relationships: [rel],
            });
```

## 202. src/components/BulkPhotoAnalysisEditForm.tsx

pr_key `Elad220/fridge-savvy-meals-tracker#44`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
      dateCookedStored: today,
      eatByDate: eatByDate.toISOString().split('T')[0],
```

**THEIRS**
```
      tags: [],
```

## 203. portfolio/src/components/background/Background.tsx

pr_key `cameronloveland/cameronloveland.github.io#46`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
        <NebulaLayer />
```

**OURS**
```

```

**THEIRS**
```
        {/* <NebulaLayer /> */}
```

## 204. apps/gateway/src/chat/chat.ts

pr_key `theopenco/llmgateway#202`, conflict_index `10`, AST verdict `content_changed`

**BASE**
```
					organizationId: project.organizationId,
					projectId: apiKey.projectId,
					apiKeyId: apiKey.id,
					providerKeyId: providerKey.id,
```

**OURS**
```
					...baseLogEntry,
```

**THEIRS**
```
					organizationId: apiKey.organizationId,
					projectId: project.id,
					apiKeyId: apiKey.id,
					providerKeyId: providerKey.id,
```

## 205. frontend/src/services/api/projects.ts

pr_key `m0st4f4-hub/MCP-ProjectManager#377`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  ProjectFileAssociation,
  ProjectFileAssociationListResponse,
```

**THEIRS**
```
  Task,
```

## 206. lib/ai-triage/triage-logic.ts

pr_key `a1baseai/a1framework#3`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  taskActionConfirmation,
  verifyAgentIdentity
} from "../workflows/basic_workflow";
import { 
  generateAgentResponse,
  triageMessageIntent 
} from "../services/openai";
```

**OURS**
```
  verifyAgentIdentity,
} from "../workflows/basic_workflow";
import { triageMessageIntent } from "../services/openai";
```

**THEIRS**
```
  verifyAgentIdentity
} from "../workflows/basic-workflow";
import { triageMessageIntent } from "../services/openai";
import { convertToThreadMessages } from "./message-utils";
```

## 207. src/batch/harvest.ts

pr_key `RadicalZephyr/bitburner-scripts#162`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
    growthAnalyze
} from "batch/expected_value";
```

**OURS**
```
    growthAnalyze,
} from 'batch/expected_value';
```

**THEIRS**
```
    growthAnalyze,
    hackThreadsForPercent,
} from "batch/expected_value";
```

## 208. packages/storage/lib/impl/index.ts

pr_key `FooQoo/PRChecklistify#32`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
export * from './instructionPathStorage.js';
```

**THEIRS**
```
export * from './claudeApiKeyStorage.js';
export * from './openaiModelStorage.js';
export * from './geminiModelStorage.js';
export * from './claudeModelStorage.js';
```

## 209. packages/adapters/sqljs-adapter/src/index.ts

pr_key `elias-sundqvist/cypher-anywhere#149`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
        const v = this.evalExpr(expr.expression, vars, params);
        if (v == null) return null;
```

**OURS**
```
        let v: any;
        if (expr.expression.type === 'Variable') {
          v = vars.get(expr.expression.name);
        } else {
          v = this.evalExpr(expr.expression, vars, params);
        }
        if (v && typeof v === 'object' && 'relationships' in v) {
          return (v as any).relationships.length;
        }
```

**THEIRS**
```
        let v: any;
        if (expr.expression.type === 'Variable') {
          v = vars.get(expr.expression.name);
        } else {
          v = this.evalExpr(expr.expression, vars, params);
        }
        if (v == null) return null;
        if (typeof v === 'object' && 'relationships' in v)
          return (v as any).relationships.length;
```

## 210. src/services/sessionManager.ts

pr_key `gabadi/ccmanager#4`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
			detectionStrategy: options.detectionStrategy ?? 'claude',
			devcontainerConfig: options.devcontainerConfig ?? undefined,
			stateMutex: new Mutex(createInitialSessionStateData()),
```

**THEIRS**
```

			// Dual-mode properties initialization
			currentMode: 'claude', // Always start in Claude mode
			bashHistory: [],
			bashState: 'idle',
```

## 211. src/components/dashboard/DashboardLayout.tsx

pr_key `abmorrill4/praeviderant-careeros-mvp#5`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  Briefcase
```

**OURS**
```
  Briefcase,
  Database,
  Upload
```

**THEIRS**
```
  Briefcase,
  Settings
```

## 212. src/pages/SchedulePage.tsx

pr_key `Markf1994/segretaria-digitale-frontend#356`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
      {pdfWarning && <p className="warning">{pdfWarning}</p>}
```

**THEIRS**
```
      {gcSyncError && (
        <p className="error">
          {gcSyncError}{' '}
          <button onClick={() => setGcSyncError('')}>×</button>
        </p>
      )}
```

## 213. src/components/bills/viewModels/useBillsViewModel.ts

pr_key `jdsalasca/childcare-front#67`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { useBillTypesByCurrencyCode } from '../../../models/BillTypeAPI';
import { useChildren } from '../../../models/ChildrenAPI';
import { CashOnHandByDyAPI } from '../../../models/CashOnHandByDyAPI';
```

**OURS**
```
import BillTypeAPI from '../../../models/BillTypeAPI';
import { useChildren } from '../../../models/ChildrenAPI';
```

**THEIRS**
```
import { performanceOptimizer } from '../../../utils/PerformanceOptimizer';
import { CashAPI } from '../../../models/CashAPI';
import { CashOnHandByDyAPI } from '../../../models/CashOnHandByDyAPI';
```

## 214. src/services/financial/gocardless.service.ts

pr_key `christianLB/ai-service#13`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
      const baseUrl = await integrationConfigService.getConfig({
        integrationType: 'gocardless',
        configKey: 'base_url'
      }) || 'https://bankaccountdata.gocardless.com/api/v2';
      
      const response = await axios.post(`${baseUrl}/token/new/`, {
```

**OURS**
```
      // Validate credential format
      const validation = this.validateCredentialFormat(secretId, secretKey);
      if (!validation.valid) {
        logger.error('Invalid credential format', { errors: validation.errors });
        throw new Error(`Invalid GoCardless credential format: ${validation.errors.join(', ')}`);
      }
      
      // Use the configured base URL for token generation
      const tokenUrl = `${this.api.defaults.baseURL}/token/new/`;
      
      logger.info(`Requesting token from: ${tokenUrl}`);
      
      // Log the request payload structure (without sensitive data)
      logger.debug('Token request payload structure', {
        hasSecretId: !!secretId,
        hasSecretKey: !!secretKey,
        payloadKeys: Object.keys({ secret_id: secretId, secret_key: secretKey })
      });
      
      const response = await axios.post(tokenUrl, {
```

**THEIRS**
```
      const baseUrl = this.baseUrl ||
        process.env.GO_BASE_URL ||
        'https://bankaccountdata.gocardless.com/api/v2';

      const response = await axios.post(`${baseUrl}/token/new/`, {
```

## 215. acm_website/src/pages/LoginPage.tsx

pr_key `jhuacmofficers/Website#13`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import './LoginPage.css'; // Import the CSS file for styling
```

**OURS**
```
import '../styles/LoginPage.css'; // Import the CSS file for styling
```

**THEIRS**
```
import './../styles/LoginPage.css';
```

## 216. src/components/game/PrizeModal.tsx

pr_key `Fran-chess/roulette-game#10`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```

  // Estado para confeti
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== "undefined" ? window.innerWidth : 0,
    height: typeof window !== "undefined" ? window.innerHeight : 0,
  });
```

**OURS**
```
  const setGameSession = useGameStore((state) => state.setGameSession);
  const setCurrentQuestion = useGameStore((state) => state.setCurrentQuestion);
  const setLastSpinResultIndex = useGameStore((state) => state.setLastSpinResultIndex);
  const setShowConfetti = useGameStore((state) => state.setShowConfetti);
  const gameSession = useGameStore((state) => state.gameSession);
```

**THEIRS**
```
  const gameSession = useGameStore((state) => state.gameSession);
  const router = useRouter();

  // Estado para confeti
  const [showConfetti, setShowConfetti] = useState(false);
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== "undefined" ? window.innerWidth : 0,
    height: typeof window !== "undefined" ? window.innerHeight : 0,
  });
```

## 217. admin/src/components/theme/ThemeForm.tsx

pr_key `digitaldemocracy2030/idobata#323`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
    disableNewComment: false,
```

**THEIRS**
```
    starterQuestions: [],
```

## 218. components/TeamSelector.tsx

pr_key `xXJV10Xx/SkiftApp#9`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Company } from '@/data/companies';
import { Users } from 'lucide-react';
import React from 'react';
```

**OURS**
```
import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useTheme } from '../context/ThemeContext';
import { COMPANIES, SHIFT_TYPES } from '../data/companies';
```

**THEIRS**
```
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Company } from '@/data/companies';
import { Users } from 'lucide-react-native';
import React from 'react';
```

## 219. src/animations/FractalsGPU/FractalsGPU.tsx

pr_key `piyarsquare/animath#106`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
      vec3 inCol = paletteColor(mod(length(z)*16.0,256.0), paletteIn);
```

**OURS**
```
      // Map the final |z| value to the palette for interior coloring
      vec3 inCol = paletteColor(clamp(maxMag * 128.0, 0.0, 255.0), paletteIn);
```

**THEIRS**
```
      // Map the final |z| value to the palette for interior coloring
      vec3 inCol = paletteColor(clamp(length(z) * 128.0, 0.0, 255.0), paletteIn);
```

## 220. AdminUI/src/pages/WorkflowsPage.tsx

pr_key `trajkovdimitar/DynamicApi#107`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
                        className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
```

**OURS**
```
                        className="btn btn-primary disabled:opacity-50"
```

**THEIRS**
```

```

## 221. src/app/features/response-chart/response-chart.ts

pr_key `FlyingV111/RequestFetcher#2`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
import {BenchmarkService} from '../../core/services/benchmark.service';
```

**THEIRS**
```
import {BenchmarkHistoryService} from '../../core/services/benchmark-history.service';
```

## 222. src/batch/expected_value.ts

pr_key `RadicalZephyr/bitburner-scripts#162`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
    // Scale by 1000 to get human readable values and convert units
    // from $/GB*ms to $/GB*s
    return 1000 * expectedHackValue / (batchTime * ramUse);
```

**OURS**
```
    // Scale by 1000 to get human readable values and convert units
    // from $/GB*ms to $/GB*s
    return (1000 * expectedHackValue) / (batchTime * ramUse);
```

**THEIRS**
```
    const batchesPerSecond = 1000 / endingPeriod;
    const expectedPerSecond = expectedHackValue * batchesPerSecond;

    return expectedPerSecond / requiredRam;
```

## 223. client/src/services/auth.api.ts

pr_key `LaFabric-LinkTIC/tockler#5`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
const API_BASE = 'https://auto.linktic.com';

export async function requestCode(email: string): Promise<void> {
    const res = await fetch(`${API_BASE}/auth/request-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    if (!res.ok) {
        throw new Error('Request code failed');
    }
}

export async function verifyCode(email: string, code: string): Promise<void> {
    const res = await fetch(`${API_BASE}/auth/verify-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
    });
    if (!res.ok) {
        throw new Error('Invalid code');
    }
}
```

**THEIRS**
```
export async function requestCode(email: string): Promise<void> {
    const res = await fetch('/auth/request-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    if (!res.ok) {
        throw new Error('Request code failed');
    }
}

export async function verifyCode(email: string, code: string): Promise<void> {
    const res = await fetch('/auth/verify-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
    });
    if (!res.ok) {
        throw new Error('Invalid code');
    }
}
```

## 224. src/services/element-factory/ElementFactoryService.ts

pr_key `johannes-editor/johannes#25`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
        container.classList.add("johannes-content-element", "math-block", "swittable", ToolboxOptions.IncludeBlockToolbarClass, ToolboxOptions.ExtraOptionsClass);
```

**OURS**
```
        container.classList.add(
            "johannes-content-element",
            "math-block",
            "swittable",
            ToolboxOptions.IncludeBlockToolbarClass,
            ToolboxOptions.ExtraOptionsClass,
            CommonClasses.ShowMathInputOnClick
        );
```

**THEIRS**
```
        container.classList.add(
            "johannes-content-element",
            "math-block",
            "swittable",
            ToolboxOptions.IncludeBlockToolbarClass,
            ToolboxOptions.ExtraOptionsClass
        );
```

## 225. components/charts/CommonChart.tsx

pr_key `estruyf/web-visitorbadge-nextjs#18`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
      />
```

**OURS**
```
      >
        <Bar
          options={{
            maintainAspectRatio: false,
            responsive: true,
          }}
          data={{
            labels: stats.map(r => r.title),
            datasets: [
              {
                label,
                data: stats.map(r => r.value),
                borderWidth: 1,
                borderColor: '#CC8312',
                backgroundColor: "#FCF2E1",
                indexAxis: 'y'
              }
            ]
          }}
        />
      </div>
```

**THEIRS**
```
        options={{
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: {
              right: 20
            }
          },
          scales: {
            x: {
              ticks: {
                display: true
              }
            },
            y: {
              ticks: {
                display: true,
                maxRotation: 0,
                callback: function(value, index) {
                  const label = stats[index]?.title || '';
                  return label.length > 30 ? label.substring(0, 30) + '...' : label;
                }
              }
            }
          },
          plugins: {
            legend: {
              display: false
            }
          }
        }}
      />
```

## 226. frontend/src/app/templates/[templateId]/edit/page.tsx

pr_key `m0st4f4-hub/MCP-ProjectManager#196`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(no base available, the direction of change is unknown)
```

**OURS**
```
    <>
<<<<<<< HEAD
      <EditProjectTemplateForm
```

**THEIRS**
```
<<<<<<< HEAD
      <TemplateForm
=======
      <EditProjectTemplateForm
```

## 227. src/AppOne.ts

pr_key `OctopBP/wosb-threejs#5`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
    engine: BABYLON.Engine;
    scene: BABYLON.Scene;
```

**OURS**
```
    renderer: WebGLRenderer
    scene: Scene
    camera: PerspectiveCamera
    gameWorld: GameWorld
    gui?: GUI
```

**THEIRS**
```
    engine: BABYLON.Engine;
    scene: BABYLON.Scene;
    gameWorld: GameWorld;
```

## 228. src/components/auth/AuthLanding.tsx

pr_key `toshiotawa/jazzify-lab#75`, conflict_index `3`, AST verdict `content_changed`

**BASE**
```
  // 開発環境でのみデバッグ情報を表示
  useEffect(() => {
    if (import.meta.env.DEV) {
      setShowDebugInfo(true);
    }
  }, []);

  const handleSendLink = async (mode: 'signup' | 'login') => {
    // バリデーション
    if (!email.trim()) {
      return toast.error(getValidationMessage('メールアドレス', 'required'));
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return toast.error(getValidationMessage('メールアドレス', 'email'));
    }
```

**OURS**
```
  // ログイン画面にいるときは、既にログイン済みならダッシュボードへ即リダイレクト
  useEffect(() => {
    if (mode === 'login' && user && !isGuest) {
      navigate('/main#dashboard', { replace: true });
    }
  }, [mode, user, isGuest, navigate]);

  // 地理情報の事前取得や国のローカル保存は行わない

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setSignupDisabled(false);
```

**THEIRS**
```
  const handleSendLink = async (mode: 'signup' | 'login') => {
    // バリデーション
    if (!email.trim()) {
      return toast.error(getValidationMessage('メールアドレス', 'required'));
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return toast.error(getValidationMessage('メールアドレス', 'email'));
    }
```

## 229. scripts/gen-codebase-index.ts

pr_key `Krashnicov/n8n-nodes-netsuite#21`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
          return cleanComment;
```

**OURS**
```
          description = cleanComment;
```

**THEIRS**
```
          // Get first sentence or truncate to 140 chars
          return truncateDescription(cleanComment);
```

## 230. tests/card-processor.test.ts

pr_key `fenrick/MiroDiagramming#124`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  test('updates card when id matches', async () => {
    const existing = {
      id: 'c2',
      title: 'old',
      getMetadata: jest.fn().mockResolvedValue({ id: 'match' }),
      setMetadata: jest.fn(),
      sync: jest.fn(),
    } as any;
    (global.miro.board.get as jest.Mock).mockImplementation(
      async ({ type }) => {
        if (type === 'tag') return [];
        if (type === 'card') return [existing];
        return [];
      },
    );
    await processor.processCards([{ id: 'match', title: 'new' }]);
    expect(global.miro.board.createCard).not.toHaveBeenCalled();
    expect(existing.title).toBe('new');
    expect(existing.setMetadata).toHaveBeenCalledWith('app.miro.cards', {
      id: 'match',
    });
  });

```

**THEIRS**
```
  test('builds identifier map once', async () => {
    const boardCard = {
      getMetadata: jest.fn().mockResolvedValue({ identifier: 'x' }),
    } as any;
    (global.miro.board.get as jest.Mock).mockImplementation(({ type }: any) => {
      if (type === 'card') return [boardCard];
      return [];
    });
    await processor.processCards([{ title: 'A' }, { title: 'B' }]);
    const cardCalls = (global.miro.board.get as jest.Mock).mock.calls.filter(
      (c: any[]) => c[0].type === 'card',
    ).length;
    expect(cardCalls).toBe(1);
    expect(boardCard.getMetadata).toHaveBeenCalledTimes(1);
    expect(processor.getCardByIdentifier('x')).toBe(boardCard);
  });

```

## 231. packages/client/src/components/chat.tsx

pr_key `elizaOS/eliza#4638`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  onDelete,
```

**THEIRS**
```
  onShowDetails,
```

## 232. src/components/fantasy/FantasyGameScreen.tsx

pr_key `toshiotawa/jazzify-lab#24`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  // 設定状態を管理（初期値はstageから取得）
  const [showGuide, setShowGuide] = useState(stage.showGuide);
  
  // stage.showGuide の変更をコンポーネントの状態に同期させる
  useEffect(() => {
    setShowGuide(stage.showGuide);
  }, [stage.showGuide]);
  
```

**THEIRS**
```
  // ★ 設定状態を追加
  const [fantasySettings, setFantasySettings] = useState({
    midiDeviceId: null as string | null,
    volume: 0.8,
    showGuide: false
  });
  
```

## 233. packages/constants/src/storage.ts

pr_key `onlook-dev/onlook#2252`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
    FILE_TRANSFER: 'file_transfer',
```

**THEIRS**
```
    API_FILES: 'api_files',
```

## 234. src/components/HeroMinimal.tsx

pr_key `cwolfbr/libra-credito-landing-page-22#103`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
                  Crédito Com Garantia de Imóvel - Home Equity
```

**OURS**
```
                  <span className="whitespace-nowrap">Crédito Com Garantia de Imóvel</span>
                  <br />
                  é mais simples na Libra!
                  <br />
                  Libere até 50% do valor do seu imóvel
```

**THEIRS**
```
                  Crédito Com Garantia de Imóvel é na Libra!
                  <br />
                  Home Equity Facilitado.
```

## 235. src/core/Recorder.ts

pr_key `doctor-assistant/web-components#22`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
    },
  };
  if (isRemote) {
    state.telemedicine = true;
    if (videoElement) {
      try {
        const context = new AudioContext();
        const source = context.createMediaElementSource(videoElement);
        const destination = context.createMediaStreamDestination();
        source.connect(destination);
        videoElementStream = destination.stream;
      } catch (error) {
        console.error('Erro ao capturar áudio do vídeo:', error);
        // Fallback to screen sharing
```

**OURS**
```
    },
  };
  if(!audioContext){
    audioContext = new AudioContext()
  }
  if (isRemote) {
    state.telemedicine = true;
    if (videoElement) {
      try {
        if (!videoElementSource) {
          videoElementSource = audioContext.createMediaElementSource(videoElement);
        }
        const destination = audioContext.createMediaStreamDestination();
        videoElementSource.connect(destination);
        videoElementStream = destination.stream;
      } catch (error) {
        console.error('Erro ao capturar áudio do vídeo:', error);
```

**THEIRS**
```
    });

    if (isRemote) {
      state.telemedicine = true;
      if (videoElement) {
```

## 236. commands/dev.ts

pr_key `StreakYC/glue-cli#7`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
  console.log(cyan(`\n[${new Date().toISOString()}] ${trigger?.type.toUpperCase()} ${trigger?.description}`));
```

**OURS**
```
  const prefix = isReplay ? "REPLAYING " : "";
  console.log(cyan(`\n[${new Date().toISOString()}] ${prefix}: ${trigger?.type.toUpperCase()} ${trigger?.description}`));
```

**THEIRS**
```
  const prefix = isReplay ? "REPLAYING " : "";
  console.log(cyan(`\n[${new Date().toISOString()}] ${prefix}${trigger?.type.toUpperCase()} ${trigger?.description}`));

  if (!isReplay) {
    lastMessage = message;
  }
```

## 237. client/src/pages/property-listings.tsx

pr_key `Winterlee1973/LadybugRealEstate#7`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
        baseUrl = '/api/search';
        // Check if 'q' is a 5-digit zip code
        if (/^\d{5}$/.test(q)) {
          currentParams.append('zipCode', q);
        } else {
          currentParams.append('q', q);
        }
```

**OURS**
```
        // Check if 'q' is a 5-digit zip code
        if (/^\d{5}$/.test(q)) {
          query = query.eq('zip_code', q);
        } else {
          // Search in title, description, address, or city
          query = query.or(`title.ilike.%${q}%,description.ilike.%${q}%,address.ilike.%${q}%,city.ilike.%${q}%`);
        }
```

**THEIRS**
```
        currentParams.append('q', q);
      } else if (zipCode) {
        currentParams.append('zipCode', zipCode);
```

## 238. pages/api/search-broadcasts.ts

pr_key `tosi29/app#135`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
// Define the PastBroadcast interface
```

**OURS**
```
// Define the PastBroadcast interface for API response compatibility
```

**THEIRS**
```
// Define the new types according to the specification
type Content = {
  text: string;
  type: "TEXT";
};

type Metadata = {
  episode_id: string;
  series_name: string;
  series_number: string;
  label?: string;
  title: string;
  duration: number;
  position?: number;
  spotify_episode_id?: string;
  youtube_video_id?: string;
};

type RetrievalResult = {
  content: Content;
  metadata: Metadata;
  score: number;
};

type RetrieveApiResponse = {
  retrievalResults: RetrievalResult[];
};

// Legacy interface for internal data conversion
```

## 239. app/_layout.tsx

pr_key `xXJV10Xx/SkiftApp#9`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { useEffect } from 'react';
```

**OURS**
```
import { useEffect, useState } from 'react';
```

**THEIRS**
```

```

## 240. apps/api/src/routes/jobs.ts

pr_key `Deharath/prompt-lab#73`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  getPreviousJob,
  type Job,
```

**THEIRS**
```
  db,
  jobs,
  getDb,
```

## 241. src/OmnichannelChatSDK.ts

pr_key `microsoft/omnichannel-chat-sdk#488`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
    public async endChat(endChatOptionalParams: EndChatOptionalParams = {}): Promise<void> {

        const cleanupMetadata = {
            RequestId: this.requestId,
            ChatId: this.chatToken.chatId as string
        };

        this.scenarioMarker.startScenario(TelemetryEvent.EndChat, cleanupMetadata);

        if (!this.isInitialized) {
            exceptionThrowers.throwUninitializedChatSDK(this.scenarioMarker, TelemetryEvent.EndChat);
```

**OURS**
```
    public async endChat(endChatOptionalParams: EndChatOptionalParams = {}): Promise<void> {
        return this.executeWithLock(() => this.internalEndChat(endChatOptionalParams));
    }

    private async internalEndChat(endChatOptionalParams: EndChatOptionalParams = {}): Promise<void> {

        const cleanupMetadata = {
            RequestId: this.requestId,
            ChatId: this.chatToken.chatId as string
        };

        this.scenarioMarker.startScenario(TelemetryEvent.EndChat, cleanupMetadata);

        if (!this.isInitialized) {
            exceptionThrowers.throwUninitializedChatSDK(this.scenarioMarker, TelemetryEvent.EndChat);
```

**THEIRS**
```
    public async endChat(endChatOptionalParams: EndChatOptionalParams = {}, bypassCoordination = false): Promise<void> {
        // Coordinate with startChat calls to prevent race conditions (unless bypassing for cleanup)
        if (!bypassCoordination) {
            await this.callCoordinator.coordinateCall(CallType.END_CHAT, this.requestId, this.chatToken?.chatId || '');
```

## 242. components/textarea.tsx

pr_key `brooksy4503/chatlima#8`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { modelID } from "@/ai/providers";
```

**OURS**
```
import { modelID, modelDetails } from "@/ai/providers";
```

**THEIRS**
```
import { modelID, ModelOrPresetID } from "@/ai/providers";
```

## 243. pkgs/ai-functions/src/ai.ts

pr_key `drivly/ai#1166`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
import { openai } from '@ai-sdk/openai'
import { createOpenAI } from '@ai-sdk/openai'
// import { createOpenAICompatible } from '@ai-sdk/openai-compatible'
```

**OURS**
```
import { model } from 'ai-providers'
```

**THEIRS**
```
import { openai } from '@ai-sdk/openai'
import { createOpenAICompatible } from '@ai-sdk/openai-compatible'
```

## 244. src/presentation/rest/routes/userRoutes.ts

pr_key `Tsutomu-Ikeda/functional-programming-di#3`, conflict_index `4`, AST verdict `content_changed`

**BASE**
```
    { method: 'GET', path: '/users/:id', handler: getUserHandler }
```

**OURS**
```
    { method: 'GET', path: '/users/:id', handler: getUserHandler },
```

**THEIRS**
```
    { method: 'GET', path: '/users/:id', handler: getUserHandler },
    { method: 'POST', path: '/users/bulk', handler: bulkCreateUsersFromCsvHandler }
```

## 245. lib/ai-triage/triage-logic.ts

pr_key `a1baseai/a1framework#3`, conflict_index `5`, AST verdict `content_changed`

**BASE**
```
            message: 'Default response sent',
            data: response
```

**OURS**
```
            message: response
```

**THEIRS**
```
            message: 'Default response sent',
            data: { response }
```

## 246. apps/shinkai-desktop/src/components/agent/agent-form.tsx

pr_key `dcSpark/shinkai-local-ai-agents#718`, conflict_index `1`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  MessageSquare,
```

**THEIRS**
```
  MessageSquare,
  Save,
```

## 247. nextjs-dopetrop/jest.config.ts

pr_key `hashimwarren/blog-starter-nextjs#3`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  // setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
```

**OURS**
```
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testPathIgnorePatterns: ["<rootDir>/tests/", "<rootDir>/tests-examples/"],
```

**THEIRS**
```
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testPathIgnorePatterns: ['<rootDir>/tests/', '<rootDir>/tests-examples/'],
```

## 248. app/founder-interviews/page.tsx

pr_key `0xFuckTheFeds/Dashcoin#277`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
  MessageCircle, 
  Users, 
  Mic, 
  Play, 
  Calendar,
```

**OURS**
```
  MessageCircle,
  Users,
  Mic,
```

**THEIRS**
```
  MessageCircle,
  Users,
  Mic,
  Calendar,
```

## 249. src/forma.ts

pr_key `timrogers/formanator#441`, conflict_index `2`, AST verdict `content_changed`

**BASE**
```
    'https://api.joinforma.com/client/api/v2/claims?is_mobile=true',
```

**OURS**
```
    'https://api.joinforma.com/client/api/v2/claims',
```

**THEIRS**
```
    buildApiUrl('/client/api/v2/claims', { is_mobile: COMMON_QUERY_PARAMS.IS_MOBILE }),
```

## 250. src/pages/DesignReports.tsx

pr_key `JayKataria23/kmtpl_web#4`, conflict_index `0`, AST verdict `content_changed`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false);
  const [shareOrder, setShareOrder] = useState<OrderDetail | null>(null);
  const [shareImageUrl, setShareImageUrl] = useState<string | null>(null);
  const shareRef = useRef<HTMLDivElement>(null);
  const [shareDesignName, setShareDesignName] = useState<string>("");
```

**THEIRS**
```
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false);
  const [shareOrder, setShareOrder] = useState<OrderDetail | null>(null);
  const [shareImageUrl, setShareImageUrl] = useState<string | null>(null);
  const shareRef = useRef<HTMLDivElement>(null);
```
