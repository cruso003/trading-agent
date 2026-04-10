/**
 * Academy lesson content — Module 1: Understanding the Gold Market
 * All content is static and based on the actual trading system philosophy.
 */

export interface LessonSection {
  type: 'paragraph' | 'subheading' | 'numbered_list' | 'bullet_list' | 'callout';
  content: string | string[];
}

export interface LessonData {
  moduleNum: number;
  lessonNum: number;
  moduleTitle: string;
  title: string;
  readingTime: string;
  sections: LessonSection[];
  takeaways: string[];
}

const LESSONS: LessonData[] = [
  {
    moduleNum: 1,
    lessonNum: 1,
    moduleTitle: 'Understanding the Gold Market',
    title: 'Why gold? The case for XAUUSD',
    readingTime: '6 min read',
    sections: [
      {
        type: 'paragraph',
        content:
          'Gold is unique among trading instruments. Unlike currency pairs that represent the relationship between two economies, or stocks that represent ownership in a company, gold is a globally recognised store of value with no liability attached to it. No central bank can print more of it. No government can default on it. This makes it fundamentally different from everything else you can trade.',
      },
      {
        type: 'paragraph',
        content:
          'XAUUSD is the ticker for gold priced in US dollars — how many dollars one troy ounce costs. It trades 24 hours a day, 5 days a week, and is one of the most liquid instruments in existence.',
      },
      {
        type: 'subheading',
        content: 'Why we trade it',
      },
      {
        type: 'numbered_list',
        content: [
          'Consistent structure — Gold trends well. When it moves, it moves with purpose. The H4 timeframe shows clean, readable structure: higher highs and higher lows in an uptrend, lower highs and lower lows in a downtrend. This structure is what the entire system is built on.',
          'Liquidity — Gold handles large order flow without distorting price. The spread is tight and execution is clean. A system that enters and exits quickly needs an instrument that absorbs those orders without slippage.',
          'Session character — Gold behaves differently in different sessions. Asia sets the range. London breaks that range and establishes direction. New York extends or reverses London\'s move. This predictable rhythm is something the system explicitly reads.',
          'Volatility with purpose — Gold can move 80–150 points in a single trading window. That\'s enough to build trades with meaningful risk-reward ratios, yet not so volatile that setups dissolve into noise.',
        ],
      },
      {
        type: 'subheading',
        content: 'Why not other instruments?',
      },
      {
        type: 'paragraph',
        content:
          "Other instruments work, but they have tradeoffs. EUR/USD has lower volatility — you need wider stops or accept smaller moves. Crypto has higher volatility but no reliable structure — patterns break down unpredictably. Stock indices react to individual company earnings and corporate news. Gold's price driver is simpler: it responds to dollar strength, yields, and risk sentiment. Once you understand those forces, you understand the instrument.",
      },
      {
        type: 'callout',
        content:
          "Gold is not a get-rich-quick instrument. The moves that look large on a chart — $20, $30, $50 in a day — require proper position sizing, clear stop losses, and respect for structure. The system was built to find specific, high-quality moments to participate. Not to trade constantly.",
      },
    ],
    takeaways: [
      'XAUUSD is priced in US dollars — gold price rises when the dollar weakens, falls when the dollar strengthens',
      'Gold has cleaner trending structure than most instruments, especially visible on the H4 timeframe',
      'Three sessions (Asia, London, New York) each have distinct character — the system is built around this',
      'Volatility is an opportunity when managed with structure, not when chased randomly',
    ],
  },
  {
    moduleNum: 1,
    lessonNum: 2,
    moduleTitle: 'Understanding the Gold Market',
    title: 'What drives gold price — macro fundamentals',
    readingTime: '7 min read',
    sections: [
      {
        type: 'paragraph',
        content:
          "You don't need to be a macroeconomist to trade gold profitably. But you do need to understand the handful of forces that move it. These forces are the background behind every H4 candle you'll ever analyse.",
      },
      {
        type: 'subheading',
        content: '1. US Dollar Strength (DXY)',
      },
      {
        type: 'paragraph',
        content:
          "Gold is priced in US dollars. When the dollar gets stronger, it takes fewer dollars to buy an ounce of gold — so gold's price falls. When the dollar weakens, gold rises. This inverse relationship is not perfect, but it holds often enough to be the first thing to check.",
      },
      {
        type: 'paragraph',
        content:
          "Watch the DXY (Dollar Index) as a background check. If DXY is in a strong uptrend, gold has a structural headwind. If DXY is falling, gold has a tailwind. The system doesn't trade DXY directly, but knowing its direction helps confirm or challenge our H4 bias.",
      },
      {
        type: 'subheading',
        content: '2. US Treasury Yields',
      },
      {
        type: 'paragraph',
        content:
          "Gold earns no yield. It just sits there. When US government bonds pay 5% interest, holding gold has an opportunity cost — you could be earning 5% instead. When yields rise sharply, money rotates from gold into bonds, and gold falls. When yields fall, gold becomes more attractive.",
      },
      {
        type: 'paragraph',
        content:
          "You don't need to watch yields in real-time. But during major economic events — Federal Reserve decisions, inflation data — yields can move sharply and gold reacts instantly. This is exactly why the system has a news filter.",
      },
      {
        type: 'subheading',
        content: '3. Risk Sentiment',
      },
      {
        type: 'paragraph',
        content:
          "Gold is a safe haven. When traders are scared — geopolitical crisis, bank failure, market crash — they buy gold. When they're confident and rotating into risk assets (stocks, high-yield), they sell gold.",
      },
      {
        type: 'paragraph',
        content:
          "You'll see this as sudden, large moves on news events. The system avoids trading in the 30 minutes around high-impact economic releases precisely because these moves can be violent and structurally unpredictable.",
      },
      {
        type: 'subheading',
        content: 'What this means for day-to-day trading',
      },
      {
        type: 'paragraph',
        content:
          "The macro picture sets the background direction for gold over weeks and months. The system reads this through the H4 timeframe — if H4 is trending up, macro forces are broadly supportive of buyers. We don't try to predict macro events. We just don't trade against the direction they've produced.",
      },
      {
        type: 'paragraph',
        content:
          "Within each session, price moves for micro reasons: order flow, institutions entering and exiting, technical levels being tested. This is where the three-pillar analysis happens. Macro explains the direction. Micro explains the timing.",
      },
      {
        type: 'callout',
        content:
          "Check the news before every session. One high-impact event — NFP, FOMC, CPI — can override any technical setup. The system does this automatically, but as a manual trader this habit is non-negotiable.",
      },
    ],
    takeaways: [
      'The three main drivers of gold: US dollar strength, Treasury yields, and risk sentiment',
      'Gold and the DXY (Dollar Index) move inversely — a rising dollar is a headwind for gold',
      'Rising yields reduce gold\'s appeal because gold earns nothing while bonds pay interest',
      'Macro direction sets the background bias. Technical analysis then finds the timing within that bias',
      'News events can override any technical setup — always check for high-impact events before a session',
    ],
  },
  {
    moduleNum: 1,
    lessonNum: 3,
    moduleTitle: 'Understanding the Gold Market',
    title: 'Session structure and the London-NY overlap',
    readingTime: '8 min read',
    sections: [
      {
        type: 'paragraph',
        content:
          "Gold doesn't behave the same at 2am as it does at 2pm. Understanding when the market is alive — and when it's just noise — is one of the most important edges available to any trader.",
      },
      {
        type: 'subheading',
        content: 'Asia (approx. 00:00 – 08:00 UTC)',
      },
      {
        type: 'paragraph',
        content:
          "Asia is the quietest session for gold. Tokyo, Sydney, and Singapore are active, but they have smaller order flow compared to what follows. Gold typically ranges in Asia — it doesn't trend hard. It tests prior levels, sometimes retests structure, and often consolidates.",
      },
      {
        type: 'paragraph',
        content:
          "Why does this matter? The Asia range becomes a reference for the rest of the day. If price breaks above Asia high during London, that's a breakout. If it fails to break Asia high, traders watch for a reversal. The system tracks Asia high and Asia low explicitly — they're fed to the AI as structural reference points every cycle.",
      },
      {
        type: 'subheading',
        content: 'London (approx. 08:00 – 12:00 UTC)',
      },
      {
        type: 'paragraph',
        content:
          "London opens and everything changes. European institutions, hedge funds, and professional traders enter the market with size. Gold typically makes its first real directional move of the day during London. Volume picks up sharply.",
      },
      {
        type: 'paragraph',
        content:
          "The first hour of London (08:00–09:00 UTC) is often the most important. This is when breakouts happen, when Asia liquidity gets swept, and when the day's direction is often established. A move that starts in the first hour of London frequently sets the tone for the rest of the trading day.",
      },
      {
        type: 'subheading',
        content: 'New York (approx. 13:00 – 17:00 UTC)',
      },
      {
        type: 'paragraph',
        content:
          "New York reinforces or reverses London. If London pushed gold up, New York might continue that move, consolidate, or reverse it depending on US economic data and dollar movement.",
      },
      {
        type: 'paragraph',
        content:
          "The London-New York overlap (13:00–17:00 UTC) is historically the highest volume period for gold. More participants, more liquidity, larger moves. This is where the most reliable momentum tends to occur.",
      },
      {
        type: 'subheading',
        content: "The system's trading windows",
      },
      {
        type: 'paragraph',
        content:
          "The AI operates in two main windows designed around when gold actually moves:",
      },
      {
        type: 'bullet_list',
        content: [
          'Window 1: 23:00 – 07:00 UTC — captures late Asia, pre-London positioning, and early London open',
          'Window 2: 08:00 – 18:00 UTC — captures the full London session and New York overlap',
        ],
      },
      {
        type: 'paragraph',
        content:
          "Outside these windows, the system sleeps. Not because nothing happens, but because the quality of setups drops sharply when institutional volume is absent.",
      },
      {
        type: 'subheading',
        content: 'The trap pattern',
      },
      {
        type: 'paragraph',
        content:
          "One of the most reliable patterns in gold is the session trap. Asia trends in one direction. London opens and runs price in the same direction — then violently reverses, trapping all the traders who bought the Asia move.",
      },
      {
        type: 'paragraph',
        content:
          "This happens because institutions use the thin Asia liquidity to move price into a level where retail stop losses and pending orders cluster. London then fills their orders against that liquidity. Knowing this pattern prevents you from being the one who gets trapped.",
      },
      {
        type: 'callout',
        content:
          "Don't trade when volume is low. Low volume means wide spreads, erratic candles, and stops that get hit by noise rather than meaningful price movement. The discipline of trading only during specific windows is built on the reality of when institutional participants are active.",
      },
    ],
    takeaways: [
      'Asia sets the range — Asia high and Asia low are structural reference points for the entire day',
      'London creates direction — the first hour of London (08:00–09:00 UTC) is the most important',
      'The London-NY overlap (13:00–17:00 UTC) is the highest-volume period for gold',
      'The session trap: Asia trends one way, London opens the same way, then reverses violently',
      'Trading outside active sessions means fighting noise, not price action',
    ],
  },
  {
    moduleNum: 1,
    lessonNum: 4,
    moduleTitle: 'Understanding the Gold Market',
    title: 'Reading market structure on gold charts',
    readingTime: '9 min read',
    sections: [
      {
        type: 'paragraph',
        content:
          "Market structure is the foundation of everything else in this system. Before momentum, before indicators, before news — you need to know whether price is trending up, trending down, or ranging. Everything else is secondary to this answer.",
      },
      {
        type: 'subheading',
        content: 'The three states',
      },
      {
        type: 'bullet_list',
        content: [
          'Uptrend: Higher highs (HH) and higher lows (HL). Each rally reaches a higher peak. Each pullback holds a higher base than the last.',
          'Downtrend: Lower highs (LH) and lower lows (LL). Each rally fails at a lower point. Each pullback breaks to a lower level than the last.',
          'Range: Neither. Price bounces between a ceiling and a floor without clearly breaking either. The system is selective in ranges and avoids them by default.',
        ],
      },
      {
        type: 'subheading',
        content: 'Why H4 is the primary reference',
      },
      {
        type: 'paragraph',
        content:
          "The system reads structure on the H4 (4-hour) timeframe as the primary directional reference. Why not H1 or M30? Because H4 is slow enough to filter out session noise while being fast enough to reflect current market conditions.",
      },
      {
        type: 'paragraph',
        content:
          "Think of H4 as the permission level. If H4 is in an uptrend, the system only looks for buy setups. It doesn't fight the structure. If H4 has no clear direction, the system becomes far more selective and often waits.",
      },
      {
        type: 'subheading',
        content: 'The EMA 9/21 as a structure confirmation tool',
      },
      {
        type: 'paragraph',
        content:
          "The system uses the 9-period and 21-period Exponential Moving Averages on H4 to confirm structural direction:",
      },
      {
        type: 'bullet_list',
        content: [
          'EMA 9 above EMA 21 → bullish structure, look for buys on pullbacks',
          'EMA 9 below EMA 21 → bearish structure, look for sells on rallies',
          'EMAs intertwined or crossing repeatedly → no clear bias, system waits',
        ],
      },
      {
        type: 'paragraph',
        content:
          "Important: the EMA gives the verdict, but you should understand why it gave that verdict by looking at actual price structure. The EMAs lag price by several hours on H4. A clean EMA signal means the trend has been established for a while — not that it's about to start. This is actually useful: it means the move has conviction.",
      },
      {
        type: 'subheading',
        content: 'The pullback principle — the most important concept in the system',
      },
      {
        type: 'paragraph',
        content:
          "We don't enter when all timeframes agree. We enter when the higher timeframe has direction, but the lower timeframes are temporarily moving against it.",
      },
      {
        type: 'paragraph',
        content:
          "Example: H4 is bullish (HHs and HLs, EMA 9 above EMA 21). Price pulls back on H1. M30 shows two or three bearish candles. That pullback is not a reversal — it's a retracement. The system looks to enter as the pullback loses momentum and buyers re-enter.",
      },
      {
        type: 'callout',
        content:
          "All timeframes agreeing = extended move, not a valid entry. If H4, H1, M30, and M15 are all pushing up simultaneously, price has already moved significantly. The optimal entry was on the pullback. Entering now means wide stop losses, poor risk-reward, and high probability of buying the top of a local move.",
      },
      {
        type: 'subheading',
        content: 'Key levels to mark on your chart',
      },
      {
        type: 'paragraph',
        content:
          "Before the AI analyses anything, these levels are already in its context. Learn to mark them yourself:",
      },
      {
        type: 'numbered_list',
        content: [
          'The last H4 swing high and swing low — where major orders and stops are placed',
          'The Asia session high and low — structural reference for the London session',
          'The current session high and low as it builds — the range the market is working within',
          'Any prior day\'s high or low that price is approaching — these attract price like magnets',
        ],
      },
      {
        type: 'paragraph',
        content:
          "When you learn to read these levels manually, you start to understand why the AI makes the decisions it makes. The decisions stop looking random and start looking systematic. That's the point of this entire module.",
      },
    ],
    takeaways: [
      'Three structural states: uptrend (HH/HL), downtrend (LH/LL), range — know which one you\'re in before anything else',
      'H4 is the primary reference — it\'s the "permission" timeframe that tells the system which side to be on',
      'EMA 9/21 on H4 confirms structure: 9 above 21 = bullish, 9 below 21 = bearish, intertwined = wait',
      'The pullback principle: enter when HTF has direction but LTF is temporarily moving against it',
      'When all timeframes agree, the move is likely extended — not just starting',
    ],
  },
];

export function getLesson(moduleNum: number, lessonNum: number): LessonData | null {
  return LESSONS.find(l => l.moduleNum === moduleNum && l.lessonNum === lessonNum) ?? null;
}

export function getLessonsForModule(moduleNum: number): LessonData[] {
  return LESSONS.filter(l => l.moduleNum === moduleNum);
}

export function getNextLesson(moduleNum: number, lessonNum: number): LessonData | null {
  const idx = LESSONS.findIndex(l => l.moduleNum === moduleNum && l.lessonNum === lessonNum);
  if (idx === -1 || idx === LESSONS.length - 1) return null;
  return LESSONS[idx + 1];
}

export function getPrevLesson(moduleNum: number, lessonNum: number): LessonData | null {
  const idx = LESSONS.findIndex(l => l.moduleNum === moduleNum && l.lessonNum === lessonNum);
  if (idx <= 0) return null;
  return LESSONS[idx - 1];
}
