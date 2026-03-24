// diagrams.js — Visual cards for 競争の戦略 (Competitive Strategy) chapters
// Each chapter maps to an array of SVG diagrams and/or cheatsheet cards.

const CHAPTER_VISUALS = {

  // ========================================================================
  // 第0章: 本書の概要
  // ========================================================================
  "第0章": [
    {
      type: "svg",
      title: "競争戦略の輪",
      render: function(container) {
        var ns = "http://www.w3.org/2000/svg";
        var svg = document.createElementNS(ns, "svg");
        svg.setAttribute("viewBox", "0 0 320 280");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.style.fontFamily = "'Noto Sans JP', sans-serif";

        // Background
        var bg = document.createElementNS(ns, "rect");
        bg.setAttribute("width", "320");
        bg.setAttribute("height", "280");
        bg.setAttribute("fill", "#141414");
        svg.appendChild(bg);

        // Center hub
        var cx = 160, cy = 140, innerR = 36, outerR = 110;

        var hubCircle = document.createElementNS(ns, "circle");
        hubCircle.setAttribute("cx", cx);
        hubCircle.setAttribute("cy", cy);
        hubCircle.setAttribute("r", innerR);
        hubCircle.setAttribute("fill", "none");
        hubCircle.setAttribute("stroke", "#D4AF37");
        hubCircle.setAttribute("stroke-width", "2");
        svg.appendChild(hubCircle);

        // Center text
        var centerLines = ["目標", "方針"];
        centerLines.forEach(function(txt, i) {
          var t = document.createElementNS(ns, "text");
          t.setAttribute("x", cx);
          t.setAttribute("y", cy - 4 + i * 16);
          t.setAttribute("text-anchor", "middle");
          t.setAttribute("fill", "#D4AF37");
          t.setAttribute("font-size", "11");
          t.setAttribute("font-weight", "bold");
          t.textContent = txt;
          svg.appendChild(t);
        });

        // Spokes
        var spokes = [
          "製品ライン", "ターゲット市場", "マーケティング",
          "販売", "流通", "製造",
          "天然資源", "労務", "調達",
          "研究開発", "財務と\nコントロール", "経営管理"
        ];
        var n = spokes.length;

        spokes.forEach(function(label, i) {
          var angle = (2 * Math.PI * i / n) - Math.PI / 2;
          var x1 = cx + innerR * Math.cos(angle);
          var y1 = cy + innerR * Math.sin(angle);
          var x2 = cx + outerR * Math.cos(angle);
          var y2 = cy + outerR * Math.sin(angle);

          // Spoke line
          var line = document.createElementNS(ns, "line");
          line.setAttribute("x1", x1);
          line.setAttribute("y1", y1);
          line.setAttribute("x2", x2);
          line.setAttribute("y2", y2);
          line.setAttribute("stroke", "#D4AF37");
          line.setAttribute("stroke-width", "1");
          line.setAttribute("stroke-opacity", "0.5");
          svg.appendChild(line);

          // Outer dot
          var dot = document.createElementNS(ns, "circle");
          dot.setAttribute("cx", x2);
          dot.setAttribute("cy", y2);
          dot.setAttribute("r", "3");
          dot.setAttribute("fill", "#D4AF37");
          svg.appendChild(dot);

          // Label
          var labelX = cx + (outerR + 16) * Math.cos(angle);
          var labelY = cy + (outerR + 16) * Math.sin(angle);
          var anchor = "middle";
          if (Math.cos(angle) < -0.3) anchor = "end";
          else if (Math.cos(angle) > 0.3) anchor = "start";

          var parts = label.split("\n");
          parts.forEach(function(part, pi) {
            var t = document.createElementNS(ns, "text");
            t.setAttribute("x", labelX);
            t.setAttribute("y", labelY + pi * 10 - (parts.length - 1) * 4);
            t.setAttribute("text-anchor", anchor);
            t.setAttribute("fill", "#F5F5F5");
            t.setAttribute("font-size", "7.5");
            t.textContent = part;
            svg.appendChild(t);
          });
        });

        // Outer ring (dashed)
        var outerRing = document.createElementNS(ns, "circle");
        outerRing.setAttribute("cx", cx);
        outerRing.setAttribute("cy", cy);
        outerRing.setAttribute("r", outerR);
        outerRing.setAttribute("fill", "none");
        outerRing.setAttribute("stroke", "#D4AF37");
        outerRing.setAttribute("stroke-width", "1");
        outerRing.setAttribute("stroke-dasharray", "4 3");
        outerRing.setAttribute("stroke-opacity", "0.4");
        svg.appendChild(outerRing);

        // Title
        var title = document.createElementNS(ns, "text");
        title.setAttribute("x", cx);
        title.setAttribute("y", 16);
        title.setAttribute("text-anchor", "middle");
        title.setAttribute("fill", "#D4AF37");
        title.setAttribute("font-size", "10");
        title.setAttribute("font-weight", "bold");
        title.textContent = "競争戦略の輪（図表I）";
        svg.appendChild(title);

        container.appendChild(svg);
      }
    },
    {
      type: "cheatsheet",
      title: "本書の3つの狙い + 暗示的 vs 明示的戦略",
      render: function(container) {
        var html = '<div class="space-y-3">';

        // 3つの狙い
        html += '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">本書の3つの狙い</h4>';
        html += '<ol class="list-decimal list-inside text-textPrimary text-xs space-y-1.5">';
        html += '<li>業界における<span class="text-cta">競争の性質</span>を決める基本原理を理解する</li>';
        html += '<li>競争業者の<span class="text-cta">ビヘイビア</span>を形づくる諸要因を把握する</li>';
        html += '<li>効果的な<span class="text-cta">競争戦略を策定</span>するための方法を習得する</li>';
        html += '</ol>';
        html += '</div>';

        // 暗示的 vs 明示的
        html += '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">暗示的戦略 vs 明示的戦略</h4>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta w-1/4"></th>';
        html += '<th class="text-left py-1 text-cta">暗示的戦略</th>';
        html += '<th class="text-left py-1 text-cta">明示的戦略</th>';
        html += '</tr></thead><tbody class="text-textPrimary">';
        html += '<tr class="border-b border-border"><td class="py-1 text-cta">定義</td>';
        html += '<td class="py-1">各職能部門の活動から<br>何となく生まれる戦略</td>';
        html += '<td class="py-1">戦略計画という作業で<br>意図的に策定される戦略</td></tr>';
        html += '<tr class="border-b border-border"><td class="py-1 text-cta">特徴</td>';
        html += '<td class="py-1">部門ごとの最適化</td>';
        html += '<td class="py-1">全体最適・一貫性</td></tr>';
        html += '<tr><td class="py-1 text-cta">結果</td>';
        html += '<td class="py-1">ベストの戦略には<br>ほとんどならない</td>';
        html += '<td class="py-1">目標とポリシーが<br>車輪のように連動する</td></tr>';
        html += '</tbody></table>';
        html += '</div>';

        // 戦略策定の4要因
        html += '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">戦略策定に影響する4つの要因</h4>';
        html += '<div class="grid grid-cols-2 gap-2 text-xs text-textPrimary">';
        html += '<div class="border border-border rounded p-2"><span class="text-cta font-bold">内部</span><br>会社の長所と短所</div>';
        html += '<div class="border border-border rounded p-2"><span class="text-cta font-bold">内部</span><br>戦略実行者の個人的特性</div>';
        html += '<div class="border border-border rounded p-2"><span class="text-cta font-bold">外部</span><br>業界の好機と脅威</div>';
        html += '<div class="border border-border rounded p-2"><span class="text-cta font-bold">外部</span><br>社会からの期待</div>';
        html += '</div>';
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;
      }
    }
  ],

  // ========================================================================
  // 第1章: 業界の構造分析法
  // ========================================================================
  "第1章": [
    {
      type: "svg",
      title: "五つの競争要因（Five Forces）",
      render: function(container) {
        var ns = "http://www.w3.org/2000/svg";
        var svg = document.createElementNS(ns, "svg");
        svg.setAttribute("viewBox", "0 0 320 280");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.style.fontFamily = "'Noto Sans JP', sans-serif";

        // Background
        var bg = document.createElementNS(ns, "rect");
        bg.setAttribute("width", "320");
        bg.setAttribute("height", "280");
        bg.setAttribute("fill", "#141414");
        svg.appendChild(bg);

        var cx = 160, cy = 145;

        // Title
        var title = document.createElementNS(ns, "text");
        title.setAttribute("x", cx);
        title.setAttribute("y", 16);
        title.setAttribute("text-anchor", "middle");
        title.setAttribute("fill", "#D4AF37");
        title.setAttribute("font-size", "10");
        title.setAttribute("font-weight", "bold");
        title.textContent = "五つの競争要因（Five Forces）";
        svg.appendChild(title);

        // Helper: rounded rect
        function addBox(x, y, w, h, label, labelLines) {
          var rect = document.createElementNS(ns, "rect");
          rect.setAttribute("x", x);
          rect.setAttribute("y", y);
          rect.setAttribute("width", w);
          rect.setAttribute("height", h);
          rect.setAttribute("rx", "4");
          rect.setAttribute("fill", "none");
          rect.setAttribute("stroke", "#D4AF37");
          rect.setAttribute("stroke-width", "1.5");
          svg.appendChild(rect);

          var lines = labelLines || [label];
          lines.forEach(function(txt, i) {
            var t = document.createElementNS(ns, "text");
            t.setAttribute("x", x + w / 2);
            t.setAttribute("y", y + h / 2 + (i - (lines.length - 1) / 2) * 13);
            t.setAttribute("text-anchor", "middle");
            t.setAttribute("dominant-baseline", "central");
            t.setAttribute("fill", "#F5F5F5");
            t.setAttribute("font-size", "9");
            t.setAttribute("font-weight", "bold");
            t.textContent = txt;
            svg.appendChild(t);
          });

          return { cx: x + w / 2, cy: y + h / 2, x: x, y: y, w: w, h: h };
        }

        // Helper: arrow line
        function addArrow(x1, y1, x2, y2, label) {
          var line = document.createElementNS(ns, "line");
          line.setAttribute("x1", x1);
          line.setAttribute("y1", y1);
          line.setAttribute("x2", x2);
          line.setAttribute("y2", y2);
          line.setAttribute("stroke", "#D4AF37");
          line.setAttribute("stroke-width", "1.2");
          line.setAttribute("marker-end", "url(#arrowhead)");
          svg.appendChild(line);

          if (label) {
            var mx = (x1 + x2) / 2;
            var my = (y1 + y2) / 2;
            var t = document.createElementNS(ns, "text");
            t.setAttribute("x", mx + 4);
            t.setAttribute("y", my - 4);
            t.setAttribute("fill", "#6B6B6B");
            t.setAttribute("font-size", "7");
            t.textContent = label;
            svg.appendChild(t);
          }
        }

        // Arrowhead marker
        var defs = document.createElementNS(ns, "defs");
        var marker = document.createElementNS(ns, "marker");
        marker.setAttribute("id", "arrowhead");
        marker.setAttribute("markerWidth", "8");
        marker.setAttribute("markerHeight", "6");
        marker.setAttribute("refX", "8");
        marker.setAttribute("refY", "3");
        marker.setAttribute("orient", "auto");
        var path = document.createElementNS(ns, "path");
        path.setAttribute("d", "M0,0 L8,3 L0,6 Z");
        path.setAttribute("fill", "#D4AF37");
        marker.appendChild(path);
        defs.appendChild(marker);
        svg.appendChild(defs);

        // Center box
        var center = addBox(100, 115, 120, 52, null, ["業界内の", "競争（敵対関係）"]);

        // Top: 新規参入の脅威
        var top = addBox(110, 28, 100, 36, null, ["新規参入の脅威"]);

        // Bottom: 代替製品の脅威
        var bottom = addBox(110, 220, 100, 36, null, ["代替製品の脅威"]);

        // Left: 供給業者の交渉力
        var left = addBox(4, 122, 80, 40, null, ["供給業者の", "交渉力"]);

        // Right: 買い手の交渉力
        var right = addBox(236, 122, 80, 40, null, ["買い手の", "交渉力"]);

        // Arrows: top -> center
        addArrow(top.cx, top.y + top.h, center.cx, center.y);
        // Arrows: bottom -> center
        addArrow(bottom.cx, bottom.y, center.cx, center.y + center.h);
        // Arrows: left -> center
        addArrow(left.x + left.w, left.cy, center.x, center.cy);
        // Arrows: right -> center
        addArrow(right.x, right.cy, center.x + center.w, center.cy);

        // Subtitle labels along arrows
        var sub1 = document.createElementNS(ns, "text");
        sub1.setAttribute("x", top.cx + 55);
        sub1.setAttribute("y", (top.y + top.h + center.y) / 2 + 2);
        sub1.setAttribute("fill", "#6B6B6B");
        sub1.setAttribute("font-size", "6.5");
        sub1.textContent = "参入障壁";
        svg.appendChild(sub1);

        var sub2 = document.createElementNS(ns, "text");
        sub2.setAttribute("x", bottom.cx + 55);
        sub2.setAttribute("y", (center.y + center.h + bottom.y) / 2 + 2);
        sub2.setAttribute("fill", "#6B6B6B");
        sub2.setAttribute("font-size", "6.5");
        sub2.textContent = "代替の脅威";
        svg.appendChild(sub2);

        var sub3 = document.createElementNS(ns, "text");
        sub3.setAttribute("x", (left.x + left.w + center.x) / 2 - 10);
        sub3.setAttribute("y", left.cy - 8);
        sub3.setAttribute("fill", "#6B6B6B");
        sub3.setAttribute("font-size", "6.5");
        sub3.setAttribute("text-anchor", "middle");
        sub3.textContent = "売り手の力";
        svg.appendChild(sub3);

        var sub4 = document.createElementNS(ns, "text");
        sub4.setAttribute("x", (center.x + center.w + right.x) / 2 + 10);
        sub4.setAttribute("y", right.cy - 8);
        sub4.setAttribute("fill", "#6B6B6B");
        sub4.setAttribute("font-size", "6.5");
        sub4.setAttribute("text-anchor", "middle");
        sub4.textContent = "買い手の力";
        svg.appendChild(sub4);

        container.appendChild(svg);
      }
    },
    {
      type: "cheatsheet",
      title: "参入障壁の6源泉",
      render: function(container) {
        var html = '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">参入障壁の6つの源泉</h4>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta w-8">#</th>';
        html += '<th class="text-left py-1 text-cta">源泉</th>';
        html += '<th class="text-left py-1 text-cta">内容</th>';
        html += '</tr></thead><tbody class="text-textPrimary">';

        var barriers = [
          ["規模の経済性", "一定期間の生産量増で単位コスト低下。大規模参入か不利なコストを強いられる"],
          ["製品差別化", "既存企業のブランド・顧客忠誠度が新規参入者に多大な投資を要求する"],
          ["必要資本額", "R&D・設備・広告・在庫等への巨額投資が参入障壁となる"],
          ["スイッチングコスト", "買い手が仕入先を変更する際の再訓練・設備更新コストが切替を阻む"],
          ["流通チャネルの確保", "既存企業がチャネルを押さえており、新規参入者は割引や広告で棚を確保する必要がある"],
          ["規模に無関係な\nコスト不利", "独占的技術、原材料の有利な確保、有利な立地、エクスペリエンス曲線、政府の規制など"]
        ];

        barriers.forEach(function(b, i) {
          var borderClass = i < barriers.length - 1 ? ' class="border-b border-border"' : '';
          html += '<tr' + borderClass + '>';
          html += '<td class="py-1.5 text-cta font-bold align-top">' + (i + 1) + '</td>';
          html += '<td class="py-1.5 font-bold align-top whitespace-pre-line">' + b[0] + '</td>';
          html += '<td class="py-1.5">' + b[1] + '</td>';
          html += '</tr>';
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
      }
    },
    {
      type: "cheatsheet",
      title: "各Forceを強める条件リスト",
      render: function(container) {
        var html = '<div class="space-y-2">';

        var forces = [
          {
            name: "新規参入の脅威が高い条件",
            items: [
              "参入障壁が低い（資本・規模・ブランド不要）",
              "既存業者の報復が弱いと予想される",
              "業界の成長率が高く魅力的",
              "参入を抑える価格が高い水準にある"
            ]
          },
          {
            name: "既存業者間の敵対関係が激しい条件",
            items: [
              "同業者が多数 or 規模が均等",
              "業界の成長が鈍化",
              "固定コスト/在庫コストが高い",
              "製品差別化がなく、スイッチングコストが低い",
              "大幅なキャパシティ増設が必要",
              "競争業者の多様性（目標・戦略がバラバラ）",
              "撤退障壁が高い"
            ]
          },
          {
            name: "代替製品の脅威が高い条件",
            items: [
              "価格対性能の改善傾向にある代替品が存在",
              "高収益の業界が生産する代替品がある",
              "代替品のスイッチングコストが低い"
            ]
          },
          {
            name: "買い手の交渉力が強い条件",
            items: [
              "買い手が集中している / 大量購入する",
              "標準品・差別化がない製品を購入",
              "スイッチングコストが低い",
              "買い手が川上統合の姿勢を持つ",
              "買い手が十分な情報を保有している"
            ]
          },
          {
            name: "供給業者の交渉力が強い条件",
            items: [
              "少数企業が供給を支配",
              "供給品が差別化されている",
              "代替品が存在しない",
              "川下統合の姿勢がある",
              "当該業界が重要な顧客ではない",
              "労働力も供給業者として考慮すべき"
            ]
          }
        ];

        forces.forEach(function(force) {
          html += '<div class="bg-surface border border-border rounded p-2">';
          html += '<h5 class="text-cta font-bold text-xs mb-1">' + force.name + '</h5>';
          html += '<ul class="text-textPrimary text-xs space-y-0.5 list-disc list-inside">';
          force.items.forEach(function(item) {
            html += '<li>' + item + '</li>';
          });
          html += '</ul></div>';
        });

        html += '</div>';
        container.innerHTML = html;
      }
    }
  ],

  // ========================================================================
  // 第2章: 競争の基本戦略
  // ========================================================================
  "第2章": [
    {
      type: "svg",
      title: "3つの基本戦略マトリクス",
      render: function(container) {
        var ns = "http://www.w3.org/2000/svg";
        var svg = document.createElementNS(ns, "svg");
        svg.setAttribute("viewBox", "0 0 320 280");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.style.fontFamily = "'Noto Sans JP', sans-serif";

        // Background
        var bg = document.createElementNS(ns, "rect");
        bg.setAttribute("width", "320");
        bg.setAttribute("height", "280");
        bg.setAttribute("fill", "#141414");
        svg.appendChild(bg);

        // Title
        var title = document.createElementNS(ns, "text");
        title.setAttribute("x", 160);
        title.setAttribute("y", 18);
        title.setAttribute("text-anchor", "middle");
        title.setAttribute("fill", "#D4AF37");
        title.setAttribute("font-size", "10");
        title.setAttribute("font-weight", "bold");
        title.textContent = "三つの基本戦略（図表2-1）";
        svg.appendChild(title);

        // Grid area
        var gx = 80, gy = 55, gw = 210, gh = 180;
        var midX = gx + gw / 2;
        var midY = gy + gh / 2;

        // Outer border
        var border = document.createElementNS(ns, "rect");
        border.setAttribute("x", gx);
        border.setAttribute("y", gy);
        border.setAttribute("width", gw);
        border.setAttribute("height", gh);
        border.setAttribute("fill", "none");
        border.setAttribute("stroke", "#D4AF37");
        border.setAttribute("stroke-width", "1.5");
        svg.appendChild(border);

        // Vertical divider
        var vDiv = document.createElementNS(ns, "line");
        vDiv.setAttribute("x1", midX);
        vDiv.setAttribute("y1", gy);
        vDiv.setAttribute("x2", midX);
        vDiv.setAttribute("y2", gy + gh);
        vDiv.setAttribute("stroke", "#D4AF37");
        vDiv.setAttribute("stroke-width", "1");
        vDiv.setAttribute("stroke-dasharray", "4 2");
        svg.appendChild(vDiv);

        // Horizontal divider
        var hDiv = document.createElementNS(ns, "line");
        hDiv.setAttribute("x1", gx);
        hDiv.setAttribute("y1", midY);
        hDiv.setAttribute("x2", gx + gw);
        hDiv.setAttribute("y2", midY);
        hDiv.setAttribute("stroke", "#D4AF37");
        hDiv.setAttribute("stroke-width", "1");
        hDiv.setAttribute("stroke-dasharray", "4 2");
        svg.appendChild(hDiv);

        // Quadrant labels
        var quadrants = [
          { x: gx + gw * 0.25, y: gy + gh * 0.25, lines: ["コスト", "リーダーシップ"], sub: "業界全体 + 低コスト" },
          { x: gx + gw * 0.75, y: gy + gh * 0.25, lines: ["差別化"], sub: "業界全体 + 特異性" },
          { x: gx + gw * 0.25, y: gy + gh * 0.75, lines: ["コスト集中"], sub: "特定セグメント + 低コスト" },
          { x: gx + gw * 0.75, y: gy + gh * 0.75, lines: ["差別化集中"], sub: "特定セグメント + 特異性" }
        ];

        quadrants.forEach(function(q) {
          q.lines.forEach(function(line, i) {
            var t = document.createElementNS(ns, "text");
            t.setAttribute("x", q.x);
            t.setAttribute("y", q.y - 4 + i * 14);
            t.setAttribute("text-anchor", "middle");
            t.setAttribute("fill", "#F5F5F5");
            t.setAttribute("font-size", "10");
            t.setAttribute("font-weight", "bold");
            t.textContent = line;
            svg.appendChild(t);
          });
          var sub = document.createElementNS(ns, "text");
          sub.setAttribute("x", q.x);
          sub.setAttribute("y", q.y + q.lines.length * 14 + 2);
          sub.setAttribute("text-anchor", "middle");
          sub.setAttribute("fill", "#6B6B6B");
          sub.setAttribute("font-size", "6.5");
          sub.textContent = q.sub;
          svg.appendChild(sub);
        });

        // Axis labels - Top (戦略的有利性)
        var axisTop = document.createElementNS(ns, "text");
        axisTop.setAttribute("x", midX);
        axisTop.setAttribute("y", gy - 10);
        axisTop.setAttribute("text-anchor", "middle");
        axisTop.setAttribute("fill", "#D4AF37");
        axisTop.setAttribute("font-size", "8");
        axisTop.textContent = "戦略的有利性";
        svg.appendChild(axisTop);

        // Column headers
        var colL = document.createElementNS(ns, "text");
        colL.setAttribute("x", gx + gw * 0.25);
        colL.setAttribute("y", gy - 2);
        colL.setAttribute("text-anchor", "middle");
        colL.setAttribute("fill", "#6B6B6B");
        colL.setAttribute("font-size", "7");
        colL.textContent = "低コスト地位";
        svg.appendChild(colL);

        var colR = document.createElementNS(ns, "text");
        colR.setAttribute("x", gx + gw * 0.75);
        colR.setAttribute("y", gy - 2);
        colR.setAttribute("text-anchor", "middle");
        colR.setAttribute("fill", "#6B6B6B");
        colR.setAttribute("font-size", "7");
        colR.textContent = "特異性";
        svg.appendChild(colR);

        // Row labels (left side, rotated) - 戦略ターゲット
        var rowLabel = document.createElementNS(ns, "text");
        rowLabel.setAttribute("x", gx - 28);
        rowLabel.setAttribute("y", midY);
        rowLabel.setAttribute("text-anchor", "middle");
        rowLabel.setAttribute("fill", "#D4AF37");
        rowLabel.setAttribute("font-size", "8");
        rowLabel.setAttribute("transform", "rotate(-90 " + (gx - 28) + " " + midY + ")");
        rowLabel.textContent = "戦略ターゲット";
        svg.appendChild(rowLabel);

        var rowTop = document.createElementNS(ns, "text");
        rowTop.setAttribute("x", gx - 6);
        rowTop.setAttribute("y", gy + gh * 0.25);
        rowTop.setAttribute("text-anchor", "middle");
        rowTop.setAttribute("fill", "#6B6B6B");
        rowTop.setAttribute("font-size", "7");
        rowTop.setAttribute("transform", "rotate(-90 " + (gx - 6) + " " + (gy + gh * 0.25) + ")");
        rowTop.textContent = "業界全体";
        svg.appendChild(rowTop);

        var rowBot = document.createElementNS(ns, "text");
        rowBot.setAttribute("x", gx - 6);
        rowBot.setAttribute("y", gy + gh * 0.75);
        rowBot.setAttribute("text-anchor", "middle");
        rowBot.setAttribute("fill", "#6B6B6B");
        rowBot.setAttribute("font-size", "7");
        rowBot.setAttribute("transform", "rotate(-90 " + (gx - 6) + " " + (gy + gh * 0.75) + ")");
        rowBot.textContent = "特定セグメント";
        svg.appendChild(rowBot);

        // "Stuck in the Middle" note
        var note = document.createElementNS(ns, "text");
        note.setAttribute("x", 160);
        note.setAttribute("y", gy + gh + 22);
        note.setAttribute("text-anchor", "middle");
        note.setAttribute("fill", "#6B6B6B");
        note.setAttribute("font-size", "7.5");
        note.textContent = "※ どれにもコミットしない = 窮地に立った企業（Stuck in the Middle）";
        svg.appendChild(note);

        container.appendChild(svg);
      }
    },
    {
      type: "cheatsheet",
      title: "3戦略の定義・前提条件・リスク比較表",
      render: function(container) {
        var html = '<div class="bg-surface border border-border rounded p-3 overflow-x-auto">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">三つの基本戦略 比較表</h4>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta w-16"></th>';
        html += '<th class="text-left py-1 text-cta">コストリーダーシップ</th>';
        html += '<th class="text-left py-1 text-cta">差別化</th>';
        html += '<th class="text-left py-1 text-cta">集中</th>';
        html += '</tr></thead>';
        html += '<tbody class="text-textPrimary">';

        html += '<tr class="border-b border-border">';
        html += '<td class="py-1.5 text-cta font-bold align-top">定義</td>';
        html += '<td class="py-1.5">業界全体で最も低いコスト地位を確保</td>';
        html += '<td class="py-1.5">業界内で「特異」と認められる何かを創造</td>';
        html += '<td class="py-1.5">特定セグメントに資源を集中し、低コスト or 差別化を達成</td>';
        html += '</tr>';

        html += '<tr class="border-b border-border">';
        html += '<td class="py-1.5 text-cta font-bold align-top">必要な<br>資源</td>';
        html += '<td class="py-1.5">設備投資、工程エンジニアリング、厳密なコスト統制、定量的目標管理</td>';
        html += '<td class="py-1.5">マーケティング力、創造性、R&D調整力、主観的測定と報酬、ブランド構築</td>';
        html += '<td class="py-1.5">上記を特定ターゲットに適合させる組み合わせ</td>';
        html += '</tr>';

        html += '<tr class="border-b border-border">';
        html += '<td class="py-1.5 text-cta font-bold align-top">防衛力</td>';
        html += '<td class="py-1.5">五つの競争要因すべてに対して防衛力（買い手・供給業者への交渉力、参入障壁、代替品への耐性）</td>';
        html += '<td class="py-1.5">ブランド忠誠度が買い手の交渉力を弱め、参入障壁を高める</td>';
        html += '<td class="py-1.5">狭い領域で最も効率的 or 最も差別化された存在になる</td>';
        html += '</tr>';

        html += '<tr>';
        html += '<td class="py-1.5 text-cta font-bold align-top">主な<br>リスク</td>';
        html += '<td class="py-1.5">';
        html += '<ul class="list-disc list-inside space-y-0.5">';
        html += '<li>技術変化でコスト優位が無効化</li>';
        html += '<li>市場ニーズの変化を見逃す</li>';
        html += '<li>模倣者の出現</li>';
        html += '</ul></td>';
        html += '<td class="py-1.5">';
        html += '<ul class="list-disc list-inside space-y-0.5">';
        html += '<li>コスト差が開きすぎて忠誠度が維持不能に</li>';
        html += '<li>買い手ニーズの変化で差別化が不要に</li>';
        html += '<li>模倣で差別化要因が消失</li>';
        html += '</ul></td>';
        html += '<td class="py-1.5">';
        html += '<ul class="list-disc list-inside space-y-0.5">';
        html += '<li>広域企業とのコスト差が拡大</li>';
        html += '<li>ターゲット内外の製品差が縮小</li>';
        html += '<li>さらに小さいニッチの出現</li>';
        html += '</ul></td>';
        html += '</tr>';

        html += '</tbody></table>';

        // Stuck in the Middle note
        html += '<div class="mt-2 p-2 border border-border rounded bg-surface">';
        html += '<span class="text-cta font-bold text-xs">窮地に立った企業（Stuck in the Middle）:</span>';
        html += '<span class="text-textPrimary text-xs"> 三つの基本戦略のいずれにも明確にコミットしない企業は低収益に陥る。大量購入顧客はコスト企業に、高マージン商売は差別化企業に奪われる。</span>';
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;
      }
    }
  ],

  // ========================================================================
  // 第3章: 競争業者分析のフレームワーク
  // ========================================================================
  "第3章": [
    {
      type: "svg",
      title: "競争業者分析の4要素と反応プロフィール",
      render: function(container) {
        var ns = "http://www.w3.org/2000/svg";
        var svg = document.createElementNS(ns, "svg");
        svg.setAttribute("viewBox", "0 0 320 280");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.style.fontFamily = "'Noto Sans JP', sans-serif";

        // Background
        var bg = document.createElementNS(ns, "rect");
        bg.setAttribute("width", "320");
        bg.setAttribute("height", "280");
        bg.setAttribute("fill", "#141414");
        svg.appendChild(bg);

        // Arrowhead marker
        var defs = document.createElementNS(ns, "defs");
        var marker = document.createElementNS(ns, "marker");
        marker.setAttribute("id", "arrowhead3");
        marker.setAttribute("markerWidth", "8");
        marker.setAttribute("markerHeight", "6");
        marker.setAttribute("refX", "8");
        marker.setAttribute("refY", "3");
        marker.setAttribute("orient", "auto");
        var path = document.createElementNS(ns, "path");
        path.setAttribute("d", "M0,0 L8,3 L0,6 Z");
        path.setAttribute("fill", "#D4AF37");
        marker.appendChild(path);
        defs.appendChild(marker);
        svg.appendChild(defs);

        // Title
        var title = document.createElementNS(ns, "text");
        title.setAttribute("x", 160);
        title.setAttribute("y", 18);
        title.setAttribute("text-anchor", "middle");
        title.setAttribute("fill", "#D4AF37");
        title.setAttribute("font-size", "10");
        title.setAttribute("font-weight", "bold");
        title.textContent = "競争業者分析の4要素";
        svg.appendChild(title);

        // Helper: box with gold border
        function addBox(x, y, w, h, lines, subtextLines) {
          var rect = document.createElementNS(ns, "rect");
          rect.setAttribute("x", x);
          rect.setAttribute("y", y);
          rect.setAttribute("width", w);
          rect.setAttribute("height", h);
          rect.setAttribute("rx", "4");
          rect.setAttribute("fill", "#1a1a1a");
          rect.setAttribute("stroke", "#D4AF37");
          rect.setAttribute("stroke-width", "1.5");
          svg.appendChild(rect);

          lines.forEach(function(txt, i) {
            var t = document.createElementNS(ns, "text");
            t.setAttribute("x", x + w / 2);
            t.setAttribute("y", y + 16 + i * 13);
            t.setAttribute("text-anchor", "middle");
            t.setAttribute("fill", "#F5F5F5");
            t.setAttribute("font-size", "9");
            t.setAttribute("font-weight", "bold");
            t.textContent = txt;
            svg.appendChild(t);
          });

          if (subtextLines) {
            subtextLines.forEach(function(txt, i) {
              var st = document.createElementNS(ns, "text");
              st.setAttribute("x", x + w / 2);
              st.setAttribute("y", y + 16 + lines.length * 13 + 4 + i * 10);
              st.setAttribute("text-anchor", "middle");
              st.setAttribute("fill", "#6B6B6B");
              st.setAttribute("font-size", "6.5");
              st.textContent = txt;
              svg.appendChild(st);
            });
          }

          return { cx: x + w / 2, cy: y + h / 2, x: x, y: y, w: w, h: h };
        }

        // Top-left: 将来の目標
        var topLeft = addBox(16, 35, 128, 50, ["将来の目標"], ["何が行動の原動力か"]);

        // Top-right: 自己認識と仮説
        var topRight = addBox(176, 35, 128, 50, ["自己認識と仮説"], ["どんな思い込みがあるか"]);

        // Bottom-left: 現在の戦略
        var botLeft = addBox(16, 120, 128, 50, ["現在の戦略"], ["現在何をしているか"]);

        // Bottom-right: 能力
        var botRight = addBox(176, 120, 128, 50, ["能力（長所と短所）"], ["何ができるか"]);

        // Center: 反応プロフィール
        var centerY = 200;
        var centerBox = addBox(70, centerY, 180, 48, ["反応プロフィール"], ["競争業者は次に何をするか"]);

        // Arrows from 4 boxes to center
        function drawArrow(fromBox, toCx, toY) {
          var line = document.createElementNS(ns, "line");
          line.setAttribute("x1", fromBox.cx);
          line.setAttribute("y1", fromBox.y + fromBox.h);
          line.setAttribute("x2", toCx);
          line.setAttribute("y2", toY);
          line.setAttribute("stroke", "#D4AF37");
          line.setAttribute("stroke-width", "1");
          line.setAttribute("marker-end", "url(#arrowhead3)");
          svg.appendChild(line);
        }

        drawArrow(topLeft, centerBox.cx - 40, centerBox.y);
        drawArrow(topRight, centerBox.cx + 40, centerBox.y);
        drawArrow(botLeft, centerBox.cx - 20, centerBox.y);
        drawArrow(botRight, centerBox.cx + 20, centerBox.y);

        // Bottom note
        var note = document.createElementNS(ns, "text");
        note.setAttribute("x", 160);
        note.setAttribute("y", 268);
        note.setAttribute("text-anchor", "middle");
        note.setAttribute("fill", "#6B6B6B");
        note.setAttribute("font-size", "7");
        note.textContent = "4要素を統合して競争業者の次の動きを予測する";
        svg.appendChild(note);

        container.appendChild(svg);
      }
    },
    {
      type: "cheatsheet",
      title: "4要素の具体的な分析項目リスト",
      render: function(container) {
        var html = '<div class="space-y-2">';

        var elements = [
          {
            name: "将来の目標",
            color: "text-cta",
            items: [
              "財務目標（収益率、成長率、配当方針）",
              "マーケット・シェアの目標",
              "技術リーダーシップへの志向",
              "社会的価値観・企業としての自画像",
              "組織構造と経営管理方式",
              "経営トップの経歴・信念・過去の成功体験",
              "取締役会の構成、全員合意の程度",
              "親会社のポートフォリオ上の位置づけ（金のなる木 / 成長事業 / 刈り取り候補）"
            ]
          },
          {
            name: "自己認識と仮説",
            color: "text-cta",
            items: [
              "自社の強み・弱みについての思い込み",
              "業界トレンドについての前提（成長率、技術動向）",
              "競争業者についての仮説（誰が脅威か）",
              "業界固有の「常識」「定型化した知恵」",
              "歴史的類推（過去の成功パターンへの執着）",
              "盲点 = 事象を正しく認識できない分野"
            ]
          },
          {
            name: "現在の戦略",
            color: "text-cta",
            items: [
              "各機能分野での主要方針（製品、マーケティング、製造等）",
              "事業間の相互関係",
              "暗示的戦略 vs 明示的戦略の識別"
            ]
          },
          {
            name: "能力（長所と短所）",
            color: "text-cta",
            items: [
              "製品ラインの広さ・深さ・品質",
              "流通チャネルの強さ",
              "マーケティング・販売力",
              "生産能力・コスト構造",
              "研究開発・技術力",
              "財務力（キャッシュフロー、借入能力）",
              "組織力（経営層の質、従業員の士気）",
              "全般的な成長力・即応力"
            ]
          }
        ];

        elements.forEach(function(el) {
          html += '<div class="bg-surface border border-border rounded p-2">';
          html += '<h5 class="' + el.color + ' font-bold text-xs mb-1">' + el.name + '</h5>';
          html += '<ul class="text-textPrimary text-xs space-y-0.5 list-disc list-inside">';
          el.items.forEach(function(item) {
            html += '<li>' + item + '</li>';
          });
          html += '</ul></div>';
        });

        // 反応プロフィール section
        html += '<div class="bg-surface border border-border rounded p-2">';
        html += '<h5 class="text-cta font-bold text-xs mb-1">反応プロフィール（統合結果）</h5>';
        html += '<ul class="text-textPrimary text-xs space-y-0.5 list-disc list-inside">';
        html += '<li>競争業者は現在の地位に満足しているか？</li>';
        html += '<li>次にどんな動きをするか？</li>';
        html += '<li>弱点はどこか？</li>';
        html += '<li>最大の報復を引き起こすのはどんな動きか？</li>';
        html += '</ul></div>';

        html += '</div>';
        container.innerHTML = html;
      }
    }
  ],

  // ========================================================================
  // 第4章: マーケット・シグナル
  // ========================================================================
  "第4章": [
    {
      type: "cheatsheet",
      title: "シグナルの種類と機能一覧",
      render: function(container) {
        var html = '<div class="space-y-2">';

        html += '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">マーケット・シグナルの種類と機能</h4>';
        html += '<p class="text-textPrimary text-xs mb-2">企業の意図・動機・目標・社内状況を直接・間接に示す行動。「真のシグナル」と「見せかけ（ブラフ）」がある。</p>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta">種類</th>';
        html += '<th class="text-left py-1 text-cta">内容</th>';
        html += '<th class="text-left py-1 text-cta">例</th>';
        html += '</tr></thead><tbody class="text-textPrimary">';

        var signals = [
          ["動きの予告\n（事前発表）", "ある行動をとる意図の公式発表。実行義務なし", "TI社の半導体メモリー\n価格予告合戦"],
          ["事後の発表", "設備拡張・販売実績などすでに完了した事柄の確認", "マーケット・シェアの\n意図的誇張"],
          ["業界事情への\nコメント", "競争業者の「仮説」を明かすと同時に、他社の仮説形成を操作", "需要予測や業界動向\nについての公式発言"],
          ["採用しなかった\n戦術", "より攻撃的な手段をあえて選ばなかったことが懐柔の意図を示す", "値下げ余力があるが\n据え置く"],
          ["間接的な反撃", "ある地域での攻撃に対し別の地域で報復", "フォルジャー vs.\nマックスウェルのコーヒー戦争"],
          ["攻撃用ブランド\n（ファイティング・\nブランド）", "競争業者への警告・抑止・攻撃吸収が目的", "コカ・コーラの\nミスター・ピブ\n（対ドクター・ペッパー）"],
          ["反トラスト訴訟", "巨額の訴訟費用を強いて市場から撤退させる戦術", "大企業が弱小企業を\n訴える戦略的訴訟"]
        ];

        signals.forEach(function(s, i) {
          var borderClass = i < signals.length - 1 ? ' class="border-b border-border"' : '';
          html += '<tr' + borderClass + '>';
          html += '<td class="py-1.5 font-bold align-top whitespace-pre-line">' + s[0] + '</td>';
          html += '<td class="py-1.5 align-top">' + s[1] + '</td>';
          html += '<td class="py-1.5 align-top whitespace-pre-line">' + s[2] + '</td>';
          html += '</tr>';
        });

        html += '</tbody></table></div>';

        // Key insight
        html += '<div class="bg-surface border border-border rounded p-2">';
        html += '<p class="text-cta font-bold text-xs mb-1">読み解きのポイント</p>';
        html += '<ul class="text-textPrimary text-xs space-y-0.5 list-disc list-inside">';
        html += '<li>第3章の競争業者分析（目標・仮説・能力）がシグナル解釈の前提</li>';
        html += '<li>過去のシグナルと実際の行動の因果関係を記録しておくと精度が向上</li>';
        html += '<li>ブラフの判別には、シグナル発信企業の「能力」と「一貫性」を確認</li>';
        html += '</ul></div>';

        html += '</div>';
        container.innerHTML = html;
      }
    },
    {
      type: "cheatsheet",
      title: "予告（事前発表）の7つの機能",
      render: function(container) {
        var html = '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">動きの予告 — 7つの機能</h4>';
        html += '<p class="text-textPrimary text-xs mb-2">予告には実行義務がないため、特に懐柔・テスト目的で多用される。</p>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta w-6">#</th>';
        html += '<th class="text-left py-1 text-cta w-20">機能</th>';
        html += '<th class="text-left py-1 text-cta">説明</th>';
        html += '</tr></thead><tbody class="text-textPrimary">';

        var functions = [
          ["先取り", "同業者に先んじて有利な地位を占める。工場建設やキャパシティ拡大の予告で競合の計画を断念させる"],
          ["脅威", "予告した行動を実行する構えを見せ、競合に特定の行動を思いとどまらせる"],
          ["反応テスト", "競争業者の反応を見て、実際に行動するかどうかを判断する材料を得る"],
          ["歓迎/不快感の伝達", "競合の動きに対する賛否を示し、業界全体の行動パターンに影響を与える"],
          ["懐柔策", "競争相手への挑発を最小限に抑え、不要な対立を避ける。値上げ前の事前通知など"],
          ["市場混乱の回避", "同時期の値上げなど、業界全体の秩序ある移行を促す調整機能"],
          ["金融筋への情報提供", "株主・アナリスト・銀行への戦略意図の伝達。資本市場からの評価を意識した発信"]
        ];

        functions.forEach(function(f, i) {
          var borderClass = i < functions.length - 1 ? ' class="border-b border-border"' : '';
          html += '<tr' + borderClass + '>';
          html += '<td class="py-1.5 text-cta font-bold align-top">' + (i + 1) + '</td>';
          html += '<td class="py-1.5 font-bold align-top">' + f[0] + '</td>';
          html += '<td class="py-1.5">' + f[1] + '</td>';
          html += '</tr>';
        });

        html += '</tbody></table>';

        // TI example
        html += '<div class="mt-2 p-2 border border-border rounded">';
        html += '<p class="text-cta font-bold text-xs">典型例: TI社の半導体メモリー価格予告</p>';
        html += '<p class="text-textPrimary text-xs mt-1">テキサス・インスツルメンツがモトローラの半値の価格を予告し、実際の投資前に競争業者を撤退に追い込んだ。先取り + 脅威の機能が同時に作用した例。</p>';
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;
      }
    }
  ],

  // ========================================================================
  // 第5章: 競争行動
  // ========================================================================
  "第5章": [
    {
      type: "cheatsheet",
      title: "約束（コミットメント）の3タイプ",
      render: function(container) {
        var html = '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">約束（コミットメント）の3タイプ</h4>';
        html += '<p class="text-textPrimary text-xs mb-2">約束は攻撃・防御の最重要コンセプト。自社の意図と経営資源を明示し、競争相手の行動に影響を与える。</p>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta w-6">#</th>';
        html += '<th class="text-left py-1 text-cta w-24">タイプ</th>';
        html += '<th class="text-left py-1 text-cta">内容</th>';
        html += '<th class="text-left py-1 text-cta">効果</th>';
        html += '</tr></thead><tbody class="text-textPrimary">';

        var commitments = [
          [
            "継続の約束",
            "現在の動き（値下げ・新製品投入等）を断固として継続する意思表示",
            "競合に「対抗しても無駄」と思わせ、追随や攻撃を断念させる"
          ],
          [
            "反撃の約束",
            "相手が特定の行動をとった場合に必ず報復すると宣言",
            "攻撃の抑止力として機能。制裁（punishment）の実績が裏付けになる"
          ],
          [
            "不侵犯の約束",
            "相手を傷つけない・特定市場に参入しないことの宣言",
            "信頼関係を構築し、不要な敵対を回避。協調的な業界関係を促進"
          ]
        ];

        commitments.forEach(function(c, i) {
          var borderClass = i < commitments.length - 1 ? ' class="border-b border-border"' : '';
          html += '<tr' + borderClass + '>';
          html += '<td class="py-1.5 text-cta font-bold align-top">' + (i + 1) + '</td>';
          html += '<td class="py-1.5 font-bold align-top">' + c[0] + '</td>';
          html += '<td class="py-1.5 align-top">' + c[1] + '</td>';
          html += '<td class="py-1.5 align-top">' + c[2] + '</td>';
          html += '</tr>';
        });

        html += '</tbody></table>';

        // 信頼性の条件
        html += '<div class="mt-2 p-2 border border-border rounded">';
        html += '<p class="text-cta font-bold text-xs mb-1">約束の信頼性を裏付ける3条件</p>';
        html += '<ol class="text-textPrimary text-xs list-decimal list-inside space-y-0.5">';
        html += '<li><span class="text-cta">実行のための資産・経営資源</span> — 約束を実行する物理的な能力があること</li>';
        html += '<li><span class="text-cta">過去の実績の一貫性</span> — 過去に同種の約束を実行してきた歴史があること</li>';
        html += '<li><span class="text-cta">公的発表による不退転の意思</span> — 後戻りできない形で公に宣言すること</li>';
        html += '</ol></div>';

        html += '</div>';
        container.innerHTML = html;
      }
    },
    {
      type: "cheatsheet",
      title: "非脅威的な動きの3カテゴリー",
      render: function(container) {
        var html = '<div class="space-y-2">';

        html += '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">非脅威的・協調的な動きの3カテゴリー</h4>';
        html += '<p class="text-textPrimary text-xs mb-2">寡占市場では「わざのゲーム」として、競争業者の報復を招かない動きを選ぶことが戦略の要諦となる。</p>';
        html += '<table class="w-full text-xs">';
        html += '<thead><tr class="border-b border-border">';
        html += '<th class="text-left py-1 text-cta w-6">#</th>';
        html += '<th class="text-left py-1 text-cta">カテゴリー</th>';
        html += '<th class="text-left py-1 text-cta">説明</th>';
        html += '<th class="text-left py-1 text-cta">典型例</th>';
        html += '</tr></thead><tbody class="text-textPrimary">';

        var categories = [
          [
            "自社だけの地位を\n変える動き",
            "競争業者の目標を直接脅かさずに自社の地位を改善する。報復リスクが最も低い",
            "タイメックスの腕時計業界参入（宝飾品店ではなくドラッグストアで販売）"
          ],
          [
            "全社追従で全体の\n地位が向上する動き",
            "コスト増に伴う値上げなど、全社が追随すれば業界全体の収益が向上する行動",
            "業界リーダーの値上げに各社が追随する協調的値上げ"
          ],
          [
            "競争業者が無関心な\n分野での動き",
            "競合が重視しないセグメントやチャネルで展開し、反撃の動機を生まない",
            "スイス時計業界が無関心だった低価格帯でのタイメックスの成長"
          ]
        ];

        categories.forEach(function(c, i) {
          var borderClass = i < categories.length - 1 ? ' class="border-b border-border"' : '';
          html += '<tr' + borderClass + '>';
          html += '<td class="py-1.5 text-cta font-bold align-top">' + (i + 1) + '</td>';
          html += '<td class="py-1.5 font-bold align-top whitespace-pre-line">' + c[0] + '</td>';
          html += '<td class="py-1.5 align-top">' + c[1] + '</td>';
          html += '<td class="py-1.5 align-top">' + c[2] + '</td>';
          html += '</tr>';
        });

        html += '</tbody></table></div>';

        // 反撃の遅れ
        html += '<div class="bg-surface border border-border rounded p-3">';
        html += '<h4 class="text-cta font-bold text-sm mb-2">反撃の遅れを生む4つの要因</h4>';
        html += '<ol class="text-textPrimary text-xs list-decimal list-inside space-y-1">';
        html += '<li><span class="text-cta font-bold">知覚の遅れ</span> — 動きの重要性に気づくのが遅れる（盲点）</li>';
        html += '<li><span class="text-cta font-bold">方向の不明</span> — どう反撃すべきかわからない</li>';
        html += '<li><span class="text-cta font-bold">準備の遅れ</span> — 反撃手段の構築に時間がかかる</li>';
        html += '<li><span class="text-cta font-bold">目標の矛盾</span> — 反撃すると自社の他の事業・戦略が損なわれる（矛盾する目標のジレンマ）</li>';
        html += '</ol>';
        html += '<p class="text-textPrimary text-xs mt-1.5">典型例: タイメックス vs. スイス時計業界（知覚の遅れ + 方向の不明）、VW vs. ビッグスリー（目標の矛盾）</p>';
        html += '</div>';

        // 寡占の基本構造
        html += '<div class="bg-surface border border-border rounded p-2">';
        html += '<p class="text-cta font-bold text-xs mb-1">寡占市場の基本構造: 囚人のジレンマ</p>';
        html += '<p class="text-textPrimary text-xs">全企業が協調すれば業界全体の利益が最大化されるが、一社だけ抜け駆けすれば短期的に大きな利益を得られる。しかし全社が抜け駆けすると全体が悪化する。</p>';
        html += '</div>';

        html += '</div>';
        container.innerHTML = html;
      }
    }
  ]
};
