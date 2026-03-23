using TMPro;
using UnityEngine;

public class MessageItem : MonoBehaviour
{
    public TMP_Text myMessage;

    void Awake()
    {
        if (myMessage == null)
            myMessage = GetComponentInChildren<TMP_Text>();
    }

    public void SetText(string text)
    {
        if (myMessage != null)
            myMessage.text = text;
    }

    public void SetColor(Color color)
    {
        if (myMessage != null)
            myMessage.color = color;
    }
}