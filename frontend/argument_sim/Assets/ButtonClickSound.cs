using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(Button))]
public class ButtonClickSound : MonoBehaviour
{
    public AudioClip clickClip;

    void Awake()
    {
        GetComponent<Button>().onClick.AddListener(PlaySound);
    }

    void PlaySound()
    {
        if (clickClip != null && UISoundPlayer.Instance != null)
        {
            Debug.Log("Playing click sound");
            UISoundPlayer.Instance.PlayClick(clickClip);
        }
    }
}