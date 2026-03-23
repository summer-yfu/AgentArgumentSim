using TMPro;
using UnityEngine;

public class GoalProgressOverlay : MonoBehaviour
{
    [Header("Goal Labels")]
    [SerializeField] private TMP_Text playerGoalText;
    [SerializeField] private TMP_Text aiGoalText;

    [Header("Progress Labels")]
    [SerializeField] private TMP_Text playerProgressText;
    [SerializeField] private TMP_Text aiProgressText;

    [Header("Progress Bars")]
    [SerializeField] private ToxicityBar playerProgressBar;
    [SerializeField] private ToxicityBar aiProgressBar;

    bool warnedMissingRefs;

    public void EnsureUI(RectTransform parent = null)
    {
        if (warnedMissingRefs)
            return;

        if (playerGoalText == null || aiGoalText == null || playerProgressText == null || aiProgressText == null || playerProgressBar == null || aiProgressBar == null)
        {
            Debug.LogWarning("GoalProgressOverlay: Assign player/AI goal texts and both progress bars in the Inspector.");
            warnedMissingRefs = true;
        }
    }

    public void SetGoals(string playerGoal, string aiGoal)
    {
        EnsureUI();
        if (playerGoalText != null)
            playerGoalText.text = $"Player goal: {HumanizeGoal(playerGoal)}";
        if (aiGoalText != null)
            aiGoalText.text = $"AI goal: {HumanizeGoal(aiGoal)}";
    }

    public void SetProgress(float playerProgress, float aiProgress)
    {
        EnsureUI();
        playerProgress = Mathf.Clamp01(playerProgress);
        aiProgress = Mathf.Clamp01(aiProgress);

        if (playerProgressText != null)
            playerProgressText.text = $"Player progress: {Mathf.RoundToInt(playerProgress * 100f)}%";
        if (aiProgressText != null)
            aiProgressText.text = $"AI progress: {Mathf.RoundToInt(aiProgress * 100f)}%";
        if (playerProgressBar != null)
            playerProgressBar.SetValue(playerProgress);
        if (aiProgressBar != null)
            aiProgressBar.SetValue(aiProgress);
    }

    string HumanizeGoal(string rawGoal)
    {
        if (string.IsNullOrWhiteSpace(rawGoal))
            return "persuasion";

        string goal = rawGoal.Trim().Replace("_", " ").Replace("-", " ");
        return char.ToUpperInvariant(goal[0]) + goal.Substring(1);
    }
}
