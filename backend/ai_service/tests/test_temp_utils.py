def test_load_temperature_default():
    from utils.temp_utils import load_temperature
    assert isinstance(load_temperature(), float)

def test_load_temperature_file(tmp_path):
    import json
    from utils.temp_utils import T_PATH, load_temperature
    temp_file = tmp_path / "temperature.json"
    temp_file.write_text(json.dumps({"temperature": 0.5}))
    # Patch T_PATH for test
    import utils.temp_utils
    utils.temp_utils.T_PATH = temp_file
    assert load_temperature() == 0.5
