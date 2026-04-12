public static class SetupSessionData
{
    public static string PlayerName = "";
    public static string AIName = "";
    public static string Relationship = "unknown";
    public static string PlayerRole = "";
    public static string AIRole = "";
    public static string Background = "";
    public static string AIPersonality = "defensive";
    public static string Goal = "persuasion";
    public static string PlayerGoal = "persuasion";
    public static string AIGoal = "persuasion";
    public static string PlayerStance = "The current behavior or situation is not acceptable.";
    public static string AIStance = "The current behavior or situation is acceptable or justified.";
    public static string SetupMode = "general";
    /// <summary>Indexed corpus id from PDF upload, applied on next InitSession if attach failed early.</summary>
    public static string PendingRagCorpusId = "";

    public static void Reset()
    {
        PlayerName = "";
        AIName = "";
        Relationship = "unknown";
        PlayerRole = "";
        AIRole = "";
        Background = "";
        AIPersonality = "defensive";
        Goal = "persuasion";
        PlayerGoal = "persuasion";
        AIGoal = "persuasion";
        PlayerStance = "The current behavior or situation is not acceptable.";
        AIStance = "The current behavior or situation is acceptable or justified.";
        SetupMode = "general";
        PendingRagCorpusId = "";
    }

    public static void ValidateAndFillDefaults()
    {
        if (string.IsNullOrWhiteSpace(PlayerName))
            PlayerName = "Player";

        if (string.IsNullOrWhiteSpace(AIName))
            AIName = "AI";

        if (string.IsNullOrWhiteSpace(Relationship))
            Relationship = "unknown";

        // PlayerRole/AI_Role stay as-is (set by ink for landlord-tenant)

        if (string.IsNullOrWhiteSpace(Background))
            Background = "No background provided.";


        if (string.IsNullOrWhiteSpace(AIPersonality))
            AIPersonality = "defensive";

        if (string.IsNullOrWhiteSpace(PlayerGoal))
            PlayerGoal = "persuasion";

        if (string.IsNullOrWhiteSpace(AIGoal))
            AIGoal = "persuasion";

        if (string.IsNullOrWhiteSpace(AIGoal) && !string.IsNullOrWhiteSpace(Goal))
            AIGoal = Goal;

        Goal = AIGoal;

        if (string.IsNullOrWhiteSpace(PlayerStance))
            PlayerStance = "The current behavior or situation is not acceptable.";

        if (string.IsNullOrWhiteSpace(AIStance))
            AIStance = "The current behavior or situation is acceptable or justified.";

        if (string.IsNullOrWhiteSpace(SetupMode))
            SetupMode = "general";
    }

    public static void ClearPendingRagCorpus()
    {
        PendingRagCorpusId = "";
    }
}
