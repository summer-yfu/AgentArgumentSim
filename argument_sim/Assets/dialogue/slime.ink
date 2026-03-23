VAR Player_name = ""
VAR AI_name = ""
VAR Relationship = ""
VAR PlayerRole = ""
VAR AI_Role = ""
VAR Background = ""
VAR Location = ""
VAR Player_belief = ""
VAR AI_belief = ""
VAR AI_Personality = ""
VAR Goal = ""
VAR PlayerGoal = ""
VAR AIGoal = ""
VAR PlayerStance = ""
VAR AIStance = ""
VAR SetupMode = "general"

-> intro

=== intro ===
Welcome to **Argument Arena Simulation**!

You are about to face an AI opponent in a debate. Your goal might be to win, calm the situation, or reach a mutual understanding.

Whether you're practicing for an upcoming debate, learning how to handle arguments better, or just here to have fun, this is the place for you.

+ [Next]
 -> GameMech
=== GameMech ===
Before the debate begins, you'll set the background of the conflict, your relationship with the AI, and the AI's personality.

If things get too heated or go off topic, an AI mediator may step in.

Before the argument begins, let's set up the scenario.

+ [Start]
    -> setup_mode

=== setup_mode ===
Which setup mode do you want?

+ [General]
    ~ SetupMode = "general"
    -> relationship

+ [Law mode]
    ~ SetupMode = "law"
    -> relationship

=== relationship ===
What is your relationship with the AI opponent?

+ [Friend]
    ~ Relationship = "friends"
    -> name_prompt

+ [Roommate]
    ~ Relationship = "roommates"
    -> name_prompt

+ [Sibling]
    ~ Relationship = "siblings"
    -> name_prompt

+ [Romantic partner]
    ~ Relationship = "couple"
    -> name_prompt

+ [Coworker]
    ~ Relationship = "coworkers"
    -> name_prompt

+ [Parent / child]
    ~ Relationship = "parent-child"
    -> name_prompt

+ [Rival / opponent]
    ~ Relationship = "opponents"
    -> name_prompt

+ [I'm the landlord (tenancy dispute)]
    ~ Relationship = "landlord-tenant"
    ~ PlayerRole = "landlord"
    ~ AI_Role = "tenant"
    -> name_prompt

+ [I'm the tenant (tenancy dispute)]
    ~ Relationship = "landlord-tenant"
    ~ PlayerRole = "tenant"
    ~ AI_Role = "landlord"
    -> name_prompt

=== name_prompt ===
# INPUT:player_name
How would you like the AI to call you?
-> END

=== ai_name_prompt ===
# INPUT:ai_name
What would you like to call the AI?
-> END

=== background_menu ===
Nice to meet you, {Player_name}.

How would you like to set up the conflict?

+ [I'll describe the situation myself]
    -> background_input_prompt

+ [Guide me step by step]
    -> location_prompt

=== background_input_prompt ===
# INPUT:background
Describe what happened in your own words.
-> END

=== location_prompt ===
# INPUT:location
Where did this happen?
-> END

=== player_belief_prompt ===
# INPUT:player_belief
What do you believe is clearly true/false in this situation?
-> END

=== ai_belief_prompt ===
# INPUT:ai_belief
What do you think the AI believes is true/false?
-> END

=== personality ===
What kind of personality should the AI have?

+ [Defensive]
    ~ AI_Personality = "defensive"
    -> player_goal

+ [Logical]
    ~ AI_Personality = "logical"
    -> player_goal

+ [Emotional]
    ~ AI_Personality = "emotional"
    -> player_goal

+ [Stubborn]
    ~ AI_Personality = "stubborn"
    -> player_goal

+ [Passive-aggressive]
    ~ AI_Personality = "passive-aggressive"
    -> player_goal

+ [Calm and diplomatic]
    ~ AI_Personality = "calm"
    -> player_goal

=== player_goal ===
What is your main goal in this argument?

+ [Persuade each other]
    ~ PlayerGoal = "persuasion"
    -> ai_goal

+ [Resolve the conflict]
    ~ PlayerGoal = "conflict_resolution"
    -> ai_goal

+ [Figure out what really happened]
    ~ PlayerGoal = "truth_seeking"
    -> ai_goal

+ [Reach a decision]
    ~ PlayerGoal = "decision"
    -> ai_goal

+ [Fight it out verbally]
    ~ PlayerGoal = "verbal_fight"
    -> ai_goal

=== ai_goal ===
What should the AI mainly be trying to achieve?

+ [Persuade you]
    ~ AIGoal = "persuasion"
    ~ Goal = AIGoal
    -> finish_setup

+ [Resolve the conflict]
    ~ AIGoal = "conflict_resolution"
    ~ Goal = AIGoal
    -> finish_setup

+ [Figure out what really happened]
    ~ AIGoal = "truth_seeking"
    ~ Goal = AIGoal
    -> finish_setup

+ [Reach a decision]
    ~ AIGoal = "decision"
    ~ Goal = AIGoal
    -> finish_setup

+ [Fight it out verbally]
    ~ AIGoal = "verbal_fight"
    ~ Goal = AIGoal
    -> finish_setup

=== finish_setup ===
Setup complete.

Relationship: {Relationship}
AI personality: {AI_Personality}
Player goal: {PlayerGoal}
AI goal: {AIGoal}

+ [Continue]
    -> END