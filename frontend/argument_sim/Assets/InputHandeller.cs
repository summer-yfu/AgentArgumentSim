using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
public class InputHandeller : MonoBehaviour
{
    // Start is called before the first frame update
    [SerializeField] TMP_InputField inputField;


    public void ValidateInput()
    {
        string input = inputField.text;

    }

}
