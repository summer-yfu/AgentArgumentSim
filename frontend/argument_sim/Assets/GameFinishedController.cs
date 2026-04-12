using System;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Controls the Game Finished popup. Assign this to the panel that shows when the match ends.
/// Buttons: Restart (→ main menu), Quit, Download chat history.
/// </summary>
public class GameFinishedController : MonoBehaviour
{
    [Header("UI References")]
    public GameObject panel;
    public TMP_Text titleText;
    public TMP_Text reasonText;
    public Button restartButton;
    public Button quitButton;
    public Button downloadButton;

    [Header("Scene to load on Restart (main menu)")]
    public int mainMenuSceneBuildIndex = 0;

    void Awake()
    {
        if (panel != null) panel.SetActive(false);
        if (restartButton != null) restartButton.onClick.AddListener(OnRestart);
        if (quitButton != null) quitButton.onClick.AddListener(OnQuit);
        if (downloadButton != null) downloadButton.onClick.AddListener(OnDownload);
    }

    public void Show(string stopReason = "")
    {
        if (panel != null) panel.SetActive(true);
        if (titleText != null) titleText.text = "Game Finished";
        if (reasonText != null)
        {
            reasonText.text = stopReason switch
            {
                "toxicity" => "The exchange became too heated. The match has been stopped.",
                "repetition" => "The conversation got stuck in repetition. The match has been stopped.",
                "goal_reached" => "A goal has been reached. The match has ended.",
                "max_rounds" => "Maximum rounds (30) reached. The match has ended.",
                "player_requested" => "You chose to end the match.",
                _ => "The match has ended."
            };
        }
    }

    public void Hide()
    {
        if (panel != null) panel.SetActive(false);
    }

    void OnRestart()
    {
        Hide();
        SceneManager.LoadScene(mainMenuSceneBuildIndex);
    }

    void OnQuit()
    {
        Application.Quit();
    }

    void OnDownload()
    {
        if (HttpClient.Instance != null)
            HttpClient.Instance.DownloadChatHistory();
    }
}
