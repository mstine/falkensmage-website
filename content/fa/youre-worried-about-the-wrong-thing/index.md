---
title: "You’re Worried About the Wrong Thing"
subtitle: "The environmental cost of AI is real. It's just not where you think it is."
date: "2026-04-06T20:17:31.356Z"
slug: "youre-worried-about-the-wrong-thing"
legacy_url: "https://feralarchitecture.com/p/youre-worried-about-the-wrong-thing"
source: "feral-architecture/2026-04-06-youre-worried-about-the-wrong-thing.md"
cover: "cover.jpg"
---

I live 25 minutes from the xAI Colossus data center in South Memphis.

I also use AI every day. To write. To build software. To think through problems that would otherwise take me three times as long to untangle. I’m not bashful about this, and if you’ve read anything else I’ve written here, you already know that.

So when someone drops into my mentions to inform me that every ChatGPT query wastes a bottle of water and I’m personally contributing to environmental collapse — I have some feelings about it. Because I can drive to an actual environmental problem caused by AI infrastructure in less time than it takes to watch an episode of something on Netflix. And I promise you, the actual problem looks nothing like what’s going viral on your timeline.

Let me tell you what’s actually happening. Then let me tell you what isn’t. And then let me tell you why the people yelling the loudest about AI and the environment are making the real problem worse, not better.

---

## The Thing Down the Road

Boxtown is a neighborhood in South Memphis. Predominantly Black. Already surrounded by an oil refinery, a steel mill, and a TVA gas plant. Cancer risk four times the national average. This is the neighborhood where Elon Musk’s xAI decided to build one of the largest AI data centers on the planet.

They installed up to 35 methane gas turbines. Without Clean Air Act permits.[^1] Without environmental review. Just... built them.

The NAACP, the Southern Environmental Law Center, and Earthjustice filed suit. The NAACP issued its first-ever national data center environmental justice framework,[^2] and the core statement was six words that should be tattooed on the forehead of every tech executive who waves job creation numbers at a community hearing: *”Jobs cannot justify the harm.”*

I drive past this reality on my way to Target.

So when I say the environmental impact of AI is real, I’m not being diplomatic. I’m not hedging. I’m not doing the thing where a tech person acknowledges environmental concerns as a throat-clearing exercise before explaining why their preferred tool is actually fine. The harm is real. I can see it from the interstate.

And — this is where it gets uncomfortable for everyone — the harm has almost nothing to do with your ChatGPT query.

---

## The Bottle of Water That Doesn’t Exist

Here’s the claim you’ve probably seen: every AI query wastes a bottle of water.

It traces to a 2023 UC Riverside paper that found GPT-3 consumed about 500 ml of water per 20–50 queries.[^3] Per *conversation*. Not per question. By the time this reached social media, it had mutated into “one bottle per query” — overstated by somewhere between 20 and 2,000 times, depending on which data center processes your request.

Google disclosed in 2025 that a median Gemini text prompt consumes 0.26 milliliters of water.[^4] That’s five drops. Sam Altman put ChatGPT at roughly 0.3 ml.[^5] Even the high-end independent estimates land around 25 ml — a couple of tablespoons, not a Poland Spring.

The ten-times-more-energy claim? Also outdated. That was roughly accurate in early 2023.[^6] By 2025, Epoch AI measured ChatGPT at about 0.3 watt-hours per query — the same as a Google search.[^7] Turns out when Google added AI-generated overviews to every search result, the gap closed from both directions. Funny how that works.

“Training one AI model emits as much CO₂ as five cars over their lifetimes.” Technically true for one specific 2019 experiment that involved 4,789 training runs over six months using neural architecture search.[^8] Google’s own researchers called the estimate 18 to 88 times too high for how anyone actually trains models.[^9] Hugging Face trained BLOOM — 176 billion parameters — on France’s nuclear grid and emitted 25 metric tons.[^10] Meaningful, but not five cars. Not even one car.

“AI will consume 25% of US electricity by 2030.” The IEA’s actual projection is 8–10%.[^11] The confusion comes from conflating share of electricity demand *growth* with share of* total* demand. These are different numbers. Treating them as interchangeable is either innumeracy or dishonesty, and I’m not sure which is more common on social media.

Here’s my favorite: “AI-generated images use 10 gallons of water each.” This one has no peer-reviewed source at all. The actual figure is roughly 15–60 milliliters. The viral Ghibli portrait trend of early 2025 generated enormous environmental anxiety and trivial environmental impact.

I know what you’re going to say: “But even if the numbers are smaller, it still adds up.”

You’re right. Let’s add it up.

Ten ChatGPT queries a day, every day, for a year: roughly 11 kilograms of CO₂. That’s 0.07% of the average American’s annual carbon footprint. It’s less impactful than virtually any other behavioral change you could make. Less than one round trip to the grocery store. Less than the energy your phone charger wastes being plugged in overnight for a year.

Your AI guilt is doing nothing. Nothing for the environment, nothing for the communities actually affected, nothing for the policy changes that would matter. It’s a purely aesthetic position — the environmental equivalent of a reusable straw.

---

## The Part Where I Get Angry

You know what “reduce your carbon footprint” is? It’s a phrase invented by BP’s PR firm. Literally. Ogilvy & Mather developed the concept for BP in 2004[^12] to shift public attention from industrial emissions to personal consumption choices. It worked spectacularly. Twenty years later, people still feel guilty about their light bulbs while the fossil fuel industry emits 35 billion tons of CO₂ annually.

The people shaming you for using AI are running the same playbook. They have individualized a systemic problem, and they’ve done it with data that is wrong by orders of magnitude. The viral claims *feel* true because guilt is sticky. A bottle of water per query! Ten gallons per image! The numbers are wrong, but the shame lands, and shame is the point. Shame makes you feel like you’re doing something by feeling bad. You’re not.

Meanwhile, here’s what’s actually happening at the systemic level — the stuff that doesn’t go viral because it requires policy, not posting:

Microsoft pledged carbon negativity by 2030. Their emissions have risen 23.4% above their 2020 baseline. Their *market-based* Scope 2 emissions — the number they put in the press release — is 259,000 metric tons. Their* location-based* Scope 2 — the number that reflects what’s actually coming out of the power plants running their data centers — exceeds 10 million metric tons. That’s a factor of 40. They claim 100% renewable energy because they buy Renewable Energy Certificates, which is a financial instrument that lets you say you’re using clean energy while the actual electrons powering your servers come from a natural gas plant in Virginia. Google does the same thing. A* Guardian* analysis found the Big Four’s actual emissions are likely 7.6 times higher than reported.[^13]

Goldman Sachs estimates that 60% of incremental data center power demand between now and 2030 will be met by natural gas.[^14] Not renewables. Not nuclear. Gas. There are 38 gigawatts of captive gas plants in development specifically for data centers. The tech industry’s nuclear contracts — Microsoft’s Three Mile Island restart, Google’s small modular reactors, Meta’s “Prometheus” procurement — are real commitments. They’re also years away. No SMRs operate in the US or Europe. Deployment is expected no earlier than the 2030s. In the meantime: gas.

Carbon removal? The Frontier Fund committed over a billion dollars. Microsoft contracted 22 million tonnes of removal in 2024. But total global carbon removal to date — all of it, everyone, every company — amounts to fewer than 10,000 tons. Microsoft’s annual emissions are 15 million metric tons. The gap is not percentage points. It is orders of magnitude.

This is what’s real. This is what matters. And this is what gets zero traction on social media because “the REC accounting framework that enables corporate greenwashing of Scope 2 emissions needs to shift to hourly geographic matching” doesn’t fit on a protest sign.

---

## The Part That’s Actually Good

I’m not here to tell you AI is fine. I’m here to tell you the truth is more complicated than the memes, and that includes the parts where AI is genuinely, measurably good for the environment.

NOAA’s AI Global Forecast System went operational in February 2026. It uses 0.3% of the computing resources of the traditional forecast system.[^15] Not 30%. Not 3%. Zero point three percent — while extending forecast accuracy by 18–24 hours. That’s not an incremental improvement. That’s a transformation of computational climate science.

Google DeepMind’s GNoME project discovered 2.2 million new crystal structures, with 380,000 predicted stable[^16] — expanding known stable materials approximately tenfold. Among them: 528 potential lithium-ion conductors for better batteries. Lawrence Berkeley’s autonomous lab is now robotically synthesizing these materials without human intervention. Carbon capture sorbents. More efficient solar cells. Battery chemistries that don’t require cobalt mined by children in the DRC.

UPS’s AI routing system eliminates 100 million driving miles annually. That’s 10 million gallons of fuel. 100,000 metric tons of CO₂ not emitted. Every year.

These aren’t hypothetical. These aren’t “AI could potentially maybe help the environment someday.” These are measured, operational, happening right now.

And here’s the paradox that nobody posting viral shame content wants to sit with: *the tool causing the infrastructure problem is also producing some of the most significant environmental breakthroughs of the decade*. Both are true. At the same time. And collapsing either side of that into a simple narrative — “AI is saving the planet” or “AI is destroying the planet” — makes you wrong and useless in equal measure.

---

## Jevons Is Laughing

There’s a concept from 1865 that explains why none of this resolves cleanly. William Stanley Jevons observed that when coal engines became more efficient, total coal consumption *increased*[^17] — because efficiency made coal cheaper, which made more uses economical, which drove demand far beyond what the efficiency gains saved.

This is happening with AI right now. NVIDIA’s chips are 10–20 times more efficient than five years ago. Microsoft’s electricity consumption tripled in the same period. Efficiency improved dramatically *per unit of compute*. Total consumption grew far faster. Satya Nadella said the quiet part loud after DeepSeek’s efficiency breakthrough: “As AI gets more efficient and accessible, we will see its use skyrocket.”[^18]

The conditions that make Jevons effects strongest — near-unlimited latent demand, rapidly falling costs, no obvious ceiling on usage types — are precisely the conditions characterizing AI right now.

So no, efficiency alone will not solve this. The hardware engineers can’t engineer their way out of a demand curve that steepens every time they make the product cheaper. This is a policy problem. Carbon pricing. Mandatory disclosure with location-based accounting, not the REC shell game. Water use regulation in drought-stressed regions. Data center environmental review that happens *before* the turbines are installed, not after the NAACP has to sue.

---

## Five Things That Are True at the Same Time

1. *Your ChatGPT query is not destroying the planet.* The per-query environmental claims dominating social media are wrong by one to three orders of magnitude. Your individual AI use is less environmentally significant than almost any other daily choice you make.
2. *The aggregate infrastructure buildout is a genuine and growing problem.* Data center electricity is on track to double by 2030. Corporate emissions are rising, not falling. Most new power is gas, not renewables. Water-intensive facilities are being built in drought-stressed regions. This is not hypothetical.
3. *Corporate sustainability claims are largely bullshit.* The gap between what companies report and what’s physically happening is measured in factors of 40. “100% renewable” is an accounting trick. Carbon removal commitments are aspirational by orders of magnitude. As IPCC lead author David Keith put it: “All this voluntary stuff and companies claiming to be green is basically greenwashing crap.”[^19]
4. *AI is producing real, sometimes transformative environmental benefits.* Not in theory. In operation. Right now. Weather forecasting, materials science, logistics, conservation. The benefits are specific, measured, and significant.
5. *And the trajectory matters more than the snapshot.* Whether AI becomes a net environmental positive or negative depends less on technology — which is improving rapidly — and more on whether governments treat AI infrastructure as a public interest requiring environmental oversight, or as an economic priority exempt from it. $736 billion in US hyperscaler spending is planned for 2025–2026. That money will lock in energy and water consumption patterns for decades. The window for effective governance is narrowing while we argue about bottles of water that don’t exist.

I live 25 minutes from one of the real problems. I use the tools every day. I refuse to pretend these things cancel each other out, and I refuse to let people who are wrong about the data shame people who are right about the utility.

The environmental cost of AI is real. It’s just not where you think it is. And your guilt is not a climate strategy.

*Stay feral, folks.*

[^1]: **Earthjustice/NAACP — xAI Colossus lawsuit**: [https://earthjustice.org/press/2026/naacp-threatens-lawsuit-over-xais-unpermitted-gas-turbines-in-mississippi](https://earthjustice.org/press/2026/naacp-threatens-lawsuit-over-xais-unpermitted-gas-turbines-in-mississippi)
[^2]: **NAACP — Data center environmental justice framework** (2026): [https://naacp.org/campaigns/stop-dirty-data-centers](https://naacp.org/campaigns/stop-dirty-data-centers)
[^3]: **“Making AI Less Thirsty”** — Li, Yang, Islam, Ren (2023): [https://arxiv.org/abs/2304.03271](https://arxiv.org/abs/2304.03271)
[^4]: **Google Gemini energy/water disclosure** (Aug 2025): [https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference/](https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference/)
[^5]: **Sam Altman — ChatGPT water usage** (Feb 2026)**:** [https://www.datacenterdynamics.com/en/news/sam-altman-chatgpt-queries-consume-034-watt-hours-of-electricity-and-0000085-gallons-of-water/](https://www.datacenterdynamics.com/en/news/sam-altman-chatgpt-queries-consume-034-watt-hours-of-electricity-and-0000085-gallons-of-water/)
[^6]: **de Vries — AI energy use in Joule** (2023): [https://www.cell.com/joule/fulltext/S2542-4351(23)00365-3](https://www.cell.com/joule/fulltext/S2542-4351(23)00365-3)
[^7]: **Epoch AI — ChatGPT energy analysis** (Feb 2025): [https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use/](https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use/)
[^8]: **Strubell, Ganesh, McCallum — Training emissions** (2019 ACL): [https://aclanthology.org/P19-1355/](https://aclanthology.org/P19-1355/)
[^9]: **Patterson et al. — Google carbon rebuttal** (2021): [https://arxiv.org/abs/2104.10350](https://arxiv.org/abs/2104.10350)
[^10]: **Hugging Face BLOOM emissions:** [https://arxiv.org/abs/2211.02001](https://arxiv.org/abs/2211.02001)
[^11]: **IEA — Data center electricity projections** (Apr 2025): [https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai](https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai)
[^12]: **BP/Ogilvy “carbon footprint” origin**: [https://interestingengineering.com/culture/carbon-footprint-coined-by-big-oil-to-blame-you-for-climate-change](https://interestingengineering.com/culture/carbon-footprint-coined-by-big-oil-to-blame-you-for-climate-change)
[^13]: **Guardian — Big Four emissions 7.6× higher than reported**: [https://www.theguardian.com/technology/2024/sep/15/data-center-gas-emissions-tech](https://www.theguardian.com/technology/2024/sep/15/data-center-gas-emissions-tech)
[^14]: **Goldman Sachs — Data center power projections**: [https://www.goldmansachs.com/pdfs/insights/pages/generational-growth-ai-data-centers-and-the-coming-us-power-surge/report.pdf](https://www.goldmansachs.com/pdfs/insights/pages/generational-growth-ai-data-centers-and-the-coming-us-power-surge/report.pdf)
[^15]: **NOAA AI Global Forecast System** (Feb 2026): [https://www.noaa.gov/news-release/noaa-deploys-new-generation-of-ai-driven-global-weather-models](https://www.noaa.gov/news-release/noaa-deploys-new-generation-of-ai-driven-global-weather-models)
[^16]: **Google DeepMind GNoME** — Nature: [https://www.nature.com/articles/s41586-023-06735-9](https://www.nature.com/articles/s41586-023-06735-9)
[^17]: **Luccioni, Strubell et al. — Jevons Paradox & AI** (ACM FAccT 2025): [https://arxiv.org/abs/2501.16548](https://arxiv.org/abs/2501.16548)
[^18]: **Nadella — Jevons Paradox after DeepSeek**: [https://fortune.com/2025/01/27/microsoft-ceo-satya-nadella-deepseek-optimism-jevons-paradox/](https://fortune.com/2025/01/27/microsoft-ceo-satya-nadella-deepseek-optimism-jevons-paradox/)
[^19]: **David Keith quote:** [https://www.computerworld.com/article/4037695/can-microsoft-build-massive-ai-data-centers-and-meet-climate-goals-without-greenwashing.html](https://www.computerworld.com/article/4037695/can-microsoft-build-massive-ai-data-centers-and-meet-climate-goals-without-greenwashing.html)
