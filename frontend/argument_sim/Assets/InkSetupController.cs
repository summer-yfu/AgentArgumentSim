using System.Collections;
using System.Collections.Generic;
using Ink.Runtime;
using SimpleFileBrowser;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class InkSetupController : MonoBehaviour
{
    [Header("Ink")]
    [SerializeField] private TextAsset inkJSON;
    private Story story;

    [Header("Dialogue UI")]
    [SerializeField] private TMP_Text dialogueText;
    [SerializeField] private Transform choicesRoot;
    [SerializeField] private Transform continueButtonRoot;
    [SerializeField] private Button choiceButtonPrefab;
    [SerializeField] private float typewriterCharsPerSecond = 40f;

    [Header("Input UI")]
    [SerializeField] private GameObject inputPanel;
    [SerializeField] private TMP_InputField inputField;
    [SerializeField] private Button confirmButton;

    [Header("Summary UI")]
    [SerializeField] private GameObject summaryPanel;
    [SerializeField] private TMP_Text summaryText;
    [SerializeField] private Button confirmSetupButton;
    [SerializeField] private Button restartButton;

    [Header("Edit Setup (optional – assign to edit on summary instead of restart)")]
    [SerializeField] private GameObject editPanel;
    [SerializeField] private TMP_InputField editPlayerName;
    [SerializeField] private TMP_InputField editRelationship;
    [SerializeField] private TMP_InputField editBackground;
    [SerializeField] private TMP_InputField editAIPersonality;
    [SerializeField] private TMP_InputField editGoal;
    [SerializeField] private TMP_InputField editPlayerRole;
    [SerializeField] private TMP_InputField editAIRole;
    [SerializeField] private TMP_InputField editPlayerStance;
    [SerializeField] private TMP_InputField editAIStance;
    [SerializeField] private TMP_InputField editSetupMode;
    [SerializeField] private Button editPanelApplyButton;
    [SerializeField] private Button editPanelCancelButton;

    [Header("Document Upload (optional)")]
    [SerializeField] private Button uploadDocumentButton;
    [SerializeField] private TMP_Text uploadStatusText;

    [Header("Scene Flow")]
    [SerializeField] private Button startArgumentButton;
    [SerializeField] private string nextSceneName = "Argument Sim";

    private string pendingInputKey = "";
    private string uploadedCorpusId = "";

    private void Start()
    {
        if (inkJSON == null)
        {
            Debug.LogError("Ink JSON is not assigned.");
            return;
        }

        story = new Story(inkJSON.text);

        if (inputPanel != null) inputPanel.SetActive(false);
        if (summaryPanel != null) summaryPanel.SetActive(false);
        if (editPanel != null) editPanel.SetActive(false);
        if (startArgumentButton != null) startArgumentButton.gameObject.SetActive(false);

        if (confirmButton != null)
            confirmButton.onClick.AddListener(OnConfirmInput);

        if (confirmSetupButton != null)
            confirmSetupButton.onClick.AddListener(OnConfirmSetup);

        if (restartButton != null)
            restartButton.onClick.AddListener(OnEditSetup);

        if (startArgumentButton != null)
            startArgumentButton.onClick.AddListener(OnStartArgument);

        if (editPanelApplyButton != null)
            editPanelApplyButton.onClick.AddListener(OnEditPanelApply);
        if (editPanelCancelButton != null)
            editPanelCancelButton.onClick.AddListener(OnEditPanelCancel);

        if (uploadDocumentButton != null)
            uploadDocumentButton.onClick.AddListener(OnUploadDocument);
        if (uploadStatusText != null)
            uploadStatusText.text = "";

        RefreshUI();
    }

private void RefreshUI()
{
    ClearChoices();

    string fullText = "";

    // Read all continuable text in current paragraph
    while (story.canContinue)
    {
        string nextLine = story.Continue().Trim();

        if (!string.IsNullOrEmpty(nextLine))
        {
            if (!string.IsNullOrEmpty(fullText))
                fullText += "\n\n";

            fullText += nextLine;
        }

        HandleTags(story.currentTags);

        // Stop if this segment requires user input
        if (!string.IsNullOrEmpty(pendingInputKey))
            break;
    }

    dialogueText.text = fullText;

    bool hasChoices = story.currentChoices.Count > 0;
    bool useTypewriter = !string.IsNullOrEmpty(fullText) && typewriterCharsPerSecond > 0f && (hasChoices || !string.IsNullOrEmpty(pendingInputKey));

    if (useTypewriter)
    {
        dialogueText.maxVisibleCharacters = 0;
        StartCoroutine(TypewriterThenShow(fullText.Length, hasChoices));
    }
    else
    {
        dialogueText.maxVisibleCharacters = int.MaxValue;
        if (string.IsNullOrEmpty(pendingInputKey))
            ShowChoices();
    }

    if (!story.canContinue && story.currentChoices.Count == 0 && string.IsNullOrEmpty(pendingInputKey))
    {
        SaveSetupData();
        ShowSummary();
    }
}

    private IEnumerator TypewriterThenShow(int totalChars, bool showChoicesWhenDone)
    {
        float interval = 1f / Mathf.Max(typewriterCharsPerSecond, 1f);
        int visible = 0;
        while (visible < totalChars)
        {
            visible = Mathf.Min(visible + 1, totalChars);
            dialogueText.maxVisibleCharacters = visible;
            yield return new WaitForSeconds(interval);
        }
        dialogueText.maxVisibleCharacters = int.MaxValue;
        if (showChoicesWhenDone)
            ShowChoices();
    }

    private void ShowChoices()
    {
        // Return early when no choices to avoid index out of range
        if (story.currentChoices == null || story.currentChoices.Count == 0)
            return;

        Debug.Log("ShowChoices");
        Debug.Log(story.currentChoices.Count);
        Debug.Log(story.currentChoices[0].text);

        bool useContinueArea = continueButtonRoot != null && story.currentChoices.Count == 1;
        string singleText = useContinueArea ? story.currentChoices[0].text.Trim() : "";
        useContinueArea = useContinueArea && (singleText == "Next" || singleText == "Start" || singleText == "Continue");

        Transform parent = useContinueArea ? continueButtonRoot : choicesRoot;
        if (useContinueArea && choicesRoot != null)
            choicesRoot.gameObject.SetActive(false);
        else if (choicesRoot != null)
            choicesRoot.gameObject.SetActive(true);
        if (continueButtonRoot != null)
            continueButtonRoot.gameObject.SetActive(useContinueArea);

        foreach (Choice choice in story.currentChoices)
        {
            Button btn = Instantiate(choiceButtonPrefab, parent);
            TMP_Text btnText = btn.GetComponentInChildren<TMP_Text>();

            if (btnText != null)
                btnText.text = choice.text;

            int choiceIndex = choice.index;
            btn.onClick.AddListener(() =>
            {
                story.ChooseChoiceIndex(choiceIndex);
                RefreshUI();
            });
        }
    }

    private void HandleTags(List<string> tags)
    {
        pendingInputKey = "";

        foreach (string tag in tags)
        {
            if (tag.StartsWith("INPUT:"))
            {
                pendingInputKey = tag.Substring("INPUT:".Length).Trim();

                inputPanel.SetActive(true);
                inputField.text = "";
                inputField.ActivateInputField();
                return;
            }
        }

        inputPanel.SetActive(false);
    }

    private void OnConfirmInput()
    {
        if (string.IsNullOrEmpty(pendingInputKey))
            return;

        string value = inputField.text.Trim();
        if (string.IsNullOrEmpty(value))
            return;

        switch (pendingInputKey)
        {
            case "player_name":
                story.variablesState["Player_name"] = value;
                story.ChoosePathString("ai_name_prompt");
                break;

            case "ai_name":
                story.variablesState["AI_name"] = value;
                story.ChoosePathString("background_menu");
                break;

            case "background":
                story.variablesState["Background"] = value;
                StartCoroutine(ParseBackgroundAndShowSummary(value));
                pendingInputKey = "";
                inputPanel.SetActive(false);
                return;

            case "location":
                story.variablesState["Location"] = value;
                story.ChoosePathString("player_belief_prompt");
                break;

            case "player_belief":
                story.variablesState["Player_belief"] = value;
                story.ChoosePathString("ai_belief_prompt");
                break;

            case "ai_belief":
                story.variablesState["AI_belief"] = value;

                string relationship = story.variablesState["Relationship"].ToString();
                string location = story.variablesState["Location"].ToString();
                string playerBelief = story.variablesState["Player_belief"].ToString();
                string aiBelief = story.variablesState["AI_belief"].ToString();

                string composedBackground =
                    $"Relationship: {relationship}\n" +
                    $"Location: {location}\n" +
                    $"Human believes this is true/false: {playerBelief}\n" +
                    $"AI believes this is true/false: {aiBelief}";

                story.variablesState["Background"] = composedBackground;
                StartCoroutine(ParseBackgroundAndContinue(composedBackground, "personality"));
                pendingInputKey = "";
                inputPanel.SetActive(false);
                return;
        }

        pendingInputKey = "";
        inputPanel.SetActive(false);
        RefreshUI();
    }

    private void SaveSetupData()
    {
        SetupSessionData.PlayerName = story.variablesState["Player_name"]?.ToString() ?? "";
        SetupSessionData.AIName = story.variablesState["AI_name"]?.ToString() ?? "";
        SetupSessionData.Relationship = story.variablesState["Relationship"]?.ToString() ?? "";
        SetupSessionData.PlayerRole = story.variablesState["PlayerRole"]?.ToString() ?? "";
        SetupSessionData.AIRole = story.variablesState["AI_Role"]?.ToString() ?? "";
        SetupSessionData.Background = story.variablesState["Background"]?.ToString() ?? "";
        SetupSessionData.AIPersonality = story.variablesState["AI_Personality"]?.ToString() ?? "";
        SetupSessionData.Goal = story.variablesState["Goal"]?.ToString() ?? "";
        SetupSessionData.PlayerGoal = story.variablesState["PlayerGoal"]?.ToString() ?? SetupSessionData.Goal;
        SetupSessionData.AIGoal = story.variablesState["AIGoal"]?.ToString() ?? SetupSessionData.Goal;
        SetupSessionData.PlayerStance = story.variablesState["PlayerStance"]?.ToString() ?? SetupSessionData.PlayerStance;
        SetupSessionData.AIStance = story.variablesState["AIStance"]?.ToString() ?? SetupSessionData.AIStance;
        SetupSessionData.SetupMode = story.variablesState["SetupMode"]?.ToString() ?? "general";
    }

    private IEnumerator ParseBackgroundAndShowSummary(string backgroundText)
    {
        yield return ParseBackgroundIntoSessionData(backgroundText, overwriteGoalAndPersonality: true);
        SetupSessionData.ValidateAndFillDefaults();
        ShowSummary();
    }

    private IEnumerator ParseBackgroundAndContinue(string backgroundText, string continuePath)
    {
        yield return ParseBackgroundIntoSessionData(backgroundText, overwriteGoalAndPersonality: false);
        pendingInputKey = "";
        inputPanel.SetActive(false);
        story.ChoosePathString(continuePath);
        RefreshUI();
    }

    private IEnumerator ParseBackgroundIntoSessionData(string backgroundText, bool overwriteGoalAndPersonality)
    {
        // Always populate from story first (names, relationship, background, etc.)
        SetupSessionData.PlayerName = story.variablesState["Player_name"]?.ToString() ?? "";
        SetupSessionData.AIName = story.variablesState["AI_name"]?.ToString() ?? "";
        SetupSessionData.Relationship = story.variablesState["Relationship"]?.ToString() ?? "";
        SetupSessionData.PlayerRole = story.variablesState["PlayerRole"]?.ToString() ?? "";
        SetupSessionData.AIRole = story.variablesState["AI_Role"]?.ToString() ?? "";
        SetupSessionData.Background = backgroundText;
        SetupSessionData.SetupMode = story.variablesState["SetupMode"]?.ToString() ?? "general";

        if (HttpClient.Instance == null)
        {
            ApplyParsedSetupToSessionData(null, overwriteGoalAndPersonality);
            yield break;
        }

        var req = new HttpClient.ParseSetupRequest
        {
            player_name = SetupSessionData.PlayerName,
            ai_name = SetupSessionData.AIName,
            relationship = SetupSessionData.Relationship,
            background = backgroundText
        };

        HttpClient.ParseSetupResponse parsed = null;
        string error = null;
        yield return HttpClient.Instance.ParseSetup(req, r => parsed = r, e => error = e);

        if (!string.IsNullOrEmpty(error))
            ApplyParsedSetupToSessionData(null, overwriteGoalAndPersonality);
        else
            ApplyParsedSetupToSessionData(parsed, overwriteGoalAndPersonality);
    }

    private void ApplyParsedSetupToSessionData(HttpClient.ParseSetupResponse parsed, bool overwriteGoalAndPersonality)
    {
        if (parsed == null)
        {
            if (overwriteGoalAndPersonality && string.IsNullOrWhiteSpace(SetupSessionData.AIPersonality)) SetupSessionData.AIPersonality = "defensive";
            if (overwriteGoalAndPersonality && string.IsNullOrWhiteSpace(SetupSessionData.PlayerGoal)) SetupSessionData.PlayerGoal = "persuasion";
            if (overwriteGoalAndPersonality && string.IsNullOrWhiteSpace(SetupSessionData.AIGoal)) SetupSessionData.AIGoal = "persuasion";
            if (string.IsNullOrWhiteSpace(SetupSessionData.PlayerStance)) SetupSessionData.PlayerStance = "The current behavior or situation is not acceptable.";
            if (string.IsNullOrWhiteSpace(SetupSessionData.AIStance)) SetupSessionData.AIStance = "The current behavior or situation is acceptable or justified.";
            SetupSessionData.Goal = SetupSessionData.AIGoal;
            return;
        }
        if (!string.IsNullOrWhiteSpace(parsed.background)) SetupSessionData.Background = parsed.background;
        if (overwriteGoalAndPersonality && !string.IsNullOrWhiteSpace(parsed.ai_personality)) SetupSessionData.AIPersonality = parsed.ai_personality;
        if (overwriteGoalAndPersonality && !string.IsNullOrWhiteSpace(parsed.player_goal)) SetupSessionData.PlayerGoal = parsed.player_goal;
        if (overwriteGoalAndPersonality && !string.IsNullOrWhiteSpace(parsed.ai_goal)) SetupSessionData.AIGoal = parsed.ai_goal;
        if (overwriteGoalAndPersonality && !string.IsNullOrWhiteSpace(parsed.goal) && string.IsNullOrWhiteSpace(SetupSessionData.AIGoal)) SetupSessionData.AIGoal = parsed.goal;
        if (!string.IsNullOrWhiteSpace(parsed.player_stance)) SetupSessionData.PlayerStance = parsed.player_stance;
        if (!string.IsNullOrWhiteSpace(parsed.ai_stance)) SetupSessionData.AIStance = parsed.ai_stance;
        SetupSessionData.Goal = SetupSessionData.AIGoal;
        if (!string.IsNullOrWhiteSpace(parsed.relationship)) SetupSessionData.Relationship = parsed.relationship;
        // For landlord-tenant: keep user's explicit role choice from Ink (e.g. "I'm the landlord").
        // Do NOT overwrite with parse_background's inference—it often swaps them incorrectly.
        bool rolesAlreadyChosen = SetupSessionData.Relationship == "landlord-tenant"
            && !string.IsNullOrWhiteSpace(SetupSessionData.PlayerRole)
            && !string.IsNullOrWhiteSpace(SetupSessionData.AIRole);
        if (!rolesAlreadyChosen)
        {
            if (!string.IsNullOrWhiteSpace(parsed.player_role)) SetupSessionData.PlayerRole = parsed.player_role;
            if (!string.IsNullOrWhiteSpace(parsed.ai_role)) SetupSessionData.AIRole = parsed.ai_role;
        }
        story.variablesState["Background"] = SetupSessionData.Background;
        if (overwriteGoalAndPersonality)
        {
            story.variablesState["AI_Personality"] = SetupSessionData.AIPersonality;
            story.variablesState["Goal"] = SetupSessionData.Goal;
            story.variablesState["PlayerGoal"] = SetupSessionData.PlayerGoal;
            story.variablesState["AIGoal"] = SetupSessionData.AIGoal;
        }
        story.variablesState["PlayerStance"] = SetupSessionData.PlayerStance;
        story.variablesState["AIStance"] = SetupSessionData.AIStance;
        story.variablesState["Relationship"] = SetupSessionData.Relationship;
        if (!string.IsNullOrWhiteSpace(SetupSessionData.PlayerRole))
            story.variablesState["PlayerRole"] = SetupSessionData.PlayerRole;
        if (!string.IsNullOrWhiteSpace(SetupSessionData.AIRole))
            story.variablesState["AI_Role"] = SetupSessionData.AIRole;
    }

    private void ShowSummary()
    {
        if (summaryPanel == null || summaryText == null)
            return;

        SetupSessionData.ValidateAndFillDefaults();

        string shortSummary = BuildShortSummary();

        string roleLine = (!string.IsNullOrWhiteSpace(SetupSessionData.PlayerRole) && !string.IsNullOrWhiteSpace(SetupSessionData.AIRole))
            ? $"Your role: {SetupSessionData.PlayerRole}, AI role: {SetupSessionData.AIRole}\n"
            : "";
        summaryText.text =
            $"Setup Complete\n\n" +
            $"Mode: {SetupSessionData.SetupMode}\n" +
            $"Your name: {SetupSessionData.PlayerName}\n" +
            $"AI name: {SetupSessionData.AIName}\n" +
            $"Relationship: {SetupSessionData.Relationship}\n" +
            roleLine +
            $"AI Personality: {SetupSessionData.AIPersonality}\n" +
            $"Player Goal: {SetupSessionData.PlayerGoal}\n" +
            $"AI Goal: {SetupSessionData.AIGoal}\n" +
            $"Player Stance: {SetupSessionData.PlayerStance}\n" +
            $"AI Stance: {SetupSessionData.AIStance}\n\n" +
            $"Background:\n{SetupSessionData.Background}";

        summaryPanel.SetActive(true);

        // Hide Start Argument initially
        if (startArgumentButton != null)
            startArgumentButton.gameObject.SetActive(false);

        // Hide setup UI
        dialogueText.gameObject.SetActive(false);
        choicesRoot.gameObject.SetActive(false);
        inputPanel.SetActive(false);
    }

    private void OnConfirmSetup()
    {
        if (summaryPanel != null)
            summaryPanel.SetActive(true);

        if (startArgumentButton != null)
            startArgumentButton.gameObject.SetActive(true);
    }

    private void OnEditSetup()
    {
        if (editPanel != null)
        {
            if (editPlayerName != null) editPlayerName.text = SetupSessionData.PlayerName ?? "";
            if (editRelationship != null) editRelationship.text = SetupSessionData.Relationship ?? "";
            if (editBackground != null) editBackground.text = SetupSessionData.Background ?? "";
            if (editAIPersonality != null) editAIPersonality.text = SetupSessionData.AIPersonality ?? "";
            if (editGoal != null) editGoal.text = FormatGoalsForEdit();
            if (editPlayerRole != null) editPlayerRole.text = SetupSessionData.PlayerRole ?? "";
            if (editAIRole != null) editAIRole.text = SetupSessionData.AIRole ?? "";
            if (editPlayerStance != null) editPlayerStance.text = SetupSessionData.PlayerStance ?? "";
            if (editAIStance != null) editAIStance.text = SetupSessionData.AIStance ?? "";
            if (editSetupMode != null) editSetupMode.text = SetupSessionData.SetupMode ?? "general";
            editPanel.SetActive(true);
        }
        else
        {
            SceneManager.LoadScene(SceneManager.GetActiveScene().name);
        }
    }

    private void OnEditPanelApply()
    {
        if (editPlayerName != null && !string.IsNullOrWhiteSpace(editPlayerName.text)) SetupSessionData.PlayerName = editPlayerName.text.Trim();
        if (editRelationship != null && !string.IsNullOrWhiteSpace(editRelationship.text)) SetupSessionData.Relationship = editRelationship.text.Trim();
        if (editBackground != null && !string.IsNullOrWhiteSpace(editBackground.text)) SetupSessionData.Background = editBackground.text.Trim();
        if (editAIPersonality != null && !string.IsNullOrWhiteSpace(editAIPersonality.text)) SetupSessionData.AIPersonality = editAIPersonality.text.Trim();
        if (editGoal != null && !string.IsNullOrWhiteSpace(editGoal.text)) ApplyGoalEditText(editGoal.text);
        if (editPlayerRole != null) SetupSessionData.PlayerRole = editPlayerRole.text?.Trim() ?? "";
        if (editAIRole != null) SetupSessionData.AIRole = editAIRole.text?.Trim() ?? "";
        if (editPlayerStance != null && !string.IsNullOrWhiteSpace(editPlayerStance.text)) SetupSessionData.PlayerStance = editPlayerStance.text.Trim();
        if (editAIStance != null && !string.IsNullOrWhiteSpace(editAIStance.text)) SetupSessionData.AIStance = editAIStance.text.Trim();
        if (editSetupMode != null && !string.IsNullOrWhiteSpace(editSetupMode.text)) SetupSessionData.SetupMode = editSetupMode.text.Trim();
        SetupSessionData.ValidateAndFillDefaults();
        SyncEditDataToStory();
        if (editPanel != null) editPanel.SetActive(false);
        RefreshSummaryText();
    }

    private void OnEditPanelCancel()
    {
        if (editPanel != null) editPanel.SetActive(false);
    }

    private void RefreshSummaryText()
    {
        if (summaryText == null) return;
        string shortSummary = BuildShortSummary();
        string roleLine = (!string.IsNullOrWhiteSpace(SetupSessionData.PlayerRole) && !string.IsNullOrWhiteSpace(SetupSessionData.AIRole))
            ? $"Your role: {SetupSessionData.PlayerRole}, AI role: {SetupSessionData.AIRole}\n"
            : "";
        summaryText.text =
            $"Setup Complete\n\n" +
            $"Mode: {SetupSessionData.SetupMode}\n" +
            $"Your name: {SetupSessionData.PlayerName}\n" +
            $"AI name: {SetupSessionData.AIName}\n" +
            $"Relationship: {SetupSessionData.Relationship}\n" +
            roleLine +
            $"AI Personality: {SetupSessionData.AIPersonality}\n" +
            $"Player Goal: {SetupSessionData.PlayerGoal}\n" +
            $"AI Goal: {SetupSessionData.AIGoal}\n" +
            $"Player Stance: {SetupSessionData.PlayerStance}\n" +
            $"AI Stance: {SetupSessionData.AIStance}\n\n" +
            $"Background:\n{SetupSessionData.Background}";
    }

    private string BuildShortSummary()
    {
        string rolePart = "";
        if (SetupSessionData.Relationship == "landlord-tenant" && !string.IsNullOrWhiteSpace(SetupSessionData.PlayerRole))
            rolePart = $"You are the {SetupSessionData.PlayerRole}, AI is the {SetupSessionData.AIRole}. ";
        return
            $"{rolePart}You are about to argue with a {SetupSessionData.AIPersonality} {SetupSessionData.Relationship}.\n" +
            $"Your goal: {SetupSessionData.PlayerGoal}.\n" +
            $"AI goal: {SetupSessionData.AIGoal}.\n" +
            $"Your current stance: {SetupSessionData.PlayerStance}\n" +
            $"AI current stance: {SetupSessionData.AIStance}";
    }

    private string FormatGoalsForEdit()
    {
        return $"Player goal: {SetupSessionData.PlayerGoal}\nAI goal: {SetupSessionData.AIGoal}";
    }

    private void ApplyGoalEditText(string rawText)
    {
        string text = rawText.Trim();
        string[] lines = text.Split('\n');
        string parsedPlayerGoal = "";
        string parsedAIGoal = "";

        foreach (string rawLine in lines)
        {
            string line = rawLine.Trim();
            if (string.IsNullOrEmpty(line))
                continue;

            string lowered = line.ToLowerInvariant();
            if (lowered.StartsWith("player goal:"))
            {
                parsedPlayerGoal = line.Substring("player goal:".Length).Trim();
            }
            else if (lowered.StartsWith("ai goal:"))
            {
                parsedAIGoal = line.Substring("ai goal:".Length).Trim();
            }
        }

        if (string.IsNullOrWhiteSpace(parsedPlayerGoal) && string.IsNullOrWhiteSpace(parsedAIGoal))
        {
            parsedPlayerGoal = text;
            parsedAIGoal = text;
        }
        else
        {
            if (string.IsNullOrWhiteSpace(parsedPlayerGoal))
                parsedPlayerGoal = SetupSessionData.PlayerGoal;
            if (string.IsNullOrWhiteSpace(parsedAIGoal))
                parsedAIGoal = SetupSessionData.AIGoal;
        }

        SetupSessionData.PlayerGoal = parsedPlayerGoal;
        SetupSessionData.AIGoal = parsedAIGoal;
        SetupSessionData.Goal = SetupSessionData.AIGoal;
    }

    /// <summary>
    /// Sync all edited SetupSessionData back to Ink story variables so data stays consistent.
    /// </summary>
    private void SyncEditDataToStory()
    {
        if (story == null)
            return;
        story.variablesState["Player_name"] = SetupSessionData.PlayerName;
        story.variablesState["Relationship"] = SetupSessionData.Relationship;
        story.variablesState["PlayerRole"] = SetupSessionData.PlayerRole;
        story.variablesState["AI_Role"] = SetupSessionData.AIRole;
        story.variablesState["Background"] = SetupSessionData.Background;
        story.variablesState["AI_Personality"] = SetupSessionData.AIPersonality;
        story.variablesState["Goal"] = SetupSessionData.Goal;
        story.variablesState["PlayerGoal"] = SetupSessionData.PlayerGoal;
        story.variablesState["AIGoal"] = SetupSessionData.AIGoal;
        story.variablesState["PlayerStance"] = SetupSessionData.PlayerStance;
        story.variablesState["AIStance"] = SetupSessionData.AIStance;
        story.variablesState["SetupMode"] = SetupSessionData.SetupMode;
    }

    private void OnStartArgument()
    {
        SetupSessionData.ValidateAndFillDefaults();
        SceneManager.LoadScene(nextSceneName);
    }

    private void ClearChoices()
    {
        if (choicesRoot != null)
        {
            for (int i = choicesRoot.childCount - 1; i >= 0; i--)
                Destroy(choicesRoot.GetChild(i).gameObject);
        }
        if (continueButtonRoot != null)
        {
            for (int i = continueButtonRoot.childCount - 1; i >= 0; i--)
                Destroy(continueButtonRoot.GetChild(i).gameObject);
            continueButtonRoot.gameObject.SetActive(false);
        }
    }

    private void OnUploadDocument()
    {
        FileBrowser.SetFilters(false, new FileBrowser.Filter("PDF", ".pdf"));
        FileBrowser.SetDefaultFilter(".pdf");
        StartCoroutine(ShowFileBrowserAndUpload());
    }

    private IEnumerator ShowFileBrowserAndUpload()
    {
        yield return FileBrowser.WaitForLoadDialog(
            FileBrowser.PickMode.Files,
            false,
            null, null,
            "Select PDF Document",
            "Upload"
        );

        if (!FileBrowser.Success || FileBrowser.Result == null || FileBrowser.Result.Length == 0)
            yield break;

        string path = FileBrowser.Result[0];
        if (uploadStatusText != null)
            uploadStatusText.text = "Uploading...";

        if (HttpClient.Instance == null)
        {
            if (uploadStatusText != null)
                uploadStatusText.text = "Error: no server connection";
            yield break;
        }

        yield return HttpClient.Instance.UploadDocument(
            path,
            resp =>
            {
                uploadedCorpusId = resp.corpus_id;
                if (uploadStatusText != null)
                    uploadStatusText.text = $"Uploaded: {resp.filename}";
                Debug.Log($"Document uploaded: {resp.filename} -> {resp.corpus_id}");
                // Bind corpus to backend session so search_documents retrieves this PDF (not only NSW Act).
                if (GameSessionManager.Instance != null && HttpClient.Instance != null)
                {
                    StartCoroutine(HttpClient.Instance.AttachRagCorpus(
                        GameSessionManager.Instance.SessionId,
                        resp.corpus_id,
                        _ =>
                        {
                            if (uploadStatusText != null)
                                uploadStatusText.text = $"Indexed & linked: {resp.filename}";
                        },
                        _ =>
                        {
                            SetupSessionData.PendingRagCorpusId = resp.corpus_id;
                            if (uploadStatusText != null)
                                uploadStatusText.text = $"Uploaded (will link at match start): {resp.filename}";
                        }
                    ));
                }
                else
                {
                    SetupSessionData.PendingRagCorpusId = resp.corpus_id;
                }
            },
            err =>
            {
                if (uploadStatusText != null)
                    uploadStatusText.text = $"Upload failed: {err}";
                Debug.LogError($"Document upload failed: {err}");
            }
        );
    }
}