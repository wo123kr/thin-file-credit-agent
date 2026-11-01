-- A 지금 한 장: 심사 시점(9월)에 바로 보이는 정보. 고객 1명 = 1행.
SELECT
  c.id,
  c.limit_bal,
  CASE WHEN c.education IN (1, 2, 3) THEN c.education ELSE 4 END AS education_grp,  -- 0 · 5 · 6 은 설명 없는 값 → 기타
  m.status                                                         AS status_now,
  m.bill                                                           AS bill_now,
  m.paid                                                           AS paid_now,
  greatest(m.bill, 0) / c.limit_bal                                AS util_now
FROM clients c
JOIN monthly m ON m.id = c.id AND m.month = 1
