using System;
using UnityEngine;

public class GameSessionManager : MonoBehaviour
{
    public static GameSessionManager Instance;

    public string SessionId { get; private set; }
    public string PlayerName { get; private set; }
    public bool MatchStopped { get; private set; }

    [Header("Screens")]
    public GameObject setupScreen;
    public GameObject chatScreen;
    [Tooltip("Game Finished popup - enable when match stops")]
    public GameFinishedController gameFinishedScreen;

    [Header("Auto Init")]
    public bool autoInitFromSetupData = true;

    void Awake()
    {
        Instance = this;
        SessionId = Guid.NewGuid().ToString();
    }

    void Start()
    {
        if (!autoInitFromSetupData)
            return;

        SetupSessionData.ValidateAndFillDefaults();
        InitSession(
            SetupSessionData.PlayerName,
            SetupSessionData.AIName,
            SetupSessionData.Relationship,
            SetupSessionData.PlayerRole,
            SetupSessionData.AIRole,
            SetupSessionData.AIPersonality,
            SetupSessionData.PlayerGoal,
            SetupSessionData.AIGoal,
            SetupSessionData.Background,
            SetupSessionData.SetupMode
        );
    }

    public void InitSession(string playerName, string aiName, string relationship, string playerRole, string aiRole, string aiPersonality, string playerGoal, string aiGoal, string background, string setupMode)
    {
        PlayerName = playerName;
        MatchStopped = false;
        if (HttpClient.Instance != null)
        {
            HttpClient.Instance.ClearChatHistory();
            if (HttpClient.Instance.inputField != null)
                HttpClient.Instance.inputField.interactable = true;
        }

        var req = new HttpClient.InitSessionRequest
        {
            session_id = SessionId,
            player_name = playerName,
            ai_name = aiName ?? "",
            relationship = relationship,
            player_role = playerRole ?? "",
            ai_role = aiRole ?? "",
            ai_personality = aiPersonality,
            goal = aiGoal,
            player_goal = playerGoal,
            ai_goal = aiGoal,
            player_stance = SetupSessionData.PlayerStance,
            ai_stance = SetupSessionData.AIStance,
            background = background,
            setup_mode = setupMode,
            rag_corpus_id = SetupSessionData.PendingRagCorpusId ?? ""
        };

        StartCoroutine(HttpClient.Instance.InitSession(req, (ok) =>
        {
            if (ok)
            {
                SetupSessionData.ClearPendingRagCorpus();
                if (setupScreen != null)
                    setupScreen.SetActive(false);
                if (chatScreen != null)
                    chatScreen.SetActive(true);
            }
        }));
    }

    public void ApplyTurnState(bool stopMatch, float toxicity, string stopReason = "")
    {
        MatchStopped = stopMatch;

        if (MatchStopped)
        {
            if (HttpClient.Instance != null && HttpClient.Instance.inputField != null)
                HttpClient.Instance.inputField.interactable = false;
            if (gameFinishedScreen != null)
                gameFinishedScreen.Show(stopReason);
        }
    }
}