using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Toxicity bar (match status). Uses a fill Image (Background + bar pair).
/// Assign barImage in Inspector to the fill Image, or it auto-finds child named "bar".
/// Bar's Image must be Type: Filled, Fill Method: Horizontal, Fill Origin: Left.
/// </summary>
public class ToxicityBar : MonoBehaviour
{
    [Tooltip("The fill Image (red part). Assign in Inspector or leave null to auto-find child named 'bar'.")]
    [SerializeField] private Image barImage;

    private void Awake()
    {
        if (barImage == null)
        {
            var bar = transform.Find("bar");
            if (bar == null) bar = transform.Find("Bar");
            if (bar != null)
                barImage = bar.GetComponent<Image>();
        }
        if (barImage == null)
        {
            Debug.LogWarning("ToxicityBar: No fill Image found. Assign barImage in Inspector or add child named 'bar' with Image component.");
            return;
        }
        // Ensure Image uses Filled type so fillAmount works (Background + bar = pair of images)
        if (barImage.type != Image.Type.Filled)
        {
            barImage.type = Image.Type.Filled;
            barImage.fillMethod = Image.FillMethod.Horizontal;
            barImage.fillOrigin = (int)Image.OriginHorizontal.Left;
        }
        SetValue(0f); // Start empty before first turn
    }

    void Start()
    {
        SetValue(0f);
    }

    /// <summary>Set bar fill (0 = empty, 1 = full). Clamped to 0..1.</summary>
    public void SetValue(float normalized)
    {
        if (barImage != null)
            barImage.fillAmount = Mathf.Clamp01(normalized);
    }
}
