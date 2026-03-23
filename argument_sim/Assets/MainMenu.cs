using System;
using System.Collections;
using System.Collections.Generic;
using JetBrains.Annotations;
using UnityEngine;
using UnityEngine.SceneManagement;
public class MainMenu : MonoBehaviour
{   
    public int secenenumber;
    public void PlayGame()
    {
        // load secne index 1 

        SceneManager.LoadSceneAsync(secenenumber);
    }

    public void QuitGame()
    {   
        Debug.Log("Quit pressed");
        Application.Quit();
        
    }
}
