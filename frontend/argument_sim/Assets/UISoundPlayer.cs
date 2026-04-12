using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class UISoundPlayer : MonoBehaviour
{
    public static UISoundPlayer Instance;

    private AudioSource audioSource;

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        audioSource = GetComponent<AudioSource>();
    }

    public void PlayClick(AudioClip clip)
    {
        if (clip != null)
            audioSource.PlayOneShot(clip);
    }
}