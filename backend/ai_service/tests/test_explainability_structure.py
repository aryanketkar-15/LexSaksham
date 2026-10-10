def test_attention_explain_structure():
    from utils.explainability_utils import attention_explain
    res = attention_explain("Test clause.")
    assert isinstance(res, dict)
    assert "tokens" in res and isinstance(res["tokens"], list)
    assert "importance" in res and isinstance(res["importance"], list)
    assert res["method"] == "attention"

def test_lime_explain_structure():
    from utils.explainability_utils import lime_explain
    res = lime_explain("Test clause.")
    assert isinstance(res, dict)
    assert "tokens" in res and isinstance(res["tokens"], list)
    assert "importance" in res and isinstance(res["importance"], list)
    assert res["method"] == "lime"

def test_shap_explain_structure():
    from utils.explainability_utils import shap_explain
    res = shap_explain("Test clause.")
    assert isinstance(res, dict)
    assert "tokens" in res and isinstance(res["tokens"], list)
    assert "importance" in res and isinstance(res["importance"], list)
    assert res["method"] == "shap"
