-- B 사람이 만든 이력 피처: 6개월 집계(tw-credit-scorecard 의 features.sql 을 긴 표에 맞게 옮김).
-- 납부 비율은 k 월에 낸 돈 ÷ k+1 월 청구액(직전 청구서). 청구가 없던 달은 빼고 평균, 1 을 넘으면 1.
WITH pairs AS (
  SELECT a.id, a.paid, b.bill AS prev_bill
  FROM monthly a JOIN monthly b ON b.id = a.id AND b.month = a.month + 1
  WHERE a.month <= 5
)
SELECT
  m.id,
  greatest(max(m.status), 0)                                          AS delinq_max_6m,
  count(*) FILTER (WHERE m.status >= 1)                                AS delinq_months_6m,
  count(*) FILTER (WHERE m.status >= 1 AND m.month <= 3)               AS delinq_months_3m,
  count(*) FILTER (WHERE m.status = -2)                                AS idle_months_6m,
  count(*) FILTER (WHERE m.bill > 0)                                   AS billed_months_6m,
  avg(greatest(m.bill, 0)) / any_value(c.limit_bal)                    AS util_avg_6m,
  max(greatest(m.bill, 0)) / any_value(c.limit_bal)                    AS util_max_6m,
  (max(m.bill) FILTER (WHERE m.month = 1) - max(m.bill) FILTER (WHERE m.month = 6)) / any_value(c.limit_bal) AS bill_trend_6m,
  avg(m.paid) / any_value(c.limit_bal)                                 AS paid_to_limit_6m,
  (SELECT avg(least(p.paid / p.prev_bill, 1.0)) FROM pairs p WHERE p.id = m.id AND p.prev_bill > 0) AS pay_ratio_avg_5m,
  (SELECT count(*) FROM pairs p WHERE p.id = m.id AND p.prev_bill > 0 AND p.paid = 0)            AS zero_pay_months_5m
FROM monthly m
JOIN clients c ON c.id = m.id
GROUP BY m.id
