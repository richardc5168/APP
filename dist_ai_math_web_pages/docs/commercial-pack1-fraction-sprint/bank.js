// 商用試賣內容包題庫（MVP）：小五分數應用題 10 單元 × 20 題 = 200 題
// 供頁面以 window.COMMERCIAL_PACK1_FRACTION_SPRINT_BANK 讀取。

(function () {
  const PACK_ID = 'commercial.pack1.g5.fraction_sprint.tw.v1';

  function gcd(a, b) {
    a = Math.abs(a);
    b = Math.abs(b);
    while (b !== 0) {
      const t = a % b;
      a = b;
      b = t;
    }
    return a || 1;
  }

  function simp(n, d) {
    if (d < 0) { d = -d; n = -n; }
    const g = gcd(n, d);
    n = n / g;
    d = d / g;
    if (d === 1) return String(n);
    return `${n}/${d}`;
  }

  function frac(n, d) {
    const s = simp(n, d);
    const parts = s.split('/');
    if (parts.length === 1) return { n: Number(parts[0]), d: 1, s };
    return { n: Number(parts[0]), d: Number(parts[1]), s };
  }

  function mulFracInt(f, k) {
    return frac(f.n * k, f.d);
  }

  function subFrac(a, b) {
    return frac(a.n * b.d - b.n * a.d, a.d * b.d);
  }

  function addFrac(a, b) {
    return frac(a.n * b.d + b.n * a.d, a.d * b.d);
  }

  function choose(arr, i) {
    return arr[i % arr.length];
  }

  // Kinds: original, remain, part_to_total, compare, remain_multi
  const UNITS = [
    { unit_id: 'U1', title: '找原量：已知 = 原量×分數', kind: 'original' },
    { unit_id: 'U2', title: '找剩下：先算剩下比例', kind: 'remain' },
    { unit_id: 'U3', title: '找部分：部分 = 原量×分數', kind: 'part_to_total' },
    { unit_id: 'U4', title: '兩步題：先部分再剩下', kind: 'remain' },
    { unit_id: 'U5', title: '比一比：差多少', kind: 'compare' },
    { unit_id: 'U6', title: '線段圖：連續量找原量', kind: 'original' },
    { unit_id: 'U7', title: '單位量：每 1 份是多少', kind: 'part_to_total' },
    { unit_id: 'U8', title: '混合分數：帶分數應用', kind: 'part_to_total' },
    { unit_id: 'U9', title: '多段剩下：同整體連續扣', kind: 'remain_multi' },
    { unit_id: 'U10', title: '綜合：誰比誰多/少', kind: 'compare' }
  ];

  const NAMES = ['小明', '小華', '小芸', '阿哲', '小安', '小倫', '小婷', '阿翔'];
  const ITEMS_COUNT = ['糖果', '貼紙', '彩色筆', '積木', '餅乾', '蘋果', '橘子', '鉛筆', '彈珠', '氣球'];
  const ITEMS_CONT = [
    { name: '繩子', unit: '公尺' }, { name: '果汁', unit: '公升' },
    { name: '路線', unit: '公里' }, { name: '布料', unit: '公尺' },
    { name: '水', unit: '公升' }, { name: '鐵絲', unit: '公尺' }
  ];

  function makeItem({ id, unit, difficulty, question, answer, hints, steps }) {
    return {
      id,
      pack_id: PACK_ID,
      kind: unit.kind,
      unit_id: unit.unit_id,
      difficulty,
      question,
      answer,
      hints,
      steps
    };
  }

  /* ── hint / step builders per kind ── */

  function hintsOriginal(fr, knownStr) {
    return [
      '先畫線段圖：把「原量」畫成 1 整條，已知部分標成對應分數。',
      `列式：已知 = 原量 × ${fr.s}，所以 原量 = 已知 ÷ ${fr.s}。`,
      `把「÷ 分數」改寫成「× 倒數」：已知 ÷ ${fr.s} = 已知 × ${fr.d}/${fr.n}。`
    ];
  }

  function stepsOriginal(fr, known, ans) {
    return [
      `讀題：已知是原量的 ${fr.s}，已知為 ${known}。`,
      `畫圖：把整條當 1，先標出 ${fr.s} 這一段就是 ${known}。`,
      `列式：${known} = 原量 × ${fr.s}。`,
      `原量 = ${known} ÷ ${fr.s} = ${known} × ${fr.d}/${fr.n}。`,
      `計算得到原量 = ${ans}。`,
      '檢查：把原量 × 分數，是否回到已知？'
    ];
  }

  function hintsRemain(frUsed) {
    const remain = subFrac(frac(1, 1), frUsed);
    return [
      '先畫線段圖：把總量畫成 1 整條，再分成「用掉」與「剩下」。',
      `用掉的是 ${frUsed.s}，剩下比例 = 1 − ${frUsed.s} = ${remain.s}。`,
      `剩下數量 = 總量 × ${remain.s}。`
    ];
  }

  function stepsRemain(total, frUsed, remainAns) {
    const remain = subFrac(frac(1, 1), frUsed);
    return [
      `總量 = ${total}。用掉比例 = ${frUsed.s}。`,
      `畫圖：整條 1 先標 ${frUsed.s}（用掉），其餘就是 ${remain.s}。`,
      `剩下比例 = 1 − ${frUsed.s} = ${remain.s}。`,
      `剩下 = ${total} × ${remain.s}。`,
      `計算：剩下 = ${remainAns}。`,
      '檢查：用掉 + 剩下 = 總量。'
    ];
  }

  function hintsRemainTwoStep(f1, f2) {
    return [
      `先找「基準量」：第二次用的 ${f2.s} 基準是「剩下的」而不是全部。`,
      `先算第一次剩下 = 總量 × (1 − ${f1.s})，再算第二次用掉 = 剩下 × ${f2.s}。`,
      `最後剩下 = 第一次剩下 − 第二次用掉。`
    ];
  }

  function stepsRemainTwoStep(total, f1, f2, remain1, used2, finalRemain) {
    return [
      `讀題：全部 = ${total}。先用 ${f1.s}，剩下的又用 ${f2.s}。`,
      `⚠️ 第二次的 ${f2.s} 是「剩下的」，不是全部的！`,
      `第一次剩下 = ${total} × (1 − ${f1.s}) = ${remain1}。`,
      `第二次用掉 = ${remain1} × ${f2.s} = ${used2}。`,
      `最後剩下 = ${remain1} − ${used2} = ${finalRemain}。`,
      `檢查：${used2} + ${finalRemain} = ${remain1}？✓`
    ];
  }

  function hintsMultiRemain(f1, f2) {
    const sum = addFrac(f1, f2);
    const remain = subFrac(frac(1, 1), sum);
    return [
      `注意：兩次都是從「全部」扣掉 → 先通分再加起來！`,
      `合計用掉 = ${f1.s} + ${f2.s} = ${sum.s}，剩下比例 = 1 − ${sum.s} = ${remain.s}。`,
      `剩下數量 = 總量 × ${remain.s}。`
    ];
  }

  function stepsMultiRemain(total, f1, f2, amt1, amt2, remainAmt) {
    const sum = addFrac(f1, f2);
    const remain = subFrac(frac(1, 1), sum);
    return [
      `讀題：全部 = ${total}。先送 ${f1.s}，又送 ${f2.s}（兩次都從全部扣）。`,
      `口訣：看到「又送了（全部的）…」→ 基準不變 → 加法！`,
      `先通分：${f1.s} + ${f2.s} = ${sum.s}。`,
      `合計送出 = ${total} × ${sum.s} = ${amt1 + amt2}。`,
      `剩下 = ${total} − ${amt1 + amt2} = ${remainAmt}。`,
      `檢查：${amt1} + ${amt2} + ${remainAmt} = ${total}？✓`
    ];
  }

  function hintsPart(frPart) {
    return [
      '先畫線段圖：把總量畫成 1 整條，圈出題目要的分數部分。',
      `列式：部分 = 總量 × ${frPart.s}。`,
      '如果出現混合分數，先轉成假分數再算。'
    ];
  }

  function stepsPart(total, frPart, partAns) {
    return [
      `總量 = ${total}。比例 = ${frPart.s}。`,
      `畫圖：整條 1 對應到 ${total}，其中 ${frPart.s} 那段就是要求的部分。`,
      `部分 = ${total} × ${frPart.s}。`,
      `計算：部分 = ${partAns}。`,
      '檢查：部分 ÷ 總量 = 比例（或接近）。'
    ];
  }

  function hintsCompare() {
    return [
      '先畫兩條同長線段（同一個總量 1），分別標出兩個分數。',
      '要比較差多少：用「大 − 小」。',
      '最後記得對應單位（顆/張/支…）。'
    ];
  }

  function stepsCompare(total, f1, f2, ans) {
    return [
      `總量 = ${total}。A = ${total} × ${f1.s}，B = ${total} × ${f2.s}。`,
      `畫圖：A 與 B 都以同一個總量 ${total} 為基準，先看哪一段較長。`,
      '先算出兩個部分各是多少。',
      `差 = |A − B| = ${ans}。`,
      '檢查：差不會超過總量。'
    ];
  }

  function hintsCompareWhoMore(f1, f2, nameA, nameB) {
    return [
      `${nameA}（${f1.s}）和${nameB}（${f2.s}）比大小：先通分。`,
      `分別算出各是多少，再看誰多誰少。`,
      '差 = 較多 − 較少。'
    ];
  }

  function stepsCompareWhoMore(total, f1, f2, a1, a2, diff, nameA, nameB, unitStr) {
    const bigger = a1 >= a2 ? nameA : nameB;
    return [
      `${nameA} = ${total} × ${f1.s} = ${a1} ${unitStr}，${nameB} = ${total} × ${f2.s} = ${a2} ${unitStr}。`,
      `比較：${bigger}比較多。`,
      `差 = ${Math.max(a1,a2)} − ${Math.min(a1,a2)} = ${diff} ${unitStr}。`,
      `檢查：${diff} < ${total}？✓`
    ];
  }

  /* ── helper: ensure total*f yields integer ── */
  function isClean(total, f) {
    return (total * f.n) % f.d === 0;
  }

  /* ── expanded fraction + total lists ── */
  const frList = [
    frac(1,2), frac(1,3), frac(2,3), frac(1,4), frac(3,4),
    frac(1,5), frac(2,5), frac(3,5), frac(4,5),
    frac(1,6), frac(5,6), frac(1,8), frac(3,8), frac(5,8), frac(7,8)
  ];

  const totals = [12, 15, 16, 18, 20, 24, 30, 32, 36, 40, 45, 48, 50, 56, 60, 72, 80, 90, 96, 120];

  /* ── question templates ── */
  const TPL_ORIG = [
    (n,it,f,k) => `${n} 有一些${it}。他把其中的 ${f.s} 用掉了，剛好用掉 ${k} 個${it}。請問原來有多少個${it}？`,
    (n,it,f,k) => `${n} 把全部${it}的 ${f.s} 送給朋友，送出了 ${k} 個。全部有多少個${it}？`,
    (n,it,f,k) => `班上有一些${it}。已知其中 ${f.s} 是 ${k} 個，全部有多少個${it}？`
  ];
  const TPL_REMAIN = [
    (n,it,f,t) => `${n} 原本有 ${t} 個${it}。他用掉了 ${f.s} 的${it}，請問還剩下多少個${it}？`,
    (n,it,f,t) => `一袋${it}有 ${t} 個。${n} 吃掉了其中的 ${f.s}，剩下幾個${it}？`,
    (n,it,f,t) => `${n} 帶了 ${t} 個${it}去學校，送出了 ${f.s} 給同學，還剩多少個？`
  ];
  const TPL_PART = [
    (n,it,f,t) => `${n} 有 ${t} 個${it}。其中有 ${f.s} 是新的，請問新的有多少個${it}？`,
    (n,it,f,t) => `圖書館有 ${t} 本書。${n} 借了其中的 ${f.s}，借了幾本？`,
    (n,it,f,t) => `${n} 的 ${t} 個${it}中，${f.s} 是紅色的，紅色有幾個？`
  ];
  const TPL_COMPARE = [
    (n,it,f1,f2,t) => `${n} 有 ${t} 個${it}。他把其中的 ${f1.s} 分給同學，另外又把 ${f2.s} 分給老師。請問分給同學和分給老師相差多少個${it}？`,
    (n,it,f1,f2,t) => `${n} 有 ${t} 個${it}，早上用 ${f1.s}，下午又用 ${f2.s}，兩次相差幾個？`
  ];

  // Generate 200 questions
  const bank = [];
  let idCounter = 1;

  for (let u = 0; u < UNITS.length; u++) {
    const unit = UNITS[u];

    for (let i = 0; i < 20; i++) {
      const name = choose(NAMES, u * 20 + i);
      const difficulty = i < 6 ? 1 : i < 14 ? 2 : 3;

      /* ── pick fraction + total ensuring integer result ── */
      let f, total, itemName;

      // default: countable item
      itemName = choose(ITEMS_COUNT, i + u);

      // pick fraction
      f = choose(frList, i + u * 3);

      // pick total ensuring clean division
      let tIdx = (i * 2 + u) % totals.length;
      total = totals[tIdx];
      for (let _try = 0; _try < totals.length; _try++) {
        if (isClean(totals[(tIdx + _try) % totals.length], f)) {
          total = totals[(tIdx + _try) % totals.length];
          break;
        }
      }

      let q = '';
      let ans = '';
      let hints = [];
      let steps = [];

      /* ========== U1: standard original (find the whole) ========== */
      if (unit.unit_id === 'U1') {
        const knownF = mulFracInt(f, total);
        q = choose(TPL_ORIG, i)(name, itemName, f, knownF.s);
        ans = String(total);
        hints = hintsOriginal(f, knownF.s);
        steps = stepsOriginal(f, knownF.s, ans);

      /* ========== U2: standard remain ========== */
      } else if (unit.unit_id === 'U2') {
        const remainF = mulFracInt(subFrac(frac(1,1), f), total);
        q = choose(TPL_REMAIN, i)(name, itemName, f, total);
        ans = remainF.s;
        hints = hintsRemain(f);
        steps = stepsRemain(total, f, ans);

      /* ========== U3: standard part_to_total ========== */
      } else if (unit.unit_id === 'U3') {
        const partF = mulFracInt(f, total);
        q = choose(TPL_PART, i)(name, itemName, f, total);
        ans = partF.s;
        hints = hintsPart(f);
        steps = stepsPart(total, f, ans);

      /* ========== U4: two-step remain (剩下的又) ========== */
      } else if (unit.unit_id === 'U4') {
        const remain1 = total * (f.d - f.n) / f.d;
        const f2Cands = frList.filter(function(x) {
          if (x.s === f.s) return false;
          if (remain1 % x.d !== 0) return false;
          var u2 = remain1 * x.n / x.d;
          return (remain1 - u2) > 0 && Number.isInteger(remain1 - u2);
        });
        if (f2Cands.length > 0) {
          const f2 = choose(f2Cands, i + u * 7);
          const used2 = remain1 * f2.n / f2.d;
          const finalRemain = remain1 - used2;
          q = `${name} 原本有 ${total} 個${itemName}。他先用掉了 ${f.s}，剩下的又用掉了 ${f2.s}，請問最後還剩下多少個${itemName}？`;
          ans = String(finalRemain);
          hints = hintsRemainTwoStep(f, f2);
          steps = stepsRemainTwoStep(total, f, f2, remain1, used2, finalRemain);
        } else {
          const remainF = mulFracInt(subFrac(frac(1,1), f), total);
          q = `${name} 原本有 ${total} 個${itemName}。他用掉了 ${f.s} 的${itemName}，請問還剩下多少個${itemName}？`;
          ans = remainF.s;
          hints = hintsRemain(f);
          steps = stepsRemain(total, f, ans);
        }

      /* ========== U5: standard compare ========== */
      } else if (unit.unit_id === 'U5') {
        const f2 = choose(frList, i + u * 5 + 1);
        const t5 = isClean(total, f2) ? total : (() => {
          for (let tt = 0; tt < totals.length; tt++) {
            const tv = totals[(tIdx + tt) % totals.length];
            if (isClean(tv, f) && isClean(tv, f2)) return tv;
          }
          return total;
        })();
        const a1 = mulFracInt(f, t5);
        const a2 = mulFracInt(f2, t5);
        const diff = frac(Math.abs(a1.n * a2.d - a2.n * a1.d), a1.d * a2.d);
        q = choose(TPL_COMPARE, i)(name, itemName, f, f2, t5);
        ans = diff.s;
        hints = hintsCompare();
        steps = stepsCompare(t5, f, f2, ans);

      /* ========== U6: 線段圖 — continuous-unit original ========== */
      } else if (unit.unit_id === 'U6') {
        const ci = choose(ITEMS_CONT, i + u);
        const knownF = mulFracInt(f, total);
        const templates = [
          `一段${ci.name}的 ${f.s} 是 ${knownF.s} ${ci.unit}。請問這段${ci.name}全長多少${ci.unit}？`,
          `${name} 量了一條${ci.name}，發現其中 ${f.s} 的長度是 ${knownF.s} ${ci.unit}，這條${ci.name}全長多少${ci.unit}？`,
          `水池裡的${ci.name === '水' ? '水' : ci.name}有 ${knownF.s} ${ci.unit}，佔全部的 ${f.s}。全部有多少${ci.unit}？`
        ];
        q = choose(templates, i);
        ans = String(total);
        hints = [
          `先畫一條線段代表全部，標出 ${f.s} 那段 = ${knownF.s} ${ci.unit}。`,
          `列式：${knownF.s} = 全部 × ${f.s}，所以 全部 = ${knownF.s} ÷ ${f.s}。`,
          `把「÷ 分數」改成「× 倒數」：${knownF.s} × ${f.d}/${f.n}，算算看！`
        ];
        steps = stepsOriginal(f, knownF.s, ans);

      /* ========== U7: 單位量 — 每份是多少 (part_to_total variant) ========== */
      } else if (unit.unit_id === 'U7') {
        const ci = choose(ITEMS_CONT, i + u + 2);
        const partAmt = total * f.n / f.d;
        const perUnit = total / f.d;
        const templates = [
          `一桶${ci.name}有 ${total} ${ci.unit}。${name} 倒了其中的 ${f.s}，請問倒了多少${ci.unit}？（每等份 = ${perUnit} ${ci.unit}）`,
          `${name} 有 ${total} ${ci.unit}的${ci.name}，用掉了 ${f.s}，用掉多少${ci.unit}？`,
          `全校要走 ${total} ${ci.unit}的${ci.name === '路線' ? '路線' : '路程'}。目前走了 ${f.s}，走了多少${ci.unit}？`
        ];
        q = choose(templates, i);
        ans = String(partAmt);
        hints = [
          `畫線段圖：全長 ${total} ${ci.unit}，分成 ${f.d} 等份。`,
          `每份 = ${total} ÷ ${f.d} = ${perUnit} ${ci.unit}。取 ${f.n} 份。`,
          `部分 = ${total} × ${f.s}，算出來填上去吧！`
        ];
        steps = stepsPart(total, f, String(partAmt));

      /* ========== U8: 混合分數 — 帶分數應用 ========== */
      } else if (unit.unit_id === 'U8') {
        // generate with larger total so answer can be interesting
        const ci = choose(ITEMS_CONT, i + u + 1);
        // Use a mixed number context: e.g. total = W whole + n/d
        // We'll use integer total * fraction that gives a sizable result
        const bigTotals = [24, 30, 36, 40, 48, 56, 60, 72, 80, 96, 120];
        const bt = choose(bigTotals, i + u * 2);
        const fMixed = choose([frac(1,4), frac(1,3), frac(2,5), frac(3,8), frac(1,6), frac(2,3), frac(3,4), frac(5,8)], i + u);
        const tv = isClean(bt, fMixed) ? bt : (() => {
          for (let tt = 0; tt < bigTotals.length; tt++) {
            if (isClean(bigTotals[(tt) % bigTotals.length], fMixed)) return bigTotals[tt % bigTotals.length];
          }
          return bt;
        })();
        const partAmt = tv * fMixed.n / fMixed.d;
        // Express total as a mixed number if possible, otherwise use integer
        const wholeP = Math.floor(tv / fMixed.d);
        const remP = tv % fMixed.d;
        const mixedStr = remP > 0 ? `${wholeP} 又 ${remP}/${fMixed.d}` : String(tv);
        const templates = [
          `一段${ci.name}長 ${tv} ${ci.unit}。${name} 用了全長的 ${fMixed.s}，請問用了多少${ci.unit}？`,
          `${name} 有 ${tv} ${ci.unit}的${ci.name}。如果取其中的 ${fMixed.s} 來用，取了多少${ci.unit}？`,
          `池塘有 ${tv} ${ci.unit}的${ci.name === '水' ? '水' : ci.name}。蒸發了 ${fMixed.s}，蒸發了多少${ci.unit}？`
        ];
        q = choose(templates, i);
        ans = String(partAmt);
        hints = [
          `看到大數乘分數 → 先把 ${tv} × ${fMixed.s} 拆開算。`,
          `${tv} × ${fMixed.n}/${fMixed.d} = (${tv} ÷ ${fMixed.d}) × ${fMixed.n}。`,
          `先除再乘：${tv} ÷ ${fMixed.d} 再 × ${fMixed.n}，算算看！`
        ];
        steps = [
          `讀題：全部 = ${tv} ${ci.unit}，取 ${fMixed.s}。`,
          `列式：${tv} × ${fMixed.s}。`,
          `先除：${tv} ÷ ${fMixed.d} = ${tv / fMixed.d}。`,
          `再乘：${tv / fMixed.d} × ${fMixed.n} = ${partAmt}。`,
          `答案 = ${partAmt} ${ci.unit}。`,
          `檢查：${partAmt} < ${tv}？✓`
        ];

      /* ========== U9: 多段剩下 — 同一整體連續扣 (remain_multi) ========== */
      } else if (unit.unit_id === 'U9') {
        // Find f1, f2 where f1+f2 < 1 and total*(1−f1−f2) is integer
        const f2Pool = frList.filter(function(x) {
          if (x.s === f.s) return false;
          const sumF = addFrac(f, x);
          if (sumF.n >= sumF.d) return false; // f1+f2 >= 1
          const remN = sumF.d - sumF.n;
          return (total * remN) % sumF.d === 0;
        });
        if (f2Pool.length > 0) {
          const f2 = choose(f2Pool, i + u * 7);
          const amt1 = total * f.n / f.d;
          const amt2 = total * f2.n / f2.d;
          const remainAmt = total - amt1 - amt2;
          const roleA = choose(['同學', '弟弟', '爸爸', '姐姐'], i);
          const roleB = choose(['老師', '妹妹', '媽媽', '哥哥'], i + 1);
          q = `${name} 有 ${total} 個${itemName}。他先送了全部的 ${f.s} 給${roleA}，又送了全部的 ${f2.s} 給${roleB}，請問還剩下多少個${itemName}？`;
          ans = String(remainAmt);
          hints = hintsMultiRemain(f, f2);
          steps = stepsMultiRemain(total, f, f2, amt1, amt2, remainAmt);
        } else {
          // fallback: single-step remain
          const remainF = mulFracInt(subFrac(frac(1,1), f), total);
          q = `${name} 原本有 ${total} 個${itemName}。他用掉了 ${f.s} 的${itemName}，請問還剩下多少個${itemName}？`;
          ans = remainF.s;
          hints = hintsRemain(f);
          steps = stepsRemain(total, f, ans);
        }

      /* ========== U10: 誰比誰多/少 (compare variant) ========== */
      } else if (unit.unit_id === 'U10') {
        const name2 = choose(NAMES, u * 20 + i + 3);
        const f2 = choose(frList, i + u * 5 + 2);
        const t10 = (() => {
          for (let tt = 0; tt < totals.length; tt++) {
            const tv = totals[(tIdx + tt) % totals.length];
            if (isClean(tv, f) && isClean(tv, f2)) return tv;
          }
          return total;
        })();
        const a1 = t10 * f.n / f.d;
        const a2 = t10 * f2.n / f2.d;
        const diff = Math.abs(a1 - a2);
        q = `果園有 ${t10} 棵果樹。${name} 負責澆其中的 ${f.s}，${name2} 負責澆 ${f2.s}。請問${name} 比 ${name2} 多澆（或少澆）幾棵？`;
        ans = String(diff);
        hints = hintsCompareWhoMore(f, f2, name, name2);
        steps = stepsCompareWhoMore(t10, f, f2, a1, a2, diff, name, name2, '棵');

      /* ========== fallback ========== */
      } else {
        const knownF = mulFracInt(f, total);
        q = `${name} 有一些${itemName}。他把其中的 ${f.s} 用掉了，剛好用掉 ${knownF.s} 個${itemName}。請問原來有多少個${itemName}？`;
        ans = String(total);
        hints = hintsOriginal(f, knownF.s);
        steps = stepsOriginal(f, knownF.s, ans);
      }

      // Ensure hints/steps exist
      if (!Array.isArray(hints) || hints.length < 3) {
        hints = [
          '先找基準量（題目是以誰為 1）。',
          '把比例寫成算式，分清楚「乘」或「除」。',
          '最後檢查答案是否合理。'
        ];
      }
      if (!Array.isArray(steps) || steps.length < 4) {
        steps = [
          '讀題找基準量。',
          '列式。',
          '計算。',
          '檢查。'
        ];
      }

      const id = `CP1-FS-${String(idCounter).padStart(4, '0')}`;
      bank.push(makeItem({ id, unit, difficulty, question: q, answer: ans, hints, steps }));
      idCounter++;
    }
  }

  window.COMMERCIAL_PACK1_FRACTION_SPRINT_BANK = bank;
})();
