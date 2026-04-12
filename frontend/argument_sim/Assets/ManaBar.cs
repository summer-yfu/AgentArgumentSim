using System.Collections;
using System.Runtime.CompilerServices;
using UnityEngine;
using UnityEngine.UI;

public class ManaBar : MonoBehaviour
{
    private Image barImage;
    private Mana manaob;

    private void Awake()
    {
        barImage = transform.Find("bar").GetComponent<Image>();

        manaob = new Mana();


    }
    private void Update()
    {
        manaob.Update();
        barImage.fillAmount = manaob.GetManaNormalized();
    }


}

public class Mana
{
    public const int MANA_MAX = 100;

    private float manaAmount;

    private float manaRegenAmount;

    public Mana()
    {
        manaAmount = 0;
        manaRegenAmount = 30f;
    }

    public void Update()
    {
        manaAmount += manaRegenAmount * Time.deltaTime;
        manaAmount = Mathf.Clamp(manaAmount, 0f, MANA_MAX);
    }

    public void TrySpendMana(int amount)
    {
        if (manaAmount >= amount)
        {
            manaAmount -= amount;
        }
    }


    public float GetManaNormalized()
    {
        return manaAmount / MANA_MAX;
    }
}