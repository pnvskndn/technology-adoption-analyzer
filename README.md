# Technology Adoption Analyzer

**Live platform: <https://technology-adoption-analyzer.streamlit.app/>**

Measuring barriers to renewable energy adoption across **44 countries (2001–2021)** —
quantifying the gap between realised deployment and the level each country's
structural conditions would support.

---

## The question

Countries at comparable income levels have reached very different points in the
energy transition. Norway and Denmark generate most of their electricity from
renewable sources; the United States, Australia and the Gulf states, at similar
income levels, remain largely fossil-based. If structural and economic conditions
determined transition outcomes, this divergence would not persist as sharply as it
does.

This project asks which conditions actually accompany higher renewable adoption,
whether those relationships differ by country rather than holding uniformly, and
how far each country sits from what its own fundamentals suggest it could reach.

Connected to **UN SDG 7** (Affordable and Clean Energy) and **SDG 13** (Climate Action).

## Findings

**Prior adoption dominates.** A country's renewable share in the previous year
predicts its current share far more strongly than income, urbanisation or
education. Deployment behaves as momentum — countries largely continue along the
trajectory they are already on.

**Wealth alone does not predict adoption.** Grouping countries by adoption profile
separates high-income renewable leaders from high-income fossil-incumbent
economies at comparable income levels. Existing energy mix and history matter
considerably more than national wealth.

**The structural gap maps unrealised potential.** Comparing realised adoption
against the level a country's fundamentals support reveals wide variation. Some
countries sit well above expectation; others well below. The largest shortfalls
are concentrated in the Gulf states.

Figures are computed live and shown in the platform rather than fixed in this
document.

## Approach

The analysis draws on eight World Bank indicators covering income and growth,
urbanisation, tertiary education, coal's share of electricity, electricity
consumption and renewable energy share, with renewable share of electricity
generation as the outcome studied. Models are trained on earlier years and
evaluated on later ones, so none is assessed on data preceding what it learned
from.

Four components run over the panel:

**Per-country attribution.** Rather than estimating one average effect per
variable across all countries, the model's prediction is decomposed for each
country individually, so the drivers identified for India can differ from those
for Norway. *(Gradient boosting, interpreted using SHAP values.)*

**Country forecasts.** A five-year projection of renewable share for every
country, each carrying an explicit uncertainty interval rather than a point
estimate. *(Prophet.)*

**Adoption archetypes.** Countries grouped by energy and economic profile rather
than by region or income band, surfacing peer sets that conventional
classifications obscure. *(K-means with PCA projection.)*

**Structural benchmark.** A model deliberately blind to each country's own
history, estimating the adoption level its fundamentals support. The residual —
realised minus expected — is the structural gap, treated as the quantity of
interest rather than error to minimise.

## Validation

Forecasts are tested against history rather than scored on in-sample fit. Models
are trained only on data up to a cut-off year, asked to project the years that
followed, and compared against what actually occurred — repeated across
successive cut-offs. For each country the platform reports how far its forecasts
have historically missed and how often reality fell inside the stated uncertainty
range.

## Limitations

The analysis identifies **associations, not causes**. It does not establish that
changing any variable would produce a given change in adoption.

**Renewable share of electricity is a partial measure** of transition progress. It
excludes heat and transport, and counts a large hydropower endowment the same as
actively deployed wind and solar — conflating geography with policy effort.

**No institutional or policy variables** are present in the dataset — no measure
of regulatory quality, market structure or policy stringency — which are likely to
matter considerably. The structural gap currently absorbs them.

**Data is annual and lagged**, giving roughly two decades of observations per
country, with World Bank indicators trailing reality by about two years.

## In development

Established policy stringency indices cover mainly high-income economies,
excluding much of the Gulf, South and Southeast Asia and Africa — largely the same
countries showing the widest structural gaps. The next phase constructs that
missing measure from policy text: classifying policy instruments by type, scope
and bindingness into a commitment score per country-year, validating it against an
established index where both exist, and testing whether policy absence explains
the structural gap.
---
