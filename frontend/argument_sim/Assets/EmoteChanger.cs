using UnityEngine;
using UnityEngine.UI;

public class EmoteChanger : MonoBehaviour
{
    [System.Serializable]
    public class EmotionSpriteEntry
    {
        public string emotion;
        public Sprite sprite;
    }

    [SerializeField] private SpriteRenderer targetSpriteRenderer;
    [SerializeField] private Image targetImage;
    [SerializeField] private Sprite defaultSprite;
    [SerializeField] private EmotionSpriteEntry[] emotionSprites;

    void Awake()
    {
        if (targetSpriteRenderer == null)
            targetSpriteRenderer = GetComponent<SpriteRenderer>();
        if (targetImage == null)
            targetImage = GetComponent<Image>();
    }

    public void SetEmotion(string emotion)
    {
        string normalized = string.IsNullOrWhiteSpace(emotion) ? "neutral" : emotion.Trim().ToLowerInvariant();
        Sprite chosen = defaultSprite;

        if (emotionSprites != null)
        {
            foreach (EmotionSpriteEntry entry in emotionSprites)
            {
                if (entry != null && entry.sprite != null && !string.IsNullOrWhiteSpace(entry.emotion) &&
                    entry.emotion.Trim().ToLowerInvariant() == normalized)
                {
                    chosen = entry.sprite;
                    break;
                }
            }
        }

        if (chosen == null)
            return;

        if (targetSpriteRenderer != null)
            targetSpriteRenderer.sprite = chosen;
        if (targetImage != null)
            targetImage.sprite = chosen;
    }
}
