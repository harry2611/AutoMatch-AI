# Resume-Ready Metrics

These are the KPI categories the project exposes end-to-end and the language you can use when presenting it.

## Metrics tracked

- `precision@k`: share of top-ranked recommendations that convert.
- `CTR`: click-through rate from ranked recommendation surfaces.
- `conversion lift`: Bayesian arm conversion rate relative to heuristic baseline.
- `revenue lift`: incremental commission revenue attributed to ranking strategy.
- `average match distance`: buyer-to-dealer distance on surfaced matches.
- `dealer response rate`: share of buyer lead actions followed by dealer response.

## Example resume bullets

- Built a Bayesian recommendation engine for an automotive marketplace that re-ranked dealer inventory in real time from buyer interaction signals and improved match quality tracking across precision@k, CTR, and conversion lift.
- Shipped a full-stack experimentation platform with FastAPI, PostgreSQL, Redis, APScheduler, pandas, NumPy, scikit-learn, Next.js, and Tailwind to compare heuristic and posterior-driven ranking strategies.
- Created dealer and admin analytics dashboards that exposed high-intent leads, vehicle demand, pricing gaps, response-time impact, and revenue lift across experiment arms.

## Talking points for interviews

- The value of the project is not only model scoring. It is the closed loop between ranking, event capture, posterior updates, and downstream business analytics.
- Revenue optimization matters because the best marketplace ranking is rarely pure probability ranking. It should trade off conversion quality against expected commission and inventory health.
- Explainability matters because buyer trust and dealer trust both improve when the system can justify why a match was recommended.
