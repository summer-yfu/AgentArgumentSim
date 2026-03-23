using System;
using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class HttpClient : MonoBehaviour
{
    public static HttpClient Instance;
    const float TypingIndicatorFrameSeconds = 0.35f;
    const float FinishPanelDelayAfterMediatorSeconds = 3f;
    static readonly Color TypingIndicatorColor = Color.black;

    [Tooltip("Base URL only, e.g. http://127.0.0.1:8191 - do NOT include /turn or /init_session")]
    public string serverUrl = "http://127.0.0.1:8191";

    string BaseUrl => serverUrl.TrimEnd('/').Replace("/turn", "").Replace("/init_session", "").Replace("/parse_setup", "").TrimEnd('/');

    [Header("Chat UI - Scroll View Viewport")]
    public TMP_InputField inputField;
    public GameObject HumanMessages;
    public GameObject AIMessages;
    [Tooltip("Must be the Content GameObject under Scroll View's Viewport")]
    public GameObject Content;
    public ScrollRect scrollRect;
    public ToxicityBar matchStatusBar;
    [Tooltip("Assign the scene object that holds the two goal labels and two progress bars.")]
    public GoalProgressOverlay goalProgressOverlay;

    [Header("Emotion Display (optional) - two separate displays in different places")]
    [Tooltip("Human emote: shows player's emotion. Assign to a GameObject in the human/player area.")]
    public EmoteChanger humanEmoteChanger;
    [Tooltip("AI emote: shows AI's emotion. Assign to a GameObject in the AI area.")]
    public EmoteChanger aiEmoteChanger;

    void Awake()
    {
        Instance = this;
        if (goalProgressOverlay == null)
            goalProgressOverlay = FindObjectOfType<GoalProgressOverlay>();
        if (goalProgressOverlay != null)
            goalProgressOverlay.EnsureUI();
    }

    [Serializable]
    public class InitSessionRequest
    {
        public string session_id;
        public string player_name;
        public string ai_name;
        public string relationship;
        public string player_role;
        public string ai_role;
        public string ai_personality;
        public string goal;
        public string player_goal;
        public string ai_goal;
        public string player_stance;
        public string ai_stance;
        public string background;
        public string setup_mode;
        public string rag_corpus_id;
    }

    [Serializable]
    public class InitSessionResponse
    {
        public bool ok;
        public string player_name;
        public string ai_name;
        public string relationship;
        public string player_role;
        public string ai_role;
        public string ai_personality;
        public string goal;
        public string player_goal;
        public string ai_goal;
        public string player_stance;
        public string ai_stance;
        public string background;
        public string setup_mode;
        public string player_emotion;
        public string ai_emotion;
        public float player_goal_progress;
        public float ai_goal_progress;
    }

    [Serializable]
    public class AttachRagCorpusRequest
    {
        public string session_id;
        public string corpus_id;
    }

    [Serializable]
    public class AttachRagCorpusResponse
    {
        public bool ok;
        public string[] rag_corpora;
    }

    [Serializable]
    public class ParseSetupRequest
    {
        public string player_name;
        public string ai_name;
        public string relationship;
        public string background;
    }

    [Serializable]
    public class ParseSetupResponse
    {
        public string background;
        public string ai_personality;
        public string goal;
        public string player_goal;
        public string ai_goal;
        public string player_stance;
        public string ai_stance;
        public string relationship;
        public string player_role;
        public string ai_role;
    }

    [Serializable]
    public class TurnRequest
    {
        public string session_id;
        public string human_input;
    }

    [Serializable]
    public class TurnResponse
    {
        public string reply;
        public string[] replies;  // Up to 2 AI messages per turn (server sends both)
        public string speaker;
        public float toxicity;
        public string player_emotion;
        public string ai_emotion;
        public float player_goal_progress;
        public float ai_goal_progress;
        public string mediator_reply;
        public bool stop_match;
        public string stop_reason;
    }

    [Serializable]
    public class UploadDocumentResponse
    {
        public bool ok;
        public string corpus_id;
        public string filename;
    }

    public IEnumerator UploadDocument(string filePath, Action<UploadDocumentResponse> onSuccess, Action<string> onError)
    {
        byte[] fileData = System.IO.File.ReadAllBytes(filePath);
        string fileName = System.IO.Path.GetFileName(filePath);

        var form = new WWWForm();
        form.AddBinaryData("file", fileData, fileName, "application/pdf");

        using var req = UnityWebRequest.Post(BaseUrl + "/upload_document", form);
        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("UploadDocument HTTP Error: " + req.error);
            onError?.Invoke(req.error);
            yield break;
        }

        var resp = JsonUtility.FromJson<UploadDocumentResponse>(req.downloadHandler.text);
        onSuccess?.Invoke(resp);
    }

    public IEnumerator AttachRagCorpus(
        string sessionId,
        string corpusId,
        System.Action<AttachRagCorpusResponse> onSuccess,
        System.Action<string> onError)
    {
        var bodyObj = new AttachRagCorpusRequest { session_id = sessionId, corpus_id = corpusId };
        string json = JsonUtility.ToJson(bodyObj);
        byte[] body = Encoding.UTF8.GetBytes(json);

        using var req = new UnityWebRequest(BaseUrl + "/attach_rag_corpus", "POST");
        req.uploadHandler = new UploadHandlerRaw(body);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("AttachRagCorpus HTTP Error: " + req.error + " " + req.downloadHandler.text);
            onError?.Invoke(req.error);
            yield break;
        }

        var resp = JsonUtility.FromJson<AttachRagCorpusResponse>(req.downloadHandler.text);
        onSuccess?.Invoke(resp);
    }

    readonly System.Collections.Generic.List<(string speaker, string text)> chatHistory = new System.Collections.Generic.List<(string, string)>();
    GameObject activeTypingMessage;
    TMP_Text activeTypingText;
    Coroutine typingIndicatorCoroutine;
    bool awaitingTurnResponse;
    Color activeTypingOriginalColor = Color.white;

    public void ClearChatHistory() => chatHistory.Clear();

    public string GetChatHistoryAsText()
    {
        var sb = new StringBuilder();
        foreach (var (_, text) in chatHistory)
            sb.AppendLine(text);
        return sb.ToString();
    }

    public void DownloadChatHistory()
    {
        var text = GetChatHistoryAsText();
        if (string.IsNullOrEmpty(text)) { Debug.Log("No chat history to save."); return; }

        var dir = System.IO.Path.Combine(Application.persistentDataPath, "chathistory");
        var fileName = $"argument_chat_{System.DateTime.Now:yyyyMMdd_HHmmss}.txt";
        System.IO.Directory.CreateDirectory(dir);
        var path = System.IO.Path.Combine(dir, fileName);

        System.IO.File.WriteAllText(path, text, Encoding.UTF8);
        GUIUtility.systemCopyBuffer = path;
        Debug.Log(
            "[Chat export] Full path (also copied to clipboard): " + path +
            "\n[Chat export] persistentDataPath root: " + Application.persistentDataPath
        );
#if UNITY_EDITOR
        UnityEditor.EditorUtility.RevealInFinder(path);
#else
        try
        {
#if UNITY_STANDALONE_WIN
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = "explorer.exe",
                Arguments = "/select,\"" + path.Replace('/', '\\') + "\"",
                UseShellExecute = true,
            });
#elif UNITY_STANDALONE_OSX
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = "open",
                Arguments = "-R \"" + path + "\"",
                UseShellExecute = false,
            });
#elif UNITY_STANDALONE_LINUX
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = "xdg-open",
                Arguments = dir,
                UseShellExecute = true,
            });
#endif
        }
        catch (System.Exception e)
        {
            Debug.LogWarning("[Chat export] Could not open folder: " + e.Message);
        }
#endif
    }

    public IEnumerator InitSession(InitSessionRequest reqObj, Action<bool> onDone)
    {
        string json = JsonUtility.ToJson(reqObj);
        byte[] body = Encoding.UTF8.GetBytes(json);

        using var req = new UnityWebRequest(BaseUrl + "/init_session", "POST");
        req.uploadHandler = new UploadHandlerRaw(body);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("InitSession HTTP Error: " + req.error);
            onDone?.Invoke(false);
            yield break;
        }

        var resp = JsonUtility.FromJson<InitSessionResponse>(req.downloadHandler.text);
        ClearChatHistory();
        // Sync SetupSessionData from server response so client always matches what server stored
        if (resp.ok)
        {
            if (!string.IsNullOrWhiteSpace(resp.player_name)) SetupSessionData.PlayerName = resp.player_name;
            if (!string.IsNullOrWhiteSpace(resp.ai_name)) SetupSessionData.AIName = resp.ai_name;
            if (!string.IsNullOrWhiteSpace(resp.relationship)) SetupSessionData.Relationship = resp.relationship;
            if (!string.IsNullOrWhiteSpace(resp.player_role)) SetupSessionData.PlayerRole = resp.player_role;
            if (!string.IsNullOrWhiteSpace(resp.ai_role)) SetupSessionData.AIRole = resp.ai_role;
            if (!string.IsNullOrWhiteSpace(resp.ai_personality)) SetupSessionData.AIPersonality = resp.ai_personality;
            if (!string.IsNullOrWhiteSpace(resp.goal)) SetupSessionData.Goal = resp.goal;
            if (!string.IsNullOrWhiteSpace(resp.player_goal)) SetupSessionData.PlayerGoal = resp.player_goal;
            if (!string.IsNullOrWhiteSpace(resp.ai_goal)) SetupSessionData.AIGoal = resp.ai_goal;
            if (!string.IsNullOrWhiteSpace(resp.player_stance)) SetupSessionData.PlayerStance = resp.player_stance;
            if (!string.IsNullOrWhiteSpace(resp.ai_stance)) SetupSessionData.AIStance = resp.ai_stance;
            if (!string.IsNullOrWhiteSpace(resp.background)) SetupSessionData.Background = resp.background;
            if (!string.IsNullOrWhiteSpace(resp.setup_mode)) SetupSessionData.SetupMode = resp.setup_mode;
        }
        UpdateEmotionSprites(
            string.IsNullOrEmpty(resp.player_emotion) ? "neutral" : resp.player_emotion,
            string.IsNullOrEmpty(resp.ai_emotion) ? "neutral" : resp.ai_emotion
        );
        UpdateGoalAndProgress(
            string.IsNullOrWhiteSpace(resp.player_goal) ? SetupSessionData.PlayerGoal : resp.player_goal,
            string.IsNullOrWhiteSpace(resp.ai_goal) ? SetupSessionData.AIGoal : resp.ai_goal,
            resp.player_goal_progress,
            resp.ai_goal_progress
        );
        onDone?.Invoke(resp.ok);
    }

    public IEnumerator ParseSetup(ParseSetupRequest reqObj, Action<ParseSetupResponse> onSuccess, Action<string> onError)
    {
        string json = JsonUtility.ToJson(reqObj);
        byte[] body = Encoding.UTF8.GetBytes(json);

        using var req = new UnityWebRequest(BaseUrl + "/parse_setup", "POST");
        req.uploadHandler = new UploadHandlerRaw(body);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("ParseSetup HTTP Error: " + req.error);
            onError?.Invoke(req.error);
            yield break;
        }

        var resp = JsonUtility.FromJson<ParseSetupResponse>(req.downloadHandler.text);
        onSuccess?.Invoke(resp);
    }

    public void OnClickSend()
    {
        if (awaitingTurnResponse)
            return;
        if (GameSessionManager.Instance != null && GameSessionManager.Instance.MatchStopped)
            return;

        string message = inputField.text.Trim();
        if (string.IsNullOrEmpty(message))
            return;

        AddMessage("player", SetupSessionData.PlayerName + ": " + message);
        inputField.text = "";

        StartCoroutine(SendTurn(message));
    }

    IEnumerator SendTurn(string message)
    {
        awaitingTurnResponse = true;
        if (inputField != null)
            inputField.interactable = false;
        ShowTypingIndicator();

        var reqObj = new TurnRequest
        {
            session_id = GameSessionManager.Instance.SessionId,
            human_input = message
        };

        string json = JsonUtility.ToJson(reqObj);
        byte[] body = Encoding.UTF8.GetBytes(json);

        using var req = new UnityWebRequest(BaseUrl + "/turn", "POST");
        req.uploadHandler = new UploadHandlerRaw(body);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError("Turn HTTP Error: " + req.error);
            RemoveTypingIndicator();
            AddMessage("ai", SetupSessionData.AIName + ": [Network Error]");
            awaitingTurnResponse = false;
            if (inputField != null && (GameSessionManager.Instance == null || !GameSessionManager.Instance.MatchStopped))
                inputField.interactable = true;
            yield break;
        }

        var resp = JsonUtility.FromJson<TurnResponse>(req.downloadHandler.text);
        FinalizeTypingIndicatorWithText(SetupSessionData.AIName + ": " + resp.reply);

        // Show additional AI replies (server may send up to 2 per turn)
        if (resp.replies != null && resp.replies.Length > 1)
        {
            for (int i = 1; i < resp.replies.Length; i++)
                AddMessage("ai", SetupSessionData.AIName + ": " + resp.replies[i]);
        }

        if (!string.IsNullOrEmpty(resp.mediator_reply))
            AddMessage("mediator", "Mediator: " + resp.mediator_reply);

        UpdateEmotionSprites(resp.player_emotion, resp.ai_emotion);
        UpdateGoalAndProgress(SetupSessionData.PlayerGoal, SetupSessionData.AIGoal, resp.player_goal_progress, resp.ai_goal_progress);

        if (matchStatusBar != null)
            matchStatusBar.SetValue(resp.stop_match ? 1f : Mathf.Clamp01(resp.toxicity));

        if (GameSessionManager.Instance != null)
        {
            if (resp.stop_match)
                yield return WaitBeforeShowingFinishPanel(resp.mediator_reply);
            GameSessionManager.Instance.ApplyTurnState(resp.stop_match, resp.toxicity, resp.stop_reason);
        }

        awaitingTurnResponse = false;
        if (inputField != null && !resp.stop_match)
            inputField.interactable = true;
    }

    void AddMessage(string speaker, string text)
    {
        chatHistory.Add((speaker, text));
        if (Content == null)
            return;
        GameObject prefab = GetPrefabForSpeaker(speaker);
        if (prefab == null)
            return;
        GameObject msg = Instantiate(prefab, Content.transform, false);
        var messagesComp = msg.GetComponent<Messages>();
        if (messagesComp != null && messagesComp.MyMessage != null)
        {
            messagesComp.MyMessage.text = text;
            if (IsMediator(speaker))
                messagesComp.MyMessage.color = Color.red;
        }
        StartCoroutine(ScrollToBottomNextFrame());
    }

    IEnumerator ScrollToBottomNextFrame()
    {
        yield return null;
        if (Content != null && scrollRect != null)
        {
            Canvas.ForceUpdateCanvases();
            LayoutRebuilder.ForceRebuildLayoutImmediate(Content.GetComponent<RectTransform>());
            scrollRect.verticalNormalizedPosition = 0f;
        }
    }

    IEnumerator WaitBeforeShowingFinishPanel(string mediatorReply)
    {
        yield return ScrollToBottomNextFrame();
        yield return null;

        if (!string.IsNullOrWhiteSpace(mediatorReply))
            yield return new WaitForSeconds(FinishPanelDelayAfterMediatorSeconds);
    }

    bool IsMediator(string speaker)
    {
        string s = (speaker ?? "").Trim().ToLowerInvariant();
        return s == "mediator";
    }

    GameObject GetPrefabForSpeaker(string speaker)
    {
        string s = (speaker ?? "").Trim().ToLowerInvariant();
        if (s == "player" || s == "human") return HumanMessages ?? AIMessages;
        if (s == "ai" || s == "ai_arguer") return AIMessages ?? HumanMessages;
        if (s == "mediator") return AIMessages ?? HumanMessages;
        return AIMessages ?? HumanMessages;
    }

    void ShowTypingIndicator()
    {
        RemoveTypingIndicator();
        GameObject prefab = GetPrefabForSpeaker("ai");
        if (prefab == null || Content == null)
            return;

        activeTypingMessage = Instantiate(prefab, Content.transform, false);
        var messagesComp = activeTypingMessage.GetComponent<Messages>();
        if (messagesComp != null && messagesComp.MyMessage != null)
        {
            activeTypingText = messagesComp.MyMessage;
            activeTypingOriginalColor = activeTypingText.color;
            activeTypingText.color = TypingIndicatorColor;
            typingIndicatorCoroutine = StartCoroutine(AnimateTypingIndicator());
        }
        StartCoroutine(ScrollToBottomNextFrame());
    }

    IEnumerator AnimateTypingIndicator()
    {
        int frame = 0;
        while (activeTypingText != null)
        {
            frame = (frame % 3) + 1;
            activeTypingText.text = new string('.', frame);
            yield return new WaitForSeconds(TypingIndicatorFrameSeconds);
        }
    }

    void RemoveTypingIndicator()
    {
        if (typingIndicatorCoroutine != null)
        {
            StopCoroutine(typingIndicatorCoroutine);
            typingIndicatorCoroutine = null;
        }
        activeTypingText = null;
        if (activeTypingMessage != null)
            Destroy(activeTypingMessage);
        activeTypingMessage = null;
    }

    void FinalizeTypingIndicatorWithText(string text)
    {
        chatHistory.Add(("ai", text));

        if (typingIndicatorCoroutine != null)
        {
            StopCoroutine(typingIndicatorCoroutine);
            typingIndicatorCoroutine = null;
        }

        if (activeTypingText != null)
        {
            activeTypingText.color = activeTypingOriginalColor;
            activeTypingText.text = text;
            activeTypingText = null;
            activeTypingMessage = null;
            StartCoroutine(ScrollToBottomNextFrame());
            return;
        }

        AddMessage("ai", text);
    }

    void UpdateEmotionSprites(string playerEmotion, string aiEmotion)
    {
        if (humanEmoteChanger != null)
            humanEmoteChanger.SetEmotion(playerEmotion);
        if (aiEmoteChanger != null)
            aiEmoteChanger.SetEmotion(aiEmotion);
    }

    void UpdateGoalAndProgress(string playerGoal, string aiGoal, float playerProgress, float aiProgress)
    {
        if (goalProgressOverlay == null)
            return;
        goalProgressOverlay.EnsureUI();
        goalProgressOverlay.SetGoals(playerGoal, aiGoal);
        goalProgressOverlay.SetProgress(playerProgress, aiProgress);
    }
}