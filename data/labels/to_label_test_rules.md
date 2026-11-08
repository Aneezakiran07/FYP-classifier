# Regions to hand label, test split, regions the rules decide

50 random test regions that the rules decide on the current code, seed 20261109, each under 1500 characters. No-marker records are left out because they have no text to read.

The test split has 2749 marker regions the rules decide, and 2281 of them pass the size rule. This gives the accuracy of the rules part.

The rule's own label is not shown, so the label you give is your own reading of the region.

This sheet comes from the **test split**. It is used once, for the final numbers, after the full run and every fix are done. Nobody tunes a prompt, a rule or a validator after looking at these regions.

Label by hand, without AI. Write a label and a one line reason into `true_label` and `notes` of the jsonl file. Leave `test_answers` empty. Use `.claude/skills/label-guidelines/SKILL.md` and the label table in CLAUDE.md, and apply the stage order when two labels fit.

`scripts/evaluate.py` refuses these labels unless `--final` is given.

## 301. artifacts/@openzeppelin/contracts/utils/Context.sol/Context.dbg.json

pr_key `SirSuhayb/sun_age#7`, conflict_index `0`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
{
  "_format": "hh-sol-dbg-1",
  "buildInfo": "../../../../build-info/5458139d90d751fd36d3b11d12e24f58.json"
}
```

**THEIRS**
```
{
  "_format": "hh-sol-dbg-1",
  "buildInfo": "../../../../build-info/519fd665c2c8c1606ebd27b6ebd5695c.json"
}
```

## 302. .gitignore

pr_key `matheusturturro/Dashtony#14`, conflict_index `0`

**BASE**
```
*src/server/sheets-key.json
```

**OURS**
```
*backend/sheets-key.json
*src/server/sheets-key.json
```

**THEIRS**
```
*backend/sheets-key.json
```

## 303. README.md

pr_key `roymichaels/lifepilotai#122`, conflict_index `1`

**BASE**
```
### 3. Firebase Console Setup
1. Open the [Firebase console](https://console.firebase.google.com/) and navigate to **Authentication → Sign‑in method**.
   Enable **Email/Password** or any other providers your app uses.
2. Under **Authentication → Settings**, add your development and production
   domains to the **Authorized domains** list (include `localhost` for local testing).
3. Copy the Firebase project credentials into your `.env` file using the variable
   names shown above.
```

**OURS**
```
### 3. Waku Identity Setup
1. Generate a new peer key for Waku using the CLI:
   ```bash
   npx waku-keygen > waku-key.json
   ```
   Keep this file safe&mdash;it acts as your login credential.
2. Start the app and choose **Import Waku Key** to load the JSON file. The key is
   stored locally and lets the client sign Waku messages.
3. After the key is imported, your profile configuration is published on the
   `/lifepilot/user-config/1/app` topic so it can be restored from any device.
```

**THEIRS**
```
### 3. Firebase Console Setup
1. Open the [Firebase console](https://console.firebase.google.com/) and navigate to **Authentication → Sign‑in method**.
   Enable **Email/Password** or any other providers your app uses.
2. Under **Authentication → Settings**, add your development and production
   domains to the **Authorized domains** list (include `localhost` for local testing).
3. When the client starts it will prompt for your Firebase project credentials.
   Enter the values for each field as requested.
```

## 304. lib/services/openai.ts

pr_key `a1baseai/a1framework#3`, conflict_index `3`

**BASE**
```
    role: (msg.sender_number === process.env.A1BASE_AGENT_NUMBER! ? "assistant" : "user") as ChatRole,
```

**OURS**
```
    role: (msg.sender_number === process.env.A1BASE_AGENT_NUMBER!
      ? "assistant"
      : "user") as ChatRole,
```

**THEIRS**
```
    role: msg.sender_number === process.env.A1BASE_AGENT_NUMBER! ? "assistant" : "user",
```

## 305. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `113`

**BASE**
```
atob@^2.1.1:
```

**OURS**
```
atob@^2.1.2:
```

**THEIRS**
```
atob@^2.1.1, atob@^2.1.2:
```

## 306. components/ShiftStats.tsx

pr_key `xXJV10Xx/SkiftApp#9`, conflict_index `0`

**BASE**
```
import { calculateWorkedHours, generateMonthSchedule, getNextShift } from '@/data/ShiftSchedules';
import { Calendar, Clock, TrendingUp, Users } from 'lucide-react';
```

**OURS**
```
import { calculateWorkedHours, generateMonthSchedule, getNextShift } from '@/lib/shiftCalculations';
import { Ionicons } from '@expo/vector-icons';
```

**THEIRS**
```
import { calculateWorkedHours, generateMonthSchedule, getNextShift } from '@/data/ShiftSchedules';
import { Calendar, Clock, TrendingUp, Users } from 'lucide-react-native';
```

## 307. pnpm-lock.yaml

pr_key `sterashima78/ts-md#47`, conflict_index `13`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  p-locate@4.1.0:
    resolution: {integrity: sha512-R79ZZ/0wAxKGu3oYMlz8jy/kbhsNrS7SKZ7PxEHBgJ5+F2mtFW2fK2cOtBh1cHYkQsbzFV7I+EoRKe6Yt0oK7A==}
    engines: {node: '>=8'}

  p-map@2.1.0:
    resolution: {integrity: sha512-y3b8Kpd8OAN444hxfBbFfj1FY/RjtTd8tzYwhUqNYXx0fXx2iX4maP4Qr6qhIKbQXI02wTLAda4fYUbDagTUFw==}
    engines: {node: '>=6'}

  p-try@2.2.0:
    resolution: {integrity: sha512-R4nPAVTAU0B9D35/Gk3uJf/7XYbQcyohSKdvAxIRSNghFl4e71hVoGnBNQz9cWaXxO2I10KTC+3jMdvvoKw6dQ==}
    engines: {node: '>=6'}

```

**THEIRS**
```
  p-locate@5.0.0:
    resolution: {integrity: sha512-LaNjtRWUBY++zB5nE/NwcaoMylSPk+S+ZHNB1TzdbMJMny6dynpAGt7X/tl/QYq3TIeE6nxHppbo2LGymrG5Pw==}
    engines: {node: '>=10'}

```

## 308. frontend/package-lock.json

pr_key `Elad220/smart-shopper#43`, conflict_index `71`

**BASE**
```
      "dev": true,
```

**OURS**
```
      "license": "MIT",
```

**THEIRS**
```
      "dev": true,
      "license": "MIT",
```

## 309. src/components/fantasy/FantasyGameEngine.tsx

pr_key `toshiotawa/jazzify-lab#183`, conflict_index `12`

**BASE**
```
      currentStage: stage,
```

**OURS**
```
      currentStage: stage,
      playMode,
```

**THEIRS**
```
      currentStage: normalizedStage,
```

## 310. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `22`

**BASE**
```
  /@esbuild/linux-arm64@0.25.6:
    resolution: {integrity: sha512-b967hU0gqKd9Drsh/UuAm21Khpoh6mPBSgz8mKRq4P5mVK8bpA+hQzmm/ZwGVULSNBzKdZPQBRT3+WuVavcWsQ==}
    engines: {node: '>=18'}
    cpu: [arm64]
    os: [linux]
    requiresBuild: true
    dev: false
```

**OURS**
```
  '@esbuild/linux-arm64@0.25.6':
```

**THEIRS**
```
  '@esbuild/darwin-x64@0.25.6':
```

## 311. src/components/ChatBox.tsx

pr_key `mocher1/chatAI#22`, conflict_index `0`

**BASE**
```
import { Send, Loader2 } from 'lucide-react';
```

**OURS**
```
import { Send, Loader2, User, Bot, AlertCircle, Settings, ExternalLink } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
```

**THEIRS**
```
import { Send, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
```

## 312. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `410`

**BASE**
```
rxjs@6.4.0, rxjs@~6.4.0:
  version "6.4.0"
  resolved "https://registry.yarnpkg.com/rxjs/-/rxjs-6.4.0.tgz#f3bb0fe7bda7fb69deac0c16f17b50b0b8790504"
  integrity sha512-Z9Yfa11F6B9Sg/BK9MnqnQ+aQYicPLtilXBp2yUtDt2JRCE0h26d33EnfO3ZxoNxG0T92OUucP3Ct7cpfkdFfw==
```

**OURS**
```
rxjs@~7.8.0:
  version "7.8.2"
  resolved "https://registry.npmjs.org/rxjs/-/rxjs-7.8.2.tgz"
  integrity sha512-dhKf903U/PQZY6boNNtAGdWbG85WAbjT/1xYoZIC7FAY0yWapOBQVsVrDl58W86//e1VpMNBtRV4MaXfdMySFA==
```

**THEIRS**
```
rxjs@6.6.7, rxjs@^6.5.2:
  version "6.6.7"
  resolved "https://registry.yarnpkg.com/rxjs/-/rxjs-6.6.7.tgz#90ac018acabf491bf65044235d5863c4dab804c9"
  integrity sha512-hTdwr+7yYNIT5n4AMYp85KA6yw2Va0FLa3Rguvbpa4W3I5xynaBZo41cM3XM+4Q6fRMj3sBYIR1VAmZMXYJvRQ==
```

## 313. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `128`

**BASE**
```
braces@^3.0.2:
  version "3.0.2"
  resolved "https://registry.yarnpkg.com/braces/-/braces-3.0.2.tgz#3454e1a462ee8d599e236df336cd9ea4f8afe107"
  integrity sha512-b8um+L1RzM3WDSzvhm6gIz1yfTbBt6YTlcEKAvsmqCZZFw46z626lVj9j1yEPW33H5H+lBQpZMP1k8l+78Ha0A==
```

**OURS**
```
braces@^3.0.2, braces@^3.0.3, braces@~3.0.2:
  version "3.0.3"
  resolved "https://registry.npmjs.org/braces/-/braces-3.0.3.tgz"
  integrity sha512-yQbXgO/OSZVD2IsiLlro+7Hf6Q18EJrKSEsdoMzKePKXct3gvD8oLcOQdIzGupr5Fj+EDe8gO/lxc1BzfMpxvA==
```

**THEIRS**
```
braces@^3.0.3, braces@~3.0.2:
  version "3.0.3"
  resolved "https://registry.yarnpkg.com/braces/-/braces-3.0.3.tgz#490332f40919452272d55a8480adc0c441358789"
  integrity sha512-yQbXgO/OSZVD2IsiLlro+7Hf6Q18EJrKSEsdoMzKePKXct3gvD8oLcOQdIzGupr5Fj+EDe8gO/lxc1BzfMpxvA==
```

## 314. pnpm-lock.yaml

pr_key `kripton36/labelvaults-pro#1`, conflict_index `1`

**BASE**
```
  js-tokens@4.0.0:
    resolution: {integrity: sha512-RdJUflcE3cUzKiMqQgsCu06FPu9UdIJO0beYbPhHN4k6apgJtifcoCtT9bcxOpYBtpD2kCM6Sbzg4CausW/PKQ==}

```

**OURS**
```

```

**THEIRS**
```
  js-tokens@4.0.0:
    resolution: {integrity: sha512-RdJUflcE3cUzKiMqQgsCu06FPu9UdIJO0beYbPhHN4k6apgJtifcoCtT9bcxOpYBtpD2kCM6Sbzg4CausW/PKQ==}

  jsonwebtoken@9.0.2:
    resolution: {integrity: sha512-PRp66vJ865SSqOlgqS8hujT5U4AOgMfhrwYIuIhfKaoSCZcirrmASQr8CX7cUg+RMih+hgznrjp99o+W4pJLHQ==}
    engines: {node: '>=12', npm: '>=6'}

  jwa@1.4.2:
    resolution: {integrity: sha512-eeH5JO+21J78qMvTIDdBXidBd6nG2kZjg5Ohz/1fpa28Z4CcsWUzJ1ZZyFq/3z3N17aZy+ZuBoHljASbL1WfOw==}

  jws@3.2.2:
    resolution: {integrity: sha512-YHlZCB6lMTllWDtSPHz/ZXTsi8S00usEV6v1tjq8tOUZzw7DpSDWVXjXDre6ed1w/pd495ODpHZYSdkRTsa0HA==}

```

## 315. src/features/XIT/BURN/BURN.vue

pr_key `Kevni92/refined-prun#1`, conflict_index `0`

**BASE**
```
      <FilterButton v-model="red">RED</FilterButton>
      <FilterButton v-model="yellow">YELLOW</FilterButton>
      <FilterButton v-model="green">GREEN</FilterButton>
      <FilterButton v-model="inf">INF</FilterButton>
```

**OURS**
```
      <RadioItem v-model="red" horizontal>RED</RadioItem>
      <RadioItem v-model="yellow" horizontal>YELLOW</RadioItem>
      <RadioItem v-model="green" horizontal>GREEN</RadioItem>
      <RadioItem v-model="inf" horizontal>INF</RadioItem>
```

**THEIRS**
```
      <FilterButton v-model="red">RED</FilterButton>
      <FilterButton v-model="yellow">YELLOW</FilterButton>
      <FilterButton v-model="green">GREEN</FilterButton>
      <FilterButton v-model="inf">INF</FilterButton>
        <Passive label="Filter:">
            <TextInput v-model="materialFilter" dark />
        </Passive>
```

## 316. frontend/package-lock.json

pr_key `m0st4f4-hub/MCP-ProjectManager#204`, conflict_index `39`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
    "node_modules/normalize-url": {
      "version": "4.5.1",
      "resolved": "https://registry.npmjs.org/normalize-url/-/normalize-url-4.5.1.tgz",
      "integrity": "sha512-9UZCFRHQdNrfTpGg8+1INIg93B6zE0aXMVFkw1WFwvO4SlZywU6aLg5Of0Ap/PgcbSw4LNxvMWXMeugwMCX0AA==",
      "license": "MIT",
      "peer": true,
      "engines": {
        "node": ">=8"
      }
    },
```

**THEIRS**
```
    "node_modules/normalize-url": {
      "version": "4.5.1",
      "resolved": "https://registry.npmjs.org/normalize-url/-/normalize-url-4.5.1.tgz",
      "integrity": "sha512-9UZCFRHQdNrfTpGg8+1INIg93B6zE0aXMVFkw1WFwvO4SlZywU6aLg5Of0Ap/PgcbSw4LNxvMWXMeugwMCX0AA==",
      "license": "MIT",
      "engines": {
        "node": ">=8"
      }
    },
```

## 317. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `161`

**BASE**
```
  /inherits@2.0.3:
    resolution: {integrity: sha512-x00IRNXNy63jwGkJmzPigoySHbaqpNuzKbBOmzK+g2OdZpQ9w+sxCN+VSB3ja7IAge2OP2qpfxTjeNcyjmW1uw==}
    dev: true
```

**OURS**
```
  ini@4.1.1: {}
```

**THEIRS**
```
  inherits@2.0.3: {}
```

## 318. content/apis/apis.do/integrations/connections.mdx

pr_key `drivly/ai#959`, conflict_index `1`

**BASE**
```
### name

- **Type**: `text`
- **Required**: No




### user

- **Type**: `relationship`
- **Required**: Yes




### integration

- **Type**: `relationship`
- **Required**: Yes




### status

- **Type**: `select`
- **Required**: No
- **Default**: `active`



### metadata

- **Type**: `json`
- **Required**: No



```

**OURS**
```
```typescript
interface Connections {
  name?: string;
  user: string;
  integration: string;
  status?: 'active' | 'inactive' | 'pending';
  metadata?: Record<string, any>;
}
```


```

**THEIRS**
```
<TSDoc>
```typescript
interface ConnectionsType {
  name?: string
  user: string | { id: string }
  integration: string | { id: string }
  status?: string
  metadata?: object
}
```
</TSDoc>
```

## 319. pnpm-lock.yaml

pr_key `sterashima78/ts-md#47`, conflict_index `26`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
  node-fetch@2.7.0:
    dependencies:
      whatwg-url: 5.0.0

```

**THEIRS**
```
  normalize-path@3.0.0: {}

```

## 320. src/providers/keysender/keyboard.ts

pr_key `claude-did-this/MCPControl#149`, conflict_index `0`

**BASE**
```
      const keyboardKey = key;
```

**OURS**
```
      const keyboardKey = this._findMatchingString(key,  VALID_KEYS);
```

**THEIRS**
```
      // Find matching key with correct casing from valid keys list
      const keyboardKey = this._findMatchingString(key, VALID_KEYS);
```

## 321. src/components/Header.tsx

pr_key `Markf1994/segretaria-digitale-frontend#486`, conflict_index `0`

**BASE**
```
          <Link to="/segnaletica-orizzontale">🚧 Orizzontale</Link>
```

**OURS**
```
          <div className="dropdown" ref={dropRef}>
            <button
              type="button"
              className="dropbtn"
              onClick={() => setDropOpen(o => !o)}
            >
              🚧 Segnaletica
            </button>
            {dropOpen && (
              <div className="dropdown-content">
                <Link to="/inventario">Segnaletica verticale/temporanea</Link>
                <Link to="/segnaletica-orizzontale">Segnaletica orizzontale</Link>
              </div>
            )}
          </div>
```

**THEIRS**
```
          <Link to="/segnaletica">🚦 Segnaletica</Link>
          <Link to="/segnaletica-orizzontale">🚧 Orizzontale</Link>
```

## 322. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `217`

**BASE**
```
  /picomatch@2.3.1:
    resolution: {integrity: sha512-JU3teHTNjmE2VCGFzuY8EXzCDVwEqB2a8fsIvwaStHhAWJEeVd1o1QD80CU6+ZdEXXSLbSsuLwJjkCBWqRQUVA==}
    engines: {node: '>=8.6'}
```

**OURS**
```
  picomatch@4.0.3: {}
```

**THEIRS**
```
  picocolors@1.1.1: {}
```

## 323. src/data/dispatchToWorker.ts

pr_key `deepaucksharma/otel-metrics#134`, conflict_index `0`

**BASE**
```
import type { ParsedSnapshot } from '@/contracts/types';
```

**OURS**
```
import type { ParsedSnapshot } from '@intellimetric/contracts/types';
import { jsonSafeParse } from '@/logic/workers/utils/jsonSafeParse';
import { mapToParsedSnapshot } from '@/logic/workers/mapping/otlpMapper';
import type { RawOtlpExportMetricsServiceRequest } from '@intellimetric/contracts/rawOtlpTypes';
import { randomId } from '@/utils/randomId';
```

**THEIRS**
```
import type { ParsedSnapshot } from '@/contracts/types';
import { randomId } from '@/utils/randomId';
```

## 324. content/apis/apis.do/work/queues.mdx

pr_key `drivly/ai#959`, conflict_index `1`

**BASE**
```
### name

- **Type**: `text`
- **Required**: Yes




### role

- **Type**: `relationship`
- **Required**: Yes




### tasks

- **Type**: `join`
- **Required**: No



```

**OURS**
```
```typescript
interface Queues {
  name: string;
  role: string;
  tasks?: any;
}
```


```

**THEIRS**
```
<TSDoc>
```typescript
interface QueuesType {
  name: string
  role: string | { id: string }
  tasks?: any
}
```
</TSDoc>
```

## 325. README.md

pr_key `PV-Bhat/vibe-check-mcp-server#15`, conflict_index `8`

**BASE**
```
GEMINI_API_KEY=your_gemini_api_key
```

**OURS**
```
# Gemini (default)
GEMINI_API_KEY=your_gemini_api_key
# Optional providers
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
# Optional overrides
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-pro
```

**THEIRS**
```
GEMINI_API_KEY=your_key
# or OPENAI_API_KEY / OPENROUTER_API_KEY
```

## 326. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `180`

**BASE**
```
dns-equal@^1.0.0:
  version "1.0.0"
  resolved "https://registry.yarnpkg.com/dns-equal/-/dns-equal-1.0.0.tgz#b39e7f1da6eb0a75ba9c17324b34753c47e0654d"
  integrity sha1-s55/HabrCnW6nBcySzR1PEfgZU0=

dns-packet@^1.3.1:
  version "1.3.1"
  resolved "https://registry.yarnpkg.com/dns-packet/-/dns-packet-1.3.1.tgz#12aa426981075be500b910eedcd0b47dd7deda5a"
  integrity sha512-0UxfQkMhYAUaZI+xrNZOz/as5KgDU0M/fQ9b6SpkyLbk3GEswDi6PADJVaYJradtRVsRIlF1zLyOodbcTCDzUg==
```

**OURS**
```
dns-packet@^5.2.2:
  version "5.6.1"
  resolved "https://registry.npmjs.org/dns-packet/-/dns-packet-5.6.1.tgz"
  integrity sha512-l4gcSouhcgIKRvyy99RNVOgxXiicE+2jZoNmaNmZ6JXiGajBOJAesk1OBlJuM5k2c+eudGdLxDqXuPCKIj6kpw==
```

**THEIRS**
```
dir-glob@^3.0.1:
  version "3.0.1"
  resolved "https://registry.yarnpkg.com/dir-glob/-/dir-glob-3.0.1.tgz#56dbf73d992a4a93ba1584f4534063fd2e41717f"
  integrity sha512-WkrWp9GR4KXfKGYzOLmTuGVi1UWFfws377n9cc55/tb6DuqyF6pcQ5AbiHEshaDpY9v6oaSr2XCDidGmMwdzIA==
  dependencies:
    path-type "^4.0.0"

dns-equal@^1.0.0:
  version "1.0.0"
  resolved "https://registry.yarnpkg.com/dns-equal/-/dns-equal-1.0.0.tgz#b39e7f1da6eb0a75ba9c17324b34753c47e0654d"
  integrity sha1-s55/HabrCnW6nBcySzR1PEfgZU0=

dns-packet@^1.3.1:
  version "1.3.1"
  resolved "https://registry.yarnpkg.com/dns-packet/-/dns-packet-1.3.1.tgz#12aa426981075be500b910eedcd0b47dd7deda5a"
  integrity sha512-0UxfQkMhYAUaZI+xrNZOz/as5KgDU0M/fQ9b6SpkyLbk3GEswDi6PADJVaYJradtRVsRIlF1zLyOodbcTCDzUg==
```

## 327. src/features/Home/components/ExperienceModal/ExperienceModal.tsx

pr_key `hllbr/Portfolio#29`, conflict_index `2`

**BASE**
```
const ExperienceModal: React.FC<ExperienceModalProps> = ({ open, selected, onClose, color, onShowDetail }) => {
  const { t } = useTranslation();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
```

**OURS**
```
const ExperienceModal: React.FC<ExperienceModalProps> = ({ open, selected, onClose, color }) => {
  const { t, i18n } = useTranslation();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
```

**THEIRS**
```
const ExperienceModal: React.FC<ExperienceModalProps> = ({ open, selected, onClose, color, onShowDetail }) => {
  const { t } = useTranslation();
  const [testOpen, setTestOpen] = useState(false);
```

## 328. examples/coding_agent.ts

pr_key `combinatrix-ai/PromptTrail.ts#22`, conflict_index `1`

**BASE**
```
  createMetadata,
  generateText,
} from '@prompttrail/core';
```

**OURS**
```
  Agent,
  SystemTemplate,
  CLISource,
} from '../packages/core/src/index.js';

// Import tool definitions from ai SDK
import { tool, type Tool } from 'ai';
import { z } from 'zod';

// Node.js modules for file and command operations
```

**THEIRS**
```
  createGenerateOptions,
  createMetadata,
  generateText,
} from '@prompttrail/core';
import { z } from 'zod';
```

## 329. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `321`

**BASE**
```
negotiator@0.6.1:
  version "0.6.1"
  resolved "https://registry.yarnpkg.com/negotiator/-/negotiator-0.6.1.tgz#2b327184e8992101177b28563fb5e7102acd0ca9"
  integrity sha1-KzJxhOiZIQEXeyhWP7XnECrNDKk=
```

**OURS**
```
negotiator@^0.6.3, negotiator@0.6.3:
  version "0.6.3"
  resolved "https://registry.npmjs.org/negotiator/-/negotiator-0.6.3.tgz"
  integrity sha512-+EUsqGPLsM+j/zdChZjsnX51g4XrHFOIXwfnCVPGlQk/k5giakcKsuxCObBRu6DSm9opw/O6slWbJdghQM4bBg==
```

**THEIRS**
```
needle@^2.5.2:
  version "2.9.1"
  resolved "https://registry.yarnpkg.com/needle/-/needle-2.9.1.tgz#22d1dffbe3490c2b83e301f7709b6736cd8f2684"
  integrity sha512-6R9fqJ5Zcmf+uYaFgdIHmLwNldn5HbK8L5ybn7Uz+ylX/rnOsSp1AHcvQSrCaFN+qNM1wpymHqD7mVasEOlHGQ==
  dependencies:
    debug "^3.2.6"
    iconv-lite "^0.4.4"
    sax "^1.2.4"

negotiator@0.6.1:
  version "0.6.1"
  resolved "https://registry.yarnpkg.com/negotiator/-/negotiator-0.6.1.tgz#2b327184e8992101177b28563fb5e7102acd0ca9"
  integrity sha1-KzJxhOiZIQEXeyhWP7XnECrNDKk=
```

## 330. content/apis/apis.do/queues.mdx

pr_key `drivly/ai#959`, conflict_index `1`

**BASE**
```
### name

- **Type**: `text`
- **Required**: Yes




### role

- **Type**: `relationship`
- **Required**: Yes




### tasks

- **Type**: `join`
- **Required**: No



```

**OURS**
```
```typescript
interface Queues {
  name: string;
  role: string;
  tasks?: any;
}
```


```

**THEIRS**
```
<TSDoc>
```typescript
interface QueuesType {
  name: string
  role: string | { id: string }
  tasks?: any
}
```
</TSDoc>
```

## 331. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `204`

**BASE**
```
  /parse-gitignore@2.0.0:
    resolution: {integrity: sha512-RmVuCHWsfu0QPNW+mraxh/xjQVw/lhUCUru8Zni3Ctq3AoMhpDTq0OVdKS6iesd6Kqb7viCV3isAL43dciOSog==}
    engines: {node: '>=14'}
    dev: false
```

**OURS**
```
  pako@0.2.9: {}
```

**THEIRS**
```
  parse-gitignore@2.0.0: {}
```

## 332. apps/web/app/s/[videoId]/page.tsx

pr_key `CapSoftware/Cap#635`, conflict_index `2`

**BASE**
```
    if (
      organizationData.length > 0 &&
      organizationData[0] &&
      organizationData[0].customDomain
    ) {
      customDomain = organizationData[0].customDomain;
      if (organizationData[0].domainVerified !== null) {
        domainVerified = true;
      }
    }
  }
```

**OURS**
```
	const sharedOrganizationsPromise = db()
		.select({ id: sharedVideos.organizationId, name: organizations.name })
		.from(sharedVideos)
		.innerJoin(organizations, eq(sharedVideos.organizationId, organizations.id))
		.where(eq(sharedVideos.videoId, videoId));
```

**THEIRS**
```
    if (
      organizationData.length > 0 &&
      organizationData[0] &&
      organizationData[0].customDomain
    ) {
      customDomain = organizationData[0].customDomain;
      if (organizationData[0].domainVerified !== null) {
        domainVerified = true;
      }
      showCapBranding = organizationData[0].showCapBranding;
    }
  }
```

## 333. frontend/package-lock.json

pr_key `Elad220/smart-shopper#43`, conflict_index `47`

**BASE**
```
      "dev": true,
```

**OURS**
```
      "license": "MIT",
```

**THEIRS**
```
      "dev": true,
      "license": "MIT",
```

## 334. apps/spruce/src/pages/adminSettings/tabs/GeneralTab/AnnouncementsTab/AnnouncementTab.tsx

pr_key `evergreen-ci/ui#826`, conflict_index `0`

**BASE**
```
import styled from "@emotion/styled";
import { H2 } from "@leafygreen-ui/typography";
import { size } from "@evg-ui/lib/constants/tokens";
import { AdminSettingsTabRoutes } from "constants/routes";
import { BaseTab } from "../BaseTab";
```

**OURS**
```
import { H2 } from "@leafygreen-ui/typography";
import { AdminSettingsGeneralSection } from "constants/routes";
import { BaseTab } from "../../BaseTab";
```

**THEIRS**
```
import styled from "@emotion/styled";
import { size } from "@evg-ui/lib/constants/tokens";
import { AdminSettingsTabRoutes } from "constants/routes";
import { BaseTab } from "../BaseTab";
```

## 335. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `237`

**BASE**
```
    http-proxy "^1.17.0"
    is-glob "^4.0.0"
    lodash "^4.17.11"
    micromatch "^3.1.10"
```

**OURS**
```
    "@tootallnate/once" "2"
    agent-base "6"
    debug "4"
```

**THEIRS**
```
    "@tootallnate/once" "1"
    agent-base "6"
    debug "4"
```

## 336. client/src/pages/workspace.tsx

pr_key `christophertmfoh/UiRevamp#3`, conflict_index `89`

**BASE**
```
                      <div className="flex items-center space-x-3 text-slate-300">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full"></div>
```

**OURS**
```
                      <div className="flex items-center space-x-3 text-slate-300">
                        <div className="w-2 h-2 bg-emerald-400 rounded-full"></div>
```

**THEIRS**
```
                      <div className="flex items-center space-x-3 text-secondary-foreground">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full"></div>
```

## 337. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `289`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
loader-utils@^2.0.0:
  version "2.0.4"
  resolved "https://registry.npmjs.org/loader-utils/-/loader-utils-2.0.4.tgz"
  integrity sha512-xXqpXoINfFhgua9xiqD8fPFHgkoq1mmmpE92WlDbm9rNRd/EbRb+Gqf908T2DMfuHjjJlksiK2RbHVOdD/MqSw==
  dependencies:
    big.js "^5.2.2"
    emojis-list "^3.0.0"
    json5 "^2.1.2"

loader-utils@3.2.1:
  version "3.2.1"
  resolved "https://registry.npmjs.org/loader-utils/-/loader-utils-3.2.1.tgz"
  integrity sha512-ZvFw1KWS3GVyYBYb7qkmRM/WwL2TQQBxgCK62rlvm4WpVQ23Nb4tYjApUlfjrEGvOs7KHEsmyUn75OHZrJMWPw==

```

**THEIRS**
```
loader-utils@^1.4.0:
  version "1.4.2"
  resolved "https://registry.yarnpkg.com/loader-utils/-/loader-utils-1.4.2.tgz#29a957f3a63973883eb684f10ffd3d151fec01a3"
  integrity sha512-I5d00Pd/jwMD2QCduo657+YM/6L3KZu++pmX9VFncxaxvHcru9jx1lBaFft+r4Mt2jK0Yhp41XlRAihzPxHNCg==
  dependencies:
    big.js "^5.2.2"
    emojis-list "^3.0.0"
    json5 "^1.0.1"

loader-utils@^2.0.0:
  version "2.0.4"
  resolved "https://registry.yarnpkg.com/loader-utils/-/loader-utils-2.0.4.tgz#8b5cb38b5c34a9a018ee1fc0e6a066d1dfcc528c"
  integrity sha512-xXqpXoINfFhgua9xiqD8fPFHgkoq1mmmpE92WlDbm9rNRd/EbRb+Gqf908T2DMfuHjjJlksiK2RbHVOdD/MqSw==
  dependencies:
    big.js "^5.2.2"
    emojis-list "^3.0.0"
    json5 "^2.1.2"

```

## 338. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `289`

**BASE**
```
      vite: 7.0.5
    dev: false
```

**OURS**
```
      vite: 6.3.5(@types/node@24.0.14)(jiti@2.4.2)(lightningcss@1.30.1)(terser@5.43.1)(yaml@2.8.0)
```

**THEIRS**
```
      vite: 6.3.5(@types/node@24.0.14)(jiti@2.4.2)(terser@5.43.1)(yaml@2.8.0)
```

## 339. docker/cloud/Dockerfile

pr_key `trysourcetool/sourcetool#78`, conflict_index `1`

**BASE**
```
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_DOMAIN=$VITE_DOMAIN
```

**OURS**
```
ENV VITE_IS_CLOUD_EDITION=true
```

**THEIRS**
```
ENV VITE_IS_CLOUD_EDITION=$VITE_IS_CLOUD_EDITION
```

## 340. app/tokendetail/[symbol]/page.tsx

pr_key `0xFuckTheFeds/Dashcoin#263`, conflict_index `1`

**BASE**
```
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-teal-500/10 border border-teal-500/20 rounded-full text-teal-400 text-sm font-medium">
                  <Sparkles className="w-4 h-4" />
                  Token Analysis
                </div>
                {researchData && researchData.Score && (
                  <ResearchScoreBadge score={Number(researchData.Score)} data={researchData} />
```

**OURS**
```
                {researchData && researchData.Score && (
                  <ResearchScoreBadge score={Number(researchData.Score)} data={researchData} />
```

**THEIRS**
```
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-teal-500/10 border border-teal-500/20 rounded-full text-teal-400 text-sm font-medium">
                  <Sparkles className="w-4 h-4" />
                  Token Analysis
                </div>
                {researchData && researchData.score && (
                  <ResearchScoreBadge score={Number(researchData.score)} data={researchData} />
```

## 341. frontend/package-lock.json

pr_key `m0st4f4-hub/MCP-ProjectManager#204`, conflict_index `27`

**BASE**
```
(empty base, both sides are additions)
```

**OURS**
```
    "node_modules/is-obj": {
      "version": "1.0.1",
      "resolved": "https://registry.npmjs.org/is-obj/-/is-obj-1.0.1.tgz",
      "integrity": "sha512-l4RyHgRqGN4Y3+9JHVrNqO+tN0rV5My76uW5/nuO4K1b6vw5G8d/cmFjP9tRfEsdhZNt0IFdZuK/c2Vr4Nb+Qg==",
      "license": "MIT",
      "peer": true,
      "engines": {
        "node": ">=0.10.0"
      }
    },
```

**THEIRS**
```
    "node_modules/is-obj": {
      "version": "1.0.1",
      "resolved": "https://registry.npmjs.org/is-obj/-/is-obj-1.0.1.tgz",
      "integrity": "sha512-l4RyHgRqGN4Y3+9JHVrNqO+tN0rV5My76uW5/nuO4K1b6vw5G8d/cmFjP9tRfEsdhZNt0IFdZuK/c2Vr4Nb+Qg==",
      "license": "MIT",
      "engines": {
        "node": ">=0.10.0"
      }
    },
```

## 342. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `256`

**BASE**
```
  /structured-clone-es@1.0.0:
    resolution: {integrity: sha512-FL8EeKFFyNQv5cMnXI31CIMCsFarSVI2bF0U0ImeNE3g/F1IvJQyqzOXxPBRXiwQfyBTlbNe88jh1jFW0O/jiQ==}
    dev: false
```

**OURS**
```
  structured-clone-es@1.0.0: {}
```

**THEIRS**
```
  strip-literal@3.0.0:
    dependencies:
      js-tokens: 9.0.1
```

## 343. frontend/package-lock.json

pr_key `Elad220/smart-shopper#43`, conflict_index `44`

**BASE**
```
      "dev": true,
```

**OURS**
```
      "license": "MIT",
```

**THEIRS**
```
      "dev": true,
      "license": "MIT",
```

## 344. yarn.lock

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `346`

**BASE**
```
once@^1.3.0, once@^1.3.1, once@^1.4.0:
```

**OURS**
```
once@^1.3.0:
```

**THEIRS**
```
once@^1.3.0, once@^1.4.0:
```

## 345. pnpm-lock.yaml

pr_key `matt3188/LEGO-track-layout-builder#9`, conflict_index `69`

**BASE**
```
      '@vitejs/plugin-vue': 5.2.4(vite@6.3.5)(vue@3.5.17)
      '@vitejs/plugin-vue-jsx': 4.2.0(vite@6.3.5)(vue@3.5.17)
```

**OURS**
```
      '@vitejs/plugin-vue': 5.2.4(vite@6.3.5(@types/node@24.0.14)(jiti@2.4.2)(lightningcss@1.30.1)(terser@5.43.1)(yaml@2.8.0))(vue@3.5.17(typescript@5.8.3))
      '@vitejs/plugin-vue-jsx': 4.2.0(vite@6.3.5(@types/node@24.0.14)(jiti@2.4.2)(lightningcss@1.30.1)(terser@5.43.1)(yaml@2.8.0))(vue@3.5.17(typescript@5.8.3))
```

**THEIRS**
```
      '@vitejs/plugin-vue': 5.2.4(vite@6.3.5(@types/node@24.0.14)(jiti@2.4.2)(terser@5.43.1)(yaml@2.8.0))(vue@3.5.17(typescript@5.8.3))
      '@vitejs/plugin-vue-jsx': 4.2.0(vite@6.3.5(@types/node@24.0.14)(jiti@2.4.2)(terser@5.43.1)(yaml@2.8.0))(vue@3.5.17(typescript@5.8.3))
```

## 346. src/app/features/tracking/components/all-tracking/all-tracking.component.html

pr_key `Saber13110/frontend#85`, conflict_index `4`

**BASE**
```
              [(ngModel)]="selectedCountry"
              name="selectedCountry"
              (change)="validateInput('reference', referenceNumber)">
```

**OURS**
```
              formControlName="selectedCountry">
```

**THEIRS**
```
              formControlName="selectedCountry"
              name="selectedCountry">
```

## 347. docs/codebase-index.json

pr_key `Krashnicov/n8n-nodes-netsuite#21`, conflict_index `47`

**BASE**
```
      "lastUpdated": "2025-03-23T02:32:08.991Z"
```

**OURS**
```
      "confidence": 1,
      "lastUpdated": "2025-03-23T09:51:38.900Z",
      "fileSize": 1566,
      "linesOfCode": 71,
      "checksum": "ea36e140f283458221152f3089bad155fc411fc7ef0b6ecbcf60e8c0f51efc93",
      "language": "TS"
```

**THEIRS**
```
      "lastUpdated": "2025-03-23T08:41:25.989Z",
      "confidence": 1
```

## 348. docs/codebase-index.json

pr_key `Krashnicov/n8n-nodes-netsuite#21`, conflict_index `31`

**BASE**
```
      "description": "{",
      "lastUpdated": "2025-03-23T02:32:08.991Z"
```

**OURS**
```
      "description": "\"name\": \"NetSuite Endpoint Connectivity Test\",",
      "confidence": 0.5,
      "lastUpdated": "2025-03-23T09:51:38.900Z",
      "fileSize": 3070,
      "linesOfCode": 148,
      "checksum": "15ce94f04ab29aa57bc0caeaf72496399b101c9274d3c0325103e6cb6ebf966f",
      "language": "JSON"
```

**THEIRS**
```
      "description": "{",
      "lastUpdated": "2025-03-23T08:41:25.989Z",
      "confidence": 0.5
```

## 349. api/agent/handler.py

pr_key `sethjuarez/sustineo#29`, conflict_index `1`

**BASE**
```
from api.model import AgentUpdateEvent, Content
```

**OURS**
```

from azure.ai.projects.aio import AIProjectClient

from api.model import AgentUpdateEvent, Content, Function
```

**THEIRS**
```
from typing import Any, Callable, Coroutine, Union
```

## 350. package.json

pr_key `devin-pilot-repos/angularspree#13`, conflict_index `9`

**BASE**
```
    "tslint": "~5.15.0",
    "typescript": "^3.5.3",
    "webpack-cli": "^3.1.2"
```

**OURS**
```
    "tslint": "~6.1.0",
    "typescript": "4.9.5",
    "webpack": "^5.99.8",
    "webpack-cli": "^3.1.2",
    "webpack-dev-server": "^5.2.1"
```

**THEIRS**
```
    "tslint": "~5.15.0",
    "typescript": "4.4.4",
    "webpack-cli": "^3.1.2"
```
