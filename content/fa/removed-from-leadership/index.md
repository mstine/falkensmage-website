---
title: "Removed From Leadership"
subtitle: "Twice in my life, an accountability practice decided I didn't belong. Neither one ever looked at my judgment."
date: "2026-11-14T23:04:00Z"
slug: "removed-from-leadership"
legacy_url: "https://feralarchitecture.com/p/removed-from-leadership"
source: "feral-architecture/2026-11-08-removed-from-leadership.md"
cover: "cover.jpg"
---

Howdy, folks.

I've been kicked out of two congregations in my life. Only one of them had a steeple.

The second one had a backlog. I had just walked off a fifteen-month consulting engagement, exhausted, and changed roles to join Cloud Foundry engineering. They tossed me onto the BOSH team for a few weeks. This team paired. Nine to six. Two people, one keyboard, all day, every day.

I had never done that before.

Every so often I'd get up and walk away from the keyboard to call my family. I had barely seen them in months.

At the end of the rotation, the verdict came back. I was "uncommitted to pairing and probably shouldn't be on an engineering team."

Nobody said my code was bad. Nobody said my design instincts were off, or that I'd missed something a pair would have caught. The finding was about where my body was between nine and six.

I'd heard that sermon before.

## The first congregation

Years earlier, I had gone all in on fundamentalism. Bellevue Baptist. If I was going to do this, I was going to fucking *do* this. Biblical marriage. Male leadership. Submission. The whole catalog.

And accountability groups.

If you didn't grow up in this, let me paint it for you. You'd sit with a few other folks from church and work through a list of questions. The list was full of sins you could have committed. You were supposed to confess them to each other. Every week, you'd go down the list and check yourself against it, out loud, in front of witnesses.

The fear that instilled was no joke. Not fear of God, exactly. Fear of the list.

And what did the list ever catch? Nothing that mattered. It caught people who were scared enough to confess, and it missed everyone who wasn't.

We drove to Bellevue from Mississippi. That drive became a problem. So we started visiting local churches to see if we could find something that fit. There was a perceived disloyalty in it, a question of whether we were committed enough, whether we'd *stay*. Eventually we "decided to stay." We acknowledged the so-called spiritual warfare. And we were removed from leadership anyway.

So we left.

Same verdict. Different vestments.

Line them up and the mechanism is identical. Neither institution measured what I could see. Both measured where I was. Miles driven. Hours at the keyboard. Whether my body was in the approved place for the approved stretch of time. And both times, what counted against me was the life I had outside the room.

There's a line in my own notes from 2020, when I first tried to write my spiritual story down: *the folks that only checked on me because I was on a list.*

That's what accountability looks like when it runs on a list. It checks whether you're on it.

## Created with good intentions

In 2015, I wrote a book about cloud-native architecture. In it is a sentence I've never found reason to take back:

> "Big design up front, exhaustive documentation, architectural review boards, and lengthy regression testing cycles all fly in the face of the speed we're seeking. Of course, all of these practices were created with good intentions. Unfortunately, none of them have provided consistently measurable improvements in the number of defects that make it into production."

Five years later, writing about church instead of software, I wrote this: *nothing that was "supposed to work" and be "by the book" ever did.*

Same sentence. Two vocabularies. Five years apart. I didn't notice it was the same sentence until this week.

What finally made me notice was a pastor's daughter.

Kate L. Johnson writes *Quips and Confessionals*. When she was a little girl, she and her sister were dancing around in dress-up clothes with wings and magic wands, and her father informed them that, as Christians, they shouldn't do magic. It was witchcraft.

Fairies. He accused his kids of witchcraft for playing fairies.

Kate grew up and wrote [the sharpest analysis of AI oversight I've read this year](https://katejohnsonwrites.substack.com/p/accusing-children-of-witchcraft-and), and she never once mentions AI. Here's her:

> "The intention of all of these rules was to protect us. Instead, it created an insular culture, rooted in fear."

And here:

> "When you constantly have to defend the things that you love, you begin to distrust your own judgment. You begin to rely on outside authorities to tell you what is safe and what is sinful."

She has a name for it. *Discernment rooted in fear.* And she knows exactly what it does to the people raised inside it: it stunts the one faculty the rules were supposedly protecting.

Her sentence about good intentions and mine about review boards are the same sentence, too. A church built rules to protect its kids, and the rules made the kids unable to judge for themselves. An engineering org built gates to protect its codebase, and the gates took the credit while something else did the work.

## The pew and the Approve button

Now look at what the industry is building around AI.

The dominant answer to "how do we keep AI safe" is *keep a human in the loop.* Put a person next to the output. Give them a button. If they push it, the work ships.

That's a pew.

You've sat in that pew. Maybe not a literal one. Maybe it was a change advisory board, or a sign-off field on a deployment form, or a sprint review where everyone nodded. So what is the button measuring?

It measures where somebody is standing. It doesn't measure what they can see. A tired engineer with thirty seconds and an Approve button satisfies "human in the loop" exactly as well as a staff engineer with the evidence, the time, and the authority to stop the train. The phrase can't tell them apart. It was never designed to.

I wrote about this from the corporate side in [You've Been Heard](https://falkensmage.com/fa/youve-been-heard/): "human in the loop" mostly means somebody's name is on the thing when it blows up. The name is the point. The name is how the institution proves you were present.

And the other camp — the folks who think AI should never touch code at all? I covered their purity machine in [The Hand on the Lion](https://falkensmage.com/fa/the-hand-on-the-lion/) and I'm not doing the purity thing again. What matters here is that both camps make the same trade. One bans the tool. One stations a body next to it. Both swap judgment for a rule, because judgment is scary, and a rule can be checked off a list.

Kate again: "The tricky thing with fear is that it always needs an enemy."

I know what you're going to say. *Matt, you're the one running a fleet of AI agents. Of course you want fewer humans checking the machine.*

No. I want the checking to be real.

And I'll confess something. In 2022, I spent an afternoon on Twitter defending code review as a control procedure. In a regulated shop, I argued, you don't get to wish it away. Auditors verify that the control procedures have been followed.

I meant it. In a regulated shop, I still mean it.

But what was I defending? Not the auditor's checkmark. An auditor verifies that the procedure was followed, not that anyone saw anything. That's the list again. What I wanted from code review was the one moment in the process where somebody gets to say *I'm not sure* and have it count.

I was defending my right to be unsure about whether or not the drive from Mississippi could go on.

The list can't hold that. The list wants committed or not, approved or not. Bellevue heard our doubt as disloyalty. The Approve button doesn't have a field for it.

## What the fleet taught me

Then I built the most ceremonied process I've ever run.

My own personal system, the cognitive scaffold I've been building with a fleet of AI agents, went through a build with every gate I could think of. Nine phases. Thirty-two plans. Two hundred forty-one commits. Researchers, planners, plan-checkers, executors, verifiers. Every review passed.

It shipped a data model where forty percent of the references pointed at nothing. Forty fucking percent.

No reviewer caught it. A single query against the live database did.

Later I wrote the lesson down as a rule, and it's one of the most useful sentences I've written this year: *When artifacts all agree with each other, that is not evidence they are right — it is evidence the same claim propagated.*

That's a congregation. Every artifact in the room confirming the same premise to every other artifact, out loud, in front of witnesses. A checklist of sins we could have committed. Nobody checking the premise against the world.

Then it got more personal. I discovered that some of the checks my agents had been writing for me to verify were sending their output somewhere I never saw. The machine read it. My screen didn't. On paper, I was the human in the loop. In practice, I was signing off on checks I could not see.

The fix wasn't adding more of me. It was a rule: never record my verification as passed from silence. Wait for the word I was asked for. And never write a check for me until you've confirmed I can see the surface it lives on.

That's what discernment looks like when you build it instead of perform it. Not a body in the pew. An eye on the thing, and a no that holds.

## Discernment is earned

The fear never tells you this part: the work has made me sharper. Every day the agents hand me something, and every day I catch something. A logic error. A judgment call that went sideways. A piece of stale knowledge the model treated as load-bearing because it was in the training data and nobody told it the world had moved. Every catch goes back into the structure. The structure catches the next one. My eyes get better.

Kate says healthy discernment is cultivated "through wisdom, experience, and years of reflection," and that it can't grow "when we are too afraid to trust ourselves." The people who study expert intuition land in the same place from the other direction: trust a gut that was trained in a world regular enough to learn, with feedback on whether it was right. Never trust a gut because of how sure it feels.

That isn't a rule. It's a practice.

And the fear-based version, the church version, the compliance version, can't produce it. It replaces the practice with a list. It trains people to look outward for permission. It produces exactly the person who can't say no, and then it stations that person next to the machine and calls it oversight.

I wrote [a line for the Hierophant](https://arcaeon.rocks/tracks/05-hierophant.html) once, the card of received doctrine at its shadow: *I gave away the question just to feel a little sure.*

That's the trade. Every time. You hand over the question, and in return you get to feel certain. The church gives you the list. The org gives you the button. And somewhere in the handoff, the faculty that could have kept you safe goes quiet.

## Where I'm standing now

Kate keeps fairy figurines all over her house now. She says they're reminders that she has permission to be herself.

I have figurines also. Some of them are physical, residing on altars and reminding me that I get to choose how to practice my spirituality. Some of them are virtual - a fleet of agents that get things wrong every single day, and a structure that lets me see it when they do, and the standing to say no. Both contain my version of permission.

I left one church that counted my miles. I got pushed out of one team that counted my hours. I'm not joining a third that counts approvals.

So here's the question I'd ask of any oversight in your life — at work, at church, inside your own head:

Does it measure where you're standing? Or what you can see?

And when you say no, does the no hold?

If it's the first one, you already know how that ends. You get removed from leadership. Usually right before you were going to leave anyway.

That's it for now.

Stay feral, folks.
