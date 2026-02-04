# API documentation

Search for news articles that mention a specific topic or keyword
The main use of News API is to search through every article published by over 150,000 news sources and blogs in the last 5 years. Think of us as Google News that you can interact with programmatically!

In this example we want to find all articles that mention Apple published today, and sort them by most popular source first (i.e. Engadget articles will be returned ahead of Mom and Pop's Little iPhone Blog). For this we need to use the /everything endpoint.

For more information about the /everything endpoint, including valid parameters for narrowing your search, see the Everything endpoint reference.

News API is a simple HTTP REST API for searching and retrieving live articles from all over the web. It can help you answer questions like:

What top stories is TechCrunch running right now?
What new articles were published about the next iPhone today?
Has my company or product been mentioned or reviewed by any blogs recently?
You can search for articles with any combination of the following criteria:

Keyword or phrase. Eg: find all articles containing the word 'Microsoft'.
Date published. Eg: find all articles published yesterday.
Source domain name. Eg: find all articles published on thenextweb.com.
Language. Eg: find all articles written in English.
You can sort the results in the following orders:

Date published
Relevancy to search keyword
Popularity of source
You need an API key to use the API - this is a unique key that identifies your requests. They're free while you're in development.

Endpoints
News API has 2 main endpoints:

Everything /v2/everything – search every article published by over 150,000 different sources large and small in the last 5 years. This endpoint is ideal for news analysis and article discovery.
Top headlines /v2/top-headlines – returns breaking news headlines for countries, categories, and singular publishers. This is perfect for use with news tickers or anywhere you want to use live up-to-date news headlines.
There is also a minor endpoint that can be used to retrieve a small subset of the publishers we can scan:

Sources /v2/top-headlines/sources – returns information (including name, description, and category) about the most notable sources available for obtaining top headlines from. This list could be piped directly through to your users when showing them some of the options available.

Request parameters
apiKey
required
Your API key. Alternatively you can provide this via the X-Api-Key HTTP header.

country
The 2-letter ISO 3166-1 code of the country you want to get headlines for. Possible options: us. Note: you can't mix this param with the sources param.

category
The category you want to get headlines for. Possible options: businessentertainmentgeneralhealthsciencesportstechnology. Note: you can't mix this param with the sources param.

sources
A comma-seperated string of identifiers for the news sources or blogs you want headlines from. Use the /top-headlines/sources endpoint to locate these programmatically or look at the sources index. Note: you can't mix this param with the country or category params.

q
Keywords or a phrase to search for.

pageSize
int
The number of results to return per page (request). 20 is the default, 100 is the maximum.

page
int
Use this to page through the results if the total results found is greater than the page size.

Response object
status
string
If the request was successful or not. Options: ok, error. In the case of error a code and message property will be populated.

totalResults
int
The total number of results available for your request.

articles
array[article]
The results of the request.

source
object
The identifier id and a display name name for the source this article came from.

author
string
The author of the article

title
string
The headline or title of the article.

description
string
A description or snippet from the article.

url
string
The direct URL to the article.

urlToImage
string
The URL to a relevant image for the article.

publishedAt
string
The date and time that the article was published, in UTC (+000)

content
string
The unformatted content of the article, where available. This is truncated to 200 chars.

## Errors
If you make a bad request we'll let you know by returning a relevant HTTP status code along with more details in the body.

Response object
status
string
If the request was successful or not. Options: ok, error. In the case of ok, the below two properties will not be present.

code
string
A short code identifying the type of error returned.

message
string
A fuller description of the error, usually including how to fix it.

HTTP status codes summary
200 - OK. The request was executed successfully.
400 - Bad Request. The request was unacceptable, often due to a missing or misconfigured parameter.
401 - Unauthorized. Your API key was missing from the request, or wasn't correct.
429 - Too Many Requests. You made too many requests within a window of time and have been rate limited. Back off for a while.
500 - Server Error. Something went wrong on our side.
Error codes
When an HTTP error is returned we populate the code and message properties in the response containing more information. Here are the possible options:

apiKeyDisabled - Your API key has been disabled.
apiKeyExhausted - Your API key has no more requests available.
apiKeyInvalid - Your API key hasn't been entered correctly. Double check it and try again.
apiKeyMissing - Your API key is missing from the request. Append it to the request with one of these methods.
parameterInvalid - You've included a parameter in your request which is currently not supported. Check the message property for more details.
parametersMissing - Required parameters are missing from the request and it cannot be completed. Check the message property for more details.
rateLimited - You have been rate limited. Back off for a while before trying the request again.
sourcesTooMany - You have requested too many sources in a single request. Try splitting the request into 2 smaller requests.
sourceDoesNotExist - You have requested a source which does not exist.
unexpectedError - This shouldn't happen, and if it does then it's our fault, not yours. Try the request again shortly.

# NewsPulse — Architectural Decisions & Implementation Rules

This document captures the **final technical decisions** for NewsPulse to avoid ambiguity, scope creep, or incorrect assumptions during development.

All choices below are **locked for v1**.

---

# 1. /trends Endpoint — Definition of “Trending”

## Problem
The News API provides:
- `/top-headlines` → curated, real-time headlines
- `/everything` → keyword-based search

`/everything` does not support true keywordless discovery.

Since NewsPulse is a **discovery-first analytics platform**, not a search engine, we must choose the correct default source.

---

## Final Decision

### Use `/top-headlines` for default trending feed

Example:

```
/top-headlines
?country=us
&language=en
&pageSize=100
```

---

## Why
- real-time headlines
- curated and relevant
- no keyword required
- ideal for trend discovery
- simpler and more reliable

Using `/everything` would turn the system into a search tool instead of an analytics dashboard.

---

## Growth Trend Definition

### Time Window
Trending is computed over **24 hours total**.

Split into:
- current window → last 12 hours
- previous window → 12–24 hours ago

### Formula

```
growth % = (current_count - previous_count) / previous_count
```

---

## Final Meaning of “Trending”

> Topics/articles with the highest positive growth rate within the last 24 hours based on `/top-headlines`.

---

# 2. Sentiment Analysis Model

## Problem
Options:
- train at runtime (slow)
- training-free baseline (weak)
- pre-trained artifact (fast & realistic)

---

## Final Decision

### Include a pre-trained model artifact in the repo

Train once offline using scikit-learn, then load at runtime.

---

## Implementation

### Stored files

```
backend/models/sentiment.pkl
backend/models/vectorizer.pkl
```

### Runtime

```
joblib.load("sentiment.pkl")
```

---

## Why
- fast startup
- predictable results
- production-like workflow
- avoids unnecessary training overhead
- demonstrates proper ML deployment practice

Pattern followed:

```
Train offline → Serve online
```

---

# 3. Article Summarization Scope

## Problem
Options:
- summarize only NewsAPI fields
- fetch full article text via URL scraping

Scraping introduces:
- legal concerns
- blocked requests
- inconsistent HTML
- slow performance
- higher complexity
- expanded project scope

---

## Final Decision

### Summarize only NewsAPI-provided fields

Use:
- title
- description
- content snippet

No scraping allowed.

---

## AI Tool

Summarization handled by:
- Google Gemini API

Example prompt:

```
Summarize this article:
Title: ...
Description: ...
Content: ...
```

---

## Why
- legal and compliant
- simple and reliable
- fast
- consistent structure
- keeps focus on ML/analytics instead of crawling

---

# Final Locked Summary

## /trends
- Source → `/top-headlines`
- Scope → country-based discovery
- Window → last 24 hours
- Growth → 12h vs previous 12h

## Sentiment
- Pre-trained sklearn model
- Stored as `.pkl`
- No runtime training

## Summaries
- Only NewsAPI text
- No scraping URLs
- Gemini for summarization

---

# Guiding Principles

All architectural choices prioritize:

- simplicity
- legality
- speed
- reliability
- ML-focused learning
- minimal infrastructure

Avoid:
- scraping
- retraining at runtime
- unnecessary complexity

---

# Status

These decisions are **final for v1** and should not be changed unless requirements explicitly evolve.


## Definition
GET https://newsapi.org/v2/everything?q=bitcoin&apiKey=YOUR_API_KEY

## Example Response 
{
"status": "ok",
"totalResults": 6423,
-"articles": [
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Mike Pearl",
"title": "Bitcoin Mining is Being Used to Offset Heating Costs in Greenhouses and Homes",
"description": "Of course, bitcoin critics would argue there is nothing truly gained here in terms of energy efficiency.",
"url": "https://gizmodo.com/bitcoin-mining-is-being-used-to-offset-heating-costs-in-greenhouses-and-homes-2000708684",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/btc-heat-1200x675.jpg",
"publishedAt": "2026-01-11T21:10:17Z",
"content": "One of the side effects of the energy-intensive process of bitcoin mining is the excess heat that is created by the involved hardware devices. Miners have to prove that theyve expended energy on comp… [+4666 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Trump’s National Bitcoin Reserve Is Still in the Works. Some States Have Already Taken Action on Theirs",
"description": "Arizona, New Hampshire, and Texas have enacted laws aimed at creating their own reserves.",
"url": "https://gizmodo.com/trumps-national-bitcoin-reserve-is-still-in-the-works-some-states-have-already-taken-action-on-theirs-2000711467",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/shutterstock_2708601327-1200x675.jpg",
"publishedAt": "2026-01-18T10:00:56Z",
"content": "During his 2024 U.S. presidential run, then-candidate Donald Trump promised to establish a strategic bitcoin reserve if he was elected for his second term in office after losing his reelection bid in… [+4591 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Emails Show Even Epstein Thought Crypto Pumps are Unethical",
"description": "In 2018, Epstein wrote that because he is \"high profile\" he had concerns about the \"questionable ethics\" of crypto pumps if he was involved.",
"url": "https://gizmodo.com/emails-show-even-epstein-thought-crypto-pumps-are-unethical-2000716448",
"urlToImage": "https://gizmodo.com/app/uploads/2026/02/crypto-spike-1200x675.jpg",
"publishedAt": "2026-02-01T21:09:57Z",
"content": "The latest dump of Epstein files from the U.S. Department of Justice has a variety of interesting emails and other documents related to Jeffrey Epsteins early interest and involvement in Bitcoin and … [+5235 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "The Disclosure of Aliens Could Cause a Bitcoin Rush, Former Bank of England Analyst Says",
"description": "She warned of \"extreme price volatility in financial markets due to catastrophising or euphoria, and a collapse in confidence.\"",
"url": "https://gizmodo.com/the-disclosure-of-aliens-could-cause-a-bitcoin-rush-former-bank-of-england-analyst-says-2000711471",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/pentagon-uap-ufo-1200x675.jpg",
"publishedAt": "2026-01-18T18:22:11Z",
"content": "According to the Sunday Times, a former analyst at the Bank of England (BoE), which is the central bank of the United Kingdom, has written to the banks governor, Andrew Bailey, regarding the need to … [+4039 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Son of Executive Overseeing U.S. Government’s Crypto Stash Accused of Stealing $40 Million",
"description": "There's a big pot of digital gold out there.",
"url": "https://gizmodo.com/son-of-executive-overseeing-u-s-governments-crypto-stash-accused-of-stealing-40-million-2000714226",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Trump-Crypto-Gains-1200x675.jpg",
"publishedAt": "2026-01-28T15:35:11Z",
"content": "Over the weekend, ZachXBT, who is an advisor to crypto investment firm Paradigm and has been called one of the best digital detectives by The New York Times, claimed that the perpetrator of a suspect… [+5016 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Mike Pearl",
"title": "Free Bitcoin Glitch Fixed When ‘Decentralized’ Crypto Exchange Uses Centralized Rollback",
"description": "Situations that expose centralization in supposedly decentralized exchanges have become par for the course in crypto.",
"url": "https://gizmodo.com/free-bitcoin-glitch-fixed-when-decentralized-crypto-exchange-uses-centralized-rollback-2000711734",
"urlToImage": "https://gizmodo.com/app/uploads/2025/10/gizmodo-social-1200x675-1.jpg",
"publishedAt": "2026-01-19T20:15:34Z",
"content": "Paradex, which is a decentralized crypto exchange (DEX) built as an appchain on top of Ethereum layer-two network Starknet, recently experienced a technical glitch that resulted in bitcoin being pric… [+3904 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Privacy Coin Zcash Drops 20% as Core Dev Team Departs Electric Coin Company",
"description": "The fears of centralizing forces in crypto are creating a lot of skittishness.",
"url": "https://gizmodo.com/privacy-coin-zcash-drops-20-as-core-dev-team-departs-electric-coin-company-2000707755",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/zcash-1200x675.jpg",
"publishedAt": "2026-01-08T21:10:40Z",
"content": "Zcash, a privacy-focused cryptocurrency based around the use of zero-knowledge proofs, saw its price fall more than 20% overnight following the abrupt resignation of its entire core development team … [+4520 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Illicit Crypto Flows Climbed to $154 Billion in 2025 as Nation States Evade Sanctions, Report Finds",
"description": "As the Trump administration is adding rocket fuel to sanction enforcement, it's also been legitimizing crypto.",
"url": "https://gizmodo.com/illicit-crypto-flows-climbed-to-154-billion-in-2025-as-nation-states-evade-sanctions-report-finds-2000708055",
"urlToImage": "https://gizmodo.com/app/uploads/2025/10/bitcoin_cryptocurrency_price-1200x675.jpg",
"publishedAt": "2026-01-09T15:30:37Z",
"content": "An early preview of Chainalysiss annual crypto crime report reveals that crypto addresses tied to criminal operations pulled in at least $154 billion during 2025, shattering prior records with a 162%… [+3972 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Democrats Ask SEC to Explain Lack of Enforcement on Trump-Linked Crypto Entities",
"description": "“Given the industry’s history of investor-harm... this turn raises troubling questions about the SEC’s priorities and effectiveness.\"",
"url": "https://gizmodo.com/democrats-ask-sec-to-explain-lack-of-enforcement-on-trump-linked-crypto-entities-2000711123",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Crypto-SEC-Enforcement-Democrats-Letter-1200x675.jpg",
"publishedAt": "2026-01-16T17:35:45Z",
"content": "Three Democrats on the House Financial Services Committee have published an open letter to Securities and Exchange Commission (SEC) Chairman Paul Atkins regarding the lack of crypto enforcement actio… [+4534 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "More Corruption Allegations Levied at Trump Over Newly Revealed UAE Crypto Deal",
"description": "U.S. Senator Chris Murphy called the reported deal “mind-blowing corruption.”",
"url": "https://gizmodo.com/more-corruption-allegations-levied-at-trump-over-newly-revealed-uae-crypto-deal-2000716952",
"urlToImage": "https://gizmodo.com/app/uploads/2026/02/Donald-Trump-UAE-World-Liberty-Financial-1200x675.jpg",
"publishedAt": "2026-02-03T16:35:49Z",
"content": "An investment firm tied to United Arab Emirates (UAE) National Security Adviser Sheikh Tahnoon bin Zayed Al Nahyan signed a contract to invest $500 million in the Trump-affiliated crypto venture Worl… [+4010 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Senators Postpone Crypto Market Bill as Coinbase Flexes Its Muscle in Washington",
"description": "Coinbase's CEO isn't happy. Senators pump the brakes.",
"url": "https://gizmodo.com/senators-postpone-crypto-market-bill-as-coinbase-flexes-its-muscle-in-washington-2000710816",
"urlToImage": "https://gizmodo.com/app/uploads/2022/06/d247600ed4f9f90c53650a2a9b7c2f60-e1768515078239-1200x675.jpg",
"publishedAt": "2026-01-15T22:45:39Z",
"content": "On Wednesday evening, the Senate Banking Committee delayed final discussions around a bill for creating greater regulatory clarity for crypto in the United States, fittingly known as the Clarity Act.… [+5574 chars]"
},
-{
-"source": {
"id": null,
"name": "Dlnews.com"
},
"author": "Tim Alper",
"title": "Bitcoin miner moves $181 million, as expert speaks of ‘key inflection point’",
"description": "Miner active in the days of Bitcoin founder Satoshi Nakamoto, says expert. Two early “Bitcoin whales” moved coins worth $181 million late last year. VanEck...",
"url": "https://www.dlnews.com/articles/markets/bitcoin-miner-moves-181-million/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/ZGlIh7NqF51sy97UH76BBQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD04MDA-/https://media.zenfs.com/en/dlnews_702/aaae3a193ad9826f037d8b564dbcd1bd",
"publishedAt": "2026-01-11T16:02:17Z",
"content": "A miner who was active in the early days of crypto has moved over $181 million worth of Bitcoin.\r\nThe miner was active in the Satoshi era, Julio Moreno of the blockchain analysis provider CryptoQuant… [+2534 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Former NYC Mayor Eric Adams Accused of Crypto Pump and Dump With NYC Token",
"description": "Adams has wasted no time finding his true calling.",
"url": "https://gizmodo.com/former-nyc-mayor-eric-adams-accused-of-crypto-pump-and-dump-with-nyc-token-2000709645",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Eric-Adams-New-York-City-Token-1200x675.jpg",
"publishedAt": "2026-01-13T15:40:20Z",
"content": "On Monday, former New York City Mayor Eric Adams, who just left office following the election of Zohran Mamdani, promoted the launch of a new NYC Token memecoin on the Solana blockchain via a press c… [+4298 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "French Tax Agent Allegedly Sold Personal Data of Crypto Users to Criminals",
"description": "The suspect admitted providing the data, but insisted she was unaware of the buyers' plans",
"url": "https://gizmodo.com/french-tax-agent-allegedly-sold-personal-data-of-crypto-users-to-criminals-2000707279",
"urlToImage": "https://gizmodo.com/app/uploads/2025/10/gizmodo-social-1200x675-1.jpg",
"publishedAt": "2026-01-10T16:46:54Z",
"content": "A French tax agent, identified as Ghalia C. in French media reports, has been accused of accessing and selling sensitive information from internal French tax authority databases. Criminals are said t… [+3584 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Mohammad Shahid",
"title": "Why MicroStrategy’s Latest Bitcoin Purchase Is Deeply Concerning",
"description": "MicroStrategy’s latest Bitcoin purchase raises structural concerns around dilution, mNAV, and shareholder value.",
"url": "https://beincrypto.com/microstrategy-latest-bitcoin-buy-4-reasons-concerning/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/wEQY1dEbz6BYiCMN0E2crQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/a1282203769aca640a55f5d7f8a005a2",
"publishedAt": "2026-01-26T19:35:58Z",
"content": "MicroStrategy disclosed its latest Bitcoin purchase on January 26. In its 4th purchase of the month, the company acquired $264.1 million in Bitcoin at an average price of $90,061 per BTC. \r\nThe acqui… [+4643 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Jake Angelo",
"title": "‘There’s so much corruption, embezzlement and missing money’: Venezuela’s rumored $60 billion Bitcoin ‘shadow reserve’ draws skepticism",
"description": "If true, the claim could significantly reshape the global bitcoin market.",
"url": "https://finance.yahoo.com/news/much-corruption-embezzlement-missing-money-173953597.html",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/hgBTgLgI6rFQFItHn24iOQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD04MDA-/https://media.zenfs.com/en/fortune_175/9c43ff50092e51810b1e8439402ab678",
"publishedAt": "2026-01-07T17:39:53Z",
"content": "When Bitcoin first launched in 2009, many investors dismissed the currency as a fringe concept and even as a scam. (Charlie Munger, Warren Buffett’s former right-hand man at Berkshire Hathaway, memor… [+3667 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Coinbase CEO: Banking Lobbyists Are Trying to Ban Their Competition",
"description": "Bank lobbyists and crypto lobbyists are publicly fighting over new legislation. Lawmakers are noticeably absent from the debate.",
"url": "https://gizmodo.com/coinbase-ceo-banking-lobbyists-are-trying-to-ban-their-competition-2000712456",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Brian-Armstrong-CEO-Coinbase-Clarity-Act-1200x675.jpg",
"publishedAt": "2026-01-21T16:20:23Z",
"content": "One of the major topics of background discussion at the 2026 edition of the World Economic Forum meeting in Davos, Switzerland, has been the showdown between the crypto industry and traditional banks… [+6422 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Aaryamann Shrivastava",
"title": "Bitcoin Price Finally Breaks from a 6-Week Bear Pattern, What’s Next?",
"description": "Bitcoin rallies into 2026 with renewed whale accumulation, yet miner selling and macro risks leave the breakout awaiting confirmation.",
"url": "https://beincrypto.com/bitcoin-price-breaks-free-but-confirmation-awaits/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/sxk82eBBbp2jVuQaIz9kDw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/559b61185d3be86fcd8de4515845a948",
"publishedAt": "2026-01-04T18:55:39Z",
"content": "Why Q1 2026 could be bullish for crypto. Photo by BeInCrypto\r\nBitcoin price surged into the new year, supported by renewed optimism and strong spot ETF inflows. The crypto king pushed higher despite … [+2567 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Aaryamann Shrivastava",
"title": "Bitcoin Stays Above $95,000, But the Real Test Begins Now",
"description": "Bitcoin reclaims $95,000 but faces its toughest resistance ahead, as long-term holder selling challenges a potential move toward $110,000.",
"url": "https://beincrypto.com/bitcoin-price-toughest-challenge-yet/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/jWaZJj1Fq0JqIPxTk4yaiw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/fac7a43c3df82c31410379340c023ae5",
"publishedAt": "2026-01-15T08:49:07Z",
"content": "Bitcoin is attempting to recover recent losses after reclaiming the $95,000 level, a move that restored short-term optimism. The rally pushed BTC to a two-month high, but the recovery is far from com… [+2595 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Oluwapelumi Adejumo",
"title": "Satoshi-Era Miner Moves Millions in Bitcoin After 15 Years of Silence",
"description": "A Satoshi-era Bitcoin miner reactivated long-dormant wallets to move 2,000 BTC, worth about $181 million, to Coinbase.",
"url": "https://beincrypto.com/satoshi-era-bitcoin-miner-shifts-millions/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/cIwBKiofYJOzpaVy0NJ6Iw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/2de9258ccbbe436bd4d34d6497d74c61",
"publishedAt": "2026-01-11T19:00:00Z",
"content": "Bitcoin mining. Photo by BeInCrypto\r\nA Bitcoin miner from the networks earliest days has emerged from dormancy to shift 2,000 BTC, a strategic profit-taking move valued at approximately $181 million.… [+2235 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Mohammad Shahid",
"title": "Cathie Wood’s ARK Invest Makes Bold Bitcoin and Nvidia Prediction",
"description": "Cathie Wood’s ARK predicts $800,000 Bitcoin by 2030 while warning Nvidia faces rising AI competition and slower growth ahead.",
"url": "https://beincrypto.com/cathie-wood-ark-invest-bitcoin-prediction/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/d0xE8VNzdCIbkYbR9SxaCg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/7314e7922ed8a200e232c5b37277f2b9",
"publishedAt": "2026-01-21T21:56:22Z",
"content": "Cathie Woods ARK Invest has laid out one of its clearest long-term views yet on Bitcoin and Nvidia, two assets that defined the 20242025 market cycle. The firms latest Big Ideas 2026 report predicts … [+3365 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Ines Ferré",
"title": "Bitcoin and broader crypto markets 'have bottomed,' Bernstein analysts say",
"description": "Bitcoin has entered 2026 with gains following a disastrous quarter. Bernstein says the cryptocurrency has hit a bottom.",
"url": "https://finance.yahoo.com/news/bitcoin-and-broader-crypto-markets-have-bottomed-bernstein-analysts-say-182315482.html",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/3PdCiuCnNPw.YGJ2K7agbw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD05MzU-/https://s.yimg.com/os/creatr-uploaded-images/2021-01/01b7b310-56a9-11eb-bffd-49151115a071",
"publishedAt": "2026-01-06T18:23:15Z",
"content": "Bitcoin (BTC-USD) hovered above $91,000 per token on Tuesday as recent momentum sparked optimism that the brutal fourth quarter sell-off may be behind it.\r\n'We believe with reasonable confidence that… [+2561 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Ananda Banerjee",
"title": "Bitcoin Bull Market Starts With a 4.5% Move? History and Charts Finally Align",
"description": "Bitcoin price is just 4.5% away from a rare historical signal last seen in 2020.Charts, flows, and leverage now converge.",
"url": "https://beincrypto.com/bitcoin-price-bull-market-trigger/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/6ODjxjo088wS2rCK29rEsQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/547f7575da5238567bce2e8a86c9bf47",
"publishedAt": "2026-01-11T12:33:29Z",
"content": "bitcoin prediction, bitcoin forecast, galaxy digital bitcoin, bitcoin 2026, bitcoin 2027. Photo by BeInCrypto\r\nBitcoin price is sitting at a decision point after a quiet pullback. Since peaking on Ja… [+3968 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Sam Boughedda",
"title": "Bernstein says bitcoin has likely bottomed, reveals price targets",
"description": "Investing.com -- Bitcoin may have already found its floor, according to Bernstein, which argues that digital asset markets are set to recover as a broader...",
"url": "https://finance.yahoo.com/news/bernstein-says-bitcoin-likely-bottomed-142240063.html",
"urlToImage": "https://s.yimg.com/cv/apiv2/cv/apiv2/social/images/yahoo-finance-default-logo.png",
"publishedAt": "2026-01-06T14:22:40Z",
"content": "Investing.com -- Bitcoin may have already found its floor, according to Bernstein, which argues that digital asset markets are set to recover as a broader tokenization cycle builds momentum.\r\nIn a no… [+1702 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Kamina Bashir",
"title": "Veteran Trader Peter Brandt’s Bitcoin Prediction Signals a 30%+ Correction",
"description": "Peter Brandt warns Bitcoin may fall over 30% based on technical patterns while dormant whales move millions after years of inactivity.",
"url": "https://beincrypto.com/peter-brandt-bitcoin-prediction-whale-activity/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/_LtKngOeDW3NyLSXYqEsQg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/f0e79342a7526a1d5abb2d38e6932017",
"publishedAt": "2026-01-20T04:22:50Z",
"content": "Veteran trader Peter Brandt has forecasted that Bitcoin (BTC) could decline toward the $58,000$62,000 zone, implying a 3337% correction from current price levels of around $92,400.\r\nHis prediction co… [+3810 chars]"
},
-{
-"source": {
"id": null,
"name": "Dlnews.com"
},
"author": "Tim Craig",
"title": "Ethereum to $40,000? Why one analyst expects the second-biggest crypto to outperform Bitcoin",
"description": "Ethereum will hit $40,000 by 2030, Standard Chartered predicts. The second-biggest crypto should also outperform Bitcoin. Increased adoption of onchain...",
"url": "https://www.dlnews.com/articles/markets/why-ethereum-will-outperform-bitcoin-by-2030-according-to-standard-chartered/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/s4rJPXhFyZ1voNX2FZn5gg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD03ODU-/https://media.zenfs.com/en/dlnews_702/22d14118bf9116f921f52b88afbc69e9",
"publishedAt": "2026-01-12T16:33:14Z",
"content": "Weaker-than-expected Bitcoin performance will enable Ethereum to outperform the top crypto and hit $40,000 by 2030, according to Standard Chartereds latest forecast.\r\nThe major British multinational … [+3621 chars]"
},
-{
-"source": {
"id": null,
"name": "Coinspeaker"
},
"author": "Godfrey Benjamin",
"title": "Hyperliquid Whale James Wynn Closes BTC Trade, Goes Long on Ethereum",
"description": "Prominent Hyperliquid whale James Wynn has closed a major Bitcoin BTC $91 165 24h volatility: 0.7% Market cap: $1.82 T Vol. 24h: $52.51 B trade in profit and...",
"url": "https://www.coinspeaker.com/hyperliquid-whale-james-wynn-closes-btc-trade-goes-long-on-ethereum/",
"urlToImage": "https://media.zenfs.com/en/coinspeaker_us_106/43346032b720a4784d7e978286e6464d",
"publishedAt": "2026-01-07T10:47:55Z",
"content": "Prominent Hyperliquid whale James Wynn has closed a major Bitcoin trade in profit and shifted his focus to Ethereum . On-chain data shows Wynn rotating capital rather than exiting the market, signali… [+2272 chars]"
},
-{
-"source": {
"id": null,
"name": "Cryptonews"
},
"author": "Tanzeel Akhtar",
"title": "Billionaire Michael Saylor’s Strategy Scoops 13,627 Bitcoin for $1.25B",
"description": "Strategy disclosed in a regulatory filing that it acquired an additional 13,627 Bitcoin between January 5 and January 11, spending approximately $1.25...",
"url": "https://cryptonews.com/news/billionaire-michael-saylors-strategy-scoops-13627-bitcoin-for-1-25b/",
"urlToImage": "https://s.yimg.com/os/en/cryptonews_us_711/487f755be3188c2ec051238202cc9651",
"publishedAt": "2026-01-12T16:48:04Z",
"content": "Strategy disclosed in a regulatory filing that it acquired an additional 13,627 Bitcoin between January 5 and January 11, spending approximately $1.25 billion at an average purchase price of $91,519 … [+2199 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Brian McGleenon",
"title": "Bitcoin price falls as BlackRock and Fidelity ETFs see heavy outflows",
"description": "Bitcoin price retreated from recent highs on Thursday as institutional investors locked in profits after a strong start to the year.",
"url": "https://uk.finance.yahoo.com/news/bitcoin-price-crypto-blackrock-fidelity-etfs-outflows-104916054.html",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/jkszcEfuq5lXiWJKSI2UKQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD04NTc-/https://s.yimg.com/os/creatr-uploaded-images/2026-01/acf49670-ec73-11f0-9ffe-aea66c85dad9",
"publishedAt": "2026-01-08T10:49:16Z",
"content": "Bitcoin (BTC-USD) retreated from recent highs on Thursday as institutional investors locked in profits after a strong start to the year. Over the past 24 hours, the price eased from around $93,000 (£… [+2552 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Yahoo Finance Video",
"title": "Bitcoin in 'sustained recovery' from October liquidity scares",
"description": "Bitcoin (BTC-USD) is holding above $91,000 after a tumultuous end to 2025, where the crypto asset saw a sell-off from its record high reached in October...",
"url": "https://finance.yahoo.com/video/bitcoin-sustained-recovery-october-liquidity-152332755.html",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/zC9d.oeA0kj6axJOVD1O2Q--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzY-/https://s.yimg.com/os/creatr-uploaded-images/2026-01/74536400-ebdc-11f0-a1ff-ce0df034836c",
"publishedAt": "2026-01-07T15:23:32Z",
"content": "Bitcoin prices have rebounded to start the year after trading in a tight range following sell-offs in the fourth quarter of last year. Forced liquidations and selling by long-term holders pushed pric… [+3564 chars]"
},
-{
-"source": {
"id": null,
"name": "Coinspeaker"
},
"author": "Wahid Pessarlay",
"title": "Bitcoin Open Interest Crashes to Lowest Since 2022, Signaling Reset",
"description": "The Bitcoin BTC $90 459 24h volatility: 0.9% Market cap: $1.81 T Vol. 24h: $19.14 B open interest just fell to late 2022 levels, when the FTX collapse...",
"url": "https://www.coinspeaker.com/bitcoin-open-interest-crashes-lowest-since-2022/",
"urlToImage": "https://s.yimg.com/os/en/coinspeaker_us_106/160e9aae0fbb4a6f3ce3a19f4a908a2f",
"publishedAt": "2026-01-09T07:59:16Z",
"content": "The Bitcoin open interest just fell to late 2022 levels, when the FTX collapse brought the crypto market down, and the leading asset fell to $15,000.\r\nAccording to a CryptoQuant analysis, leading cry… [+2265 chars]"
},
-{
-"source": {
"id": null,
"name": "Coinspeaker"
},
"author": "José Rafael Peña Gholam",
"title": "CZ Predicts Bitcoin ‘Super-Cycle’ in 2026, Breaking Historic Pattern",
"description": "Binance founder Changpeng Zhao said he expects Bitcoin BTC $89 460 24h volatility: 0.2% Market cap: $1.79 T Vol. 24h: $42.75 B to enter a “super-cycle” in...",
"url": "https://www.coinspeaker.com/changpeng-cz-zhao-predicts-bitcoin-super-cycle-2026/",
"urlToImage": "https://s.yimg.com/os/en/coinspeaker_us_106/cead1c682816ae18e0c8980e4388bb39",
"publishedAt": "2026-01-23T20:02:39Z",
"content": "Binance founder Changpeng Zhao said he expects Bitcoin to enter a “super-cycle” in 2026, potentially breaking the cryptocurrency’s historic four-year pattern of price peaks and crashes.\r\nSpeaking on … [+2159 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin price rises as Trump backtracks on Greenland tariff threat",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_8e811f05-4aaa-42e2-bc73-9f30a6ebac56",
"urlToImage": null,
"publishedAt": "2026-01-22T09:53:55Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "By Rocky Swift and Rae Wee",
"title": "Dollar rallies on prospects for new Fed chief; Bitcoin tumbles",
"description": "By Rocky Swift and Rae Wee TOKYO, Jan 30 (Reuters) - The dollar rose on Friday, clawing back some of its slide on the week, after U.S.",
"url": "https://finance.yahoo.com/news/dollar-poised-weekly-slide-global-011116344.html",
"urlToImage": "https://s.yimg.com/os/en/reuters.com/90b9a7775bd3b8d9bb5a60dfcb7f647f",
"publishedAt": "2026-01-30T06:55:01Z",
"content": "By Rocky Swift and Rae Wee\r\nTOKYO, Jan 30 (Reuters) - The dollar rose on Friday, clawing back some of its slide on the week, after U.S. President Donald Trump said he would soon announce his nominee … [+3748 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin price slides as gold rallies on weaker dollar",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_2a171124-15bc-456c-be25-99c6bfa0bd96",
"urlToImage": null,
"publishedAt": "2026-01-29T09:51:42Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin hovers near $77,000 with 'broader downtrend intact'",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_31e2f544-49db-4ea1-8e35-6b2187067019",
"urlToImage": null,
"publishedAt": "2026-02-02T03:18:55Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin Slides Toward 91K as CME Gaps Come Into Focus",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_3ff72130-4e9a-4725-afe9-804637f5e543",
"urlToImage": null,
"publishedAt": "2026-01-07T18:17:10Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Yahoo Finance Video",
"title": "Bitcoin price outlook: Why this expert predicts at least $130K",
"description": "Bitcoin is holding onto gains as the CLARITY Act continues to face delays. Delta Blockchain Fund founder and general partner Kavita Gupta joins Market...",
"url": "https://finance.yahoo.com/video/bitcoin-price-outlook-why-expert-130018124.html",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/qZDip1Sabg7E8EfHjtc2qA--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzQ-/https://s.yimg.com/os/creatr-uploaded-images/2026-01/7c85ec70-f25c-11f0-bfdf-3da0de7f8b3f",
"publishedAt": "2026-01-16T13:00:18Z",
"content": "Bitcoin, I'm just looking at. Okay, we're back at 95. What is driving that Kavita and I'm curious where where you see that headed near to intermediate term? What are what are some of the potential ca… [+1667 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Jim Cramer issues blunt warning, predicts next Bitcoin bottom",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_a4a2df13-5fb2-47c5-9f20-f669e6862edd",
"urlToImage": null,
"publishedAt": "2026-02-02T19:37:35Z",
"content": "If you click 'Accept all', we and our partners, including 246 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "CoinDesk"
},
"author": "CoinDesk",
"title": "Bitcoin above $95K as spot BTC ETFs score largest inflow since October",
"description": "U.S. spot bitcoin ETFs saw their largest daily inflows in three months, with $753.7 million recorded on Tuesday. Is this a sign that investors have rotated...",
"url": "https://videos.coindesk.com/previews/FKG29wnb",
"urlToImage": "https://s.yimg.com/os/en/coindesk_75/d43bbb213b23e2f5f1950df1e02acdda",
"publishedAt": "2026-01-14T17:12:33Z",
"content": "U.S. spot bitcoin ETFs saw their largest daily inflows in three months, with $753.7 million recorded on Tuesday. Is this a sign that investors have rotated back into risk assets following the year-en… [+75 chars]"
},
-{
-"source": {
"id": null,
"name": "Cryptonews"
},
"author": "Anas Hassan",
"title": "Bitcoin Open Interest Drops 31% as Analysts Call a Market Bottom and Eye $105k Breakout",
"description": "Bitcoin open interest has plunged over 31% from its 2025 peak, now stabilizing around $10 billion as analysts identify this decline as a critical bottoming...",
"url": "https://cryptonews.com/news/bitcoin-open-interest-drops-31-as-analysts-call-a-market-bottom-and-eye-105k-breakout/",
"urlToImage": "https://s.yimg.com/os/en/cryptonews_us_711/4c550ffe9435c15d945e9de02fc93cee",
"publishedAt": "2026-01-14T15:49:37Z",
"content": "Bitcoin open interest has plunged over 31% from its 2025 peak, now stabilizing around $10 billion as analysts identify this decline as a critical bottoming formation that could propel BTC toward a $1… [+3903 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Lockridge Okoth",
"title": "$2.3 Billion in Bitcoin and Ethereum Options Set to Expire—Is a Volatility Shock Looming?",
"description": "Nearly $2.3 billion in Bitcoin and Ethereum options expire as traders brace for volatility reset, strike magnets, & post-expiry price swings.",
"url": "https://beincrypto.com/bitcoin-ethereum-options-expiry-2026-3/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/iw5yZcmw7pAICzKxT_SaSg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/5f037abc0f537421edfe1645e77b5464",
"publishedAt": "2026-01-23T05:09:24Z",
"content": "Nearly $2.3 billion worth of Bitcoin and Ethereum options expire today, placing crypto markets at a critical inflection point as traders prepare for a potential volatility reset.\r\nWith positioning he… [+3341 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Ananda Banerjee",
"title": "Bitcoin Price Prediction Still Warns of $78,000 Risk — But Tiring Sellers Spark Bounce Hope",
"description": "Bitcoin price prediction shows downside risk toward $78,000, but fading selling pressure hints at a short-term bounce. What's next for BTC?",
"url": "https://beincrypto.com/bitcoin-price-prediction-78k-analysis/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/d0xE8VNzdCIbkYbR9SxaCg--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/7314e7922ed8a200e232c5b37277f2b9",
"publishedAt": "2026-01-26T06:36:59Z",
"content": "Bitcoin is down just over 1% in the past 24 hours, but the bigger story is not the daily move. Over the weekend, the Bitcoin price came dangerously close to confirming a bearish breakdown before stag… [+4502 chars]"
},
-{
-"source": {
"id": null,
"name": "BeInCrypto"
},
"author": "Lockridge Okoth",
"title": "Nearly $3 Billion in Bitcoin and Ethereum Options Expire as Markets Test Breakout Conviction",
"description": "Nearly $3 billion in Bitcoin and Ethereum options expire as markets test whether Bitcoin’s breakout can hold and if Ethereum follows.",
"url": "https://beincrypto.com/bitcoin-ethereum-options-expiry-2026-2/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/uCAmFNXQWchUOaY2W1Invw--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD02NzU-/https://media.zenfs.com/en/beincrypto_us_662/33132922a1707aca1f74a819da2d74d1",
"publishedAt": "2026-01-16T05:12:53Z",
"content": "Nearly $3 billion worth of Bitcoin and Ethereum options are set to expire on January 16. This puts derivatives markets in focus just as crypto prices test the strength of a recent rally.\r\nWhile Bitco… [+3924 chars]"
},
-{
-"source": {
"id": null,
"name": "Cryptonews"
},
"author": "Anas Hassan",
"title": "Dalio: U.S. Nears Crisis Point as Bitcoin Trapped by American Selling Pressure",
"description": "Ray Dalio warned the U.S. stands “on the brink” of transitioning from Stage 5 pre-breakdown to Stage 6 systemic collapse as Bitcoin is trading defensively at...",
"url": "https://cryptonews.com/news/dalio-us-nears-crisis-point-as-bitcoin-trapped-by-american-selling-pressure-is-btc-the-answer/",
"urlToImage": "https://s.yimg.com/os/en/cryptonews_us_711/d4af6d435327beb663bef476491f23e6",
"publishedAt": "2026-01-27T16:34:29Z",
"content": "Ray Dalio warned the U.S. stands “on the brink” of transitioning from Stage 5 pre-breakdown to Stage 6 systemic collapse as Bitcoin is trading defensively at $88,000, trapped in a 60-day range by rec… [+5036 chars]"
},
-{
-"source": {
"id": null,
"name": "CoinDesk"
},
"author": "CoinDesk",
"title": "The Blockspace Pod: Our Predictions For 2026",
"description": "Charlie and Colin drop their 6 major predictions for 2026. From a silver supply shock and Bitcoin hash rate stagnation to the rise of prediction markets and ...",
"url": "https://videos.coindesk.com/previews/2MAfTFGl",
"urlToImage": "https://media.zenfs.com/en/coindesk_75/071b020ef669b73588adb46f6a0d99aa",
"publishedAt": "2026-01-05T13:54:57Z",
"content": "Charlie and Colin drop their 6 major predictions for 2026. From a silver supply shock and Bitcoin hash rate stagnation to the rise of prediction markets and AI data center delays. Find out why big ba… [+74 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Winklevoss Twins Shut Down NFT Marketplace in Another Sign Crypto Art Is Dead",
"description": "You know what's cooler than a million dollars? A .jpeg that's been cataloged on an immutable blockchain that no one wants to buy.",
"url": "https://gizmodo.com/winklevoss-twins-shut-down-nft-marketplace-in-another-sign-crypto-art-is-dead-2000714660",
"urlToImage": "https://gizmodo.com/app/uploads/2024/11/Cameron-and-Tyler-Winklevoss-1.jpg",
"publishedAt": "2026-01-27T23:10:56Z",
"content": "Tyler and Cameron Winklevoss’s crypto exchange, Gemini, has announced the closure of Nifty Gateway, a non-fungible token (NFT) marketplace that the exchange had previously acquired in 2019. Nifty Gat… [+4359 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Gold Has Been Acting More Like Bitcoin Lately",
"description": "Gold added more than two entire Bitcoin market caps in 72 Hours.",
"url": "https://gizmodo.com/gold-has-been-acting-more-like-bitcoin-lately-2000715946",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/gold_bar-1200x675.jpg",
"publishedAt": "2026-01-30T13:50:55Z",
"content": "Comparisons between bitcoin and gold have been made since the earliest days of the crypto assets existence. Satoshi Nakamoto once likened his creation to a base metal like gold that could be instantl… [+4038 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "NYSE’s Tokenized Stocks Create More Questions for Crypto’s Relevance",
"description": "Given that Bitcoin was created to circumvent traditional finance, what are we even doing here?",
"url": "https://gizmodo.com/nyses-tokenized-stocks-create-more-questions-for-cryptos-relevance-2000711752",
"urlToImage": "https://gizmodo.com/app/uploads/2022/09/2b695d06fce5fcfd3e1673e4cb965ee4.jpg",
"publishedAt": "2026-01-20T10:00:29Z",
"content": "On Monday, the New York Stock Exchange (NYSE) announced the development of its tokenized securities platform for trading U.S. stocks via blockchain technology. The new platform is said to enable trad… [+3706 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin hoarder Strategy reveals $17.44 billion unrealized loss in fourth quarter",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_f84d7fee-9abc-4e0d-8971-8cc838ead0db",
"urlToImage": null,
"publishedAt": "2026-01-05T22:49:52Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin rises above $92,000 in sign of 'bullish trend' to start 2026",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_7359abbc-23c6-4a5b-996f-382377d04f43",
"urlToImage": null,
"publishedAt": "2026-01-05T14:50:57Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Michael Saylor Predicts Bitcoin at $21 Million by 2045—Here’s the Math Behind the Moonshot",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_985de6ef-3225-4085-a541-d861ce17e6a2",
"urlToImage": null,
"publishedAt": "2026-01-06T13:40:31Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin price fall sparks concern among cryptocurrency experts: 'Less cooperation in trade globally'",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_a2a9dc52-98cf-4bea-a260-01b707a234b5",
"urlToImage": null,
"publishedAt": "2026-01-08T04:30:00Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "MSCI’s Move on MicroStrategy Is Rattling Bitcoin Markets | US Crypto News",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_b0925170-fe2e-49e4-98a0-80d2381e91b9",
"urlToImage": null,
"publishedAt": "2026-01-08T17:49:02Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Quantum computing threatens the $2 trillion Bitcoin network. BTQ Technologies says it has a defense.",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_98c71115-6919-4628-9f01-d524cbe34e6e",
"urlToImage": null,
"publishedAt": "2026-01-12T12:30:00Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Binance Founder CZ Says ‘Super Cycle’ Incoming as VanEck Unveils $2.9M Bitcoin Target",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_f00df37d-c794-4da6-9aa5-4c5e64587511",
"urlToImage": null,
"publishedAt": "2026-01-10T16:40:10Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin Price Crashes to Zero on Paradex Exchange as Glitch Fuels Mass Liquidations",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_679fe27a-f102-4d48-ae38-3eaa33863b6a",
"urlToImage": null,
"publishedAt": "2026-01-19T17:35:20Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "On This Date 16 Years Ago, Seller Offered 500 Bitcoin for $1 — Worth $45 Million Today",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_d0dd5d43-35ff-4e22-971c-bcec143426bf",
"urlToImage": null,
"publishedAt": "2026-01-25T03:15:00Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "The Bitcoin Milestone Hitting Next Month That Most Retail Traders Are Missing",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_cc74592e-8eb6-4a01-bb5b-77192927e05b",
"urlToImage": null,
"publishedAt": "2026-01-29T15:42:00Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Why Is Gold Beating Bitcoin? Tom Lee Explains What’s Really Happening",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_f70c0bb1-b224-474c-be48-cd0d93605367",
"urlToImage": null,
"publishedAt": "2026-01-27T23:25:52Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin to $53m? Yes, VanEck really just made that price prediction",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_d0f2ed0c-502b-4b0c-966c-682d3d7eec2d",
"urlToImage": null,
"publishedAt": "2026-01-09T11:15:08Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin Dominance Steady, XRP On-Chain Surges, Solana Outperforms—Is Altcoin Season Starting?",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_b4d93f2c-af03-4cdb-a123-25b873b97476",
"urlToImage": null,
"publishedAt": "2026-01-20T16:03:23Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "BlackRock’s Bitcoin ETF Sees Biggest Inflow in Three Months as Crypto Prices Rise",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_92914fec-5dcb-4bc0-a5f4-f90b3602f083",
"urlToImage": null,
"publishedAt": "2026-01-05T05:44:25Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin rises above $93,000 in sign of 'bullish trend' to start 2026",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_8a9edd6e-baa7-48ae-9112-e539467b7979",
"urlToImage": null,
"publishedAt": "2026-01-05T17:53:16Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin and Ethereum Pinned at Max Pain as $2.2 Billion Options Expire into Macro Storm",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_913834bd-6799-433f-8faf-8521b98d9be0",
"urlToImage": null,
"publishedAt": "2026-01-09T05:58:09Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "'Big Short' investor Michael Burry details the 'sickening scenarios' possible if bitcoin continues to fall",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_4d07ea38-da37-4430-a10d-2065225d364a",
"urlToImage": null,
"publishedAt": "2026-02-03T15:47:10Z",
"content": "If you click 'Accept all', we and our partners, including 246 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin To Hit $100,000 in 48 Hours, Says World’s ‘Smartest Man,’ Following ‘Correct’ XRP Rally Call",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_2284407b-326b-44c4-8c4a-3d9b1350bfef",
"urlToImage": null,
"publishedAt": "2026-01-06T09:52:15Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and/or access information on a device (in other words, use … [+714 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Ark Invest bought $21.5 million of crypto company shares as bitcoin fell under $90,000",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_c5f4cdeb-0daa-42ec-a433-bfe2fa48c23a",
"urlToImage": null,
"publishedAt": "2026-01-26T10:14:45Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Strive prices upsized preferred stock offering at $90 to retire debt and buy bitcoin",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_f70cead5-aa0d-40a3-9857-f9ce98d2a8a4",
"urlToImage": null,
"publishedAt": "2026-01-23T15:40:25Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Why Is Bitcoin Crashing Today? The BTC USD Experiment Is Over As It Crashes to $81K",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_a6ba5efd-62f4-439d-b573-89e5de6062cc",
"urlToImage": null,
"publishedAt": "2026-01-30T11:00:02Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Gold in 'extreme greed' sentiment as it adds entire bitcoin market cap in one day",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_b5d400fa-a895-4241-af7b-cb32fd0a1ff0",
"urlToImage": null,
"publishedAt": "2026-01-29T13:00:32Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin, ether fall as shutdown clock hits and markets brace for a messy Monday",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_c1d1691b-fe89-40b4-b3ea-9ac7af077d5f",
"urlToImage": null,
"publishedAt": "2026-01-31T07:29:47Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Bitcoin plunges near $77,000 as geopolitical risks deepens amid U.S-Iran tension",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_ef055309-4e48-4bdb-8f3e-85a3aa64024a",
"urlToImage": null,
"publishedAt": "2026-01-31T14:46:46Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Tom Lee Claims Parabolic Gold and Silver Move Is Masking Bullish Bitcoin and Ethereum Signals",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_0de4310b-486c-429d-a57b-36782c6f4165",
"urlToImage": null,
"publishedAt": "2026-01-27T11:45:07Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "TheStreet"
},
"author": "Pooja Rajkumari",
"title": "Bank of America warns major threat could push trillions out of U.S. banks",
"description": "Brian Moynihan made a grim warning about stablecoins. During a Jan. 15 earnings call, the Bank of America CEO told analysts that as much as $6 trillion in...",
"url": "https://www.thestreet.com/crypto/markets/bank-of-america-warns-major-threat-could-push-trillions-out-of-u-s-banks",
"urlToImage": "https://s.yimg.com/os/en/thestreet_881/b96ff992c66cee9c3a3a6df806759a61",
"publishedAt": "2026-01-16T18:10:30Z",
"content": "Brian Moynihan made a grim warning about stablecoins.\r\nDuring a Jan. 15 earnings call, the Bank of America CEO told analysts that as much as $6 trillion in deposits could migrate from the United Stat… [+5005 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "The Company That Just Buys Bitcoin Booked $17 Billion in Q4 Losses",
"description": "Strategy's business model results in wild swings, but since it hasn't sold any bitcoin, these are just paper losses",
"url": "https://gizmodo.com/the-company-that-just-buys-bitcoin-booked-17-billion-in-q4-losses-2000705317",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/strategy-1200x675.jpg",
"publishedAt": "2026-01-05T22:30:46Z",
"content": "Preeminent bitcoin treasury company Strategy reported a $17.44 billion unrealized loss in the fourth quarter of 2025 due to the crypto assets underperformance near the end of the year. Digital asset … [+4762 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Bitcoin Price Not Following ‘Digital Gold’ Narrative Amid Greenland Tensions",
"description": "Digital currency still shows vulnerability to the whims of the world.",
"url": "https://gizmodo.com/bitcoin-price-not-following-digital-gold-narrative-amid-greenland-tensions-2000712910",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Bitcoin-Digital-Gold-Narrative-1200x675.jpg",
"publishedAt": "2026-01-22T14:30:42Z",
"content": "While the original Bitcoin whitepaper mostly focused on the crypto network as a peer-to-peer digital cash system for decentralized payments, the narrative around the worlds largest and most valuable … [+3507 chars]"
},
-{
-"source": {
"id": "business-insider",
"name": "Business Insider"
},
"author": "amorrell@businessinsider.com (Alex Morrell)",
"title": "Goldman Sachs breaks down what the doomsayers get wrong about the US economy in 8 charts",
"description": "Investors gripped with concern over the US economy can relax. Goldman Sachs explains why common worries, including frothy valuations, are overblown.",
"url": "https://www.businessinsider.com/goldman-sachs-bears-are-wrong-us-stocks-will-rise-2026-1",
"urlToImage": "https://i.insider.com/6966b71264858d02d21849b1?width=1200&format=jpeg",
"publishedAt": "2026-01-14T10:33:01Z",
"content": "American investors are worried.\r\nThey've been worried for a while now: that a recession is coming, that stock valuations are overheated, and that AI spending is the only thing keeping the economy (an… [+7496 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Trump’s Pick for Fed Chair Points to Growing Bitcoin-Dollar Synthesis",
"description": "Warsh's hawkish stance on Fed policy may have disappointed the crypto world, but he said Bitcoin was effectively gold for anyone under the age of 40.",
"url": "https://gizmodo.com/trumps-pick-for-fed-chair-points-to-growing-bitcoin-dollar-synthesis-2000716347",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Kevin-Warsh-smiling-while-wearing-sunglasses-1200x675.jpg",
"publishedAt": "2026-01-31T20:57:01Z",
"content": "On Friday, it was revealed that President Trumps pick to replace Federal Reserve Chairman Jerome Powell in May will be Kevin Warsh, who previously served as a member of the Federal Reserve Board of G… [+4659 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "How Winter Storm Fern Slowed Down the Bitcoin Network",
"description": "When an immutable blockchain meets unstoppable force of nature.",
"url": "https://gizmodo.com/how-winter-storm-fern-slowed-down-the-bitcoin-network-2000715094",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/Bitcoin-network-slow-winter-storm-1200x675.jpg",
"publishedAt": "2026-01-28T19:35:27Z",
"content": "The Bitcoin network hashrate, which is the amount of computing power that is pointed at the crypto network, saw a massive decline over the weekend, falling from just over 1,000 exahashes per second o… [+5001 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Report Shows Massive Increase in Iranian Bitcoin Adoption Amid Nationwide Unrest",
"description": "Turns out people might like to circumvent centralized financial infrastructure in times of political upheaval.",
"url": "https://gizmodo.com/iranian-bitcoin-adoption-amid-nationwide-unrest-2000711457",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/iran-btc-1200x675.jpg",
"publishedAt": "2026-01-17T20:47:27Z",
"content": "A new report from blockchain analytics firm Chainalysis indicates there has been a massive increase in Bitcoin adoption in Iran over the past month, as the country deals with nationwide unrest and pr… [+3833 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Will Bitcoin Price ‘Keep Bleeding’? Analyst Warns of Further Declines as Tom Lee Faces Backlash Over Missed Targets",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_7576042d-fb47-48f5-a426-1e846ebc19e6",
"urlToImage": null,
"publishedAt": "2026-01-30T09:10:20Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": null,
"title": "Viral Prediction: 5,000 XRP Will Equal 1 Bitcoin by End of 2026—The Math Behind the $18.40 XRP Target",
"description": null,
"url": "https://consent.yahoo.com/v2/collectConsent?sessionId=1_cc-session_42801ab5-57e9-4434-8206-a8c4e014531c",
"urlToImage": null,
"publishedAt": "2026-01-15T16:20:20Z",
"content": "If you click 'Accept all', we and our partners, including 245 who are part of the IAB Transparency &amp; Consent Framework, will also store and / or access information on a device (in other words, us… [+1046 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Mike Pearl",
"title": "Trump Family Makes $1.4 Billion Off Crypto in 2025, Offsetting Losses Elsewhere",
"description": "Crypto is now said to account for roughly 20% of the family’s $6.8 billion fortune.",
"url": "https://gizmodo.com/trump-family-makes-1-4-billion-off-crypto-in-2025-offsetting-losses-elsewhere-2000711770",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/shutterstock_2524666605-1200x675.jpg",
"publishedAt": "2026-01-21T10:00:44Z",
"content": "Donald Trump was dubbed the Crypto President before he even took office early last year, as the 45th and 47th President of the United States promised to do everything from establishing a strategic bi… [+3959 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Coinbase Makes Preparations to Face Crypto’s Quantum Computing Threat",
"description": "Fears of quantum computing breaking the back of blockchains are getting more realistic.",
"url": "https://gizmodo.com/coinbase-makes-preparations-to-face-cryptos-quantum-computing-threat-2000713591",
"urlToImage": "https://gizmodo.com/app/uploads/2022/06/d247600ed4f9f90c53650a2a9b7c2f60-e1768515078239-1200x675.jpg",
"publishedAt": "2026-01-24T12:30:24Z",
"content": "U.S.-based crypto exchange giant Coinbase has established an independent advisory board to evaluate and provide guidance on the threat quantum computing may pose to the cryptography used in blockchai… [+4370 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Crypto Hardware Wallet Maker Ledger Impacted by Third-Party Data Breach",
"description": "Crypto wasn't stolen this time, but data was leaked with the potential to lead to thefts later on.",
"url": "https://gizmodo.com/crypto-hardware-wallet-maker-ledger-impacted-by-third-party-data-breach-2000706407",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/letter-700x675.jpg",
"publishedAt": "2026-01-07T10:00:21Z",
"content": "Crypto hardware wallet provider Ledger has disclosed a security incident at its third-party payment processor, Global-e, exposing customer names and contact information. The breach affected an undisc… [+4365 chars]"
},
-{
-"source": {
"id": null,
"name": "Kotaku"
},
"author": "Lewis Parker",
"title": "Devs Behind Steam Game With Over 300,000 Reviews Hit The Panic Button After A Malicious Mod Starts Deleting Fans’ Data",
"description": "People Playground players are being urged to wipe their Steam Workshop mod lists\nThe post Devs Behind Steam Game With Over 300,000 Reviews Hit The Panic Button After A Malicious Mod Starts Deleting Fans’ Data appeared first on Kotaku.",
"url": "https://kotaku.com/people-playground-steam-mod-workshop-virus-2000665028",
"urlToImage": "https://kotaku.com/app/uploads/2026/02/ss_4f88bbde84018182a0dd974ada72378248055993.1920x1080-e1770042758220-1200x675.jpg",
"publishedAt": "2026-02-02T14:53:03Z",
"content": "The creators of People Playground, a lo-fi, cartoonishly gory sandbox with over 300,000 Steam reviews, have warned players to update the game immediately and delete all of their mods after a maliciou… [+1770 chars]"
},
-{
-"source": {
"id": null,
"name": "Gizmodo.com"
},
"author": "Kyle Torpey",
"title": "Tether Freezes $182 Million in Stablecoins as Reports Point to Heavy Crypto Use by Venezuela",
"description": "There's a new spotlight on crypto that's used to avoid sanctions after the abduction of Venezuelan President Nicolas Maduro.",
"url": "https://gizmodo.com/tether-freezes-182-million-in-stablecoins-as-reports-point-to-heavy-crypto-use-by-venezuela-2000709276",
"urlToImage": "https://gizmodo.com/app/uploads/2026/01/maduro_venezuela-1200x675.jpg",
"publishedAt": "2026-01-12T20:45:30Z",
"content": "Over the weekend, The Wall Street Journal reported on the use of stablecoins, specifically Tethers USDT, to circumvent sanctions imposed by the United States on Venezuela. The report indicates PdVSA,… [+5626 chars]"
},
-{
-"source": {
"id": null,
"name": "Cryptonews"
},
"author": "Sujha Sundararajan",
"title": "Bitmine Continues To Stake Ethereum, Adds Another $344.4M Worth ETH",
"description": "Tom Lee’s Bitmine has added nearly 100,000 ETH, valued at about $344.4 million on Thursday, lifting its Ethereum holdings to 908,192 ETH, worth $2.95...",
"url": "https://cryptonews.com/news/bitmine-continues-to-stake-ethereum-adds-another-344-4m-worth-eth/",
"urlToImage": "https://media.zenfs.com/en/cryptonews_us_711/20472ff7f17057c6837430f25a0641b5",
"publishedAt": "2026-01-08T07:45:15Z",
"content": "Tom Lees Bitmine has added nearly 100,000 ETH, valued at about $344.4 million on Thursday, lifting its Ethereum holdings to 908,192 ETH, worth $2.95 billion.\r\nThe additional staking comes hours after… [+1494 chars]"
},
-{
-"source": {
"id": null,
"name": "Internet"
},
"author": "info@thehackernews.com (The Hacker News)",
"title": "Researchers Uncover NodeCordRAT Hidden in npm Bitcoin-Themed Packages",
"description": "Cybersecurity researchers have discovered three malicious npm packages that are designed to deliver a previously undocumented malware called NodeCordRAT.\nThe names of the packages, all of which were taken down as of November 2025, are listed below. They were …",
"url": "https://thehackernews.com/2026/01/researchers-uncover-nodecordrat-hidden.html",
"urlToImage": "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgtexcKpvH8t1IN9Taxc25I-ykg1l98ahAsVYMYGLTw9Yy7W9ULsjlRNgMG0yUOpKRueTn5N36hOYSrgYP_-vZBuUYCzGgVleyQk0bZULbbIPYrfJxLPsZkJBQDjwooYWOllT3ifqBb5_T-JW6WywfZFvtKB2LQPySRO2kmhIfTQgxUSshZwyBNoC1J2nNv/s790-rw-e365/npm-malware.jpg",
"publishedAt": "2026-01-08T10:31:00Z",
"content": "Cybersecurity researchers have discovered three malicious npm packages that are designed to deliver a previously undocumented malware called NodeCordRAT.\r\nThe names of the packages, all of which were… [+1911 chars]"
},
-{
-"source": {
"id": "business-insider",
"name": "Business Insider"
},
"author": "Theron Mohamed",
"title": "Warren Buffett said he would have spent $100 billion without blinking — and cash is like 'oxygen' but 'not a good asset'",
"description": "Warren Buffett said in an interview filmed last May and aired this week that he would have been \"willing to spend $100 billion this afternoon.\"",
"url": "https://www.businessinsider.com/warren-buffett-cnbc-interview-berkshire-hathaway-deals-acquisitions-cash-investing-2026-1",
"urlToImage": "https://i.insider.com/6967982464858d02d21850b6?width=1200&format=jpeg",
"publishedAt": "2026-01-14T14:10:35Z",
"content": "Warren Buffett is the CEO of Berkshire Hathaway.Nati Harnik/AP\r\n<ul><li>Warren Buffett didn't like Berkshire having so much cash and would have happily spent $100 billion.</li><li>He compared cash to… [+3140 chars]"
},
-{
-"source": {
"id": null,
"name": "Yahoo Entertainment"
},
"author": "Reuters",
"title": "BitGo Holdings prices US IPO at $18, Bloomberg News reports",
"description": "Crypto custody startup BitGo Holdings priced its U.S. initial public offering above its indicated range on Wednesday, raising $212.8 million and ​paving the ...",
"url": "https://finance.yahoo.com/news/bitgo-holdings-prices-us-ipo-022338898.html",
"urlToImage": "https://s.yimg.com/os/en/reuters-finance.com/058b4a4637d4fb486d8be66a1df04cc3",
"publishedAt": "2026-01-22T02:23:38Z",
"content": "Jan 21 (Reuters) - Crypto custody startup BitGo Holdings priced its U.S. initial public offering above its indicated range on Wednesday, raising $212.8 million and paving the way for the first stock … [+1946 chars]"
},
-{
-"source": {
"id": null,
"name": "Kotaku"
},
"author": "Zack Zwiezen",
"title": "‘Infinite Money Glitch’ Finally Gave People Good Deals On Trade-Ins So GameStop Killed It",
"description": "Okay, wait, wait...not that much power to the players\nThe post ‘Infinite Money Glitch’ Finally Gave People Good Deals On Trade-Ins So GameStop Killed It appeared first on Kotaku.",
"url": "https://kotaku.com/infinite-money-glitch-switch-2-gamestop-fixed-patched-used-games-2000661415",
"urlToImage": "https://kotaku.com/app/uploads/2026/01/infinite-glitch-1200x675.jpg",
"publishedAt": "2026-01-20T23:12:09Z",
"content": "A YouTuber reportedly discovered a way to generate infinite money via a strange trade-in deal glitch at GameStop. After making a video about it, the company figured out what was going on and has now … [+3192 chars]"
},
-{
-"source": {
"id": null,
"name": "Theregister.com"
},
"author": "Jessica Lyons",
"title": "Brightspeed investigates breach as crims post stolen data for sale",
"description": "Crimson Collective claims 'sophisticated attack' that allows them to 'disconnect every user from their mobile service'\nInternet service provider Brightspeed confirmed that it's investigating criminals' claims that they stole more than a million customers' rec…",
"url": "https://www.theregister.com/2026/01/06/brightspeed_investigates_breach/",
"urlToImage": "https://regmedia.co.uk/2019/12/03/shutterstock_for_sale.jpg",
"publishedAt": "2026-01-06T20:54:45Z",
"content": "Internet service provider Brightspeed confirmed that it's investigating criminals' claims that they stole more than a million customers' records and have listed them for sale for three bitcoin, or ab… [+2229 chars]"
},
-{
-"source": {
"id": null,
"name": "24/7 Wall St."
},
"author": "Sam Daodu",
"title": "Standard Chartered’s $8 XRP Target Looks Conservative as Q1 2026 Catalysts Align—Here’s the Bull Case",
"description": "This XRP price prediction 2026 begins with a bold institutional call that may actually be understated. Standard Chartered’s $8 target reflects measured...",
"url": "https://247wallst.com/investing/2026/01/12/standard-chartereds-8-xrp-target-looks-conservative-as-q1-2026-catalysts-align-heres-the-bull-case/",
"urlToImage": "https://s.yimg.com/ny/api/res/1.2/QIwRNdnNDIv17KdyeYfMqA--/YXBwaWQ9aGlnaGxhbmRlcjt3PTEyMDA7aD04MDA-/https://media.zenfs.com/en/24_7_wall_st__718/2df8490dd7650fb5634edbcc3b945d97",
"publishedAt": "2026-01-12T14:13:17Z",
"content": "Tamisclao / Shutterstock.com\r\n<ul><li>Standard Chartered projects $8 XRP by 2026 based on sustained ETF inflows and RLUSD adoption.\r\n</li><li>XRP ETFs absorbed $1.3B in 50 days with zero net outflows… [+7505 chars]"
},
-{
-"source": {
"id": null,
"name": "TheStreet"
},
"author": "Anand Sinha",
"title": "Mysterious trader buys millions ahead of Supreme Court's Trump tariff ruling",
"description": "On Jan. 7, the U.S. Supreme Court deferred ruling on the litigation challenging President Donald Trump's global tariffs The new date for the next ruling is...",
"url": "https://www.thestreet.com/crypto/markets/mysterious-trader-buys-millions-ahead-of-supreme-courts-trump-tariff-ruling",
"urlToImage": "https://s.yimg.com/os/en/thestreet_881/0a815ea35fc4a99b5487ced1906c0959",
"publishedAt": "2026-01-09T20:05:03Z",
"content": "On Jan. 7, the U.S. Supreme Court deferred ruling on the litigation challenging President Donald Trump's global tariffs\r\nThe new date for the next ruling is set for Jan. 14.\r\nWhen Trump announced swe… [+3274 chars]"
},
-{
-"source": {
"id": null,
"name": "Cryptonews"
},
"author": "Amin Ayan",
"title": "Tom Lee–Linked Bitmine Sits on $6B in Unrealized Losses on ETH Reserve",
"description": "Bitmine Immersion Technologies, a publicly traded digital asset treasury firm linked to investor Tom Lee, is facing more than $6 billion in unrealized losses...",
"url": "https://cryptonews.com/news/tom-lee-linked-bitmine-sits-on-6b-in-unrealized-losses-on-eth-reserve/",
"urlToImage": "https://s.yimg.com/os/en/cryptonews_us_711/3c9b9b20dfa3d09a9f0b6afb3452e7fc",
"publishedAt": "2026-02-01T07:56:33Z",
"content": "Bitmine Immersion Technologies, a publicly traded digital asset treasury firm linked to investor Tom Lee, is facing more than $6 billion in unrealized losses on its Ether reserves after the latest do… [+3375 chars]"
},
-{
-"source": {
"id": "new-scientist",
"name": "New Scientist"
},
"author": "Michael Le Page, Leah Crane, Joshua Howgego, Matthew Sparkes",
"title": "The 5 worst ideas of the 21st century – and how they went wrong",
"description": "They offered so much promise, but ultimately turned sour. These are the most disappointing ideas since the turn of the millennium",
"url": "https://www.newscientist.com/article/2511248-the-5-worst-ideas-of-the-21st-century-and-how-they-went-wrong/",
"urlToImage": "https://images.newscientist.com/wp-content/uploads/2026/01/16121057/SEI_280925076.jpg",
"publishedAt": "2026-01-19T16:00:06Z",
"content": "Stephan Walter\r\nThese are our selections for the worst fumbles of the 21st century: ideas that were great, but got twisted or misused and didnt deliver on their original promise.\r\nBitcoin\r\nFor years,… [+19781 chars]"
},
-{
-"source": {
"id": null,
"name": "Github.com"
},
"author": "mermaidnicheboutique-code",
"title": "I built a quantum internet that runs on your WiFi",
"description": "World's first quantum internet over WiFi - 445 qubits across 3 IBM quantum computers - mermaidnicheboutique-code/luxbin-quantum-internet",
"url": "https://github.com/mermaidnicheboutique-code/luxbin-quantum-internet",
"urlToImage": "https://opengraph.githubassets.com/597bed33d709cdef8df2bbeb96a1e896a4dd0ec4955c29f451e92aa2b0bcd5dd/mermaidnicheboutique-code/luxbin-quantum-internet",
"publishedAt": "2026-01-08T22:09:07Z",
"content": "The world's first quantum internet running over consumer WiFi\r\nI built a quantum internet that runs on your home WiFi.\r\nNot a simulation. Not a concept. Running RIGHT NOW on:\r\n<ul><li>3 IBM quantum c… [+8813 chars]"
}
]
}
