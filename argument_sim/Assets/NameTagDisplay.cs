using TMPro;
using UnityEngine;

public class NameTagDisplay : MonoBehaviour
{
    [SerializeField] private TMP_Text nameText;
    [SerializeField] private bool isPlayerName = true;

    void OnEnable()
    {
        if (nameText == null) return;
        SetupSessionData.ValidateAndFillDefaults();
        nameText.text = isPlayerName ? SetupSessionData.PlayerName : SetupSessionData.AIName;
    }
}
