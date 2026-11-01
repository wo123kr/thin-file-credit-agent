# 실험 2 — A 만 보고 시작한 에이전트

제안 16개 · 채택 2개. 수치는 개발 데이터 5겹 × 3번 교차 검증의 평균 차이.

| 라운드 | 이름 | 가설 | ΔAUC 얇은 이력 | ΔAUC 전체 | 오른 쌍 | 결정 | 이유 |
|---|---|---|---|---|---|---|---|
| 1 | 연체_최근성과_최대 | 과거에 연체(status>=1)가 있었더라도 얼마나 최근인지, 얼마나 심했는지가 다음 달 연체를 가른다. 이력이 얇은 고객은 9월 한 시점만 보면 놓치는 과거 연체 경험을 반영한다. | +0.0075 | +0.0139 | 0.667 | 기각 | 오른 쌍 67% < 70% |
| 1 | 상태_추세와_변동 | 최근 3달 평균 상환 상태와 이전 3달 평균의 차이는 악화·개선 방향을 나타내며, 9월 단일 상태로는 알 수 없는 변화를 포착한다. | +0.0126 | +0.0127 | 0.867 | 채택 | 기준 통과 |
| 1 | 청구납부_짝_커버리지 | 납부액이 직전 달 청구액을 얼마나 덮었는지(상환 커버리지)는 상환 의지와 여력을 보여준다. 청구가 있었던 달들만 평균해 이력이 얇아도 계산되며, 부족하게 낸 달의 수도 연체 위험을 나타낸다. | +0.0119 | +0.0034 | 1.0 | 채택 | 기준 통과 |
| 1 | 마지막사용_경과와_활동수 | 마지막으로 청구가 발생한 이후 경과한 달 수와 사용 없음(-2) 달 수는 카드가 휴면인지 막 활성화됐는지를 나타내며, 얇은 이력 고객 내에서 연체 위험 차이를 만든다. | -0.0017 | +0.0001 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 -0.0017 < +0.002 · 오른 쌍 40% < 70% |
| 2 | 과납_전액납부_여부 | 청구가 있었던 달 중 전액 납부(-1) 상태였던 비율과 과납(bill<0) 경험은 연체와 거리가 먼 안정적 상환자를 가려낸다. 이력이 얇아도 청구가 있던 달만 보므로 계산되며, 기존 커버리지 평균과 달리 상태 코드 기반의 습관을 반영한다. | +0.0018 | +0.0007 | 0.6 | 기각 | 얇은 이력 ΔAUC 평균 +0.0018 < +0.002 · 오른 쌍 60% < 70% |
| 2 | 상태_청구_불일치 | 상태가 연체(>=1)인데 직전 달 청구 대비 납부가 충분했거나, 상태가 양호(<=0)인데 납부가 거의 없는 불일치는 기록 이상이나 일시적 자금 사정을 드러낸다. 얇은 이력 고객에서 상태와 금액의 짝을 함께 보는 정보다. | +0.0001 | -0.0003 | 0.533 | 기각 | 얇은 이력 ΔAUC 평균 +0.0001 < +0.002 · 오른 쌍 53% < 70% |
| 2 | 청구_증가_가속 | 최근 달로 갈수록 청구액이 한도 대비 빠르게 늘어나는 고객은 상환 부담이 커져 연체 위험이 높다. 청구가 있는 달들 사이의 순서 기반 기울기를 쓰므로 상태 코드 추세와는 다른 정보이며 이력이 얇아도 계산된다. | +0.0009 | -0.0010 | 0.6 | 기각 | 얇은 이력 ΔAUC 평균 +0.0009 < +0.002 · 오른 쌍 60% < 70% |
| 2 | 납부_공백_최근성 | 청구가 있었는데 다음 달 납부가 0이었던 달이 얼마나 최근인지와 연속 몇 달인지는 현금흐름 단절을 보여준다. 연체 최근성과 달리 상태 코드가 아니라 청구와 납부의 짝에서 나온 신호라 얇은 이력 고객의 놓친 정보를 잡는다. | +0.0039 | +0.0012 | 0.667 | 기각 | 오른 쌍 67% < 70% |
| 3 | 상태_한달변화와_최선대비 | 3달 평균 추세로는 안 보이는 직전 달 대비 상태 급변(s1-s2)과, 과거 최선 상태 대비 지금의 악화 폭을 따로 본다. 청구가 적은 고객은 상태 한 번의 변화가 곧 위험 신호가 된다. | +0.0006 | +0.0000 | 0.533 | 기각 | 얇은 이력 ΔAUC 평균 +0.0006 < +0.002 · 오른 쌍 53% < 70% |
| 3 | 커버리지_최근_변화 | 평균 커버리지는 이미 쓰고 있으므로, 최근 2개 짝의 납부 커버리지와 이전 짝 평균의 차이로 상환 태도가 나빠지는지 좋아지는지 본다. 청구가 있던 달의 짝만 써서 이력이 얇아도 계산된다. | -0.0018 | -0.0002 | 0.333 | 기각 | 얇은 이력 ΔAUC 평균 -0.0018 < +0.002 · 오른 쌍 33% < 70% |
| 3 | 이월_미상환잔액_한도대비 | 직전 달 청구 중 납부로 덮이지 못한 절대 잔액을 한도로 나눈 값은, 비율 커버리지가 놓치는 실제 이월 부담 크기를 보여준다. 최근 값과 최대값을 함께 써서 부담의 수준과 정점을 모두 반영한다. | -0.0015 | +0.0010 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 -0.0015 < +0.002 · 오른 쌍 40% < 70% |
| 3 | 리볼빙_의존도 | 청구가 있던 달 중 최소 금액만 내며 리볼빙(status=0)으로 버틴 비율은 전액 납부 여부와 다른 습관 신호이며, 자금 여력이 빠듯한 고객을 가려낸다. 분모를 청구 있는 달로 잡아 이력이 얇아도 정의된다. | +0.0003 | +0.0004 | 0.467 | 기각 | 얇은 이력 ΔAUC 평균 +0.0003 < +0.002 · 오른 쌍 47% < 70% |
| 4 | 한도_초과_최고사용률 | 6개월 중 청구액이 한도 대비 가장 높았던 정점과 한도를 넘긴 달의 수는 9월 한 시점 사용률(util_now)이 못 보는 자금 압박을 드러낸다. 청구가 몇 달 없어도 최대값과 개수로 계산되므로 이력이 얇은 고객에게도 적용된다. | +0.0003 | -0.0003 | 0.4 | 기각 | 얇은 이력 ΔAUC 평균 +0.0003 < +0.002 · 오른 쌍 40% < 70% |
| 4 | 신규_결제액_한도대비 | 이번 달 청구에서 이월된 미상환분(다음 달 쪽 청구 − 납부)을 빼면 그 달의 신규 사용액이 남고, 이는 이월 잔액과 다른 소비 행태 신호다. 연체 직전에 지출을 늘리거나 급히 쓰는 고객을 가르며, 청구가 적은 고객도 짝이 있는 달만 평균해 계산된다. | -0.0037 | +0.0004 | 0.333 | 기각 | 얇은 이력 ΔAUC 평균 -0.0038 < +0.002 · 오른 쌍 33% < 70% |
| 4 | 첫청구_경과와_중간공백 | 첫 청구가 발생한 시점이 얼마나 오래됐는지와 그 사이 청구가 끊긴 달의 수는 신규 활성화 고객, 오래된 휴면 후 재사용 고객, 꾸준한 소액 사용자를 구분한다. 마지막 사용 이후 경과가 아니라 첫 사용 시점과 중간 단절을 보므로 기각된 방향과 다르다. | -0.0002 | -0.0002 | 0.467 | 기각 | 얇은 이력 ΔAUC 평균 -0.0002 < +0.002 · 오른 쌍 47% < 70% |
| 4 | 납부액_일관성과_최근_대비 | 납부한 달들 사이 납부액의 변동계수는 정액 최소납부 습관인지 들쭉날쭉한 자금 사정인지를 보여준다. 9월 납부액을 과거 평균 납부액과 비교한 값은 청구와 무관한 납부 행동의 급감을 잡아내며, 납부가 있었던 달만 쓰므로 얇은 이력에서도 정의된다. | +0.0007 | -0.0017 | 0.6 | 기각 | 얇은 이력 ΔAUC 평균 +0.0007 < +0.002 · 오른 쌍 60% < 70% · 전체 ΔAUC -0.0017 |

## SQL

### 연체_최근성과_최대 (기각)

```sql
SELECT c.id, MIN(CASE WHEN m.status >= 1 THEN m.month END) AS f_months_since_delinq, MAX(m.status) AS f_max_status_6m FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### 상태_추세와_변동 (채택)

```sql
SELECT c.id, AVG(CASE WHEN m.month <= 3 THEN m.status END) - AVG(CASE WHEN m.month > 3 THEN m.status END) AS f_status_trend, STDDEV_POP(m.status) AS f_status_std FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### 청구납부_짝_커버리지 (채택)

```sql
SELECT c.id, AVG(CASE WHEN p.bill > 0 THEN LEAST(m.paid / p.bill, 2.0) END) AS f_pay_cover_avg, SUM(CASE WHEN p.bill > 0 AND m.paid < p.bill THEN 1 ELSE 0 END) AS f_underpay_cnt FROM clients c LEFT JOIN monthly m ON m.id = c.id LEFT JOIN monthly p ON p.id = m.id AND p.month = m.month + 1 GROUP BY c.id
```

### 마지막사용_경과와_활동수 (기각)

```sql
SELECT c.id, MIN(CASE WHEN m.bill > 0 THEN m.month END) - 1 AS f_months_since_last_bill, SUM(CASE WHEN m.status = -2 THEN 1 ELSE 0 END) AS f_unused_cnt FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### 과납_전액납부_여부 (기각)

```sql
SELECT c.id, AVG(CASE WHEN m.bill > 0 THEN (CASE WHEN m.status = -1 THEN 1.0 ELSE 0.0 END) END) AS f_full_pay_ratio, SUM(CASE WHEN m.bill < 0 THEN 1 ELSE 0 END) AS f_overpay_months FROM clients c LEFT JOIN monthly m ON m.id = c.id GROUP BY c.id
```

### 상태_청구_불일치 (기각)

```sql
WITH p AS (SELECT cur.id, cur.month, cur.status, cur.paid, prev.bill AS prev_bill FROM monthly cur JOIN monthly prev ON prev.id = cur.id AND prev.month = cur.month + 1) SELECT c.id, SUM(CASE WHEN p.prev_bill > 0 AND p.status <= 0 AND p.paid < 0.05 * p.prev_bill THEN 1 ELSE 0 END) AS f_good_status_low_pay, SUM(CASE WHEN p.prev_bill > 0 AND p.status >= 1 AND p.paid >= p.prev_bill THEN 1 ELSE 0 END) AS f_late_status_full_pay FROM clients c LEFT JOIN p ON p.id = c.id GROUP BY c.id
```

### 청구_증가_가속 (기각)

```sql
WITH b AS (SELECT m.id, m.month, m.bill / NULLIF(c.limit_bal, 0) AS u FROM monthly m JOIN clients c ON c.id = m.id WHERE m.bill > 0) SELECT c.id, -REGR_SLOPE(b.u, b.month) AS f_util_slope, MAX(b.u) - MIN(b.u) AS f_util_range FROM clients c LEFT JOIN b ON b.id = c.id GROUP BY c.id
```

### 납부_공백_최근성 (기각)

```sql
WITH p AS (SELECT cur.id, cur.month, cur.paid, prev.bill AS prev_bill FROM monthly cur JOIN monthly prev ON prev.id = cur.id AND prev.month = cur.month + 1 WHERE prev.bill > 0) SELECT c.id, MIN(CASE WHEN p.paid = 0 THEN p.month END) AS f_zero_pay_recency, SUM(CASE WHEN p.paid = 0 THEN 1 ELSE 0 END) AS f_zero_pay_cnt FROM clients c LEFT JOIN p ON p.id = c.id GROUP BY c.id
```

### 상태_한달변화와_최선대비 (기각)

```sql
WITH p AS (SELECT id, MAX(CASE WHEN month=1 THEN status END) AS s1, MAX(CASE WHEN month=2 THEN status END) AS s2, MIN(CASE WHEN month>=2 THEN status END) AS smin FROM monthly GROUP BY id) SELECT id, (s1 - s2) AS f_status_step, (s1 - smin) AS f_status_vs_best FROM p
```

### 커버리지_최근_변화 (기각)

```sql
WITH pr AS (SELECT a.id, a.month AS m, LEAST(GREATEST(a.paid / NULLIF(b.bill,0), 0), 1.5) AS cv FROM monthly a JOIN monthly b ON a.id=b.id AND b.month=a.month+1 WHERE b.bill>0) SELECT c.id, AVG(CASE WHEN pr.m<=2 THEN pr.cv END) - AVG(CASE WHEN pr.m>=3 THEN pr.cv END) AS f_cover_recent_delta FROM clients c LEFT JOIN pr ON pr.id=c.id GROUP BY c.id
```

### 이월_미상환잔액_한도대비 (기각)

```sql
WITH pr AS (SELECT a.id, a.month AS m, GREATEST(b.bill - a.paid, 0) AS carry FROM monthly a JOIN monthly b ON a.id=b.id AND b.month=a.month+1 WHERE b.bill>0) SELECT c.id, MAX(CASE WHEN pr.m=1 THEN pr.carry END) / NULLIF(c.limit_bal,0) AS f_carry_limit_recent, MAX(pr.carry) / NULLIF(c.limit_bal,0) AS f_carry_limit_max FROM clients c LEFT JOIN pr ON pr.id=c.id GROUP BY c.id, c.limit_bal
```

### 리볼빙_의존도 (기각)

```sql
SELECT c.id, SUM(CASE WHEN m.status=0 AND m.bill>0 THEN 1 ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN m.bill>0 THEN 1 ELSE 0 END),0) AS f_revolve_share FROM clients c LEFT JOIN monthly m ON m.id=c.id GROUP BY c.id
```

### 한도_초과_최고사용률 (기각)

```sql
SELECT m.id, MAX(m.bill) / NULLIF(c.limit_bal, 0) AS f_peak_util, SUM(CASE WHEN m.bill > c.limit_bal THEN 1 ELSE 0 END) AS f_overlimit_cnt FROM monthly m JOIN clients c ON c.id = m.id GROUP BY m.id, c.limit_bal
```

### 신규_결제액_한도대비 (기각)

```sql
WITH p AS (SELECT a.id, a.month, a.bill - GREATEST(b.bill - a.paid, 0) AS new_spend FROM monthly a JOIN monthly b ON b.id = a.id AND b.month = a.month + 1) SELECT c.id, MAX(CASE WHEN p.month = 1 THEN p.new_spend END) / NULLIF(c.limit_bal, 0) AS f_new_spend_now, AVG(p.new_spend) / NULLIF(c.limit_bal, 0) AS f_new_spend_avg FROM clients c LEFT JOIN p ON p.id = c.id GROUP BY c.id, c.limit_bal
```

### 첫청구_경과와_중간공백 (기각)

```sql
SELECT id, MAX(CASE WHEN bill > 0 THEN month END) AS f_first_bill_age, (MAX(CASE WHEN bill > 0 THEN month END) - MIN(CASE WHEN bill > 0 THEN month END) + 1) - COUNT(CASE WHEN bill > 0 THEN 1 END) AS f_inner_gap_cnt FROM monthly GROUP BY id
```

### 납부액_일관성과_최근_대비 (기각)

```sql
SELECT id, STDDEV_SAMP(CASE WHEN paid > 0 THEN paid END) / NULLIF(AVG(CASE WHEN paid > 0 THEN paid END), 0) AS f_paid_cv, MAX(CASE WHEN month = 1 THEN paid END) / NULLIF(AVG(CASE WHEN month > 1 AND paid > 0 THEN paid END), 0) AS f_paid_now_vs_hist FROM monthly GROUP BY id
```
