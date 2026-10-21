# FEC records behind the fact card and S35

These are the pages captured on 2026-10-21 (UTC) with `node scripts/fec_capture.mjs` (`config/fec.json`). Each `.txt` holds the page's text as captured, with its URL at the top; the two receipts pages list private donors, so their text stays in `takes/s35/fec/` (git-ignored). The screenshots are in `takes/s35/fec/` (git-ignored). The FEC's summary data run to the end of September 2026; itemized ("processed") rows lag by weeks.

## Leading the Future: super PAC, C00916114

- Committee profile and financial summary: https://www.fec.gov/data/committee/C00916114/?cycle=2026
  - Registered August 15, 2025 (Nevada).
  - Raised $75,981,640.00. Contributions total $75,100,000.00, all itemized individual contributions.
  - Spent $52,127,818.63. Of that, $47,000,000.00 went as contributions to other committees, and its own independent expenditures are $0.00.
  - Cash on hand $23,853,821.37 (08/15/2025–09/30/2026).
- Receipts: https://www.fec.gov/data/receipts/?committee_id=C00916114&two_year_transaction_period=2026
  - 08/22/2025: Marc L. Andreessen $12.5M, Benjamin Horowitz $12.5M, A16Z Capital Management LLC $25M.
  - 09/12/2025: Greg Brockman $12.5M, Anna Brockman $12.5M.
  - Perplexity AI Inc. $100,000.
  - **Check this:** the list also shows Andreessen, Horowitz and a16z rows again on 02/11/2026 for the same amounts. The summary's $75.1M total counts only one set of these, so the 2026 rows look like re-reported (amended or memo) entries. Open each row's details and its filing image before quoting either date.
- Disbursements: https://www.fec.gov/data/disbursements/?committee_id=C00916114&two_year_transaction_period=2026
  - Repeated $5,000,000 contributions to **Think Big** and **American Mission**, which are its affiliated super PACs, and $3,000,000 to American Mission Florida.
- Filings, the quarterly reports with their PDFs: https://www.fec.gov/data/committee/C00916114/?cycle=2026&tab=filings
  - October Quarterly 2026 (FEC-2022785, filed 10/15/2026), July Quarterly, April Quarterly and Year-End 2025.
- Think Big, C00923417, the super PAC that spends LTF's money: https://www.fec.gov/data/committee/C00923417/?cycle=2026
  - Raised $23,021,600.71.
  - Independent expenditures $17,224,117.88 (through 08/31/2026).

## Public First: super PAC, C00930503

- Committee profile and financial summary: https://www.fec.gov/data/committee/C00930503/?cycle=2026
  - Registered December 12, 2025 (DC).
  - Raised $4,910,605.00, of which $3,910,605.00 is individual contributions.
  - Spent $4,432,043.07. Of that, $4,340,000.00 went as contributions to other committees, and its own independent expenditures are $0.00.
- Receipts: https://www.fec.gov/data/receipts/?committee_id=C00930503&two_year_transaction_period=2026
  - $1,000,000 from Public First Action Inc. (02/24/2026).
  - Individual contributions, including $1,000,000 from Dario Amodei (05/04/2026) and other individuals.
  - **No corporate contribution from Anthropic appears here.**
- Filings: https://www.fec.gov/data/committee/C00930503/?cycle=2026&tab=filings

## Public First Action Inc.: electioneering-communication filer, C30003586

- https://www.fec.gov/data/committee/C30003586/ and its filings tab: https://www.fec.gov/data/committee/C30003586/?tab=filings
  - It is a nonprofit that files with the FEC only for electioneering communications: one 24-hour report, filed 03/10/2026 (FEC-1952561).
  - Its donors, Anthropic among them, are not reported to the FEC.

## Meta's American Technology Excellence Project

- It has no FEC committee; the FEC committee search finds nothing under that name. It is reported to work in state races, so its filings would be with state agencies.

## Against the fact card (`config/o.json` "fact_card")

1. **"$55.7 million on 95 midterm ads, by a New York Times tally of Sept. 29, 2026. None mentioned data centers."** This is the NYT's count of ads across all AI-aligned groups. It is not an FEC figure, and the FEC records can't confirm it. The card already attributes it.
   - The Times piece: https://www.nytimes.com/interactive/2026/09/29/us/politics/ai-super-pac-money-midterm-elections.html. The date is taken from its URL; nytimes.com refuses automated fetches.
   - As relayed by AI Weekly (published Sept. 30, 2026, 10:58 UTC): https://aiweekly.co/alerts/nyt-openai-and-anthropic-aligned-super-pacs-spent-557m-on-midterms-skipped-data
2. **"Leading the Future is backed by Greg Brockman and Andreessen Horowitz."** Confirmed by LTF's FEC receipts: Greg and Anna Brockman, Marc Andreessen, Ben Horowitz and a16z.
3. **"Public First, which wants stronger AI regulation, is backed by Anthropic."** Not visible in FEC records as a corporate gift.
   - Public First's FEC receipts show $1M from Public First Action and individual gifts, including Anthropic's CEO personally.
   - Anthropic's money (the $40M on card line 3) goes to Public First Action, a nonprofit whose donors the FEC doesn't see. That figure and its "restricted to policy and public education" caveat rest on news reports and Anthropic's own statement, and the card attributes them.
   - "Backed by" is fair as reported, but the FEC trail runs through the nonprofit.
4. **"Meta runs its own super PAC, the American Technology Excellence Project."** It has no FEC committee (state-level), which fits the card's wording. Source: the news report on the card.
