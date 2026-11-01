# 실험 1 — 사람 피처(B) 위에서 시작한 에이전트

제안 16개 · 채택 0개. 수치는 개발 데이터 5겹 × 3번 교차 검증의 평균 차이(표는 기록에 저장된 값 그대로, 이유 문장은 원값을 소수 4자리로 반올림).

| 라운드 | 이름 | 가설 | ΔAUC 얇은 이력 | ΔAUC 전체 | 오른 쌍 | 결정 | 이유 |
|---|---|---|---|---|---|---|---|
| 1 | status_transitions | 상환 상태가 달마다 바뀌는 횟수와 최근 3달 대 이전 3달의 악화 정도는 얇은 이력에서도 납부 행태의 불안정성을 보여 주며, 현재 피처의 단순 집계(최장·횟수)에는 순서 정보가 담겨 있지 않다. | +0.00181 | -0.00015 | 0.733 | 기각 | 얇은 이력 ΔAUC 평균 +0.0018 < +0.002 |
| 1 | months_since_last_bill | 마지막으로 청구가 발생한 뒤 경과한 달 수(휴면 기간)가 길면 재활성 직후 상환 행태가 달라지고, 최근에 사용을 시작한 신규성 고객은 연체 위험이 다르다. 기존 피처의 사용 달 수와 달리 타이밍을 반영한다. | +0.00006 | +0.00010 | 0.467 | 기각 | 얇은 이력 ΔAUC 평균 +0.0001 < +0.002 · 오른 쌍 47% < 70% |
| 1 | bill_paid_pairing | 직전 달 청구가 있는데 이번 달 납부가 청구의 일부에도 못 미치는 달의 비중과 마지막 달 미납 잔액(직전 청구 − 납부)의 한도 대비 크기는 청구와 납부를 짝지은 정보로, 얇은 이력에서도 상환 능력 부족 신호가 된다. | -0.00095 | -0.00011 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 -0.0010 < +0.002 · 오른 쌍 40% < 70% |
| 1 | recent_activity_shift | 최근 3달 대비 이전 3달의 청구 규모 변화와 최근 달의 사용 재개(이전 -2 또는 청구 0 뒤 청구 발생) 여부는 갑작스러운 자금 필요를 나타내며, 얇은 이력 고객의 연체를 가를 수 있다. | +0.00130 | +0.00036 | 0.733 | 기각 | 얇은 이력 ΔAUC 평균 +0.0013 < +0.002 |
| 2 | overbill_vs_limit | 청구액이 한도를 초과했거나 한도에 근접해 있는 달 수와 한도 초과 정도는 한도 소진 압박을 나타내며, 평균·최대 비율과 달리 임계 초과 빈도라서 얇은 이력 고객의 연체 위험을 가를 수 있다. | +0.00055 | -0.00005 | 0.467 | 기각 | 얇은 이력 ΔAUC 평균 +0.0006 < +0.002 · 오른 쌍 47% < 70% |
| 2 | negative_bill_credit | 과납(청구 음수)이 있거나 청구가 정확히 0인 달이 있는 고객은 선결제 습관이나 계좌 정리 성향이 있어 연체 위험이 낮을 수 있고, 기존 피처는 음수 청구를 구분하지 않는다. | -0.00133 | -0.00024 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 -0.0013 < +0.002 · 오른 쌍 40% < 70% |
| 2 | status_bill_mismatch | 상환 상태는 연체(≥1)인데 청구액이 0 이하이거나, 상태가 전액 납부(-1)·무사용(-2)인데 청구가 큰 달은 데이터상 모순된 행태로 특이 계좌를 드러낸다. 얇은 이력에서는 이런 불일치가 위험 신호일 수 있다. | +0.00010 | +0.00004 | 0.533 | 기각 | 얇은 이력 ΔAUC 평균 +0.0001 < +0.002 · 오른 쌍 53% < 70% |
| 2 | revolving_streak_current | 9월부터 거슬러 올라가 연속으로 리볼빙(0) 이상 상태가 이어진 길이와 마지막으로 정상(-1/-2) 상태였던 이후 경과는 현재 부담의 지속성을 보여 주며, 단순 횟수와 달리 연속성(순서)을 반영한다. | -0.00003 | +0.00033 | 0.667 | 기각 | 얇은 이력 ΔAUC 평균 -0.0000 < +0.002 · 오른 쌍 67% < 70% |
| 3 | status_among_billed | 기존 연체 피처는 청구가 없는 달(-2 등)까지 6개월에 섞어 집계해서 이력이 얇은 고객에서는 희석된다. 실제로 청구가 있었던 달만 따로 본 평균 상환 상태와 가장 최근 청구월의 상태는, 사용한 달의 상환 행태를 더 선명하게 드러낸다. | -0.00072 | +0.00000 | 0.533 | 기각 | 얇은 이력 ΔAUC 평균 -0.0007 < +0.002 · 오른 쌍 53% < 70% |
| 3 | repeated_payment_amount | 매달 같은 금액을 반복해서 내는 것은 자동이체나 최소금액 납부 습관을 뜻하고, 납부액이 매번 달라지는 것은 임시 변통식 납부를 뜻한다. 이 납부 패턴은 비율 피처에 담기지 않은 정보라서 얇은 이력 고객의 연체를 가를 수 있다. | -0.00127 | +0.00034 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 -0.0013 < +0.002 · 오른 쌍 40% < 70% |
| 3 | bill_dispersion_positive | 청구가 있었던 달들만 놓고 보면 청구액의 변동계수와 최소/최대 비율은 사용 패턴이 일정한지를 보여 준다. 일정한 소액 사용자와 불규칙하게 몰아 쓰는 사용자는 연체 위험이 다를 수 있고, 평균·최대 비율 피처에는 일관성 정보가 없다. | +0.00158 | -0.00023 | 0.667 | 기각 | 얇은 이력 ΔAUC 평균 +0.0016 < +0.002 · 오른 쌍 67% < 70% |
| 3 | payment_concentration | 납부가 한두 달에 몰려 있는지(최대 납부액의 총납부 대비 비중)와 실제로 납부한 달 수는 납부의 꾸준함을 보여 준다. 평균 납부액만 쓰는 기존 피처는 이를 구분하지 못하고, 얇은 이력에서는 꾸준히 내는 고객과 한 번에 몰아 내는 고객의 연체 위험이 갈릴 수 있다. | +0.00010 | +0.00005 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 +0.0001 < +0.002 · 오른 쌍 40% < 70% |
| 4 | limit_bal_rank_thin | 카드 한도는 발급사가 심사 시점에 평가한 신용도를 압축한 값인데, 같은 이력이 얇은 고객이라도 학력 집단 내 한도 상대 위치(백분위)는 발급 심사 정보를 더 선명히 드러내 연체 위험을 가를 수 있다. 단순 한도 단위 변환이 아니라 학력별 상대 순위이다. | -0.00150 | +0.00011 | 0.333 | 기각 | 얇은 이력 ΔAUC 평균 -0.0015 < +0.002 · 오른 쌍 33% < 70% |
| 4 | late_paid_vs_early_status | 가장 오래된 달(4월)의 상환 상태에서 최근 달(9월)까지 상태가 개선되었는지 악화되었는지의 방향과, 최근 2달 상태 합과 이전 4달 상태 평균의 차이는 상태 궤적의 기울기를 담는다. 얇은 이력에서도 상태 코드는 청구와 무관하게 기록되므로 새 정보가 된다. | +0.00027 | -0.00018 | 0.6 | 기각 | 얇은 이력 ΔAUC 평균 +0.0003 < +0.002 · 오른 쌍 60% < 70% |
| 4 | paid_vs_prev_bill_last_month | 9월 납부가 8월 청구 전액을 덮었는지(납부 ÷ 직전 청구)와 8월 청구가 양수일 때 9월 납부 후 잔액 규모는 다음 달 연체 직전의 상환 행동을 직접 보여 준다. 평균 비율이 아니라 마지막 한 달의 짝에 집중해 희석을 피한다. | +0.00095 | +0.00032 | 0.667 | 기각 | 얇은 이력 ΔAUC 평균 +0.0010 < +0.002 · 오른 쌍 67% < 70% |
| 4 | status_minus1_vs_zero_mix | 전액 납부(-1) 달과 리볼빙(0) 달의 구성은 '거래자'와 '리볼빙 사용자'를 구분하는 신호이고, 청구가 적은 고객에서는 리볼빙을 택한다는 것 자체가 유동성 압박을 의미한다. 최근 3달 안에서 리볼빙 달 수와 전액납부 달 수를 따로 센다. | +0.00125 | +0.00021 | 0.733 | 기각 | 얇은 이력 ΔAUC 평균 +0.0012 < +0.002 |

## SQL

### status_transitions (기각)

```sql
WITH m AS (SELECT id, month, status, LAG(status) OVER (PARTITION BY id ORDER BY month) AS prev_status FROM monthly), t AS (SELECT id, SUM(CASE WHEN prev_status IS NOT NULL AND status <> prev_status THEN 1 ELSE 0 END) AS chg, AVG(CASE WHEN month <= 3 THEN status END) - AVG(CASE WHEN month > 3 THEN status END) AS worsen FROM m GROUP BY id) SELECT c.id, t.chg AS f_status_change_cnt, t.worsen AS f_status_worsen_3v3 FROM clients c LEFT JOIN t ON t.id = c.id
```

### months_since_last_bill (기각)

```sql
WITH t AS (SELECT id, MIN(CASE WHEN bill > 0 THEN month END) AS last_bill_month, MAX(CASE WHEN bill > 0 THEN month END) AS first_bill_month FROM monthly GROUP BY id) SELECT c.id, t.last_bill_month - 1 AS f_months_since_last_bill, t.first_bill_month - t.last_bill_month AS f_bill_span_months FROM clients c LEFT JOIN t ON t.id = c.id
```

### bill_paid_pairing (기각)

```sql
WITH p AS (SELECT id, month, bill, paid, LEAD(bill) OVER (PARTITION BY id ORDER BY month) AS prev_bill FROM monthly), t AS (SELECT id, AVG(CASE WHEN prev_bill > 0 THEN CASE WHEN paid < 0.5 * prev_bill THEN 1.0 ELSE 0.0 END END) AS short_rate, MAX(CASE WHEN month = 1 THEN prev_bill - paid END) AS gap_now FROM p GROUP BY id) SELECT c.id, t.short_rate AS f_underpay_half_rate, t.gap_now / NULLIF(c.limit_bal, 0) AS f_unpaid_gap_now_to_limit FROM clients c LEFT JOIN t ON t.id = c.id
```

### recent_activity_shift (기각)

```sql
WITH m AS (SELECT id, month, status, bill, LEAD(bill) OVER (PARTITION BY id ORDER BY month) AS prev_bill, LEAD(status) OVER (PARTITION BY id ORDER BY month) AS prev_status FROM monthly), t AS (SELECT id, (SUM(CASE WHEN month <= 3 THEN GREATEST(bill,0) END) - SUM(CASE WHEN month > 3 THEN GREATEST(bill,0) END)) AS shift, MAX(CASE WHEN month <= 2 AND bill > 0 AND (prev_bill IS NULL OR prev_bill <= 0 OR prev_status = -2) THEN 1 ELSE 0 END) AS restart FROM m GROUP BY id) SELECT c.id, t.shift / NULLIF(c.limit_bal, 0) AS f_bill_shift_3v3_to_limit, t.restart AS f_restart_recent FROM clients c LEFT JOIN t ON t.id = c.id
```

### overbill_vs_limit (기각)

```sql
SELECT c.id, SUM(CASE WHEN m.bill > c.limit_bal THEN 1 ELSE 0 END) AS f_over_limit_months, SUM(CASE WHEN m.bill > 0.9 * c.limit_bal THEN 1 ELSE 0 END) AS f_near_limit_months FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### negative_bill_credit (기각)

```sql
SELECT c.id, SUM(CASE WHEN m.bill < 0 THEN 1 ELSE 0 END) AS f_overpaid_months, SUM(CASE WHEN m.bill = 0 AND m.status > -2 THEN 1 ELSE 0 END) AS f_zero_bill_active_months FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### status_bill_mismatch (기각)

```sql
SELECT c.id, SUM(CASE WHEN m.status >= 1 AND m.bill <= 0 THEN 1 ELSE 0 END) AS f_delinq_no_bill_months, SUM(CASE WHEN m.status = -1 AND m.bill > 0.3 * c.limit_bal THEN 1 ELSE 0 END) AS f_fullpay_bigbill_months FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### revolving_streak_current (기각)

```sql
WITH x AS (SELECT id, month, status, MIN(CASE WHEN status < 0 THEN month END) OVER (PARTITION BY id) AS first_clean FROM monthly) SELECT c.id, MIN(CASE WHEN x.status < 0 THEN x.month END) - 1 AS f_streak_nonclean_now, SUM(CASE WHEN x.status = 0 THEN 1 ELSE 0 END) AS f_revolve_months FROM clients c LEFT JOIN x ON x.id = c.id GROUP BY c.id
```

### status_among_billed (기각)

```sql
SELECT c.id, AVG(m.status) FILTER (WHERE m.bill > 0) AS f_status_avg_billed, ARG_MIN(m.status, m.month) FILTER (WHERE m.bill > 0) AS f_status_last_billed FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### repeated_payment_amount (기각)

```sql
WITH p AS (SELECT id, month, paid, LEAD(paid) OVER (PARTITION BY id ORDER BY month) AS paid_prev FROM monthly) SELECT c.id, COUNT(*) FILTER (WHERE p.paid > 0 AND p.paid = p.paid_prev) AS f_same_pay_months, COUNT(DISTINCT p.paid) FILTER (WHERE p.paid > 0) AS f_distinct_pay_amounts FROM clients c LEFT JOIN p ON p.id = c.id GROUP BY c.id
```

### bill_dispersion_positive (기각)

```sql
SELECT c.id, STDDEV_SAMP(m.bill) FILTER (WHERE m.bill > 0) / NULLIF(AVG(m.bill) FILTER (WHERE m.bill > 0), 0) AS f_bill_cv_pos, MIN(m.bill) FILTER (WHERE m.bill > 0) / NULLIF(MAX(m.bill) FILTER (WHERE m.bill > 0), 0) AS f_bill_min_max_pos FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### payment_concentration (기각)

```sql
SELECT c.id, MAX(m.paid) / NULLIF(SUM(m.paid), 0) AS f_pay_lumpy_share, COUNT(*) FILTER (WHERE m.paid > 0) AS f_paid_months FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### limit_bal_rank_thin (기각)

```sql
SELECT id, PERCENT_RANK() OVER (PARTITION BY CASE WHEN education IN (1,2,3) THEN education ELSE 4 END ORDER BY limit_bal) AS f_limit_rank_in_edu FROM clients
```

### late_paid_vs_early_status (기각)

```sql
SELECT id, MAX(CASE WHEN month=1 THEN status END) - MAX(CASE WHEN month=6 THEN status END) AS f_status_slope_end, AVG(CASE WHEN month IN (1,2) THEN status END) - AVG(CASE WHEN month IN (3,4,5,6) THEN status END) AS f_status_recent_vs_old FROM monthly GROUP BY id
```

### paid_vs_prev_bill_last_month (기각)

```sql
WITH a AS (SELECT id, MAX(CASE WHEN month=1 THEN paid END) AS paid1, MAX(CASE WHEN month=2 THEN bill END) AS bill2 FROM monthly GROUP BY id) SELECT a.id, CASE WHEN bill2 > 0 THEN LEAST(paid1 / bill2, 2.0) END AS f_last_cover_ratio, CASE WHEN bill2 > 0 THEN CAST(paid1 >= bill2 AS INTEGER) END AS f_last_fully_covered FROM a
```

### status_minus1_vs_zero_mix (기각)

```sql
SELECT id, SUM(CASE WHEN month<=3 AND status=0 THEN 1 ELSE 0 END) AS f_revolve_cnt_3m, SUM(CASE WHEN month<=3 AND status=-1 THEN 1 ELSE 0 END) AS f_fullpay_cnt_3m, SUM(CASE WHEN status=-1 THEN 1 ELSE 0 END) - SUM(CASE WHEN status=0 THEN 1 ELSE 0 END) AS f_fullpay_minus_revolve_6m FROM monthly GROUP BY id
```
