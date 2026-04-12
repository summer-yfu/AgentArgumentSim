using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;
using Ink.Runtime;
public class DialogueManager: MonoBehaviour
{
    [Header("Dialogue UI")]

    [SerializeField] private GameObject dialoguePanel;
    private static DialogueManager  instance;

    [SerializeField] private TMP_Text dialogueText;

    private Story currentStory;
    private bool dialogueisplaying;
    private void Awake()
    {
        if (instance!= null)
        {
            Debug.LogWarning("WARNING WARNING WARNING, dialogue manager already exist in scene.");
        }
        instance = this;
    }

    private void Update()
    {
        if (!dialogueisplaying)
        {
            return;
        }
        if (InputManager.GetInstance().GetSubmitPressed())
        {
            ContinueStory();
        }
    } 
    public static DialogueManager GetInstance()
    {
        return instance;
    }

    private void Start()
    {
        dialogueisplaying = false;
        dialoguePanel.SetActive(false);
    }

    public void EnterDialogueMode(TextAsset inkJSON)
    {
        currentStory = new Story(inkJSON.text);
        dialogueisplaying = true;
        dialoguePanel.SetActive(true);


    }

    private void ExitDialogueMode () {
        dialogueisplaying = false;
        dialoguePanel.SetActive(false);
        dialogueText.text = "";
    }
    private void ContinueStory()
    {
        if (currentStory.canContinue)
        {
            dialogueText.text = currentStory.Continue();
        }
        else
        {
            ExitDialogueMode();
        }
    }

}